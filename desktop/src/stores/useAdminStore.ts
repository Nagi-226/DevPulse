import { create } from "zustand";
import type { DashboardData, AdminUser, PendingReview } from "../types";
import { api } from "../utils/api-client";

interface AdminState {
  dashboard: DashboardData | null;
  dashboardLoading: boolean;
  users: AdminUser[];
  usersTotal: number;
  usersLoading: boolean;
  usersPage: number;
  pendingReviews: PendingReview[];
  reviewsTotal: number;
  reviewsLoading: boolean;
  error: string | null;

  fetchDashboard: (days?: number) => Promise<void>;
  fetchUsers: (page?: number, q?: string) => Promise<void>;
  fetchPendingReviews: (page?: number) => Promise<void>;
  toggleUserBan: (userId: number, banned: boolean) => Promise<boolean>;
  updateUserRole: (userId: number, role: string) => Promise<boolean>;
  approveReview: (repoId: number) => Promise<boolean>;
  rejectReview: (repoId: number) => Promise<boolean>;
  triggerCrawl: () => Promise<boolean>;
  reset: () => void;
}

export const useAdminStore = create<AdminState>((set, get) => ({
  dashboard: null,
  dashboardLoading: false,
  users: [],
  usersTotal: 0,
  usersLoading: false,
  usersPage: 1,
  pendingReviews: [],
  reviewsTotal: 0,
  reviewsLoading: false,
  error: null,

  fetchDashboard: async (days = 30) => {
    set({ dashboardLoading: true });
    try {
      const data = await api.getDashboard(days);
      set({ dashboard: data as unknown as DashboardData, dashboardLoading: false });
    } catch (err) {
      set({ dashboardLoading: false, error: String(err) });
    }
  },

  fetchUsers: async (page = 1, q = "") => {
    set({ usersLoading: true });
    try {
      const response = await api.getAdminUsers(page, 25, q);
      const data = response as unknown as { total: number; items: AdminUser[] };
      set({
        users: data.items,
        usersTotal: data.total,
        usersPage: page,
        usersLoading: false,
      });
    } catch {
      set({ usersLoading: false });
    }
  },

  fetchPendingReviews: async (page = 1) => {
    set({ reviewsLoading: true });
    try {
      const response = await api.getPendingReviews(page, 25);
      const data = response as unknown as { total: number; items: PendingReview[] };
      set({
        pendingReviews: data.items,
        reviewsTotal: data.total,
        reviewsLoading: false,
      });
    } catch {
      set({ reviewsLoading: false });
    }
  },

  toggleUserBan: async (userId, banned) => {
    try {
      await api.toggleUserBan(userId, banned);
      await get().fetchUsers(get().usersPage);
      return true;
    } catch {
      return false;
    }
  },

  updateUserRole: async (userId, role) => {
    try {
      await api.updateUserRole(userId, role);
      await get().fetchUsers(get().usersPage);
      return true;
    } catch {
      return false;
    }
  },

  approveReview: async (repoId) => {
    try {
      await api.approveReview(repoId);
      await get().fetchPendingReviews();
      return true;
    } catch {
      return false;
    }
  },

  rejectReview: async (repoId) => {
    try {
      await api.rejectReview(repoId);
      await get().fetchPendingReviews();
      return true;
    } catch {
      return false;
    }
  },

  triggerCrawl: async () => {
    try {
      await api.adminTriggerCrawl();
      return true;
    } catch {
      return false;
    }
  },

  reset: () => {
    set({
      dashboard: null,
      users: [],
      usersTotal: 0,
      pendingReviews: [],
      reviewsTotal: 0,
      error: null,
    });
  },
}));
