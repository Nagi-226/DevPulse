import { create } from "zustand";
import type { User, AuthResponse } from "../types";
import { api } from "../utils/api-client";

/** localStorage keys */
const ACCESS_TOKEN_KEY = "devpulse_access_token";
const REFRESH_TOKEN_KEY = "devpulse_refresh_token";
const USER_KEY = "devpulse_user";

/**
 * 从 localStorage 读取持久化的用户和 Token.
 */
function loadPersistedState(): { user: User | null; token: string | null; refreshToken: string | null } {
  try {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    const user = userStr ? (JSON.parse(userStr) as User) : null;
    return { user, token, refreshToken };
  } catch {
    return { user: null, token: null, refreshToken: null };
  }
}

/**
 * 持久化认证状态到 localStorage.
 */
function persistState(token: string, refreshToken: string, user: User): void {
  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, token);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // localStorage 不可用
  }
}

/**
 * 清除 localStorage 中的认证状态.
 */
function clearPersistedState(): void {
  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {
    // silent
  }
}

/** 认证 Store 接口 */
interface AuthState {
  /** 当前用户 */
  user: User | null;
  /** 是否加载中 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** JWT access token */
  token: string | null;
  /** JWT refresh token */
  refreshToken: string | null;
  /** 是否已登录 */
  isAuthenticated: boolean;

  /** 用户注册 */
  register: (email: string, password: string, confirmPassword: string, displayName?: string) => Promise<boolean>;
  /** 用户登录 */
  login: (email: string, password: string) => Promise<boolean>;
  /** 退出登录 */
  logout: () => void;
  /** 刷新 Token */
  refreshTokenAction: () => Promise<boolean>;
  /** 获取当前用户信息 */
  fetchUser: () => Promise<void>;
  /** 清除错误 */
  clearError: () => void;
}

/**
 * Zustand Store：管理用户认证状态。
 *
 * 功能：
 * - 注册/登录/退出
 * - Token 自动持久化到 localStorage
 * - 页面刷新后自动恢复登录态
 * - 401 自动刷新 Token
 */
export const useAuthStore = create<AuthState>((set, get) => {
  const persisted = loadPersistedState();

  return {
    user: persisted.user,
    token: persisted.token,
    refreshToken: persisted.refreshToken,
    isAuthenticated: !!persisted.token && !!persisted.user,
    loading: false,
    error: null,

    register: async (email, password, confirmPassword, displayName?) => {
      set({ loading: true, error: null });
      try {
        const response = await api.register(email, password, confirmPassword, displayName);
        const authResp = response as unknown as AuthResponse;

        persistState(authResp.access_token, authResp.refresh_token, authResp.user);
        set({
          user: authResp.user,
          token: authResp.access_token,
          refreshToken: authResp.refresh_token,
          isAuthenticated: true,
          loading: false,
        });
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : "注册失败，请重试";
        set({ loading: false, error: message });
        return false;
      }
    },

    login: async (email, password) => {
      set({ loading: true, error: null });
      try {
        const response = await api.login(email, password);
        const authResp = response as unknown as AuthResponse;

        persistState(authResp.access_token, authResp.refresh_token, authResp.user);
        set({
          user: authResp.user,
          token: authResp.access_token,
          refreshToken: authResp.refresh_token,
          isAuthenticated: true,
          loading: false,
        });
        return true;
      } catch (err) {
        const message = err instanceof Error ? err.message : "登录失败，请重试";
        set({ loading: false, error: message });
        return false;
      }
    },

    logout: () => {
      clearPersistedState();
      set({
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null,
      });
    },

    refreshTokenAction: async () => {
      const { refreshToken } = get();
      if (!refreshToken) return false;

      try {
        const response = await api.refreshToken(refreshToken);
        const data = response as unknown as {
          access_token: string;
          refresh_token: string;
        };

        try {
          localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token);
          localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token);
        } catch {
          // silent
        }

        set({
          token: data.access_token,
          refreshToken: data.refresh_token,
        });
        return true;
      } catch {
        // Refresh 失败，清除登录态
        const { logout } = get();
        logout();
        return false;
      }
    },

    fetchUser: async () => {
      try {
        const userData = await api.getMe();
        const user = userData as unknown as User;
        set({ user });
        try {
          localStorage.setItem(USER_KEY, JSON.stringify(user));
        } catch {
          // silent
        }
      } catch {
        // 获取用户信息失败，可能 token 过期
        // 不主动清除登录态，等待 401 处理
      }
    },

    clearError: () => set({ error: null }),
  };
});
