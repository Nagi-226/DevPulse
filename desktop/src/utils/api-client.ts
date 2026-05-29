import type {
  Repo,
  WeeklyReport,
  SearchResult,
  FavoriteItem,
  StarHistoryResponse,
  LanguageStat,
  Comment,
  LikeInfo,
  InteractionStats,
  RecommendationResponse,
  DashboardData,
  AdminUser,
  PendingReview,
} from "../types";
import { getTrendingCache, setTrendingCache, getDetailCache, setDetailCache } from "./cache";

function detectBaseUrl(): string {
  if (
    typeof import.meta !== "undefined" &&
    (import.meta as any).env?.VITE_API_BASE
  ) {
    return (import.meta as any).env.VITE_API_BASE;
  }
  if (typeof window !== "undefined") {
    const win = window as any;
    if (win.__TAURI_INTERNALS__) {
      return "http://127.0.0.1:8000";
    }
  }
  return "/api/v1";
}

const BASE_URL = detectBaseUrl();

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
  fromCache?: boolean;
  pagination?: {
    page: number;
    page_size: number;
    total: number;
  };
}

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

function getAccessToken(): string | null {
  try {
    return localStorage.getItem("devpulse_access_token");
  } catch {
    return null;
  }
}

function getRefreshToken(): string | null {
  try {
    return localStorage.getItem("devpulse_refresh_token");
  } catch {
    return null;
  }
}

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

async function request<T>(
  endpoint: string,
  options?: RequestInit,
  maxRetries = 5,
  retryDelayMs = 1000,
): Promise<T & { fromCache?: boolean }> {
  const url = `${BASE_URL}${endpoint}`;
  let lastError: unknown;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  const token = getAccessToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (response.status === 401 && token) {
        const newToken = await tryRefreshToken();
        if (newToken) {
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

      await cacheResponse(endpoint, options, data);

      return data as T & { fromCache?: boolean };
    } catch (err) {
      lastError = err;
      if (err instanceof ApiError) {
        break;
      }
      if (attempt < maxRetries) {
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
      }
    }
  }

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
      !endpoint.includes("/stats") &&
      !endpoint.includes("/comments") &&
      !endpoint.includes("/recommended")
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
      !endpoint.includes("/stats") &&
      !endpoint.includes("/comments") &&
      !endpoint.includes("/recommended")
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

  getRepo: (owner: string, repo: string) =>
    request<Repo>(`/repos/${encodeURIComponent(owner + "/" + repo)}`),

  getWeeklyReports: (limit = 10) =>
    request<FlatListResponse<WeeklyReport>>(
      `/repos/weekly-reports?limit=${limit}`,
    ),

  getWeeklyReport: (reportId: number) =>
    request<WeeklyReport>(`/repos/weekly-reports/${reportId}`),

  triggerCrawl: (language = "", since = "weekly", source = "github") =>
    request<{ message: string }>(
      `/repos/crawl?language=${language}&since=${since}&source=${source}`,
      { method: "POST" },
    ),

  getSchedulerJobs: () =>
    request<Array<{ id: string; name: string; next_run: string | null }>>(
      "/scheduler/jobs",
    ),

  search: (
    keyword: string,
    language: string = "",
    page: number = 1,
    pageSize: number = 25,
  ) =>
    request<SearchResult>(
      `/repos/?q=${encodeURIComponent(keyword)}&language=${encodeURIComponent(language)}&page=${page}&page_size=${pageSize}`,
    ),

  starRepo: (fullName: string) =>
    request<{ message: string; repo_id: number }>(
      `/repos/${encodeURIComponent(fullName)}/star`,
      { method: "POST" },
    ),

  unstarRepo: (fullName: string) =>
    request<{ message: string }>(
      `/repos/${encodeURIComponent(fullName)}/star`,
      { method: "DELETE" },
    ),

  getFavorites: (page: number = 1, pageSize: number = 25) =>
    request<FlatListResponse<FavoriteItem>>(
      `/repos/collections?page=${page}&page_size=${pageSize}`,
    ),

  getStarHistory: (fullName: string, period: string = "30d") =>
    request<{ items: StarHistoryResponse[] }>(
      `/repos/${encodeURIComponent(fullName)}/star-history?period=${period}`,
    ),

  getLanguageStats: () =>
    request<FlatListResponse<LanguageStat>>("/repos/stats/languages"),

  // ── 认证 ────────────────────────────────────────
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

  getMe: () => request<Record<string, unknown>>("/auth/me"),

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

  updateFcmToken: (fcmToken: string) =>
    request<{ message: string }>("/auth/fcm-token", {
      method: "PUT",
      body: JSON.stringify({ fcm_token: fcmToken }),
    }),

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

  // ── Phase 4: 互动 ──────────────────────────────
  getComments: (fullName: string, page = 1, pageSize = 20) =>
    request<FlatListResponse<Comment>>(
      `/repos/${encodeURIComponent(fullName)}/comments?page=${page}&page_size=${pageSize}`,
    ),

  postComment: (fullName: string, content: string, parentId?: number) =>
    request<Comment>(
      `/repos/${encodeURIComponent(fullName)}/comments`,
      {
        method: "POST",
        body: JSON.stringify({ content, parent_id: parentId || null }),
      },
    ),

  deleteComment: (fullName: string, commentId: number) =>
    request<{ deleted: boolean }>(
      `/repos/${encodeURIComponent(fullName)}/comments/${commentId}`,
      { method: "DELETE" },
    ),

  toggleLike: (fullName: string) =>
    request<LikeInfo>(
      `/repos/${encodeURIComponent(fullName)}/like`,
      { method: "POST" },
    ),

  getLikesCount: (fullName: string) =>
    request<{ likes_count: number; is_liked: boolean }>(
      `/repos/${encodeURIComponent(fullName)}/likes-count`,
    ),

  getInteractions: (fullName: string) =>
    request<InteractionStats>(
      `/repos/${encodeURIComponent(fullName)}/interactions`,
    ),

  // ── Phase 4: 推荐 ──────────────────────────────
  getRecommended: (limit = 10) =>
    request<RecommendationResponse>(
      `/repos/recommended?limit=${limit}`,
    ),

  // ── Phase 4: Admin ─────────────────────────────
  getDashboard: (days = 30) =>
    request<DashboardData>(
      `/admin/dashboard?days=${days}`,
    ),

  getAdminUsers: (page = 1, pageSize = 25, q = "") =>
    request<FlatListResponse<AdminUser>>(
      `/admin/users?page=${page}&page_size=${pageSize}&q=${encodeURIComponent(q)}`,
    ),

  toggleUserBan: (userId: number, banned: boolean) =>
    request<{ user_id: number; is_active: boolean }>(
      `/admin/users/${userId}/ban`,
      {
        method: "PUT",
        body: JSON.stringify({ banned }),
      },
    ),

  updateUserRole: (userId: number, role: string) =>
    request<{ user_id: number; role: string }>(
      `/admin/users/${userId}/role`,
      {
        method: "PUT",
        body: JSON.stringify({ role }),
      },
    ),

  getPendingReviews: (page = 1, pageSize = 25) =>
    request<FlatListResponse<PendingReview>>(
      `/admin/pending-reviews?page=${page}&page_size=${pageSize}`,
    ),

  approveReview: (repoId: number) =>
    request<{ repo_id: number; review_status: string; message: string }>(
      `/admin/approve/${repoId}`,
      { method: "POST" },
    ),

  rejectReview: (repoId: number) =>
    request<{ repo_id: number; review_status: string; message: string }>(
      `/admin/reject/${repoId}`,
      { method: "POST" },
    ),

  adminTriggerCrawl: (language = "", since = "weekly", source = "github") =>
    request<{ language: string; since: string; source: string }>(
      `/admin/trigger-crawl?language=${language}&since=${since}&source=${source}`,
      { method: "POST" },
    ),
};

export { ApiError };
