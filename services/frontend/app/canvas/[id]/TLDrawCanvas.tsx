'use client';

import { useEffect, useState } from 'react';
import { Tldraw, Editor } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';

interface TLDrawCanvasProps {
  initialData?: any;
  onSave?: (editor: any) => void;
}

export default function TLDrawCanvas({ initialData, onSave }: TLDrawCanvasProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Set up auto-save interval
  useEffect(() => {
    if (!onSave || !mounted) return;

    const autoSaveInterval = setInterval(() => {
      const editor = (window as any).tldrawEditor;
      if (editor) {
        onSave(editor);
      }
    }, 300000); // 5 minutes = 300,000 milliseconds

    return () => {
      clearInterval(autoSaveInterval);
    };
  }, [onSave, mounted]);

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading canvas...</p>
        </div>
      </div>
    );
  }

  return (
    <Tldraw
      snapshot={initialData}
      onMount={(editor: Editor) => {
        // Store editor reference globally for save button
        (window as any).tldrawEditor = editor;
        
        // Load existing canvas data if available
        if (initialData) {
          try {
            editor.store.loadSnapshot(initialData);
          } catch (err) {
            console.error('Failed to load canvas snapshot:', err);
          }
        }
      }}
    />
  );
}
