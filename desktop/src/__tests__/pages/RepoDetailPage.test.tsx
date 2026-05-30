import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { RepoDetailPage } from '../../pages/RepoDetailPage';

// ── Mock stores ─────────────────────────────────
const mockFetchRepo = vi.fn();
const mockToggleFavorite = vi.fn();
const mockFetchStarHistory = vi.fn();
const mockToggleLike = vi.fn();
const mockFetchLikesCount = vi.fn();
const mockResetInteraction = vi.fn();

const mockRepo = {
  id: 1,
  full_name: 'microsoft/graphrag',
  owner: 'microsoft',
  name: 'graphrag',
  description: 'A modular graph-based RAG system',
  language: 'Python',
  topics: ['rag', 'llm'],
  total_stars: 10000,
  stars_since: 500,
  forks: 2000,
  forks_since: 50,
  open_issues: 42,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2025-01-15T00:00:00Z',
  url: 'https://github.com/microsoft/graphrag',
  trending_rank: 1,
  trending_since: 'weekly',
  readme_summary: 'GraphRAG is a structured approach to RAG',
  key_points: ['Modular design', 'Graph-based'],
  tags: ['ai', 'nlp'],
  confidence_score: 0.85,
  is_favorited: false,
};

vi.mock('../../stores/useRepoDetailStore', () => ({
  useRepoDetailStore: (selector: (state: unknown) => unknown) => {
    const state = {
      repo: mockRepo,
      loading: false,
      error: null,
      isFavorite: false,
      starHistory: [],
      starHistoryLoading: false,
      fetchRepo: mockFetchRepo,
      toggleFavorite: mockToggleFavorite,
      fetchStarHistory: mockFetchStarHistory,
    };
    return selector(state);
  },
}));

vi.mock('../../stores/useInteractionStore', () => ({
  useInteractionStore: (selector: (state: unknown) => unknown) => {
    const state = {
      likeInfo: { liked: false, count: 3 },
      likeLoading: false,
      toggleLike: mockToggleLike,
      fetchLikesCount: mockFetchLikesCount,
      reset: mockResetInteraction,
      comments: [],
      commentsTotal: 0,
      commentsLoading: false,
      fetchComments: vi.fn(),
      postComment: vi.fn(),
      stats: null,
      statsLoading: false,
      fetchStats: vi.fn(),
    };
    return selector(state);
  },
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: unknown) => unknown) => {
    const state = { isAuthenticated: false, user: null };
    return selector(state);
  },
}));

// ── Mock components ─────────────────────────────
vi.mock('../../components/CommentSection', () => ({
  CommentSection: ({ fullName }: { fullName: string }) => (
    <div data-testid="comment-section">comments for {fullName}</div>
  ),
}));

vi.mock('../../components/ShareButton', () => ({
  ShareButton: ({ fullName }: { fullName: string; description: string }) => (
    <button data-testid="share-button">Share {fullName}</button>
  ),
}));

vi.mock('../../utils/cache', () => ({
  getDetailCache: vi.fn().mockResolvedValue(null),
}));

// ── Mock recharts (heavy lib, not needed for unit tests) ──
vi.mock('recharts', () => ({
  LineChart: () => <div>Chart</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('RepoDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
  });

  it('renders repo header', () => {
    render(
      <MemoryRouter initialEntries={['/repo/microsoft/graphrag']}>
        <RepoDetailPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('microsoft/graphrag')).toBeInTheDocument();
  });

  it('shows interaction buttons', () => {
    render(
      <MemoryRouter initialEntries={['/repo/microsoft/graphrag']}>
        <RepoDetailPage />
      </MemoryRouter>,
    );

    // The like button should render
    const likeButton = screen.getByText(/点赞/);
    expect(likeButton).toBeInTheDocument();

    // The favorite button should render
    const favButton = screen.getByText(/收藏/);
    expect(favButton).toBeInTheDocument();

    // Share button should be present
    expect(screen.getByTestId('share-button')).toBeInTheDocument();
  });
});
