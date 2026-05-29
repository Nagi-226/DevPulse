import { useEffect, useState } from "react";
import { useInteractionStore } from "../stores/useInteractionStore";
import { useAuthStore } from "../stores/useAuthStore";
import { Link } from "react-router-dom";

interface CommentSectionProps {
  fullName: string;
}

/** 评论列表 + 发表评论表单组件 */
export function CommentSection({ fullName }: CommentSectionProps) {
  const comments = useInteractionStore((s) => s.comments);
  const commentsTotal = useInteractionStore((s) => s.commentsTotal);
  const commentsLoading = useInteractionStore((s) => s.commentsLoading);
  const fetchComments = useInteractionStore((s) => s.fetchComments);
  const postComment = useInteractionStore((s) => s.postComment);

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);

  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchComments(fullName);
  }, [fullName, fetchComments]);

  const handleSubmit = async () => {
    if (!content.trim()) return;
    setSubmitting(true);
    const ok = await postComment(fullName, content.trim());
    if (ok) setContent("");
    setSubmitting(false);
  };

  return (
    <div className="mt-6 rounded-xl border border-slate-700 bg-slate-800/30 p-6">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
        <svg className="h-5 w-5 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        评论 ({commentsTotal})
      </h2>

      {/* 发表评论表单 */}
      {isAuthenticated ? (
        <div className="mt-4 flex gap-3">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-primary-500/20 text-sm font-medium text-primary-400">
            {(user?.display_name || user?.email || "?")[0].toUpperCase()}
          </div>
          <div className="flex-1">
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="写下你的想法..."
              rows={3}
              maxLength={2000}
              className="w-full rounded-lg border border-slate-600 bg-slate-700/50 px-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 resize-none"
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {content.length}/2000
              </span>
              <button
                onClick={handleSubmit}
                disabled={!content.trim() || submitting}
                className="rounded-lg bg-primary-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                style={{ minHeight: 36 }}
              >
                {submitting ? "发送中..." : "发送"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-4 rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 text-center text-sm text-slate-400">
          <Link to="/auth" className="text-primary-400 hover:text-primary-300">
            登录
          </Link>
          {" "}后即可发表评论
        </div>
      )}

      {/* 评论列表 */}
      <div className="mt-6 space-y-4">
        {commentsLoading && comments.length === 0 && (
          <div className="flex items-center justify-center py-8">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
          </div>
        )}

        {!commentsLoading && comments.length === 0 && (
          <div className="py-8 text-center text-sm text-slate-500">
            暂无评论，来发表第一条吧
          </div>
        )}

        {comments.map((comment) => (
          <div
            key={comment.id}
            className="flex gap-3 rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
          >
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-medium text-slate-300">
              {comment.display_name[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200">
                  {comment.display_name}
                </span>
                <span className="text-xs text-slate-500">
                  {comment.created_at
                    ? new Date(comment.created_at).toLocaleDateString("zh-CN")
                    : ""}
                </span>
              </div>
              <p className="mt-1 text-sm text-slate-300 whitespace-pre-wrap break-words">
                {comment.content}
              </p>
              {comment.replies_count > 0 && (
                <span className="mt-1 text-xs text-primary-400">
                  {comment.replies_count} 条回复
                </span>
              )}
            </div>
          </div>
        ))}

        {commentsTotal > comments.length && (
          <button
            onClick={() => fetchComments(fullName, Math.ceil(comments.length / 20) + 1)}
            className="w-full rounded-lg py-2 text-sm text-slate-400 hover:text-slate-200 transition-colors"
            style={{ minHeight: 40 }}
          >
            加载更多评论
          </button>
        )}
      </div>
    </div>
  );
}
