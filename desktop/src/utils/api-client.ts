import type {
  Repo,
  WeeklyReport,
  SearchResult,
  FavoriteItem,
  StarHistoryResponse,
  LanguageStat,
} from "../types";
import { getTrendingCache, setTrendingCache, getDetailCache, setDetailCache } from "./cache";

/**
 * 多端 API 基地址检测，按优先级：
 * 1. VITE_API_BASE 环境变量（移动端/鸿蒙/自定义生产环境）
 * 2. Tauri 桌面生产环境 → 直连本地后端 http://127.0.0.1:8000
 * 3. Vite 开发服务器          → /api/v1（走 Vite 代理）
 *
 * 注意：后端路由无 /api/v1 前缀，仅在 Vite dev 中用它做代理标识。
 */
function detectBaseUrl(): string {
  // 优先级 1: 环境变量（移动端 Capacitor / 鸿蒙 WebView / 自定义构建）
  if (
    typeof import.meta !== "undefined" &&
    (import.meta as any).env?.VITE_API_BASE
  ) {
    return (import.meta as any).env.VITE_API_BASE;
  }
  // 优先级 2: Tauri 生产环境
  if (typeof window !== "undefined") {
    const win = window as any;
    if (win.__TAURI_INTERNALS__) {
      return "http://127.0.0.1:8000";
    }
  }
  // 优先级 3: Vite 开发代理
  return "/api/v1";
}

const BASE_URL = detectBaseUrl();

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  /** 是否来自离线缓存 */
  fromCache?: boolean;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
  };
}

/** 扁平列表响应格式（后端实际使用） */
interface FlatListResponse<T> {
  total: number;
  page?: number;
  limit?: number;
  page_size?: number;
  items: T[];
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * 获取存储在 localStorage 中的 JWT access token.
 */
function getAccessToken(): string | null {
  try {
    return localStorage.getItem("devpulse_access_token");
  } catch {
    return null;
  }
}

/**
 * 获取存储在 localStorage 中的 JWT refresh token.
 */
function getRefreshToken(): string | null {
  try {
    return localStorage.getItem("devpulse_refresh_token");
  } catch {
    return null;
  }
}

/**
 * 尝试刷新 access token（静默刷新）。
 * 成功返回新的 access token，失败返回 null。
 */
async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) return null;

    const data = await response.json();
    const newAccess = data.access_token;
    const newRefresh = data.refresh_token;

    if (newAccess) {
      try {
        localStorage.setItem("devpulse_access_token", newAccess);
        if (newRefresh) {
          localStorage.setItem("devpulse_refresh_token", newRefresh);
        }
      } catch {
        // localStorage 不可用
      }
      return newAccess;
    }
  } catch {
    // 刷新失败
  }
  return null;
}

/**
 * 带缓存层 + 重试 + JWT 认证的请求函数。
 *
 * 流程：
 * 1. 自动附加 Authorization: Bearer <token>
 * 2. 发送网络请求
 * 3. 成功 → 将响应存入 Dexie 缓存 + 返回数据
 * 4. 401 → 尝试 refresh token → 重试原请求
 * 5. 失败 → 尝试从 Dexie 缓存读取 fallback 数据
 */
async function request<T>(
  endpoint: string,
  options?: RequestInit,
  maxRetries = 5,
  retryDelayMs = 1000,
): Promise<T & { fromCache?: boolean }> {
  const url = `${BASE_URL}${endpoint}`;
  let lastError: unknown;

  // ── 构建请求头（自动附加 JWT）──────────────
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // ── 网络请求（含重试）──────────────────────
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // ── 401 → 尝试 refresh token ──────────
      if (response.status === 401 && token) {
        const newToken = await tryRefreshToken();
        if (newToken) {
          // 用新 token 重试
          headers["Authorization"] = `Bearer ${newToken}`;
          const retryResponse = await fetch(url, {
            ...options,
            headers,
          });
          if (retryResponse.ok) {
            const data = await retryResponse.json();
            await cacheResponse(endpoint, options, data);
            return data as T & { fromCache?: boolean };
          }
        }
        // refresh 也失败，清除 token，触发重新登录
        try {
          localStorage.removeItem("devpulse_access_token");
          localStorage.removeItem("devpulse_refresh_token");
        } catch {
          // silent
        }
        throw new ApiError(401, "认证已过期，请重新登录");
      }

      if (!response.ok) {
        throw new ApiError(
          response.status,
          `API error: ${response.statusText}`,
        );
      }
      const data = await response.json();

      // ── 写入缓存（仅 GET 请求）─────────────
      await cacheResponse(endpoint, options, data);

      return data as T & { fromCache?: boolean };
    } catch (err) {
      lastError = err;
      if (err instanceof ApiError) {
        // 4xx/5xx 不重试（除了 401 已处理）
        break;
      }
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
      }
    }
  }

  // ── 网络失败 → 尝试离线缓存 ───────────────
  try {
    const cached = await getCachedResponse(endpoint);
    if (cached) {
      return { ...cached as Record<string, unknown>, fromCache: true } as unknown as T & { fromCache?: boolean };
    }
  } catch {
    // 缓存读取失败
  }

  throw lastError;
}

/** 缓存 GET 响应 */
async function cacheResponse(
  endpoint: string,
  options: RequestInit | undefined,
  data: unknown,
): Promise<void> {
  if (options?.method && options.method !== "GET") return;
  try {
    if (endpoint.startsWith("/repos/trending")) {
      const urlParams = new URLSearchParams(endpoint.split("?")[1] || "");
      const since = urlParams.get("since") || "weekly";
      const language = urlParams.get("language") || "";
      await setTrendingCache(since, language, data);
    } else if (
      endpoint.includes("/repos/") &&
      !endpoint.includes("/trending") &&
      !endpoint.includes("/collections") &&
      !endpoint.includes("/stats")
    ) {
      const match = endpoint.match(/\/repos\/([^/?]+)/);
      if (match && match[1]) {
        await setDetailCache(match[1], data);
      }
    }
  } catch {
    // 缓存写入失败不阻塞
  }
}

/** 读取离线缓存 */
async function getCachedResponse(endpoint: string): Promise<unknown | null> {
  try {
    if (endpoint.startsWith("/repos/trending")) {
      const urlParams = new URLSearchParams(endpoint.split("?")[1] || "");
      const since = urlParams.get("since") || "weekly";
      const language = urlParams.get("language") || "";
      return await getTrendingCache(since, language);
    } else if (
      endpoint.includes("/repos/") &&
      !endpoint.includes("/trending") &&
      !endpoint.includes("/collections") &&
      !endpoint.includes("/stats")
    ) {
      const match = endpoint.match(/\/repos\/([^/?]+)/);
      if (match && match[1]) {
        return await getDetailCache(match[1]);
      }
    }
  } catch {
    // silent
  }
  return null;
}

export const api = {
  /** 获取 Trending 仓库列表 */
  getTrending: (since = "weekly", language = "", source = "github", page = 1, pageSize = 25) =>
    request<FlatListResponse<Repo>>(
      `/repos/trending?since=${since}&language=${language}&source=${source}&page=${page}&page_size=${pageSize}`,
    ),

  /** 获取单个仓库详情 */
  getRepo: (owner: string, repo: string) =>
    request<Repo>(`/repos/${encodeURIComponent(owner + "/" + repo)}`),

  /** 获取周报列表 */
  getWeeklyReports: (limit = 10) =>
    request<FlatListResponse<WeeklyReport>>(
      `/repos/weekly-reports?limit=${limit}`,
    ),

  /** 获取单个周报 */
  getWeeklyReport: (reportId: number) =>
    request<WeeklyReport>(`/repos/weekly-reports/${reportId}`),

  /** 触发爬虫 */
  triggerCrawl: (language = "", since = "weekly", source = "github") =>
    request<{ message: string }>(
      `/repos/crawl?language=${language}&since=${since}&source=${source}`,
      { method: "POST" },
    ),

  /** 调度器状态 */
  getSchedulerJobs: () =>
    request<Array<{ id: string; name: string; next_run: string | null }>>(
      "/scheduler/jobs",
    ),

  // ── 搜索 ────────────────────────────────────────

  /** 搜索仓库（按名称/描述/标签） */
  search: (
    keyword: string,
    language: string = "",
    page: number = 1,
    pageSize: number = 25,
  ) =>
    request<SearchResult>(
      `/repos/?q=${encodeURIComponent(keyword)}&language=${encodeURIComponent(language)}&page=${page}&page_size=${pageSize}`,
    ),

  // ── 收藏 ────────────────────────────────────────

  /** 收藏仓库 */
  starRepo: (fullName: string) =>
    request<{ message: string; repo_id: number }>(
      `/repos/${encodeURIComponent(fullName)}/star`,
      { method: "POST" },
    ),

  /** 取消收藏仓库 */
  unstarRepo: (fullName: string) =>
    request<{ message: string }>(
      `/repos/${encodeURIComponent(fullName)}/star`,
      { method: "DELETE" },
    ),

  /** 获取收藏列表 */
  getFavorites: (page: number = 1, pageSize: number = 25) =>
    request<FlatListResponse<FavoriteItem>>(
      `/repos/collections?page=${page}&page_size=${pageSize}`,
    ),

  // ── 趋势与统计 ──────────────────────────────────

  /** 获取仓库 Star 历史趋势（30 天） */
  getStarHistory: (fullName: string, period: string = "30d") =>
    request<{ items: StarHistoryResponse[] }>(
      `/repos/${encodeURIComponent(fullName)}/star-history?period=${period}`,
    ),

  /** 获取语言分布统计 */
  getLanguageStats: () =>
    request<FlatListResponse<LanguageStat>>("/repos/stats/languages"),

  // ── 认证 ────────────────────────────────────────

  /** 用户注册 */
  register: (email: string, password: string, confirmPassword: string, displayName?: string) =>
    request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
      user: Record<string, unknown>;
    }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        confirm_password: confirmPassword,
        display_name: displayName,
      }),
    }),

  /** 用户登录 */
  login: (email: string, password: string) =>
    request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
      user: Record<string, unknown>;
    }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  /** 获取当前用户信息 */
  getMe: () => request<Record<string, unknown>>("/auth/me"),

  /** 刷新 Token */
  refreshToken: (refreshToken: string) =>
    request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
    }>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  /** 更新 FCM Token */
  updateFcmToken: (fcmToken: string) =>
    request<{ message: string }>("/auth/fcm-token", {
      method: "PUT",
      body: JSON.stringify({ fcm_token: fcmToken }),
    }),

  /** 更新推送偏好 */
  updatePreferences: (prefs: {
    push_enabled?: boolean;
    push_weekly_report?: boolean;
    push_important_project?: boolean;
  }) =>
    request<{
      push_enabled: boolean;
      push_weekly_report: boolean;
      push_important_project: boolean;
    }>("/auth/preferences", {
      method: "PUT",
      body: JSON.stringify(prefs),
    }),
};

export { ApiError };
