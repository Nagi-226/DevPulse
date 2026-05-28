import { create } from "zustand";
import type { Repo, TrendingSource } from "../types";
import { api } from "../utils/api-client";

/** Trending 页面状态接口 */
interface TrendingState {
  repos: Repo[];
  loading: boolean;
  error: string | null;
  language: string;
  since: "daily" | "weekly" | "monthly";
  source: TrendingSource;
  useApi: boolean;

  /** 获取 Trending 数据 */
  fetchTrending: () => Promise<void>;
  setLanguage: (lang: string) => void;
  setSince: (since: "daily" | "weekly" | "monthly") => void;
  setSource: (source: TrendingSource) => void;
  setUseApi: (useApi: boolean) => void;
}

/**
 * Zustand store：管理 Trending 列表的数据状态。
 *
 * 支持多数据源（GitHub/GitLab/Gitee）和语言筛选。
 */
export const useTrendingStore = create<TrendingState>((set, get) => ({
  repos: [],
  loading: false,
  error: null,
  language: "",
  since: "weekly",
  source: "github",
  useApi: true,

  fetchTrending: async () => {
    const { since, language, source, useApi } = get();
    set({ loading: true, error: null });

    try {
      if (useApi) {
        const langParam = language || "";
        const response = await api.getTrending(since, langParam, source);
        const items = (response as unknown as { items: Repo[] }).items ?? [];
        set({ repos: items, loading: false });
      }
      // 不使用 API 时由 mock 逻辑处理（如有需要可回退到旧 mock）
    } catch {
      set({
        loading: false,
        error: "API 连接失败，请检查网络后重试",
      });
    }
  },

  setLanguage: (lang: string) => set({ language: lang }),
  setSince: (since: "daily" | "weekly" | "monthly") => {
    set({ since });
    useTrendingStore.getState().fetchTrending();
  },
  setSource: (source: TrendingSource) => {
    set({ source });
    useTrendingStore.getState().fetchTrending();
  },
  setUseApi: (useApi: boolean) => {
    set({ useApi });
    useTrendingStore.getState().fetchTrending();
  },
}));
