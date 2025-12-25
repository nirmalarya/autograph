'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { API_ENDPOINTS } from '@/lib/api-config';

export default function NewCanvasPage() {
  const router = useRouter();
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(true);

  useEffect(() => {
    createNewCanvas();
  }, []);

  const createNewCanvas = async () => {
    try {
      // Check authentication
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Decode JWT to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));

      // Create a new canvas diagram
      const response = await fetch(API_ENDPOINTS.diagrams.create, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': payload.sub,
        },
        body: JSON.stringify({
          title: 'Untitled Canvas',
          type: 'canvas',
          canvas_data: {
            // Empty TLDraw canvas initial state
            store: {},
            schema: {
              schemaVersion: 2,
              sequences: {
                com: 5,
              },
            },
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create canvas');
      }

      const newDiagram = await response.json();

      // Redirect to the canvas editor
      router.push(`/canvas/${newDiagram.id}`);
    } catch (err: any) {
      console.error('Failed to create canvas:', err);
      setError(err.message || 'Failed to create canvas');
      setCreating(false);
    }
  };

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Creating new canvas...</p>
      </div>
    </main>
  );
}
