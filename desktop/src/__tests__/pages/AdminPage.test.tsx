import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminPage } from '../../pages/AdminPage';

// ── Controllable mock state ─────────────────────
const mockFetchDashboard = vi.fn();
const mockFetchUsers = vi.fn();
const mockToggleUserBan = vi.fn();
const mockUpdateUserRole = vi.fn();
const mockFetchPendingReviews = vi.fn();
const mockApproveReview = vi.fn();
const mockRejectReview = vi.fn();
const mockTriggerCrawl = vi.fn();

let mockDashboard: unknown = null;

const dashboardData = {
  summary: {
    dau: 150,
    page_views: 5000,
    favorites_count: 200,
    llm_cost: 3.75,
  },
  daily_trend: [
    { date: '2025-01-01', page_views: 100, dau: 50 },
    { date: '2025-01-02', page_views: 150, dau: 60 },
  ],
};

vi.mock('../../stores/useAdminStore', () => ({
  useAdminStore: (selector: (state: unknown) => unknown) => {
    const state = {
      dashboard: mockDashboard,
      dashboardLoading: false,
      users: [],
      usersTotal: 0,
      usersLoading: false,
      usersPage: 1,
      pendingReviews: [],
      reviewsTotal: 0,
      reviewsLoading: false,
      error: null,
      fetchDashboard: mockFetchDashboard,
      fetchUsers: mockFetchUsers,
      toggleUserBan: mockToggleUserBan,
      updateUserRole: mockUpdateUserRole,
      fetchPendingReviews: mockFetchPendingReviews,
      approveReview: mockApproveReview,
      rejectReview: mockRejectReview,
      triggerCrawl: mockTriggerCrawl,
      reset: vi.fn(),
    };
    return selector(state);
  },
}));

// ── Mock recharts ──────────────────────────────
vi.mock('recharts', () => ({
  LineChart: () => null,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('AdminPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard for admin', () => {
    mockDashboard = dashboardData;
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );

    // Dashboard tab should be visible
    expect(screen.getByText('📊 看板')).toBeInTheDocument();
    expect(screen.getByText('👥 用户')).toBeInTheDocument();
    expect(screen.getByText('✅ 审核')).toBeInTheDocument();

    // Dashboard stats should render
    expect(screen.getByText('DAU')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('shows no dashboard data when dashboard is null (non-admin)', () => {
    mockDashboard = null;
    render(
      <MemoryRouter>
        <AdminPage />
      </MemoryRouter>,
    );

    // Tabs should still be visible
    expect(screen.getByText('📊 看板')).toBeInTheDocument();

    // But DAU stat should NOT be visible (dashboard is null)
    expect(screen.queryByText('150')).not.toBeInTheDocument();
  });
});
