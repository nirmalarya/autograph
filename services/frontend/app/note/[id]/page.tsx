'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { API_ENDPOINTS } from '@/lib/api-config';

export default function NoteEditorPage() {
  const router = useRouter();
  const params = useParams();
  const diagramId = params.id as string;
  
  const [diagram, setDiagram] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);

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
      
      const response = await fetch(API_ENDPOINTS.diagrams.get(diagramId), {
        headers: {
          'X-User-ID': payload.sub,
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Note not found');
        } else if (response.status === 403) {
          throw new Error('You do not have permission to access this note');
        }
        throw new Error('Failed to load note');
      }

      const data = await response.json();
      setDiagram(data);
    } catch (err: any) {
      console.error('Failed to fetch note:', err);
      setError(err.message || 'Failed to load note');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading note...</p>
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
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToDashboard}
                className="text-gray-600 hover:text-gray-900 transition"
              >
                ← Back
              </button>
              <div className="border-l border-gray-300 h-6"></div>
              <h1 className="text-lg font-semibold text-gray-900">
                {diagram?.title || 'Untitled Note'}
              </h1>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                v{diagram?.current_version || 1}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition">
                Share
              </button>
              <button className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition">
                Save
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Note Editor Area */}
      <div className="h-[calc(100vh-4rem)] bg-white">
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="text-6xl mb-4">📝</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Note Editor</h2>
            <p className="text-gray-600 mb-4">
              Your note "{diagram?.title}" has been created successfully!
            </p>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 max-w-md mx-auto">
              <h3 className="font-semibold text-gray-900 mb-2">Note Details:</h3>
              <div className="text-left space-y-1 text-sm">
                <p><span className="font-medium">ID:</span> {diagram?.id}</p>
                <p><span className="font-medium">Type:</span> {diagram?.file_type}</p>
                <p><span className="font-medium">Version:</span> {diagram?.current_version}</p>
                <p><span className="font-medium">Created:</span> {new Date(diagram?.created_at).toLocaleString()}</p>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Markdown editor integration coming soon...
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
