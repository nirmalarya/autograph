'use client';

import { List } from 'react-window';
import { useEffect, useState, useRef } from 'react';
import OptimizedImage from './OptimizedImage';

interface Diagram {
  id: string;
  title: string;
  file_type: 'canvas' | 'note' | 'mixed';
  created_at: string;
  updated_at: string;
  last_activity?: string;
  current_version: number;
  version_count?: number;
  thumbnail_url?: string;
  owner_email?: string;
  size_bytes?: number;
  export_count?: number;
  collaborator_count?: number;
  comment_count?: number;
}

interface VirtualListProps {
  diagrams: Diagram[];
  onDiagramClick: (diagram: Diagram) => void;
  selectedDiagrams: Set<string>;
  onToggleSelect: (diagramId: string) => void;
  searchQuery?: string;
  formatBytes: (bytes?: number) => string;
  highlightSearchTerm?: (text: string, searchTerm: string) => React.ReactNode;
  userEmail?: string;
}

// Helper function to calculate list dimensions
function useListDimensions() {
  const [dimensions, setDimensions] = useState({
    width: 1200,
    height: 800,
  });

  useEffect(() => {
    const updateDimensions = () => {
      const width = window.innerWidth;
      const height = window.innerHeight - 300; // Account for header and filters

      setDimensions({
        width: width - 50,
        height: Math.max(600, height),
      });
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  return dimensions;
}

export default function VirtualList({
  diagrams,
  onDiagramClick,
  selectedDiagrams,
  onToggleSelect,
  searchQuery,
  formatBytes,
  highlightSearchTerm,
  userEmail,
}: VirtualListProps) {
  const dimensions = useListDimensions();
  const listRef = useRef<any>(null);

  // Row renderer for each list item
  const Row = ({ index, style, ariaAttributes }: any) => {
    const diagram = diagrams[index];
    const isPending = diagram.id.startsWith('temp-');

    return (
      <div style={style} {...ariaAttributes}>
        <div
          className={`bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition ${
            isPending ? 'optimistic-create optimistic-pending' : ''
          } ${
            selectedDiagrams.has(diagram.id)
              ? 'bg-blue-50 dark:bg-blue-900/20'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
          }`}
        >
          <div className="flex items-center px-6 py-4 gap-4">
            {/* Checkbox */}
            <div className="flex-shrink-0">
              <input
                type="checkbox"
                checked={selectedDiagrams.has(diagram.id)}
                onChange={() => onToggleSelect(diagram.id)}
                onClick={(e) => e.stopPropagation()}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
            </div>

            {/* Thumbnail */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="flex-shrink-0 cursor-pointer"
            >
              <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center overflow-hidden">
                {diagram.thumbnail_url ? (
                  <OptimizedImage 
                    src={diagram.thumbnail_url} 
                    alt={diagram.title}
                    className="w-full h-full object-cover"
                    width={64}
                    height={64}
                    fallback={
                      <svg className="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    }
                  />
                ) : (
                  <svg className="w-8 h-8 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                )}
              </div>
            </div>

            {/* Title */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="flex-1 min-w-0 cursor-pointer"
            >
              <div className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                {searchQuery && highlightSearchTerm 
                  ? highlightSearchTerm(diagram.title, searchQuery) 
                  : diagram.title}
              </div>
            </div>

            {/* Type */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="flex-shrink-0 cursor-pointer"
            >
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100">
                {diagram.file_type}
              </span>
            </div>

            {/* Owner */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden md:block flex-shrink-0 w-32 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400 truncate">
                {diagram.owner_email || userEmail || 'Unknown'}
              </div>
            </div>

            {/* Last Updated */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden lg:block flex-shrink-0 w-28 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {new Date(diagram.updated_at).toLocaleDateString()}
              </div>
            </div>

            {/* Last Activity */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden xl:block flex-shrink-0 w-28 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {diagram.last_activity ? new Date(diagram.last_activity).toLocaleDateString() : '-'}
              </div>
            </div>

            {/* Version */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden lg:block flex-shrink-0 w-16 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400">v{diagram.current_version}</div>
            </div>

            {/* Version Count */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden xl:block flex-shrink-0 w-16 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400">{diagram.version_count || 1}</div>
            </div>

            {/* Size */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="hidden xl:block flex-shrink-0 w-20 cursor-pointer"
            >
              <div className="text-sm text-gray-600 dark:text-gray-400">{formatBytes(diagram.size_bytes)}</div>
            </div>

            {/* Stats (compact for smaller screens) */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="flex-shrink-0 flex gap-3 text-xs text-gray-600 dark:text-gray-400 cursor-pointer"
            >
              <span title="Exports">📤 {diagram.export_count || 0}</span>
              <span title="Collaborators">👥 {diagram.collaborator_count || 1}</span>
              <span title="Comments">💬 {diagram.comment_count || 0}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="virtual-list-container">
      {/* Table Header */}
      <div className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center px-6 py-3 gap-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          <div className="flex-shrink-0 w-4">
            {/* Checkbox column */}
          </div>
          <div className="flex-shrink-0 w-16">Preview</div>
          <div className="flex-1 min-w-0">Title</div>
          <div className="flex-shrink-0">Type</div>
          <div className="hidden md:block flex-shrink-0 w-32">Owner</div>
          <div className="hidden lg:block flex-shrink-0 w-28">Updated</div>
          <div className="hidden xl:block flex-shrink-0 w-28">Activity</div>
          <div className="hidden lg:block flex-shrink-0 w-16">Version</div>
          <div className="hidden xl:block flex-shrink-0 w-16">Versions</div>
          <div className="hidden xl:block flex-shrink-0 w-20">Size</div>
          <div className="flex-shrink-0 w-28">Stats</div>
        </div>
      </div>

      {/* Virtual List */}
      <List
        listRef={listRef}
        defaultHeight={dimensions.height}
        rowCount={diagrams.length}
        rowHeight={88} // Height of each row
        overscanCount={5}
        className="virtual-list"
        rowComponent={Row}
        rowProps={{}}
      />
      
      {/* Virtual scrolling info */}
      <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400 py-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <p>
          Showing {diagrams.length.toLocaleString()} diagrams with virtual scrolling
          {diagrams.length > 100 && ' • Only visible items are rendered for optimal performance'}
        </p>
      </div>
    </div>
  );
}
