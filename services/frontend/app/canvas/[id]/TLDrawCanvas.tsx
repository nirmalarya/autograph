'use client';

import { useEffect, useState, useCallback } from 'react';
import { Tldraw, Editor, TLUiOverrides } from '@tldraw/tldraw';
import '@tldraw/tldraw/tldraw.css';

interface TLDrawCanvasProps {
  initialData?: any;
  onSave?: (editor: any) => void;
  theme?: 'light' | 'dark';
}

export default function TLDrawCanvas({ initialData, onSave, theme = 'light' }: TLDrawCanvasProps) {
  const [mounted, setMounted] = useState(false);
  const [editor, setEditor] = useState<Editor | null>(null);

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

  // Update theme when it changes
  useEffect(() => {
    if (!editor || !mounted) return;
    
    if (theme === 'dark') {
      editor.user.updateUserPreferences({ colorScheme: 'dark' });
    } else {
      editor.user.updateUserPreferences({ colorScheme: 'light' });
    }
  }, [theme, editor, mounted]);

  // Touch gesture handling
  useEffect(() => {
    if (!editor || !mounted) return;

    // Enable touch gestures
    const handleTouchStart = (e: TouchEvent) => {
      // Long-press detection for context menu
      if (e.touches.length === 1) {
        const touch = e.touches[0];
        const longPressTimer = setTimeout(() => {
          // Trigger context menu on long press
          const event = new MouseEvent('contextmenu', {
            bubbles: true,
            cancelable: true,
            clientX: touch.clientX,
            clientY: touch.clientY,
          });
          e.target?.dispatchEvent(event);
        }, 500); // 500ms for long press

        const handleTouchEnd = () => {
          clearTimeout(longPressTimer);
          document.removeEventListener('touchend', handleTouchEnd);
          document.removeEventListener('touchmove', handleTouchMove);
        };

        const handleTouchMove = () => {
          clearTimeout(longPressTimer);
          document.removeEventListener('touchend', handleTouchEnd);
          document.removeEventListener('touchmove', handleTouchMove);
        };

        document.addEventListener('touchend', handleTouchEnd);
        document.addEventListener('touchmove', handleTouchMove);
      }
    };

    // Add touch event listeners
    const canvasElement = document.querySelector('.tl-container');
    if (canvasElement) {
      canvasElement.addEventListener('touchstart', handleTouchStart as any);
    }

    return () => {
      if (canvasElement) {
        canvasElement.removeEventListener('touchstart', handleTouchStart as any);
      }
    };
  }, [editor, mounted]);

  // Custom UI overrides for touch-friendly interface
  const uiOverrides: TLUiOverrides = {
    // TLDraw handles touch gestures natively
    // Context menu styling is handled via CSS
  };

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
    <div className={theme === 'dark' ? 'tldraw__editor--dark' : ''} style={{ width: '100%', height: '100%' }}>
      <Tldraw
        snapshot={initialData}
        overrides={uiOverrides}
        onMount={(editor: Editor) => {
          // Store editor reference globally for save button
          (window as any).tldrawEditor = editor;
          setEditor(editor);
          
          // Load existing canvas data if available
          if (initialData) {
            try {
              editor.store.loadSnapshot(initialData);
            } catch (err) {
              console.error('Failed to load canvas snapshot:', err);
            }
          }

          // Configure touch-friendly settings
          // TLDraw 2.4.0 has built-in touch gesture support:
          // - Pinch to zoom (2 fingers pinch in/out)
          // - Two-finger pan (2 fingers drag)
          // - Single finger to draw/select
          // These are enabled by default in TLDraw
          
          // Apply theme to editor
          if (theme === 'dark') {
            editor.user.updateUserPreferences({ colorScheme: 'dark' });
          } else {
            editor.user.updateUserPreferences({ colorScheme: 'light' });
          }
        }}
      />
    </div>
  );
}
