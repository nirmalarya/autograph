'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useState } from 'react';

interface MobileBottomNavProps {
  onCreateClick?: () => void;
}

export default function MobileBottomNav({ onCreateClick }: MobileBottomNavProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [showSearchModal, setShowSearchModal] = useState(false);

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return pathname === '/dashboard' || pathname === '/';
    }
    return pathname?.startsWith(path);
  };

  const handleNavigation = (path: string, action?: () => void) => {
    if (action) {
      action();
    } else {
      router.push(path);
    }
  };

  return (
    <>
      {/* Mobile Bottom Navigation - Only visible on mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg z-50 safe-area-bottom">
        <div className="flex items-center justify-around h-16">
          {/* Home Tab */}
          <button
            onClick={() => handleNavigation('/dashboard')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition touch-manipulation ${
              isActive('/dashboard')
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <svg
              className="w-6 h-6 mb-1"
              fill={isActive('/dashboard') ? 'currentColor' : 'none'}
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            <span className="text-xs font-medium">Home</span>
          </button>

          {/* Search Tab */}
          <button
            onClick={() => setShowSearchModal(true)}
            className={`flex flex-col items-center justify-center flex-1 h-full transition touch-manipulation ${
              showSearchModal
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <svg
              className="w-6 h-6 mb-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <span className="text-xs font-medium">Search</span>
          </button>

          {/* Create Tab - Center with elevated button */}
          <button
            onClick={() => onCreateClick?.()}
            className="flex flex-col items-center justify-center flex-1 h-full transition touch-manipulation"
          >
            <div className="flex items-center justify-center w-14 h-14 -mt-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full shadow-lg">
              <svg
                className="w-7 h-7 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </div>
            <span className="text-xs font-medium text-gray-600 dark:text-gray-400 mt-1">Create</span>
          </button>

          {/* AI Generate Tab */}
          <button
            onClick={() => handleNavigation('/ai-generate')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition touch-manipulation ${
              isActive('/ai-generate')
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <svg
              className="w-6 h-6 mb-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            <span className="text-xs font-medium">AI</span>
          </button>

          {/* Profile Tab */}
          <button
            onClick={() => handleNavigation('/profile')}
            className={`flex flex-col items-center justify-center flex-1 h-full transition touch-manipulation ${
              isActive('/profile')
                ? 'text-blue-600 dark:text-blue-400'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <svg
              className="w-6 h-6 mb-1"
              fill={isActive('/profile') ? 'currentColor' : 'none'}
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
            <span className="text-xs font-medium">Profile</span>
          </button>
        </div>
      </nav>

      {/* Search Modal */}
      {showSearchModal && (
        <div className="md:hidden fixed inset-0 bg-white dark:bg-gray-900 z-50 flex flex-col">
          {/* Header */}
          <div className="flex items-center gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowSearchModal(false)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition touch-manipulation"
            >
              <svg
                className="w-6 h-6 text-gray-600 dark:text-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            <input
              type="text"
              placeholder="Search diagrams..."
              autoFocus
              className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Search Results */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
              <svg
                className="w-16 h-16 mx-auto mb-4 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <p className="text-lg font-medium">Start typing to search</p>
              <p className="text-sm mt-2">Find diagrams by title, type, or content</p>
            </div>
          </div>
        </div>
      )}

      {/* Spacer to prevent content from being hidden behind bottom nav */}
      <div className="md:hidden h-16" />
    </>
  );
}
