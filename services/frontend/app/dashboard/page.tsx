'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [diagramTitle, setDiagramTitle] = useState('');
  const [diagramType, setDiagramType] = useState<'canvas' | 'note' | 'mixed'>('canvas');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info (simple decode, not verification)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.email, sub: payload.sub });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    setLoading(false);
  }, [router]);

  const handleCreateDiagram = async () => {
    if (!diagramTitle.trim()) {
      setError('Please enter a diagram title');
      return;
    }

    setCreating(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8082/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user?.sub || '',
        },
        body: JSON.stringify({
          title: diagramTitle,
          file_type: diagramType,
          canvas_data: diagramType === 'canvas' || diagramType === 'mixed' ? { shapes: [] } : null,
          note_content: diagramType === 'note' || diagramType === 'mixed' ? '' : null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create diagram');
      }

      const diagram = await response.json();
      
      // Redirect to the appropriate editor
      if (diagramType === 'canvas') {
        router.push(`/canvas/${diagram.id}`);
      } else if (diagramType === 'note') {
        router.push(`/note/${diagram.id}`);
      } else {
        router.push(`/canvas/${diagram.id}`); // Mixed defaults to canvas view
      }
    } catch (err: any) {
      console.error('Failed to create diagram:', err);
      setError(err.message || 'Failed to create diagram');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">AutoGraph v3</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to AutoGraph v3
          </h2>
          <p className="text-gray-600">
            Start creating professional diagrams with AI assistance
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                My Diagrams
              </h3>
              <span className="text-2xl">📊</span>
            </div>
            <p className="text-gray-600 mb-4">
              View and manage your diagrams
            </p>
            <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition">
              View Diagrams
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                New Diagram
              </h3>
              <span className="text-2xl">✨</span>
            </div>
            <p className="text-gray-600 mb-4">
              Create a new diagram from scratch
            </p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
            >
              Create Diagram
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                AI Generation
              </h3>
              <span className="text-2xl">🤖</span>
            </div>
            <p className="text-gray-600 mb-4">
              Generate diagrams with AI
            </p>
            <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition">
              Generate with AI
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Templates
              </h3>
              <span className="text-2xl">📋</span>
            </div>
            <p className="text-gray-600 mb-4">
              Start from a template
            </p>
            <button className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-md font-medium hover:bg-gray-300 transition">
              Browse Templates
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Shared with Me
              </h3>
              <span className="text-2xl">👥</span>
            </div>
            <p className="text-gray-600 mb-4">
              Diagrams shared by others
            </p>
            <button className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-md font-medium hover:bg-gray-300 transition">
              View Shared
            </button>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Settings
              </h3>
              <span className="text-2xl">⚙️</span>
            </div>
            <p className="text-gray-600 mb-4">
              Manage your account
            </p>
            <a href="/settings/security" className="block w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-md font-medium hover:bg-gray-300 transition text-center">
              Open Settings
            </a>
          </div>
        </div>

        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            🎉 Welcome to AutoGraph v3!
          </h3>
          <p className="text-blue-800">
            You've successfully registered and logged in. The dashboard is currently under development.
            More features coming soon!
          </p>
        </div>
      </div>

      {/* Create Diagram Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New Diagram</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Diagram Title
                </label>
                <input
                  id="title"
                  type="text"
                  value={diagramTitle}
                  onChange={(e) => setDiagramTitle(e.target.value)}
                  placeholder="My Architecture Diagram"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={creating}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Diagram Type
                </label>
                <div className="space-y-2">
                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="canvas"
                      checked={diagramType === 'canvas'}
                      onChange={(e) => setDiagramType(e.target.value as 'canvas')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Canvas</div>
                      <div className="text-sm text-gray-600">Visual diagram with shapes and connections</div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="note"
                      checked={diagramType === 'note'}
                      onChange={(e) => setDiagramType(e.target.value as 'note')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Note</div>
                      <div className="text-sm text-gray-600">Markdown document with text</div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="mixed"
                      checked={diagramType === 'mixed'}
                      onChange={(e) => setDiagramType(e.target.value as 'mixed')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Mixed</div>
                      <div className="text-sm text-gray-600">Canvas and notes combined</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setDiagramTitle('');
                  setDiagramType('canvas');
                  setError('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateDiagram}
                disabled={creating || !diagramTitle.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
