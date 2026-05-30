import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useRecommendationStore } from '../../stores/useRecommendationStore';

// ── Mock api-client ──────────────────────────────
const mockGetRecommended = vi.fn();

vi.mock('../../utils/api-client', () => ({
  api: {
    getRecommended: (...args: unknown[]) => mockGetRecommended(...args),
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

describe('useRecommendationStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useRecommendationStore.getState().reset();
  });

  it('fetchRecommendations loads items into state', async () => {
    const mockItems = [
      {
        repo: {
          id: 1,
          full_name: 'facebook/react',
          owner: 'facebook',
          name: 'react',
          description: 'A JS library',
          language: 'JavaScript',
          topics: ['ui'],
          total_stars: 200000,
          stars_since: 500,
          forks: 40000,
          forks_since: 100,
          url: 'https://github.com/facebook/react',
          trending_rank: 1,
          trending_since: 'weekly',
          is_favorited: false,
        },
        score: 0.95,
        reason: 'Based on your interests',
      },
    ];

    mockGetRecommended.mockResolvedValue({
      items: mockItems,
      method: 'collaborative',
      fallback_level: 1,
    });

    await useRecommendationStore.getState().fetchRecommended(10);

    const state = useRecommendationStore.getState();
    expect(state.items).toHaveLength(1);
    expect(state.items[0].repo.full_name).toBe('facebook/react');
    expect(state.items[0].score).toBe(0.95);
    expect(state.method).toBe('collaborative');
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });
});
