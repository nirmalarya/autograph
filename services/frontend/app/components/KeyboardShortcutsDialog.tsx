'use client';

import { useEffect, useState } from 'react';

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

interface KeyboardShortcutsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function KeyboardShortcutsDialog({
  isOpen,
  onClose,
}: KeyboardShortcutsDialogProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isMac, setIsMac] = useState(true);

  // Detect platform on mount
  useEffect(() => {
    setIsMac(navigator.platform.toUpperCase().indexOf('MAC') >= 0);
  }, []);

  // Close on Escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Prevent body scroll when dialog is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modKey = isMac ? '⌘' : 'Ctrl';
  const altKey = isMac ? '⌥' : 'Alt';
  const shiftKey = isMac ? '⇧' : 'Shift';

  // Comprehensive list of keyboard shortcuts
  const shortcuts: Shortcut[] = [
    // General
    { keys: [modKey, 'K'], description: 'Open command palette', category: 'General' },
    { keys: [modKey, '?'], description: 'Show keyboard shortcuts', category: 'General' },
    { keys: [modKey, 'S'], description: 'Save diagram', category: 'General' },
    { keys: [modKey, 'P'], description: 'Print / Export', category: 'General' },
    { keys: ['Esc'], description: 'Close dialog / Cancel', category: 'General' },
    { keys: [modKey, ','], description: 'Open settings', category: 'General' },
    { keys: [modKey, '/'], description: 'Focus search', category: 'General' },

    // Navigation
    { keys: [modKey, '1'], description: 'Go to Dashboard', category: 'Navigation' },
    { keys: [modKey, '2'], description: 'Go to Recent', category: 'Navigation' },
    { keys: [modKey, '3'], description: 'Go to Starred', category: 'Navigation' },
    { keys: [modKey, '4'], description: 'Go to Shared', category: 'Navigation' },
    { keys: [modKey, '5'], description: 'Go to Trash', category: 'Navigation' },
    { keys: ['↑', '↓'], description: 'Navigate items', category: 'Navigation' },
    { keys: ['Enter'], description: 'Open selected item', category: 'Navigation' },
    { keys: ['Backspace'], description: 'Go back', category: 'Navigation' },

    // Canvas - Drawing Tools
    { keys: ['V'], description: 'Select tool', category: 'Canvas - Tools' },
    { keys: ['R'], description: 'Rectangle tool', category: 'Canvas - Tools' },
    { keys: ['O'], description: 'Circle tool', category: 'Canvas - Tools' },
    { keys: ['A'], description: 'Arrow tool', category: 'Canvas - Tools' },
    { keys: ['L'], description: 'Line tool', category: 'Canvas - Tools' },
    { keys: ['T'], description: 'Text tool', category: 'Canvas - Tools' },
    { keys: ['P'], description: 'Pen tool', category: 'Canvas - Tools' },
    { keys: ['F'], description: 'Frame/Figure tool', category: 'Canvas - Tools' },
    { keys: ['H'], description: 'Hand tool (pan)', category: 'Canvas - Tools' },

    // Canvas - Editing
    { keys: [modKey, 'C'], description: 'Copy', category: 'Canvas - Editing' },
    { keys: [modKey, 'X'], description: 'Cut', category: 'Canvas - Editing' },
    { keys: [modKey, 'V'], description: 'Paste', category: 'Canvas - Editing' },
    { keys: [modKey, 'D'], description: 'Duplicate', category: 'Canvas - Editing' },
    { keys: [modKey, 'Z'], description: 'Undo', category: 'Canvas - Editing' },
    { keys: [modKey, shiftKey, 'Z'], description: 'Redo', category: 'Canvas - Editing' },
    { keys: [modKey, 'Y'], description: 'Redo (alternative)', category: 'Canvas - Editing' },
    { keys: ['Delete'], description: 'Delete selected', category: 'Canvas - Editing' },
    { keys: ['Backspace'], description: 'Delete selected', category: 'Canvas - Editing' },

    // Canvas - Selection
    { keys: [modKey, 'A'], description: 'Select all', category: 'Canvas - Selection' },
    { keys: [modKey, shiftKey, 'A'], description: 'Deselect all', category: 'Canvas - Selection' },
    { keys: ['Shift', '+ Click'], description: 'Add to selection', category: 'Canvas - Selection' },
    { keys: [modKey, '+ Click'], description: 'Toggle selection', category: 'Canvas - Selection' },

    // Canvas - Grouping & Alignment
    { keys: [modKey, 'G'], description: 'Group selection', category: 'Canvas - Grouping' },
    { keys: [modKey, shiftKey, 'G'], description: 'Ungroup selection', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'L'], description: 'Align left', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'R'], description: 'Align right', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'T'], description: 'Align top', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'B'], description: 'Align bottom', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'H'], description: 'Align center horizontal', category: 'Canvas - Grouping' },
    { keys: [modKey, altKey, 'V'], description: 'Align center vertical', category: 'Canvas - Grouping' },

    // Canvas - Z-Order
    { keys: [modKey, ']'], description: 'Bring forward', category: 'Canvas - Z-Order' },
    { keys: [modKey, '['], description: 'Send backward', category: 'Canvas - Z-Order' },
    { keys: [modKey, shiftKey, ']'], description: 'Bring to front', category: 'Canvas - Z-Order' },
    { keys: [modKey, shiftKey, '['], description: 'Send to back', category: 'Canvas - Z-Order' },

    // Canvas - View
    { keys: [modKey, '0'], description: 'Zoom to 100%', category: 'Canvas - View' },
    { keys: [modKey, '1'], description: 'Zoom to fit', category: 'Canvas - View' },
    { keys: [modKey, '2'], description: 'Zoom to selection', category: 'Canvas - View' },
    { keys: [modKey, '+'], description: 'Zoom in', category: 'Canvas - View' },
    { keys: [modKey, '-'], description: 'Zoom out', category: 'Canvas - View' },
    { keys: ['Space', '+ Drag'], description: 'Pan canvas', category: 'Canvas - View' },
    { keys: ['G'], description: 'Toggle grid', category: 'Canvas - View' },
    { keys: [modKey, 'L'], description: 'Lock/Unlock element', category: 'Canvas - View' },
    { keys: [modKey, shiftKey, 'H'], description: 'Hide/Show element', category: 'Canvas - View' },

    // Canvas - Insert
    { keys: ['/'], description: 'Open insert menu', category: 'Canvas - Insert' },
    { keys: [modKey, 'I'], description: 'Insert icon', category: 'Canvas - Insert' },
    { keys: [modKey, 'E'], description: 'Insert emoji', category: 'Canvas - Insert' },

    // Text Editing
    { keys: [modKey, 'B'], description: 'Bold', category: 'Text Editing' },
    { keys: [modKey, 'I'], description: 'Italic', category: 'Text Editing' },
    { keys: [modKey, 'U'], description: 'Underline', category: 'Text Editing' },
    { keys: [modKey, shiftKey, 'X'], description: 'Strikethrough', category: 'Text Editing' },
    { keys: [modKey, 'K'], description: 'Insert link', category: 'Text Editing' },

    // File Operations
    { keys: [modKey, 'N'], description: 'New diagram', category: 'File Operations' },
    { keys: [modKey, 'O'], description: 'Open diagram', category: 'File Operations' },
    { keys: [modKey, 'W'], description: 'Close diagram', category: 'File Operations' },
    { keys: [modKey, shiftKey, 'S'], description: 'Save as', category: 'File Operations' },
    { keys: [modKey, 'E'], description: 'Export', category: 'File Operations' },

    // Collaboration
    { keys: [modKey, shiftKey, 'C'], description: 'Add comment', category: 'Collaboration' },
    { keys: [modKey, shiftKey, 'M'], description: 'Mention user', category: 'Collaboration' },
    { keys: [modKey, shiftKey, 'U'], description: 'Show collaborators', category: 'Collaboration' },

    // Version History
    { keys: [modKey, shiftKey, 'H'], description: 'Show version history', category: 'Version History' },
    { keys: [modKey, shiftKey, 'R'], description: 'Restore version', category: 'Version History' },

    // Presentation Mode
    { keys: ['F11'], description: 'Toggle fullscreen', category: 'Presentation' },
    { keys: [modKey, shiftKey, 'P'], description: 'Presentation mode', category: 'Presentation' },
    { keys: ['→'], description: 'Next slide', category: 'Presentation' },
    { keys: ['←'], description: 'Previous slide', category: 'Presentation' },
  ];

  // Filter shortcuts based on search query
  const filteredShortcuts = shortcuts.filter((shortcut) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      shortcut.description.toLowerCase().includes(query) ||
      shortcut.category.toLowerCase().includes(query) ||
      shortcut.keys.some((key) => key.toLowerCase().includes(query))
    );
  });

  // Group shortcuts by category
  const groupedShortcuts = filteredShortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, Shortcut[]>);

  const categories = Object.keys(groupedShortcuts).sort();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Keyboard Shortcuts
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search shortcuts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
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
          </div>

          {/* Platform indicator */}
          <div className="mt-3 text-sm text-gray-500">
            Showing shortcuts for {isMac ? 'macOS' : 'Windows/Linux'}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {categories.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No shortcuts found matching "{searchQuery}"
            </div>
          ) : (
            <div className="space-y-6">
              {categories.map((category) => (
                <div key={category}>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 sticky top-0 bg-white py-2 border-b border-gray-200">
                    {category}
                  </h3>
                  <div className="space-y-2">
                    {groupedShortcuts[category].map((shortcut, index) => (
                      <div
                        key={`${category}-${index}`}
                        className="flex items-center justify-between py-2 px-3 rounded hover:bg-gray-50 transition-colors"
                      >
                        <span className="text-gray-700">
                          {shortcut.description}
                        </span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, keyIndex) => (
                            <span key={keyIndex} className="flex items-center">
                              <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded shadow-sm">
                                {key}
                              </kbd>
                              {keyIndex < shortcut.keys.length - 1 && (
                                <span className="mx-1 text-gray-400">+</span>
                              )}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              Press <kbd className="px-2 py-1 text-xs font-semibold text-gray-800 bg-white border border-gray-300 rounded">Esc</kbd> to close
            </div>
            <div>
              {filteredShortcuts.length} shortcut{filteredShortcuts.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
