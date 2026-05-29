import { create } from "zustand";
import type { RecommendedRepo, RecommendationResponse } from "../types";
import { api } from "../utils/api-client";

interface RecommendationState {
  items: RecommendedRepo[];
  loading: boolean;
  method: string;
  fallbackLevel: number;
  error: string | null;

  fetchRecommended: (limit?: number) => Promise<void>;
  reset: () => void;
}

export const useRecommendationStore = create<RecommendationState>((set) => ({
  items: [],
  loading: false,
  method: "popular",
  fallbackLevel: 3,
  error: null,

  fetchRecommended: async (limit = 10) => {
    set({ loading: true, error: null });
    try {
      const response = await api.getRecommended(limit);
      const data = response as unknown as RecommendationResponse;
      set({
        items: data.items || [],
        method: data.method,
        fallbackLevel: data.fallback_level,
        loading: false,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载推荐失败";
      set({ loading: false, error: message });
    }
  },

  reset: () => {
    set({
      items: [],
      loading: false,
      method: "popular",
      fallbackLevel: 3,
      error: null,
    });
  },
}));
