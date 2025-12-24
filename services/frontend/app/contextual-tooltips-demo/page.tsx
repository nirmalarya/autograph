/**
 * Demo page for Contextual Tooltips
 * Shows various tooltips in action
 */

'use client';

import React from 'react';
import { ContextualTooltipWrapper, useSetTooltipContext } from '../components/ContextualTooltips';
import {
  Search,
  Grid,
  List,
  Filter,
  PlusCircle,
  Settings,
  HelpCircle,
  Share2,
  Download,
  MessageSquare,
  Users,
  GitBranch,
  Zap,
  FileText,
  Palette,
} from 'lucide-react';

export default function ContextualTooltipsDemo() {
  // Set the context for this page
  useSetTooltipContext('dashboard');

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Contextual Tooltips Demo
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Hover over the elements below to see contextual tooltips in action.
            Click the tooltip settings button in the bottom-right corner to customize.
          </p>
        </div>

        {/* Dashboard Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Dashboard Elements
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ContextualTooltipWrapper tooltipId="dashboard-create-diagram">
              <button
                id="create-diagram-button"
                className="p-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex flex-col items-center gap-2"
              >
                <PlusCircle className="w-8 h-8" />
                <span className="font-medium">Create Diagram</span>
              </button>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="dashboard-search">
              <div
                id="search-input"
                className="p-6 bg-gray-100 dark:bg-gray-800 rounded-lg flex flex-col items-center gap-2"
              >
                <Search className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Search</span>
              </div>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="dashboard-view-toggle">
              <div
                id="view-toggle"
                className="p-6 bg-gray-100 dark:bg-gray-800 rounded-lg flex flex-col items-center gap-2"
              >
                <div className="flex gap-2">
                  <Grid className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                  <List className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </div>
                <span className="font-medium text-gray-900 dark:text-gray-100">View Toggle</span>
              </div>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="dashboard-filters">
              <button
                id="filter-button"
                className="p-6 bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors flex flex-col items-center gap-2"
              >
                <Filter className="w-8 h-8 text-gray-600 dark:text-gray-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Filters</span>
              </button>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* Canvas Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Canvas Tools
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <ContextualTooltipWrapper tooltipId="canvas-toolbar">
              <div
                id="canvas-toolbar"
                className="p-6 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex flex-col items-center gap-2"
              >
                <Palette className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Drawing Tools</span>
              </div>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="canvas-properties">
              <div
                id="properties-panel"
                className="p-6 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex flex-col items-center gap-2"
              >
                <Settings className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Properties</span>
              </div>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="canvas-insert-menu">
              <button
                id="insert-button"
                className="p-6 bg-purple-100 dark:bg-purple-900/20 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <PlusCircle className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Insert</span>
              </button>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* AI & Mermaid Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            AI & Diagram-as-Code
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ContextualTooltipWrapper tooltipId="ai-prompt-input">
              <div
                id="ai-prompt-input"
                className="p-6 bg-yellow-100 dark:bg-yellow-900/20 rounded-lg flex flex-col items-center gap-2"
              >
                <Zap className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">AI Generation</span>
              </div>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="mermaid-editor">
              <div
                id="mermaid-editor"
                className="p-6 bg-green-100 dark:bg-green-900/20 rounded-lg flex flex-col items-center gap-2"
              >
                <FileText className="w-8 h-8 text-green-600 dark:text-green-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Code Editor</span>
              </div>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* Collaboration Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Collaboration
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ContextualTooltipWrapper tooltipId="collab-share-button">
              <button
                id="share-button"
                className="p-6 bg-pink-100 dark:bg-pink-900/20 rounded-lg hover:bg-pink-200 dark:hover:bg-pink-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <Share2 className="w-8 h-8 text-pink-600 dark:text-pink-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Share</span>
              </button>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="collab-comments">
              <button
                id="comments-button"
                className="p-6 bg-pink-100 dark:bg-pink-900/20 rounded-lg hover:bg-pink-200 dark:hover:bg-pink-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <MessageSquare className="w-8 h-8 text-pink-600 dark:text-pink-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Comments</span>
              </button>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="collab-cursors">
              <div
                id="active-users"
                className="p-6 bg-pink-100 dark:bg-pink-900/20 rounded-lg flex flex-col items-center gap-2"
              >
                <Users className="w-8 h-8 text-pink-600 dark:text-pink-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Active Users</span>
              </div>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* Export & Version History */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Export & History
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <ContextualTooltipWrapper tooltipId="export-button">
              <button
                id="export-button"
                className="p-6 bg-orange-100 dark:bg-orange-900/20 rounded-lg hover:bg-orange-200 dark:hover:bg-orange-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <Download className="w-8 h-8 text-orange-600 dark:text-orange-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Export</span>
              </button>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="version-history">
              <button
                id="version-history-button"
                className="p-6 bg-orange-100 dark:bg-orange-900/20 rounded-lg hover:bg-orange-200 dark:hover:bg-orange-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <GitBranch className="w-8 h-8 text-orange-600 dark:text-orange-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Version History</span>
              </button>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* Help Section */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Help & Settings
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <ContextualTooltipWrapper tooltipId="help-button">
              <button
                id="help-button"
                className="p-6 bg-blue-100 dark:bg-blue-900/20 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <HelpCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Help Center</span>
              </button>
            </ContextualTooltipWrapper>

            <ContextualTooltipWrapper tooltipId="keyboard-shortcuts">
              <button
                id="keyboard-shortcuts-button"
                className="p-6 bg-blue-100 dark:bg-blue-900/20 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-900/30 transition-colors flex flex-col items-center gap-2"
              >
                <Settings className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                <span className="font-medium text-gray-900 dark:text-gray-100">Shortcuts</span>
              </button>
            </ContextualTooltipWrapper>
          </div>
        </section>

        {/* Instructions */}
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-6 h-6 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                How to Use Contextual Tooltips
              </h3>
              <ul className="space-y-2 text-gray-700 dark:text-gray-300">
                <li>• <strong>Hover</strong> over any element with a tooltip to see helpful information</li>
                <li>• <strong>Click the X button</strong> on a tooltip to dismiss it permanently</li>
                <li>• <strong>Click the tooltip settings button</strong> (bottom-right) to enable/disable all tooltips</li>
                <li>• Use the settings panel to <strong>reset dismissed tooltips</strong></li>
                <li>• Tooltips automatically adapt to <strong>light and dark modes</strong></li>
                <li>• They work with <strong>keyboard navigation</strong> and screen readers</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
