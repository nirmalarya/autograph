'use client';

import { useState } from 'react';
import { API_ENDPOINTS } from '@/lib/api-config';

interface Comment {
  id: string;
  file_id: string;
  user_id: string;
  parent_id: string | null;
  content: string;
  position_x?: number;
  position_y?: number;
  element_id?: string;
  text_start?: number;
  text_end?: number;
  text_content?: string;
  is_resolved: boolean;
  resolved_at?: string;
  resolved_by?: string;
  is_private: boolean;
  created_at: string;
  updated_at: string;
  user: {
    id: string;
    full_name: string;
    email: string;
    avatar_url?: string;
  };
  replies_count: number;
  reactions: Record<string, number>;
  mentions: string[];
  permalink: string;
}

interface CommentThreadProps {
  diagramId: string;
  comments: Comment[];
  onReply: (parentId: string) => void;
  onResolve: (commentId: string) => void;
  onDelete: (commentId: string) => void;
  onRefresh: () => void;
}

function CommentItem({
  comment,
  diagramId,
  isReply = false,
  onReply,
  onResolve,
  onDelete,
}: {
  comment: Comment;
  diagramId: string;
  isReply?: boolean;
  onReply: (parentId: string) => void;
  onResolve: (commentId: string) => void;
  onDelete: (commentId: string) => void;
}) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyText, setReplyText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmitReply = async () => {
    if (!replyText.trim()) {
      alert('Please enter a reply');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));

      const response = await fetch(API_ENDPOINTS.diagrams.comments.create(diagramId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': payload.sub,
        },
        body: JSON.stringify({
          content: replyText,
          parent_id: comment.id, // This is the key field for threading!
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create reply');
      }

      // Clear form and refresh
      setReplyText('');
      setShowReplyForm(false);

      // Trigger parent refresh
      window.location.reload(); // Simple refresh for now
    } catch (err) {
      console.error('Failed to create reply:', err);
      alert('Failed to add reply. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`${isReply ? 'ml-8 mt-2' : 'mt-4'} border-l-2 ${isReply ? 'border-gray-200' : 'border-blue-300'} pl-4`}>
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        {/* Comment Header */}
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold text-sm">
              {comment.user.full_name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="font-medium text-sm text-gray-900">{comment.user.full_name || 'Unknown User'}</p>
              <p className="text-xs text-gray-500">{formatDate(comment.created_at)}</p>
            </div>
          </div>
          {comment.is_resolved && (
            <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">Resolved</span>
          )}
        </div>

        {/* Selected Text (if this is a note comment) */}
        {comment.text_content && (
          <div className="mb-2 p-2 bg-gray-50 border border-gray-200 rounded text-xs">
            <p className="text-gray-500 mb-1">On text:</p>
            <p className="italic text-gray-700">"{comment.text_content.substring(0, 80)}{comment.text_content.length > 80 ? '...' : ''}"</p>
          </div>
        )}

        {/* Comment Content */}
        <p className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">{comment.content}</p>

        {/* Comment Actions */}
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="hover:text-blue-600 font-medium transition"
          >
            Reply
          </button>
          {comment.replies_count > 0 && (
            <span className="font-medium">{comment.replies_count} {comment.replies_count === 1 ? 'reply' : 'replies'}</span>
          )}
          {!comment.is_resolved && !isReply && (
            <button
              onClick={() => onResolve(comment.id)}
              className="hover:text-green-600 font-medium transition"
            >
              Resolve
            </button>
          )}
          <button
            onClick={() => onDelete(comment.id)}
            className="hover:text-red-600 font-medium transition"
          >
            Delete
          </button>
        </div>

        {/* Reply Form */}
        {showReplyForm && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <textarea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              placeholder="Type your reply..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              rows={3}
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={() => {
                  setShowReplyForm(false);
                  setReplyText('');
                }}
                className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 transition"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitReply}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50"
                disabled={submitting}
              >
                {submitting ? 'Posting...' : 'Post Reply'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function CommentThread({
  diagramId,
  comments,
  onReply,
  onResolve,
  onDelete,
  onRefresh,
}: CommentThreadProps) {
  // Organize comments into threads (parent comments with their replies)
  const topLevelComments = comments.filter(c => !c.parent_id);
  const repliesMap = new Map<string, Comment[]>();

  // Group replies by parent_id
  comments.forEach(comment => {
    if (comment.parent_id) {
      const parentReplies = repliesMap.get(comment.parent_id) || [];
      parentReplies.push(comment);
      repliesMap.set(comment.parent_id, parentReplies);
    }
  });

  if (comments.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p className="text-sm">No comments yet. Be the first to comment!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {topLevelComments.map(comment => (
        <div key={comment.id}>
          {/* Parent Comment */}
          <CommentItem
            comment={comment}
            diagramId={diagramId}
            isReply={false}
            onReply={onReply}
            onResolve={onResolve}
            onDelete={onDelete}
          />

          {/* Nested Replies */}
          {repliesMap.get(comment.id)?.map(reply => (
            <CommentItem
              key={reply.id}
              comment={reply}
              diagramId={diagramId}
              isReply={true}
              onReply={onReply}
              onResolve={onResolve}
              onDelete={onDelete}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
