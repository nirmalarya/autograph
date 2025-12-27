'use client';

import { useState } from 'react';
import { useSwipeGesture } from '@/src/hooks/useSwipeGesture';

export default function SwipeGestureDemo() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [swipeCount, setSwipeCount] = useState({ left: 0, right: 0 });
  const [lastSwipe, setLastSwipe] = useState<'left' | 'right' | null>(null);

  useSwipeGesture({
    onSwipeLeft: () => {
      setSidebarOpen(false);
      setSwipeCount(prev => ({ ...prev, left: prev.left + 1 }));
      setLastSwipe('left');
      setTimeout(() => setLastSwipe(null), 500);
    },
    onSwipeRight: () => {
      setSidebarOpen(true);
      setSwipeCount(prev => ({ ...prev, right: prev.right + 1 }));
      setLastSwipe('right');
      setTimeout(() => setLastSwipe(null), 500);
    },
    minSwipeDistance: 50,
    maxSwipeTime: 300,
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 relative overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-80 bg-white dark:bg-gray-800 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="swipe-sidebar"
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Menu
            </h2>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition"
              aria-label="Close sidebar"
              data-testid="close-sidebar-button"
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
          </div>

          <nav className="space-y-2">
            <a href="#" className="block px-4 py-3 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition">
              Home
            </a>
            <a href="#" className="block px-4 py-3 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition">
              Dashboard
            </a>
            <a href="#" className="block px-4 py-3 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition">
              Projects
            </a>
            <a href="#" className="block px-4 py-3 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white transition">
              Settings
            </a>
          </nav>

          <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
              How to Use
            </h3>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
              <li>• Swipe right to open</li>
              <li>• Swipe left to close</li>
              <li>• Or use the button</li>
            </ul>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
          data-testid="overlay"
        />
      )}

      {/* Main Content */}
      <main className="p-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Swipe Gesture Demo
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Feature #607: Mobile menu swipe gestures
              </p>
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition"
              aria-label="Toggle sidebar"
              data-testid="toggle-sidebar-button"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-md">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Sidebar Status
              </div>
              <div className={`text-xl font-bold ${sidebarOpen ? 'text-green-600' : 'text-gray-400'}`}>
                {sidebarOpen ? 'Open' : 'Closed'}
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-md">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                Last Swipe
              </div>
              <div className={`text-xl font-bold ${lastSwipe ? 'text-blue-600' : 'text-gray-400'}`}>
                {lastSwipe ? (lastSwipe === 'left' ? '← Left' : 'Right →') : 'None'}
              </div>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            How to Test
          </h2>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-300 font-bold">
                1
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Swipe Right to Open
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Place your finger on the left edge of the screen and swipe right. The sidebar will slide in.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-300 font-bold">
                2
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Swipe Left to Close
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  When the sidebar is open, swipe left anywhere on the screen to close it.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-300 font-bold">
                3
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Smooth Animation
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  Notice the smooth slide animation (300ms with ease-in-out timing).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Swipe Statistics
          </h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-md">
              <div className="text-sm text-blue-600 dark:text-blue-400 mb-1">
                Right Swipes (Open)
              </div>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400" data-testid="swipe-right-count">
                {swipeCount.right}
              </div>
            </div>

            <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-md">
              <div className="text-sm text-purple-600 dark:text-purple-400 mb-1">
                Left Swipes (Close)
              </div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400" data-testid="swipe-left-count">
                {swipeCount.left}
              </div>
            </div>
          </div>
        </div>

        {/* Technical Details */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Technical Details
          </h2>
          <div className="space-y-3 text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Hook: <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">useSwipeGesture</code></span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Minimum distance: <strong>50px</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Maximum time: <strong>300ms</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Animation: <strong>300ms ease-in-out</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>Touch events: <strong>touchstart, touchmove, touchend</strong></span>
            </div>
          </div>
        </div>

        {/* Mobile Note */}
        <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-1">
                Best on Mobile
              </h3>
              <p className="text-yellow-800 dark:text-yellow-200 text-sm">
                Swipe gestures work best on touch devices. Try on your phone or tablet, or use Chrome DevTools device mode.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
