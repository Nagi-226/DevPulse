import { create } from "zustand";
import type { Repo } from "../types";
import { api } from "../utils/api-client";

/** 搜索页面状态接口 */
interface SearchState {
  /** 当前搜索关键词 */
  query: string;
  /** 搜索结果列表 */
  results: Repo[];
  /** 是否加载中 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 当前语言过滤 */
  language: string;
  /** 结果总数 */
  total: number;

  /** 执行搜索 */
  search: (query: string, language: string) => Promise<void>;
  /** 清空搜索状态 */
  clear: () => void;
}

/**
 * Zustand store：管理搜索页面状态。
 * 调用 api.search() 获取搜索结果。
 */
export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  loading: false,
  error: null,
  language: "",
  total: 0,

  search: async (query: string, language: string) => {
    const trimmed = query.trim();
    set({ query: trimmed, language, loading: true, error: null });

    // 空关键词时清空结果
    if (!trimmed) {
      set({ results: [], total: 0, loading: false });
      return;
    }

    try {
      const response = await api.search(trimmed, language);
      set({
        results: response.items ?? [],
        total: response.total ?? 0,
        loading: false,
      });
    } catch (err) {
      set({
        results: [],
        total: 0,
        loading: false,
        error: err instanceof Error ? err.message : "搜索失败，请重试",
      });
    }
  },

  clear: () => set({ query: "", results: [], error: null, total: 0, language: "" }),
}));
