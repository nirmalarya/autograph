/**
 * Feature: Contextual Tooltips System
 * 
 * Provides helpful, context-aware tooltips throughout the UI to guide users.
 * Tooltips can be toggled on/off and respect user preferences.
 */

'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import Tooltip, { TooltipPosition } from './Tooltip';
import { HelpCircle, X, Settings } from 'lucide-react';

// Tooltip definitions - organized by page/context
export interface ContextualTooltipDefinition {
  id: string;
  target: string; // Selector or element identifier
  content: React.ReactNode;
  position?: TooltipPosition;
  importance: 'high' | 'medium' | 'low'; // High importance shown first
  context?: string; // Page or feature context (e.g., 'dashboard', 'canvas', 'diagram-editor')
  learnMoreUrl?: string; // Link to help docs
}

// Predefined tooltips for common UI elements
export const CONTEXTUAL_TOOLTIPS: ContextualTooltipDefinition[] = [
  // Dashboard tooltips
  {
    id: 'dashboard-create-diagram',
    target: 'create-diagram-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Create Diagram</div>
        <div className="text-xs">Start a new diagram with canvas, Mermaid code, or AI generation</div>
      </div>
    ),
    position: 'bottom',
    importance: 'high',
    context: 'dashboard',
  },
  {
    id: 'dashboard-search',
    target: 'search-input',
    content: (
      <div>
        <div className="font-semibold mb-1">Search Diagrams</div>
        <div className="text-xs">Find diagrams by name, content, or tags. Use filters for advanced search.</div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'dashboard',
  },
  {
    id: 'dashboard-view-toggle',
    target: 'view-toggle',
    content: (
      <div>
        <div className="font-semibold mb-1">Switch View</div>
        <div className="text-xs">Toggle between grid and list view for your diagrams</div>
      </div>
    ),
    position: 'left',
    importance: 'low',
    context: 'dashboard',
  },
  {
    id: 'dashboard-filters',
    target: 'filter-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Filter & Sort</div>
        <div className="text-xs">Filter by type, date, author, or folder. Sort by various criteria.</div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'dashboard',
  },

  // Canvas/Editor tooltips
  {
    id: 'canvas-toolbar',
    target: 'canvas-toolbar',
    content: (
      <div>
        <div className="font-semibold mb-1">Drawing Tools</div>
        <div className="text-xs">
          <div>Rectangle (R), Circle (O), Arrow (A)</div>
          <div>Line (L), Text (T), Pen (P)</div>
          <div>Press V to return to selection mode</div>
        </div>
      </div>
    ),
    position: 'right',
    importance: 'high',
    context: 'canvas',
  },
  {
    id: 'canvas-zoom',
    target: 'zoom-controls',
    content: (
      <div>
        <div className="font-semibold mb-1">Zoom Controls</div>
        <div className="text-xs">
          <div>Ctrl/Cmd + Scroll to zoom</div>
          <div>Space + Drag to pan</div>
          <div>Ctrl/Cmd + 0 to reset zoom</div>
        </div>
      </div>
    ),
    position: 'left',
    importance: 'medium',
    context: 'canvas',
  },
  {
    id: 'canvas-properties',
    target: 'properties-panel',
    content: (
      <div>
        <div className="font-semibold mb-1">Properties Panel</div>
        <div className="text-xs">Customize selected elements: colors, styles, sizes, and more</div>
      </div>
    ),
    position: 'left',
    importance: 'medium',
    context: 'canvas',
  },
  {
    id: 'canvas-undo-redo',
    target: 'undo-redo-buttons',
    content: (
      <div>
        <div className="font-semibold mb-1">Undo & Redo</div>
        <div className="text-xs">
          <div>Ctrl/Cmd + Z to undo</div>
          <div>Ctrl/Cmd + Shift + Z to redo</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'low',
    context: 'canvas',
  },
  {
    id: 'canvas-insert-menu',
    target: 'insert-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Insert Elements</div>
        <div className="text-xs">
          <div>Add shapes, icons, figures, or diagrams</div>
          <div>Press / to quickly search and insert</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'high',
    context: 'canvas',
  },

  // AI Generation tooltips
  {
    id: 'ai-prompt-input',
    target: 'ai-prompt-input',
    content: (
      <div>
        <div className="font-semibold mb-1">AI Diagram Generation</div>
        <div className="text-xs">
          <div>Describe your diagram in natural language</div>
          <div>Example: "Create a microservices architecture for an e-commerce platform"</div>
        </div>
      </div>
    ),
    position: 'top',
    importance: 'high',
    context: 'ai-generation',
  },
  {
    id: 'ai-diagram-type',
    target: 'diagram-type-selector',
    content: (
      <div>
        <div className="font-semibold mb-1">Diagram Type</div>
        <div className="text-xs">Select the type of diagram to generate: architecture, sequence, ERD, flowchart, etc.</div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'ai-generation',
  },

  // Mermaid/Code tooltips
  {
    id: 'mermaid-editor',
    target: 'mermaid-editor',
    content: (
      <div>
        <div className="font-semibold mb-1">Mermaid Code Editor</div>
        <div className="text-xs">
          <div>Write diagram-as-code with Mermaid syntax</div>
          <div>Changes update the preview in real-time</div>
        </div>
      </div>
    ),
    position: 'right',
    importance: 'high',
    context: 'mermaid',
  },
  {
    id: 'mermaid-preview',
    target: 'mermaid-preview',
    content: (
      <div>
        <div className="font-semibold mb-1">Live Preview</div>
        <div className="text-xs">See your diagram render in real-time as you type</div>
      </div>
    ),
    position: 'left',
    importance: 'medium',
    context: 'mermaid',
  },

  // Collaboration tooltips
  {
    id: 'collab-share-button',
    target: 'share-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Share Diagram</div>
        <div className="text-xs">
          <div>Share with team members or create public links</div>
          <div>Set permissions: view-only or edit access</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'high',
    context: 'collaboration',
  },
  {
    id: 'collab-comments',
    target: 'comments-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Comments & Feedback</div>
        <div className="text-xs">
          <div>Add comments to specific elements</div>
          <div>Use @mentions to notify team members</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'collaboration',
  },
  {
    id: 'collab-cursors',
    target: 'active-users',
    content: (
      <div>
        <div className="font-semibold mb-1">Active Collaborators</div>
        <div className="text-xs">See who's currently viewing or editing this diagram</div>
      </div>
    ),
    position: 'bottom',
    importance: 'low',
    context: 'collaboration',
  },

  // Export tooltips
  {
    id: 'export-button',
    target: 'export-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Export Diagram</div>
        <div className="text-xs">
          <div>Download as PNG, SVG, PDF, or Markdown</div>
          <div>Customize resolution and quality settings</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'high',
    context: 'export',
  },

  // Version History tooltips
  {
    id: 'version-history',
    target: 'version-history-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Version History</div>
        <div className="text-xs">
          <div>View all saved versions of this diagram</div>
          <div>Compare changes or restore previous versions</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'version-history',
  },

  // Settings tooltips
  {
    id: 'theme-toggle',
    target: 'theme-toggle',
    content: (
      <div>
        <div className="font-semibold mb-1">Theme Toggle</div>
        <div className="text-xs">Switch between light and dark mode</div>
      </div>
    ),
    position: 'bottom',
    importance: 'low',
    context: 'settings',
  },
  {
    id: 'keyboard-shortcuts',
    target: 'keyboard-shortcuts-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Keyboard Shortcuts</div>
        <div className="text-xs">
          <div>View all available keyboard shortcuts</div>
          <div>Press ? to open shortcut reference</div>
        </div>
      </div>
    ),
    position: 'bottom',
    importance: 'medium',
    context: 'settings',
  },

  // Help tooltips
  {
    id: 'help-button',
    target: 'help-button',
    content: (
      <div>
        <div className="font-semibold mb-1">Help Center</div>
        <div className="text-xs">
          <div>Browse documentation and tutorials</div>
          <div>Press ? to open help center</div>
        </div>
      </div>
    ),
    position: 'left',
    importance: 'high',
    context: 'help',
  },
];

// Context for managing contextual tooltips state
interface ContextualTooltipsContextType {
  enabled: boolean;
  toggleEnabled: () => void;
  dismissTooltip: (id: string) => void;
  isDismissed: (id: string) => boolean;
  resetDismissed: () => void;
  showSettingsPanel: boolean;
  setShowSettingsPanel: (show: boolean) => void;
  currentContext?: string;
  setCurrentContext: (context: string) => void;
}

const ContextualTooltipsContext = createContext<ContextualTooltipsContextType>({
  enabled: true,
  toggleEnabled: () => {},
  dismissTooltip: () => {},
  isDismissed: () => false,
  resetDismissed: () => {},
  showSettingsPanel: false,
  setShowSettingsPanel: () => {},
  currentContext: undefined,
  setCurrentContext: () => {},
});

export function useContextualTooltips() {
  return useContext(ContextualTooltipsContext);
}

// Provider component
interface ContextualTooltipsProviderProps {
  children: React.ReactNode;
  defaultEnabled?: boolean;
  defaultContext?: string;
}

export function ContextualTooltipsProvider({
  children,
  defaultEnabled = true,
  defaultContext,
}: ContextualTooltipsProviderProps) {
  const [enabled, setEnabled] = useState(defaultEnabled);
  const [dismissedTooltips, setDismissedTooltips] = useState<Set<string>>(new Set());
  const [showSettingsPanel, setShowSettingsPanel] = useState(false);
  const [currentContext, setCurrentContext] = useState<string | undefined>(defaultContext);
  const [mounted, setMounted] = useState(false);

  // Load preferences from localStorage
  useEffect(() => {
    setMounted(true);
    const savedEnabled = localStorage.getItem('contextual-tooltips-enabled');
    if (savedEnabled !== null) {
      setEnabled(savedEnabled === 'true');
    }

    const savedDismissed = localStorage.getItem('contextual-tooltips-dismissed');
    if (savedDismissed) {
      try {
        const dismissed = JSON.parse(savedDismissed);
        setDismissedTooltips(new Set(dismissed));
      } catch (e) {
        console.error('Failed to parse dismissed tooltips', e);
      }
    }
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem('contextual-tooltips-enabled', enabled.toString());
  }, [enabled, mounted]);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem(
      'contextual-tooltips-dismissed',
      JSON.stringify(Array.from(dismissedTooltips))
    );
  }, [dismissedTooltips, mounted]);

  const toggleEnabled = useCallback(() => {
    setEnabled((prev) => !prev);
  }, []);

  const dismissTooltip = useCallback((id: string) => {
    setDismissedTooltips((prev) => new Set(prev).add(id));
  }, []);

  const isDismissed = useCallback(
    (id: string) => {
      return dismissedTooltips.has(id);
    },
    [dismissedTooltips]
  );

  const resetDismissed = useCallback(() => {
    setDismissedTooltips(new Set());
  }, []);

  return (
    <ContextualTooltipsContext.Provider
      value={{
        enabled,
        toggleEnabled,
        dismissTooltip,
        isDismissed,
        resetDismissed,
        showSettingsPanel,
        setShowSettingsPanel,
        currentContext,
        setCurrentContext,
      }}
    >
      {children}
    </ContextualTooltipsContext.Provider>
  );
}

// Wrapper component for elements that should have contextual tooltips
interface ContextualTooltipWrapperProps {
  tooltipId: string;
  children: React.ReactElement;
  forceShow?: boolean; // Force show tooltip (for demos/onboarding)
}

export function ContextualTooltipWrapper({
  tooltipId,
  children,
  forceShow = false,
}: ContextualTooltipWrapperProps) {
  const { enabled, isDismissed, dismissTooltip, currentContext } = useContextualTooltips();
  const [showDismissButton, setShowDismissButton] = useState(false);

  // Find the tooltip definition
  const tooltipDef = CONTEXTUAL_TOOLTIPS.find((t) => t.id === tooltipId);

  if (!tooltipDef) {
    return children;
  }

  // Don't show if disabled, dismissed, or context doesn't match
  const shouldShow =
    forceShow ||
    (enabled &&
      !isDismissed(tooltipId) &&
      (!currentContext || !tooltipDef.context || tooltipDef.context === currentContext));

  if (!shouldShow) {
    return children;
  }

  const tooltipContent = (
    <div
      className="max-w-xs"
      onMouseEnter={() => setShowDismissButton(true)}
      onMouseLeave={() => setShowDismissButton(false)}
    >
      <div className="relative">
        {tooltipDef.content}
        {showDismissButton && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              dismissTooltip(tooltipId);
            }}
            className="absolute top-0 right-0 p-1 hover:bg-gray-800 dark:hover:bg-gray-600 rounded transition-colors"
            aria-label="Dismiss tooltip"
          >
            <X className="w-3 h-3" />
          </button>
        )}
        {tooltipDef.learnMoreUrl && (
          <a
            href={tooltipDef.learnMoreUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-400 hover:text-blue-300 mt-2 inline-flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
          >
            Learn more <HelpCircle className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );

  return (
    <Tooltip content={tooltipContent} position={tooltipDef.position} delay={500} size="lg">
      {children}
    </Tooltip>
  );
}

// Settings panel for managing contextual tooltips
export function ContextualTooltipsSettings() {
  const {
    enabled,
    toggleEnabled,
    resetDismissed,
    showSettingsPanel,
    setShowSettingsPanel,
  } = useContextualTooltips();

  if (!showSettingsPanel) return null;

  return (
    <div
      className="fixed inset-0 z-[9998] flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={() => setShowSettingsPanel(false)}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Contextual Tooltips
            </h2>
          </div>
          <button
            onClick={() => setShowSettingsPanel(false)}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
            aria-label="Close settings"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-750 rounded-lg">
            <div>
              <div className="font-medium text-gray-900 dark:text-gray-100">
                Show Contextual Tooltips
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Display helpful tooltips throughout the interface
              </div>
            </div>
            <button
              onClick={toggleEnabled}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${enabled ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'}
              `}
              role="switch"
              aria-checked={enabled}
              aria-label="Toggle contextual tooltips"
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${enabled ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-750 rounded-lg">
            <div className="font-medium text-gray-900 dark:text-gray-100 mb-2">
              Reset Dismissed Tooltips
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Show all tooltips again, including ones you've dismissed
            </div>
            <button
              onClick={resetDismissed}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-sm font-medium"
            >
              Reset All Tooltips
            </button>
          </div>

          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
            <div className="flex items-start gap-2">
              <HelpCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900 dark:text-blue-100">
                <div className="font-medium mb-1">Tip</div>
                <div>
                  Hover over any tooltip and click the X button to dismiss it permanently.
                  You can always reset them here.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={() => setShowSettingsPanel(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

// Floating button to toggle contextual tooltips settings
export function ContextualTooltipsToggle() {
  const { enabled, setShowSettingsPanel } = useContextualTooltips();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <button
      onClick={() => setShowSettingsPanel(true)}
      className={`
        fixed bottom-24 right-6 z-40
        p-3 rounded-full shadow-lg transition-all
        ${
          enabled
            ? 'bg-blue-600 hover:bg-blue-700 text-white'
            : 'bg-gray-300 dark:bg-gray-700 hover:bg-gray-400 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300'
        }
        touch-target-large
      `}
      aria-label="Toggle contextual tooltips settings"
      title="Contextual Tooltips Settings"
    >
      <HelpCircle className="w-5 h-5" />
    </button>
  );
}

// Export hook to set current context from pages
export function useSetTooltipContext(context: string) {
  const { setCurrentContext } = useContextualTooltips();

  useEffect(() => {
    setCurrentContext(context);
    return () => {
      // Clear context on unmount - TypeScript needs explicit string
      setCurrentContext('');
    };
  }, [context, setCurrentContext]);
}
