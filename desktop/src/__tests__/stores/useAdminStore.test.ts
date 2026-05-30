import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAdminStore } from '../../stores/useAdminStore';

// ── Mock api-client ──────────────────────────────
const mockGetDashboard = vi.fn();
const mockGetAdminUsers = vi.fn();
const mockToggleUserBan = vi.fn();
const mockGetPendingReviews = vi.fn();

vi.mock('../../utils/api-client', () => ({
  api: {
    getDashboard: (...args: unknown[]) => mockGetDashboard(...args),
    getAdminUsers: (...args: unknown[]) => mockGetAdminUsers(...args),
    toggleUserBan: (...args: unknown[]) => mockToggleUserBan(...args),
    getPendingReviews: (...args: unknown[]) => mockGetPendingReviews(...args),
  },
  ApiError: class extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.name = 'ApiError';
      this.status = status;
    }
  },
}));

describe('useAdminStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAdminStore.getState().reset();
  });

  describe('fetchDashboard', () => {
    it('loads dashboard stats', async () => {
      const dashboardData = {
        summary: {
          dau: 150,
          page_views: 5000,
          favorites_count: 200,
          llm_cost: 3.75,
        },
        daily_trend: [
          { date: '2025-01-01', page_views: 100, dau: 50 },
        ],
      };

      mockGetDashboard.mockResolvedValue(dashboardData);

      await useAdminStore.getState().fetchDashboard(30);

      const state = useAdminStore.getState();
      expect(state.dashboard).not.toBeNull();
      expect(state.dashboard!.summary.dau).toBe(150);
      expect(state.dashboardLoading).toBe(false);
    });
  });

  describe('fetchUsers', () => {
    it('loads user list', async () => {
      const mockUsers = [
        { id: 1, email: 'alice@test.com', display_name: 'Alice', role: 'user', is_active: true, created_at: '2025-01-01' },
        { id: 2, email: 'bob@test.com', display_name: 'Bob', role: 'admin', is_active: false, created_at: '2025-01-02' },
      ];

      mockGetAdminUsers.mockResolvedValue({
        total: 2,
        items: mockUsers,
      });

      await useAdminStore.getState().fetchUsers(1);

      const state = useAdminStore.getState();
      expect(state.users).toHaveLength(2);
      expect(state.users[0].email).toBe('alice@test.com');
      expect(state.usersTotal).toBe(2);
      expect(state.usersLoading).toBe(false);
    });
  });

  describe('toggleBan', () => {
    it('updates user ban state and refreshes', async () => {
      mockToggleUserBan.mockResolvedValue({ user_id: 1, is_active: false });
      const refreshedUsers = [
        { id: 1, email: 'alice@test.com', display_name: 'Alice', role: 'user', is_active: false, created_at: '2025-01-01' },
      ];
      mockGetAdminUsers.mockResolvedValue({ total: 1, items: refreshedUsers });

      const result = await useAdminStore.getState().toggleUserBan(1, true);

      expect(result).toBe(true);
      expect(mockToggleUserBan).toHaveBeenCalledWith(1, true);
    });
  });
});
