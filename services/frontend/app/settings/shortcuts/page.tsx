'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Keyboard, RotateCcw, Save, X, Check } from 'lucide-react';
import Button from '../../components/Button';

interface ShortcutConfig {
  id: string;
  action: string;
  keys: string[];
  category: string;
  description: string;
  customizable: boolean;
}

const DEFAULT_SHORTCUTS: ShortcutConfig[] = [
  // General
  { id: 'cmd-k', action: 'openCommandPalette', keys: ['Meta', 'K'], category: 'General', description: 'Open command palette', customizable: true },
  { id: 'cmd-?', action: 'showShortcuts', keys: ['Meta', 'Shift', '/'], category: 'General', description: 'Show keyboard shortcuts', customizable: true },
  { id: 'cmd-s', action: 'save', keys: ['Meta', 'S'], category: 'General', description: 'Save diagram', customizable: true },
  { id: 'cmd-p', action: 'export', keys: ['Meta', 'P'], category: 'General', description: 'Print / Export', customizable: true },
  { id: 'cmd-/', action: 'focusSearch', keys: ['Meta', '/'], category: 'General', description: 'Focus search', customizable: true },
  
  // Navigation
  { id: 'cmd-1', action: 'goDashboard', keys: ['Meta', '1'], category: 'Navigation', description: 'Go to Dashboard', customizable: true },
  { id: 'cmd-2', action: 'goRecent', keys: ['Meta', '2'], category: 'Navigation', description: 'Go to Recent', customizable: true },
  { id: 'cmd-3', action: 'goStarred', keys: ['Meta', '3'], category: 'Navigation', description: 'Go to Starred', customizable: true },
  
  // Canvas - Tools
  { id: 'tool-v', action: 'selectTool', keys: ['V'], category: 'Canvas - Tools', description: 'Select tool', customizable: true },
  { id: 'tool-r', action: 'rectangleTool', keys: ['R'], category: 'Canvas - Tools', description: 'Rectangle tool', customizable: true },
  { id: 'tool-o', action: 'circleTool', keys: ['O'], category: 'Canvas - Tools', description: 'Circle tool', customizable: true },
  { id: 'tool-a', action: 'arrowTool', keys: ['A'], category: 'Canvas - Tools', description: 'Arrow tool', customizable: true },
  { id: 'tool-l', action: 'lineTool', keys: ['L'], category: 'Canvas - Tools', description: 'Line tool', customizable: true },
  { id: 'tool-t', action: 'textTool', keys: ['T'], category: 'Canvas - Tools', description: 'Text tool', customizable: true },
  { id: 'tool-p', action: 'penTool', keys: ['P'], category: 'Canvas - Tools', description: 'Pen tool', customizable: true },
  { id: 'tool-f', action: 'frameTool', keys: ['F'], category: 'Canvas - Tools', description: 'Frame/Figure tool', customizable: true },
  
  // Canvas - Editing
  { id: 'cmd-c', action: 'copy', keys: ['Meta', 'C'], category: 'Canvas - Editing', description: 'Copy', customizable: false },
  { id: 'cmd-x', action: 'cut', keys: ['Meta', 'X'], category: 'Canvas - Editing', description: 'Cut', customizable: false },
  { id: 'cmd-v', action: 'paste', keys: ['Meta', 'V'], category: 'Canvas - Editing', description: 'Paste', customizable: false },
  { id: 'cmd-d', action: 'duplicate', keys: ['Meta', 'D'], category: 'Canvas - Editing', description: 'Duplicate', customizable: true },
  { id: 'cmd-z', action: 'undo', keys: ['Meta', 'Z'], category: 'Canvas - Editing', description: 'Undo', customizable: false },
  { id: 'cmd-shift-z', action: 'redo', keys: ['Meta', 'Shift', 'Z'], category: 'Canvas - Editing', description: 'Redo', customizable: false },
  
  // Canvas - Grouping
  { id: 'cmd-g', action: 'group', keys: ['Meta', 'G'], category: 'Canvas - Grouping', description: 'Group selection', customizable: true },
  { id: 'cmd-shift-g', action: 'ungroup', keys: ['Meta', 'Shift', 'G'], category: 'Canvas - Grouping', description: 'Ungroup selection', customizable: true },
  
  // File Operations
  { id: 'cmd-n', action: 'newDiagram', keys: ['Meta', 'N'], category: 'File Operations', description: 'New diagram', customizable: true },
  { id: 'cmd-o', action: 'openDiagram', keys: ['Meta', 'O'], category: 'File Operations', description: 'Open diagram', customizable: true },
];

export default function ShortcutsSettingsPage() {
  const router = useRouter();
  const [shortcuts, setShortcuts] = useState<ShortcutConfig[]>(DEFAULT_SHORTCUTS);
  const [editingShortcut, setEditingShortcut] = useState<string | null>(null);
  const [recordingKeys, setRecordingKeys] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [isMac, setIsMac] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Detect platform
    setIsMac(navigator.platform.toUpperCase().indexOf('MAC') >= 0);
    
    // Load custom shortcuts from localStorage
    const savedShortcuts = localStorage.getItem('custom_shortcuts');
    if (savedShortcuts) {
      try {
        const custom = JSON.parse(savedShortcuts);
        setShortcuts(prevShortcuts => 
          prevShortcuts.map(shortcut => {
            const customized = custom[shortcut.id];
            return customized ? { ...shortcut, keys: customized.keys } : shortcut;
          })
        );
      } catch (err) {
        console.error('Failed to load custom shortcuts:', err);
      }
    }
  }, []);

  const startRecording = (shortcutId: string) => {
    setEditingShortcut(shortcutId);
    setRecordingKeys([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!editingShortcut) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    const keys: string[] = [];
    
    if (e.metaKey) keys.push('Meta');
    if (e.ctrlKey) keys.push('Ctrl');
    if (e.altKey) keys.push('Alt');
    if (e.shiftKey) keys.push('Shift');
    
    // Add the key itself if it's not a modifier
    if (e.key && !['Meta', 'Control', 'Alt', 'Shift'].includes(e.key)) {
      keys.push(e.key.toUpperCase());
    }
    
    if (keys.length > 0) {
      setRecordingKeys(keys);
    }
  };

  const saveShortcut = () => {
    if (!editingShortcut || recordingKeys.length === 0) return;
    
    setShortcuts(prevShortcuts =>
      prevShortcuts.map(shortcut =>
        shortcut.id === editingShortcut
          ? { ...shortcut, keys: recordingKeys }
          : shortcut
      )
    );
    
    setEditingShortcut(null);
    setRecordingKeys([]);
    setHasChanges(true);
  };

  const cancelEdit = () => {
    setEditingShortcut(null);
    setRecordingKeys([]);
  };

  const resetToDefault = (shortcutId: string) => {
    const defaultShortcut = DEFAULT_SHORTCUTS.find(s => s.id === shortcutId);
    if (!defaultShortcut) return;
    
    setShortcuts(prevShortcuts =>
      prevShortcuts.map(shortcut =>
        shortcut.id === shortcutId
          ? { ...shortcut, keys: defaultShortcut.keys }
          : shortcut
      )
    );
    
    setHasChanges(true);
  };

  const resetAllToDefault = () => {
    if (!confirm('Reset all shortcuts to default? This cannot be undone.')) return;
    
    setShortcuts(DEFAULT_SHORTCUTS);
    setHasChanges(true);
  };

  const saveAllShortcuts = () => {
    const customShortcuts: Record<string, { keys: string[] }> = {};
    
    shortcuts.forEach(shortcut => {
      const defaultShortcut = DEFAULT_SHORTCUTS.find(s => s.id === shortcut.id);
      if (defaultShortcut && JSON.stringify(shortcut.keys) !== JSON.stringify(defaultShortcut.keys)) {
        customShortcuts[shortcut.id] = { keys: shortcut.keys };
      }
    });
    
    localStorage.setItem('custom_shortcuts', JSON.stringify(customShortcuts));
    setHasChanges(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const formatKeys = (keys: string[]): string => {
    return keys.map(key => {
      if (key === 'Meta') return isMac ? '⌘' : 'Ctrl';
      if (key === 'Alt') return isMac ? '⌥' : 'Alt';
      if (key === 'Shift') return isMac ? '⇧' : 'Shift';
      if (key === 'Ctrl') return 'Ctrl';
      if (key === '/') return '?';
      return key;
    }).join(' + ');
  };

  const filteredShortcuts = shortcuts.filter(shortcut =>
    searchQuery === '' ||
    shortcut.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    shortcut.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const categories = Array.from(new Set(filteredShortcuts.map(s => s.category)));

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <a href="/dashboard" className="text-xl font-bold text-gray-900 dark:text-gray-100 hover:text-gray-700 dark:hover:text-gray-300 transition">
                AutoGraph
              </a>
              <span className="text-gray-400">→</span>
              <a href="/settings" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition">
                Settings
              </a>
              <span className="text-gray-400">→</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">Keyboard Shortcuts</span>
            </div>
            <div className="flex items-center gap-4">
              {hasChanges && (
                <Button onClick={saveAllShortcuts} variant="primary" size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  Save Changes
                </Button>
              )}
              {saved && (
                <span className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                  <Check className="w-4 h-4" />
                  Saved!
                </span>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-start gap-4 mb-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Keyboard className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                Keyboard Shortcuts
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Customize keyboard shortcuts to match your workflow. Click on any shortcut to change it.
              </p>
            </div>
          </div>

          {/* Search and Actions */}
          <div className="flex gap-4 items-center mt-6">
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder="Search shortcuts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 pl-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
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
            <Button onClick={resetAllToDefault} variant="secondary">
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset All
            </Button>
          </div>
        </div>

        {/* Platform Indicator */}
        <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            <strong>Platform:</strong> {isMac ? 'macOS' : 'Windows/Linux'} — Shortcuts automatically adapt to your operating system.
          </p>
        </div>

        {/* Shortcuts List */}
        <div className="space-y-6">
          {categories.map(category => (
            <div key={category} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {category}
                </h2>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredShortcuts
                  .filter(s => s.category === category)
                  .map(shortcut => {
                    const isEditing = editingShortcut === shortcut.id;
                    const isDefault = JSON.stringify(shortcut.keys) === JSON.stringify(DEFAULT_SHORTCUTS.find(s => s.id === shortcut.id)?.keys);
                    
                    return (
                      <div
                        key={shortcut.id}
                        className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700/50 transition"
                      >
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {shortcut.description}
                          </p>
                          {!shortcut.customizable && (
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              System shortcut (cannot be changed)
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          {isEditing ? (
                            <>
                              <div
                                className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-500 rounded-lg min-w-[150px] text-center"
                                onKeyDown={handleKeyDown}
                                tabIndex={0}
                                autoFocus
                              >
                                <span className="text-sm font-semibold text-blue-800 dark:text-blue-200">
                                  {recordingKeys.length > 0
                                    ? formatKeys(recordingKeys)
                                    : 'Press keys...'}
                                </span>
                              </div>
                              <Button
                                onClick={saveShortcut}
                                variant="primary"
                                size="sm"
                                disabled={recordingKeys.length === 0}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button onClick={cancelEdit} variant="secondary" size="sm">
                                <X className="w-4 h-4" />
                              </Button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => shortcut.customizable && startRecording(shortcut.id)}
                                disabled={!shortcut.customizable}
                                className={`px-4 py-2 rounded-lg font-mono text-sm transition ${
                                  shortcut.customizable
                                    ? 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 cursor-pointer'
                                    : 'bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-500 cursor-not-allowed'
                                }`}
                              >
                                {formatKeys(shortcut.keys)}
                              </button>
                              {shortcut.customizable && !isDefault && (
                                <Button
                                  onClick={() => resetToDefault(shortcut.id)}
                                  variant="secondary"
                                  size="sm"
                                  title="Reset to default"
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 flex justify-between items-center">
          <a
            href="/settings"
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition"
          >
            ← Back to settings
          </a>
          {hasChanges && (
            <p className="text-sm text-orange-600 dark:text-orange-400">
              You have unsaved changes
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
