import { create } from "zustand";
import type { Comment, LikeInfo, InteractionStats } from "../types";
import { api } from "../utils/api-client";

interface InteractionState {
  comments: Comment[];
  commentsTotal: number;
  commentsLoading: boolean;
  commentsPage: number;
  likeInfo: LikeInfo;
  likeLoading: boolean;
  stats: InteractionStats | null;
  statsLoading: boolean;

  fetchComments: (fullName: string, page?: number) => Promise<void>;
  postComment: (fullName: string, content: string) => Promise<boolean>;
  deleteComment: (fullName: string, commentId: number) => Promise<boolean>;
  toggleLike: (fullName: string) => Promise<void>;
  fetchLikesCount: (fullName: string) => Promise<void>;
  fetchStats: (fullName: string) => Promise<void>;
  reset: () => void;
}

export const useInteractionStore = create<InteractionState>((set, get) => ({
  comments: [],
  commentsTotal: 0,
  commentsLoading: false,
  commentsPage: 1,
  likeInfo: { liked: false, count: 0 },
  likeLoading: false,
  stats: null,
  statsLoading: false,

  fetchComments: async (fullName, page = 1) => {
    set({ commentsLoading: true });
    try {
      const response = await api.getComments(fullName, page);
      const data = response as unknown as { total: number; items: Comment[] };
      set({
        comments: page === 1 ? data.items : [...get().comments, ...data.items],
        commentsTotal: data.total,
        commentsPage: page,
        commentsLoading: false,
      });
    } catch {
      set({ commentsLoading: false });
    }
  },

  postComment: async (fullName, content) => {
    try {
      await api.postComment(fullName, content);
      await get().fetchComments(fullName, 1);
      await get().fetchStats(fullName);
      return true;
    } catch {
      return false;
    }
  },

  deleteComment: async (fullName, commentId) => {
    try {
      await api.deleteComment(fullName, commentId);
      await get().fetchComments(fullName, 1);
      await get().fetchStats(fullName);
      return true;
    } catch {
      return false;
    }
  },

  toggleLike: async (fullName) => {
    set({ likeLoading: true });
    try {
      const response = await api.toggleLike(fullName);
      const data = response as unknown as LikeInfo;
      set({ likeInfo: data, likeLoading: false });
    } catch {
      set({ likeLoading: false });
    }
  },

  fetchLikesCount: async (fullName) => {
    try {
      const response = await api.getLikesCount(fullName);
      const data = response as unknown as { likes_count: number; is_liked: boolean };
      set({ likeInfo: { liked: data.is_liked, count: data.likes_count } });
    } catch {
      // silent
    }
  },

  fetchStats: async (fullName) => {
    set({ statsLoading: true });
    try {
      const response = await api.getInteractions(fullName);
      const data = response as unknown as InteractionStats;
      set({ stats: data, statsLoading: false });
    } catch {
      set({ statsLoading: false });
    }
  },

  reset: () => {
    set({
      comments: [],
      commentsTotal: 0,
      commentsLoading: false,
      commentsPage: 1,
      likeInfo: { liked: false, count: 0 },
      likeLoading: false,
      stats: null,
      statsLoading: false,
    });
  },
}));
