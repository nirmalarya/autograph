'use client';

import { useState } from 'react';
import MobileBottomNav from '../components/MobileBottomNav';

export default function MobileNavDemoPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [actionLog, setActionLog] = useState<string[]>([]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setActionLog((prev) => [...prev.slice(-9), `[${timestamp}] ${message}`]);
  };

  const handleCreateClick = () => {
    setCreateModalOpen(true);
    addLog('Create button clicked');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto p-4 pb-24">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">
          Mobile Bottom Navigation Demo
        </h1>
        <p className="text-gray-600 mb-6">
          This demo showcases the mobile bottom navigation bar. Resize your
          browser to mobile width or use developer tools to see it in action.
        </p>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-3 text-blue-900">
            How to View
          </h2>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">•</span>
              <span>
                <strong>Desktop:</strong> Open browser DevTools (F12), toggle
                device toolbar (Ctrl+Shift+M), select a mobile device
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">•</span>
              <span>
                <strong>Or:</strong> Resize your browser window to mobile width
                (&lt; 768px)
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">•</span>
              <span>
                <strong>Mobile device:</strong> View directly on your phone or
                tablet
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">•</span>
              <span>
                The bottom navigation will appear fixed at the bottom of the
                screen
              </span>
            </li>
          </ul>
        </div>

        {/* Features */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">
            Navigation Tabs
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <span className="text-xl">🏠</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Home</h3>
                  <p className="text-sm text-gray-600">Dashboard view</p>
                </div>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <span className="text-xl">🔍</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Search</h3>
                  <p className="text-sm text-gray-600">
                    Search modal with fullscreen UI
                  </p>
                </div>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <span className="text-xl">➕</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Create</h3>
                  <p className="text-sm text-gray-600">
                    Elevated center button
                  </p>
                </div>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <span className="text-xl">👤</span>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">Profile</h3>
                  <p className="text-sm text-gray-600">User profile page</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features List */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">
            Key Features
          </h2>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Fixed positioning:</strong> Always visible at bottom of
                screen
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Touch-friendly:</strong> Large tap targets (48px+) for
                easy mobile use
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Active state:</strong> Visual feedback showing current
                tab
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Icons + labels:</strong> Clear visual hierarchy with
                SVG icons
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Responsive:</strong> Only shows on mobile/tablet (&lt;
                768px)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Dark mode:</strong> Supports dark color scheme
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Safe area:</strong> Respects device safe areas (notch,
                etc.)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Search modal:</strong> Fullscreen search experience
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-600 mt-1">✓</span>
              <span>
                <strong>Content spacer:</strong> Prevents content from hiding
                behind nav
              </span>
            </li>
          </ul>
        </div>

        {/* Action Log */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">
            Action Log
          </h2>
          <div className="space-y-2 font-mono text-sm">
            {actionLog.length === 0 ? (
              <p className="text-gray-500 italic">
                No actions yet. Tap navigation buttons to see interactions.
              </p>
            ) : (
              actionLog.map((log, index) => (
                <div
                  key={index}
                  className="text-gray-700 bg-gray-50 p-2 rounded"
                >
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Technical Details */}
        <div className="bg-gray-100 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">
            Technical Details
          </h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p>
              <strong>Breakpoint:</strong> Shows below 768px (md breakpoint)
            </p>
            <p>
              <strong>Height:</strong> 64px (16 Tailwind units)
            </p>
            <p>
              <strong>Z-index:</strong> 50 (above most content)
            </p>
            <p>
              <strong>Position:</strong> Fixed to bottom-0 left-0 right-0
            </p>
            <p>
              <strong>Framework:</strong> Next.js 14+ with App Router
            </p>
            <p>
              <strong>Navigation:</strong> Uses useRouter and usePathname hooks
            </p>
            <p>
              <strong>Styling:</strong> Tailwind CSS with dark mode variants
            </p>
            <p>
              <strong>Accessibility:</strong> ARIA labels and semantic HTML
            </p>
          </div>
        </div>

        {/* Sample Content */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900">
            Sample Content
          </h2>
          <p className="text-gray-700 mb-4">
            This is sample content to demonstrate scrolling behavior. The
            bottom navigation stays fixed while you scroll.
          </p>
          <div className="space-y-4">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">
                  Section {i + 1}
                </h3>
                <p className="text-gray-600">
                  Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
                  do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav onCreateClick={handleCreateClick} />

      {/* Create Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full">
            <h3 className="text-xl font-semibold mb-4 text-gray-900">
              Create New Diagram
            </h3>
            <p className="text-gray-600 mb-6">
              This is a placeholder for the create dialog. In a real app, this
              would show creation options.
            </p>
            <button
              onClick={() => {
                setCreateModalOpen(false);
                addLog('Create modal closed');
              }}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
