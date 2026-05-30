import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { CommentSection } from '../../components/CommentSection';

// ── Controllable mock state ─────────────────────
let mockIsAuthenticated = true;
const mockFetchComments = vi.fn();
const mockPostComment = vi.fn();

vi.mock('../../stores/useInteractionStore', () => ({
  useInteractionStore: (selector: (state: unknown) => unknown) => {
    const state = {
      comments: [
        { id: 1, content: 'Great project!', display_name: 'Alice', created_at: '2025-01-01', replies_count: 0 },
        { id: 2, content: 'Love it', display_name: 'Bob', created_at: '2025-01-02', replies_count: 2 },
      ],
      commentsTotal: 2,
      commentsLoading: false,
      fetchComments: mockFetchComments,
      postComment: mockPostComment,
    };
    return selector(state);
  },
}));

vi.mock('../../stores/useAuthStore', () => ({
  useAuthStore: (selector: (state: unknown) => unknown) => {
    const state = {
      isAuthenticated: mockIsAuthenticated,
      user: mockIsAuthenticated ? { display_name: 'TestUser', email: 'test@test.com' } : null,
    };
    return selector(state);
  },
}));

// ── Helpers ──────────────────────────────────────
function renderCommentSection(fullName = 'microsoft/graphrag') {
  return render(
    <MemoryRouter>
      <CommentSection fullName={fullName} />
    </MemoryRouter>,
  );
}

describe('CommentSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsAuthenticated = true;
    mockPostComment.mockResolvedValue(true);
  });

  it('renders when user is logged in', () => {
    renderCommentSection();
    expect(screen.getByPlaceholderText('写下你的想法...')).toBeInTheDocument();
  });

  it('shows login prompt when user not logged in', () => {
    mockIsAuthenticated = false;
    renderCommentSection();
    expect(screen.getByText('后即可发表评论')).toBeInTheDocument();
  });

  it('calls postComment on submit', async () => {
    const user = userEvent.setup();
    renderCommentSection();

    const textarea = screen.getByPlaceholderText('写下你的想法...');
    await user.type(textarea, 'Nice library!');

    const sendButton = screen.getByRole('button', { name: '发送' });
    await user.click(sendButton);

    await waitFor(() => {
      expect(mockPostComment).toHaveBeenCalledWith('microsoft/graphrag', 'Nice library!');
    });
  });

  it('shows character counter (0/2000)', () => {
    renderCommentSection();
    expect(screen.getByText('0/2000')).toBeInTheDocument();
  });
});
