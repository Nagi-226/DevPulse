import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { TrendingPage } from '../../pages/TrendingPage';

// ── Mock stores ─────────────────────────────────
const mockFetchTrending = vi.fn();
const mockSetLanguage = vi.fn();
const mockSetSince = vi.fn();
const mockSetSource = vi.fn();
const mockFetchRecommended = vi.fn();

const mockRepos = [
  {
    id: 1,
    full_name: 'microsoft/graphrag',
    owner: 'microsoft',
    name: 'graphrag',
    description: 'Graph RAG',
    language: 'Python',
    topics: ['rag'],
    total_stars: 10000,
    stars_since: 500,
    forks: 2000,
    forks_since: 50,
    url: 'https://github.com/microsoft/graphrag',
    trending_rank: 1,
    trending_since: 'weekly',
    is_favorited: false,
  },
];

vi.mock('../../stores/useTrendingStore', () => ({
  useTrendingStore: (selector: (state: unknown) => unknown) => {
    const state = {
      repos: mockRepos,
      loading: false,
      error: null,
      language: 'Python',
      since: 'weekly',
      source: 'github',
      fetchTrending: mockFetchTrending,
      setLanguage: mockSetLanguage,
      setSince: mockSetSince,
      setSource: mockSetSource,
    };
    return selector(state);
  },
}));

vi.mock('../../stores/useRecommendationStore', () => ({
  useRecommendationStore: (selector: (state: unknown) => unknown) => {
    const state = {
      items: [],
      loading: false,
      method: 'popular',
      fallbackLevel: 3,
      error: null,
      fetchRecommended: mockFetchRecommended,
      reset: vi.fn(),
    };
    return selector(state);
  },
}));

// ── Mock components used by TrendingPage ─────────
vi.mock('../../components/TrendingList', () => ({
  TrendingList: ({ repos: r, loading: l, error: e }: {
    repos: unknown[];
    loading: boolean;
    error: string | null;
    onRetry: () => void;
  }) => (
    <div data-testid="trending-list">
      <span>items: {r.length}</span>
      <span>loading: {String(l)}</span>
      {e && <span>error: {e}</span>}
    </div>
  ),
}));

vi.mock('../../components/DataSourceTabs', () => ({
  DataSourceTabs: ({ active, onChange }: { active: string; onChange: (s: string) => void }) => (
    <div data-testid="datasource-tabs" onClick={() => onChange('gitlab')}>source: {active}</div>
  ),
}));

vi.mock('../../components/LanguageFilter', () => ({
  LanguageFilter: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <div data-testid="language-filter">lang: {value}</div>
  ),
}));

vi.mock('../../components/OfflineBanner', () => ({
  OfflineBanner: () => <div data-testid="offline-banner" />,
}));

vi.mock('../../utils/cache', () => ({
  getTrendingCache: vi.fn().mockResolvedValue(null),
}));

describe('TrendingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true });
  });

  it('renders trending tab bar', () => {
    render(
      <MemoryRouter>
        <TrendingPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('🔥 Trending')).toBeInTheDocument();
    expect(screen.getByText('🧠 为你推荐')).toBeInTheDocument();
  });

  it('shows trending list with mock data', () => {
    render(
      <MemoryRouter>
        <TrendingPage />
      </MemoryRouter>,
    );

    const list = screen.getByTestId('trending-list');
    expect(list).toBeInTheDocument();
    expect(list.textContent).toContain('items: 1');
  });
});
