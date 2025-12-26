'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useOfflineStorage } from '@/hooks/useOfflineStorage';
import ExportDialog from '../../components/ExportDialog';
import CommentThread from '../../components/CommentThread';
import { API_ENDPOINTS } from '@/lib/api-config';

// Dynamically import TLDraw to avoid SSR issues
const TLDrawCanvas = dynamic(() => import('./TLDrawCanvas'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading canvas...</p>
      </div>
    </div>
  ),
});

export default function CanvasEditorPage() {
  const router = useRouter();
  const params = useParams();
  const diagramId = params.id as string;
  
  const [diagram, setDiagram] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [canvasTheme, setCanvasTheme] = useState<'light' | 'dark'>('light');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [selectedShapes, setSelectedShapes] = useState<string[]>([]);
  const [frames, setFrames] = useState<Array<{ id: string; name: string; x: number; y: number; w: number; h: number }>>([]);
  const [showCommentDialog, setShowCommentDialog] = useState(false);
  const [commentElementId, setCommentElementId] = useState<string>('');
  const [commentPosition, setCommentPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [commentText, setCommentText] = useState('');
  const [commentTextStart, setCommentTextStart] = useState<number | null>(null);
  const [commentTextEnd, setCommentTextEnd] = useState<number | null>(null);
  const [commentTextContent, setCommentTextContent] = useState<string>('');
  const [showCommentsPanel, setShowCommentsPanel] = useState(false);
  const [comments, setComments] = useState<any[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);

  // Offline storage hook
  const {
    isOnline,
    isSyncing,
    cacheDiagram,
    getCachedDiagram,
    addPendingEdit,
    syncError,
  } = useOfflineStorage();

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.email, sub: payload.sub });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    // Load canvas theme preference from localStorage
    const savedCanvasTheme = localStorage.getItem(`canvas_theme_${diagramId}`) as 'light' | 'dark' | null;
    if (savedCanvasTheme) {
      setCanvasTheme(savedCanvasTheme);
    }

    // Fetch diagram data
    fetchDiagram();
  }, [diagramId, router]);

  const fetchDiagram = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));
      
      // Try to fetch from server first
      if (isOnline) {
        try {
          const response = await fetch(API_ENDPOINTS.diagrams.get(diagramId), {
            headers: {
              'X-User-ID': payload.sub,
            },
          });

          if (!response.ok) {
            if (response.status === 404) {
              throw new Error('Diagram not found');
            } else if (response.status === 403) {
              throw new Error('You do not have permission to access this diagram');
            }
            throw new Error('Failed to load diagram');
          }

          const data = await response.json();
          setDiagram(data);
          
          // Cache the diagram for offline access
          await cacheDiagram({
            id: data.id,
            title: data.title,
            type: data.type,
            canvas_data: data.canvas_data,
            note_content: data.note_content,
            thumbnail_url: data.thumbnail_url,
            updated_at: data.updated_at,
            cached_at: Date.now(),
          });
          
          return;
        } catch (fetchError) {
          console.warn('Failed to fetch from server, trying cache...', fetchError);
        }
      }
      
      // If offline or fetch failed, try to load from cache
      const cachedDiagram = await getCachedDiagram(diagramId);
      if (cachedDiagram) {
        console.log('Loading diagram from offline cache');
        setDiagram({
          id: cachedDiagram.id,
          title: cachedDiagram.title,
          type: cachedDiagram.type,
          canvas_data: cachedDiagram.canvas_data,
          note_content: cachedDiagram.note_content,
          thumbnail_url: cachedDiagram.thumbnail_url,
          updated_at: cachedDiagram.updated_at,
          current_version: 1, // Default version for cached diagrams
        });
      } else {
        throw new Error('Diagram not available offline');
      }
    } catch (err: any) {
      console.error('Failed to fetch diagram:', err);
      setError(err.message || 'Failed to load diagram');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = useCallback(async (editor: any) => {
    if (!editor || !diagram) return;

    try {
      setSaving(true);
      const snapshot = editor.store.getSnapshot();
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));

      const updateData = {
        title: diagram.title,
        canvas_data: snapshot,
        note_content: diagram.note_content,
      };

      if (isOnline) {
        // Try to save to server
        try {
          const response = await fetch(API_ENDPOINTS.diagrams.update(diagramId), {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'X-User-ID': payload.sub,
            },
            body: JSON.stringify(updateData),
          });

          if (!response.ok) {
            throw new Error('Failed to save diagram');
          }

          const updated = await response.json();
          setDiagram(updated);
          setLastSaved(new Date());
          
          // Update cache with latest data
          await cacheDiagram({
            id: updated.id,
            title: updated.title,
            type: updated.type,
            canvas_data: updated.canvas_data,
            note_content: updated.note_content,
            thumbnail_url: updated.thumbnail_url,
            updated_at: updated.updated_at,
            cached_at: Date.now(),
          });
        } catch (saveError) {
          console.warn('Failed to save to server, queuing for later...', saveError);
          // Queue the edit for later sync
          await addPendingEdit({
            diagram_id: diagramId,
            type: 'update',
            data: updateData,
          });
          
          // Update local diagram state
          const updatedDiagram = {
            ...diagram,
            ...updateData,
            updated_at: new Date().toISOString(),
          };
          setDiagram(updatedDiagram);
          setLastSaved(new Date());
          
          // Update cache
          await cacheDiagram({
            id: updatedDiagram.id,
            title: updatedDiagram.title,
            type: updatedDiagram.type,
            canvas_data: updatedDiagram.canvas_data,
            note_content: updatedDiagram.note_content,
            thumbnail_url: updatedDiagram.thumbnail_url,
            updated_at: updatedDiagram.updated_at,
            cached_at: Date.now(),
          });
          
          alert('Saved offline. Changes will sync when you\'re back online.');
        }
      } else {
        // Offline - queue the edit for later sync
        await addPendingEdit({
          diagram_id: diagramId,
          type: 'update',
          data: updateData,
        });
        
        // Update local diagram state
        const updatedDiagram = {
          ...diagram,
          ...updateData,
          updated_at: new Date().toISOString(),
        };
        setDiagram(updatedDiagram);
        setLastSaved(new Date());
        
        // Update cache
        await cacheDiagram({
          id: updatedDiagram.id,
          title: updatedDiagram.title,
          type: updatedDiagram.type,
          canvas_data: updatedDiagram.canvas_data,
          note_content: updatedDiagram.note_content,
          thumbnail_url: updatedDiagram.thumbnail_url,
          updated_at: updatedDiagram.updated_at,
          cached_at: Date.now(),
        });
        
        console.log('Saved offline. Changes will sync when you\'re back online.');
      }
    } catch (err) {
      console.error('Failed to save diagram:', err);
      alert('Failed to save diagram. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [diagram, diagramId, isOnline, cacheDiagram, addPendingEdit]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const toggleCanvasTheme = () => {
    const newTheme = canvasTheme === 'light' ? 'dark' : 'light';
    setCanvasTheme(newTheme);
    localStorage.setItem(`canvas_theme_${diagramId}`, newTheme);
  };

  const handleAddComment = useCallback((elementId: string, position: { x: number; y: number }) => {
    setCommentElementId(elementId);
    setCommentPosition(position);
    setCommentTextStart(null);
    setCommentTextEnd(null);
    setCommentTextContent('');
    setShowCommentDialog(true);
    setCommentText('');
  }, []);

  const handleAddNoteComment = useCallback((elementId: string, textStart: number, textEnd: number, textContent: string) => {
    setCommentElementId(elementId);
    setCommentTextStart(textStart);
    setCommentTextEnd(textEnd);
    setCommentTextContent(textContent);
    setCommentPosition({ x: 0, y: 0 }); // Not needed for text comments
    setShowCommentDialog(true);
    setCommentText('');
  }, []);

  const handleSubmitComment = useCallback(async () => {
    if (!commentText.trim()) {
      alert('Please enter a comment');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const payload = JSON.parse(atob(token.split('.')[1]));

      // Determine if this is a text selection comment or a canvas element comment
      const isTextComment = commentTextStart !== null && commentTextEnd !== null;

      const requestBody: any = {
        content: commentText,
        element_id: commentElementId,
        is_private: false,
      };

      if (isTextComment) {
        // Note text selection comment
        requestBody.text_start = commentTextStart;
        requestBody.text_end = commentTextEnd;
        requestBody.text_content = commentTextContent;
      } else {
        // Canvas element comment
        requestBody.position_x = commentPosition.x;
        requestBody.position_y = commentPosition.y;
      }

      const response = await fetch(API_ENDPOINTS.diagrams.comments.create(diagramId), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': payload.sub,
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error('Failed to create comment');
      }

      // Success - close dialog and refresh
      setShowCommentDialog(false);
      setCommentText('');
      setCommentTextStart(null);
      setCommentTextEnd(null);
      setCommentTextContent('');
      alert('Comment added successfully!');

      // Optionally, add a visual indicator to the shape
      // This would require storing comment metadata and rendering icons

      // Refresh comments if panel is open
      if (showCommentsPanel) {
        fetchComments();
      }

    } catch (err) {
      console.error('Failed to create comment:', err);
      alert('Failed to add comment. Please try again.');
    }
  }, [commentText, commentElementId, commentPosition, commentTextStart, commentTextEnd, commentTextContent, diagramId, router, showCommentsPanel]);

  const fetchComments = useCallback(async () => {
    if (!diagramId) return;

    setLoadingComments(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const payload = JSON.parse(atob(token.split('.')[1]));

      const response = await fetch(API_ENDPOINTS.diagrams.comments.list(diagramId), {
        headers: {
          'X-User-ID': payload.sub,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setComments(data.comments || []);
      }
    } catch (err) {
      console.error('Failed to fetch comments:', err);
    } finally {
      setLoadingComments(false);
    }
  }, [diagramId]);

  const handleResolveComment = useCallback(async (commentId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const payload = JSON.parse(atob(token.split('.')[1]));

      const response = await fetch(API_ENDPOINTS.diagrams.comments.resolve(diagramId, commentId), {
        method: 'POST',
        headers: {
          'X-User-ID': payload.sub,
        },
      });

      if (response.ok) {
        alert('Comment resolved!');
        fetchComments(); // Refresh comments
      }
    } catch (err) {
      console.error('Failed to resolve comment:', err);
      alert('Failed to resolve comment');
    }
  }, [diagramId, fetchComments]);

  const handleDeleteComment = useCallback(async (commentId: string) => {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const payload = JSON.parse(atob(token.split('.')[1]));

      const response = await fetch(API_ENDPOINTS.diagrams.comments.delete(diagramId, commentId), {
        method: 'DELETE',
        headers: {
          'X-User-ID': payload.sub,
        },
      });

      if (response.ok) {
        alert('Comment deleted!');
        fetchComments(); // Refresh comments
      }
    } catch (err) {
      console.error('Failed to delete comment:', err);
      alert('Failed to delete comment');
    }
  }, [diagramId, fetchComments]);

  // Fetch comments when panel is opened
  useEffect(() => {
    if (showCommentsPanel) {
      fetchComments();
    }
  }, [showCommentsPanel, fetchComments]);

  // Add Ctrl+S / Cmd+S keyboard shortcut for manual save
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Check for Ctrl+S (Windows/Linux) or Cmd+S (Mac)
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault(); // Prevent browser's default save dialog
        
        const editor = (window as any).tldrawEditor;
        if (editor && !saving) {
          handleSave(editor);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleSave, saving]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading diagram...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleBackToDashboard}
            className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="fixed inset-0 flex flex-col bg-gray-50">
      {/* Header */}
      <nav className="flex-shrink-0 bg-white shadow-sm border-b border-gray-200 z-10">
        <div className="max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToDashboard}
                className="text-gray-600 hover:text-gray-900 transition"
                title="Back to Dashboard"
              >
                ← Back
              </button>
              <div className="border-l border-gray-300 h-6"></div>
              <h1 className="text-lg font-semibold text-gray-900">
                {diagram?.title || 'Untitled Diagram'}
              </h1>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                v{diagram?.current_version || 1}
              </span>
            </div>
            <div className="flex items-center gap-4">
              {/* Offline/Sync Status */}
              {!isOnline && (
                <span className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 bg-amber-600 rounded-full animate-pulse"></span>
                  Offline
                </span>
              )}
              {isSyncing && (
                <span className="flex items-center gap-2 text-xs text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                  <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
                  Syncing...
                </span>
              )}
              {syncError && (
                <span className="flex items-center gap-2 text-xs text-red-600 bg-red-50 px-3 py-1 rounded-full" title={syncError}>
                  <span className="w-2 h-2 bg-red-600 rounded-full"></span>
                  Sync Error
                </span>
              )}
              {lastSaved && (
                <span className="text-xs text-gray-500">
                  Saved at {lastSaved.toLocaleTimeString()}
                </span>
              )}
              <span className="text-sm text-gray-600">{user?.email}</span>
              {/* Canvas Theme Toggle */}
              <button
                onClick={toggleCanvasTheme}
                className="p-2 text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition"
                title={`Canvas theme: ${canvasTheme}`}
                aria-label="Toggle canvas theme"
              >
                {canvasTheme === 'dark' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                )}
              </button>
              <button 
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
                title="Share (coming soon)"
              >
                Share
              </button>
              <button 
                onClick={() => {
                  // Get selected shapes from editor
                  const editor = (window as any).tldrawEditor;
                  if (editor) {
                    const selected = editor.getSelectedShapeIds();
                    setSelectedShapes(selected);
                    
                    // Get all frames from the canvas
                    const allShapes = editor.getCurrentPageShapes();
                    const frameShapes = allShapes.filter((shape: any) => shape.type === 'frame');
                    const extractedFrames = frameShapes.map((frame: any) => ({
                      id: frame.id,
                      name: frame.props?.name || '',
                      x: frame.x,
                      y: frame.y,
                      w: frame.props?.w || 0,
                      h: frame.props?.h || 0,
                    }));
                    setFrames(extractedFrames);
                  }
                  setShowExportDialog(true);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md transition"
                title="Export diagram"
              >
                Export
              </button>
              <button
                onClick={() => setShowCommentsPanel(!showCommentsPanel)}
                className={`px-4 py-2 text-sm font-medium transition rounded-md ${
                  showCommentsPanel
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="View comments and threads"
              >
                💬 Comments {comments.length > 0 && `(${comments.length})`}
              </button>
              <button
                onClick={() => {
                  const editor = (window as any).tldrawEditor;
                  if (editor) {
                    handleSave(editor);
                  }
                }}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Canvas Area with Comments Panel */}
      <div className="flex-1 flex relative bg-white overflow-hidden">
        {/* Main Canvas */}
        <div className={`transition-all duration-300 ${showCommentsPanel ? 'flex-1' : 'w-full'}`}>
          <TLDrawCanvas
            initialData={diagram?.canvas_data}
            onSave={handleSave}
            theme={canvasTheme}
            diagramId={diagramId}
            onAddComment={handleAddComment}
            onAddNoteComment={handleAddNoteComment}
          />
        </div>

        {/* Comments Panel */}
        {showCommentsPanel && (
          <div className="w-96 border-l border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">
                  Comments & Threads
                </h2>
                <button
                  onClick={() => setShowCommentsPanel(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              {loadingComments ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-500">Loading comments...</p>
                </div>
              ) : (
                <CommentThread
                  diagramId={diagramId}
                  comments={comments}
                  onReply={() => {}}
                  onResolve={handleResolveComment}
                  onDelete={handleDeleteComment}
                  onRefresh={fetchComments}
                />
              )}
            </div>
          </div>
        )}
      </div>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        diagramId={diagramId}
        canvasData={diagram?.canvas_data}
        selectedShapes={selectedShapes}
        frames={frames}
      />

      {/* Comment Dialog */}
      {showCommentDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {commentTextContent ? 'Add Comment to Note Text' : 'Add Comment'}
            </h3>

            {/* Show selected text for note comments */}
            {commentTextContent && (
              <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-md">
                <p className="text-xs text-gray-500 mb-1">Selected text:</p>
                <p className="text-sm text-gray-700 italic">"{commentTextContent.substring(0, 100)}{commentTextContent.length > 100 ? '...' : ''}"</p>
              </div>
            )}

            <textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder="Type your comment here..."
              className="w-full h-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowCommentDialog(false);
                  setCommentText('');
                  setCommentTextStart(null);
                  setCommentTextEnd(null);
                  setCommentTextContent('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitComment}
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              >
                Add Comment
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
