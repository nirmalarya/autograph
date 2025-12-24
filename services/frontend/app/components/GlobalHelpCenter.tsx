/**
 * Global Help Center Component
 * 
 * Provides global access to the help center with:
 * - Floating help button (bottom-right)
 * - Global keyboard shortcut (?)
 * - Accessible from anywhere in the app
 */

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { HelpCircle } from 'lucide-react';

// Dynamically import HelpCenter to reduce initial bundle size
const HelpCenter = dynamic(() => import('./HelpCenter'), {
  ssr: false,
});

export default function GlobalHelpCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Global keyboard shortcut: ? key
  useEffect(() => {
    if (!mounted) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Check if ? key is pressed (Shift + /)
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Don't trigger if user is typing in an input/textarea
        const target = e.target as HTMLElement;
        if (
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable
        ) {
          return;
        }
        
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mounted]);

  const handleOpen = useCallback(() => {
    setIsOpen(true);
  }, []);

  const handleClose = useCallback(() => {
    setIsOpen(false);
  }, []);

  if (!mounted) return null;

  return (
    <>
      {/* Floating Help Button */}
      <button
        onClick={handleOpen}
        className="fixed bottom-6 right-6 z-40 p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200 touch-target-large group"
        aria-label="Open help center (Press ? key)"
        title="Help Center (Press ? key)"
      >
        <HelpCircle className="w-6 h-6" />
        <span className="absolute bottom-full right-0 mb-2 px-3 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          Help (Press ?)
        </span>
      </button>

      {/* Help Center Modal */}
      <HelpCenter isOpen={isOpen} onClose={handleClose} />
    </>
  );
}
