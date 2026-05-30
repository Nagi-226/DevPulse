import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useInteractionStore } from '../../stores/useInteractionStore';

// ── Mock api-client ──────────────────────────────
const mockGetComments = vi.fn();
const mockPostComment = vi.fn();
const mockDeleteComment = vi.fn();
const mockToggleLike = vi.fn();
const mockGetInteractions = vi.fn();

vi.mock('../../utils/api-client', () => ({
  api: {
    getComments: (...args: unknown[]) => mockGetComments(...args),
    postComment: (...args: unknown[]) => mockPostComment(...args),
    deleteComment: (...args: unknown[]) => mockDeleteComment(...args),
    toggleLike: (...args: unknown[]) => mockToggleLike(...args),
    getInteractions: (...args: unknown[]) => mockGetInteractions(...args),
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

describe('useInteractionStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useInteractionStore.getState().reset();
  });

  describe('fetchComments', () => {
    it('loads comments into state', async () => {
      const mockItems = [
        { id: 1, content: 'Great!', display_name: 'Alice', created_at: '2025-01-01', replies_count: 0 },
        { id: 2, content: 'Nice work', display_name: 'Bob', created_at: '2025-01-02', replies_count: 1 },
      ];

      mockGetComments.mockResolvedValue({
        total: 2,
        items: mockItems,
      });

      await useInteractionStore.getState().fetchComments('microsoft/graphrag');

      const state = useInteractionStore.getState();
      expect(state.comments).toHaveLength(2);
      expect(state.comments[0].content).toBe('Great!');
      expect(state.commentsTotal).toBe(2);
      expect(state.commentsLoading).toBe(false);
    });
  });

  describe('postComment', () => {
    it('adds new comment and refreshes', async () => {
      // First set up existing comments
      const existingItems = [{ id: 1, content: 'Old', display_name: 'A', created_at: '2025-01-01', replies_count: 0 }];

      mockGetComments.mockResolvedValue({ total: 1, items: existingItems });
      await useInteractionStore.getState().fetchComments('microsoft/graphrag');

      // Now mock post + refresh
      mockPostComment.mockResolvedValue({ id: 2, content: 'New!' });
      const refreshedItems = [
        { id: 1, content: 'Old', display_name: 'A', created_at: '2025-01-01', replies_count: 0 },
        { id: 2, content: 'New!', display_name: 'TestUser', created_at: '2025-01-03', replies_count: 0 },
      ];
      mockGetComments.mockResolvedValue({ total: 2, items: refreshedItems });
      mockGetInteractions.mockResolvedValue({ comments_count: 2, likes_count: 0 });

      const result = await useInteractionStore.getState().postComment('microsoft/graphrag', 'New!');

      expect(result).toBe(true);
      expect(mockPostComment).toHaveBeenCalledWith('microsoft/graphrag', 'New!');
    });
  });

  describe('toggleLike', () => {
    it('updates like state', async () => {
      mockToggleLike.mockResolvedValue({ liked: true, count: 5 });

      await useInteractionStore.getState().toggleLike('microsoft/graphrag');

      const state = useInteractionStore.getState();
      expect(state.likeInfo.liked).toBe(true);
      expect(state.likeInfo.count).toBe(5);
      expect(state.likeLoading).toBe(false);
    });
  });

  describe('deleteComment', () => {
    it('removes comment and refreshes list', async () => {
      mockDeleteComment.mockResolvedValue({ deleted: true });
      const remainingItems = [{ id: 2, content: 'Remaining', display_name: 'B', created_at: '2025-01-02', replies_count: 0 }];
      mockGetComments.mockResolvedValue({ total: 1, items: remainingItems });
      mockGetInteractions.mockResolvedValue({ comments_count: 1, likes_count: 0 });

      const result = await useInteractionStore.getState().deleteComment('microsoft/graphrag', 1);

      expect(result).toBe(true);
      expect(mockDeleteComment).toHaveBeenCalledWith('microsoft/graphrag', 1);
    });
  });
});
