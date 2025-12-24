'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';

interface Command {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  shortcut?: string;
  category: 'files' | 'commands' | 'navigation';
  action: () => void | Promise<void>;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateDiagram?: (type: 'canvas' | 'note' | 'mixed' | 'mermaid') => void;
  diagrams?: Array<{
    id: string;
    title: string;
    file_type: string;
  }>;
}

export default function CommandPalette({
  isOpen,
  onClose,
  onCreateDiagram,
  diagrams = [],
}: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Load recent commands from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentCommands');
    if (stored) {
      try {
        setRecentCommands(JSON.parse(stored));
      } catch (e) {
        console.error('Failed to parse recent commands:', e);
      }
    }
  }, []);

  // Save command to recent
  const saveRecentCommand = useCallback((commandId: string) => {
    setRecentCommands((prev) => {
      const updated = [commandId, ...prev.filter((id) => id !== commandId)].slice(0, 5);
      localStorage.setItem('recentCommands', JSON.stringify(updated));
      return updated;
    });
  }, []);

  // Define available commands
  const commands: Command[] = [
    // File commands
    {
      id: 'new-canvas',
      label: 'New Canvas Diagram',
      description: 'Create a new canvas diagram with drawing tools',
      icon: '🎨',
      category: 'commands',
      action: () => {
        saveRecentCommand('new-canvas');
        onCreateDiagram?.('canvas');
        onClose();
      },
    },
    {
      id: 'new-note',
      label: 'New Note',
      description: 'Create a new markdown note',
      icon: '📝',
      category: 'commands',
      action: () => {
        saveRecentCommand('new-note');
        onCreateDiagram?.('note');
        onClose();
      },
    },
    {
      id: 'new-mermaid',
      label: 'New Mermaid Diagram',
      description: 'Create a new diagram-as-code with Mermaid',
      icon: '⚡',
      category: 'commands',
      action: () => {
        saveRecentCommand('new-mermaid');
        onCreateDiagram?.('mermaid');
        onClose();
      },
    },
    // Navigation commands
    {
      id: 'go-dashboard',
      label: 'Go to Dashboard',
      description: 'Navigate to main dashboard',
      icon: '🏠',
      shortcut: 'Ctrl+H',
      category: 'navigation',
      action: () => {
        saveRecentCommand('go-dashboard');
        router.push('/dashboard');
        onClose();
      },
    },
    {
      id: 'go-starred',
      label: 'Go to Starred',
      description: 'View your starred diagrams',
      icon: '⭐',
      category: 'navigation',
      action: () => {
        saveRecentCommand('go-starred');
        router.push('/dashboard?tab=starred');
        onClose();
      },
    },
    {
      id: 'go-recent',
      label: 'Go to Recent',
      description: 'View recently accessed diagrams',
      icon: '🕐',
      category: 'navigation',
      action: () => {
        saveRecentCommand('go-recent');
        router.push('/dashboard?tab=recent');
        onClose();
      },
    },
    {
      id: 'go-shared',
      label: 'Go to Shared with Me',
      description: 'View diagrams shared with you',
      icon: '👥',
      category: 'navigation',
      action: () => {
        saveRecentCommand('go-shared');
        router.push('/dashboard?tab=shared');
        onClose();
      },
    },
    {
      id: 'go-trash',
      label: 'Go to Trash',
      description: 'View deleted diagrams',
      icon: '🗑️',
      category: 'navigation',
      action: () => {
        saveRecentCommand('go-trash');
        router.push('/dashboard?tab=trash');
        onClose();
      },
    },
    // File navigation
    ...diagrams.map((diagram) => ({
      id: `open-${diagram.id}`,
      label: diagram.title,
      description: `Open ${diagram.file_type} diagram`,
      icon: diagram.file_type === 'canvas' ? '🎨' : diagram.file_type === 'note' ? '📝' : '📊',
      category: 'files' as const,
      action: () => {
        saveRecentCommand(`open-${diagram.id}`);
        router.push(`/editor/${diagram.id}`);
        onClose();
      },
    })),
  ];

  // Fuzzy match function
  const fuzzyMatch = (text: string, query: string): boolean => {
    if (!query) return true;
    
    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    
    // Direct substring match
    if (lowerText.includes(lowerQuery)) return true;
    
    // Fuzzy matching: check if all query characters appear in order
    let queryIndex = 0;
    for (let i = 0; i < lowerText.length && queryIndex < lowerQuery.length; i++) {
      if (lowerText[i] === lowerQuery[queryIndex]) {
        queryIndex++;
      }
    }
    return queryIndex === lowerQuery.length;
  };

  // Filter and sort commands
  const filteredCommands = commands.filter((cmd) => {
    const matchLabel = fuzzyMatch(cmd.label, query);
    const matchDesc = cmd.description ? fuzzyMatch(cmd.description, query) : false;
    return matchLabel || matchDesc;
  });

  // Prioritize recent commands
  const sortedCommands = [...filteredCommands].sort((a, b) => {
    const aRecent = recentCommands.indexOf(a.id);
    const bRecent = recentCommands.indexOf(b.id);
    
    if (aRecent >= 0 && bRecent >= 0) return aRecent - bRecent;
    if (aRecent >= 0) return -1;
    if (bRecent >= 0) return 1;
    
    return a.category.localeCompare(b.category);
  });

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % sortedCommands.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + sortedCommands.length) % sortedCommands.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (sortedCommands[selectedIndex]) {
          sortedCommands[selectedIndex].action();
        }
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, selectedIndex, sortedCommands, onClose]);

  // Reset state when opened
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
      if (selectedElement) {
        selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-2xl w-full max-w-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="p-4 border-b">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            placeholder="Type a command or search..."
            className="w-full px-4 py-2 text-lg border-none outline-none"
          />
          <p className="text-xs text-gray-500 mt-2">
            Use ↑↓ to navigate, Enter to select, Esc to close
          </p>
        </div>

        {/* Commands List */}
        <div
          ref={listRef}
          className="max-h-96 overflow-y-auto"
        >
          {sortedCommands.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p className="text-lg mb-2">No commands found</p>
              <p className="text-sm">Try a different search term</p>
            </div>
          ) : (
            sortedCommands.map((cmd, index) => {
              const isRecent = recentCommands.includes(cmd.id);
              return (
                <div
                  key={cmd.id}
                  className={`flex items-center px-4 py-3 cursor-pointer transition-colors ${
                    index === selectedIndex
                      ? 'bg-blue-50 border-l-4 border-blue-500'
                      : 'border-l-4 border-transparent hover:bg-gray-50'
                  }`}
                  onClick={() => cmd.action()}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  {/* Icon */}
                  <div className="flex-shrink-0 mr-3 text-2xl">
                    {cmd.icon || '📄'}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 truncate">
                        {cmd.label}
                      </span>
                      {isRecent && (
                        <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                          Recent
                        </span>
                      )}
                    </div>
                    {cmd.description && (
                      <p className="text-sm text-gray-500 truncate">
                        {cmd.description}
                      </p>
                    )}
                  </div>

                  {/* Shortcut */}
                  {cmd.shortcut && (
                    <div className="ml-4 text-xs text-gray-400 font-mono">
                      {cmd.shortcut}
                    </div>
                  )}

                  {/* Category badge */}
                  <div className="ml-4">
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        cmd.category === 'commands'
                          ? 'bg-green-100 text-green-700'
                          : cmd.category === 'navigation'
                          ? 'bg-purple-100 text-purple-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {cmd.category}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-4">
            <span>
              <kbd className="px-2 py-1 bg-white border rounded">⌘K</kbd> to toggle
            </span>
            <span>
              <kbd className="px-2 py-1 bg-white border rounded">↑↓</kbd> to navigate
            </span>
            <span>
              <kbd className="px-2 py-1 bg-white border rounded">Enter</kbd> to select
            </span>
          </div>
          <div>
            {sortedCommands.length} command{sortedCommands.length !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </div>
  );
}
