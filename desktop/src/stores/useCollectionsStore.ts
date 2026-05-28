import { create } from "zustand";
import type { FavoriteItem } from "../types";
import { api } from "../utils/api-client";

/** 收藏页面状态接口 */
interface CollectionsState {
  /** 收藏列表 */
  favorites: FavoriteItem[];
  /** 是否加载中 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;

  /** 获取收藏列表 */
  fetchFavorites: () => Promise<void>;
  /** 收藏项目 */
  star: (fullName: string) => Promise<boolean>;
  /** 取消收藏 */
  unstar: (fullName: string) => Promise<boolean>;
  /** 检查是否已收藏 */
  isStarred: (fullName: string) => boolean;
}

/**
 * Zustand store：管理收藏列表状态。
 * 调用 api.getFavorites()/starRepo()/unstarRepo()。
 */
export const useCollectionsStore = create<CollectionsState>((set, get) => ({
  favorites: [],
  loading: false,
  error: null,

  fetchFavorites: async () => {
    set({ loading: true, error: null });
    try {
      const response = await api.getFavorites();
      set({
        favorites: response.items ?? [],
        loading: false,
      });
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : "获取收藏列表失败",
      });
    }
  },

  star: async (fullName: string) => {
    try {
      await api.starRepo(fullName);
      // 重新拉取列表以获取最新数据
      await get().fetchFavorites();
      return true;
    } catch {
      set({ error: "收藏失败，请重试" });
      return false;
    }
  },

  unstar: async (fullName: string) => {
    try {
      await api.unstarRepo(fullName);
      // 从本地列表中移除
      set((state) => ({
        favorites: state.favorites.filter((f) => f.full_name !== fullName),
      }));
      return true;
    } catch {
      set({ error: "取消收藏失败，请重试" });
      return false;
    }
  },

  isStarred: (fullName: string) => {
    return get().favorites.some((f) => f.full_name === fullName);
  },
}));
