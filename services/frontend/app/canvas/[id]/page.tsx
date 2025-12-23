'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import dynamic from 'next/dynamic';

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

    // Fetch diagram data
    fetchDiagram();
  }, [diagramId, router]);

  const fetchDiagram = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));
      
      const response = await fetch(`http://localhost:8082/${diagramId}`, {
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

      const response = await fetch(`http://localhost:8082/${diagramId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': payload.sub,
        },
        body: JSON.stringify({
          title: diagram.title,
          canvas_data: snapshot,
          note_content: diagram.note_content,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save diagram');
      }

      const updated = await response.json();
      setDiagram(updated);
      setLastSaved(new Date());
    } catch (err) {
      console.error('Failed to save diagram:', err);
      alert('Failed to save diagram. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [diagram, diagramId]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

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
              {lastSaved && (
                <span className="text-xs text-gray-500">
                  Saved at {lastSaved.toLocaleTimeString()}
                </span>
              )}
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button 
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
                title="Share (coming soon)"
              >
                Share
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

      {/* Canvas Area - Full height with TLDraw */}
      <div className="flex-1 relative bg-white overflow-hidden">
        <TLDrawCanvas 
          initialData={diagram?.canvas_data}
          onSave={handleSave}
        />
      </div>
    </main>
  );
}
