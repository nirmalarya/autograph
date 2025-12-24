'use client';

import { Grid } from 'react-window';
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

interface VirtualGridProps {
  diagrams: Diagram[];
  onDiagramClick: (diagram: Diagram) => void;
  selectedDiagrams: Set<string>;
  onToggleSelect: (diagramId: string) => void;
  searchQuery?: string;
  formatBytes: (bytes?: number) => string;
  highlightSearchTerm?: (text: string, searchTerm: string) => React.ReactNode;
}

// Helper function to calculate grid dimensions
function useGridDimensions() {
  const [dimensions, setDimensions] = useState({
    columnCount: 4,
    columnWidth: 300,
    rowHeight: 350,
    width: 1200,
    height: 800,
  });

  useEffect(() => {
    const updateDimensions = () => {
      const width = window.innerWidth;
      const height = window.innerHeight - 300; // Account for header and filters

      let columnCount = 4;
      if (width < 640) columnCount = 1;       // mobile
      else if (width < 768) columnCount = 2;  // tablet
      else if (width < 1024) columnCount = 3; // small desktop
      else columnCount = 4;                    // large desktop

      const columnWidth = Math.floor((width - 100) / columnCount);
      const rowHeight = 350;

      setDimensions({
        columnCount,
        columnWidth,
        rowHeight,
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

export default function VirtualGrid({
  diagrams,
  onDiagramClick,
  selectedDiagrams,
  onToggleSelect,
  searchQuery,
  formatBytes,
  highlightSearchTerm,
}: VirtualGridProps) {
  const dimensions = useGridDimensions();
  const gridRef = useRef<any>(null);

  // Calculate row count based on total items and columns
  const rowCount = Math.ceil(diagrams.length / dimensions.columnCount);

  // Cell renderer for each grid item
  const Cell = ({ columnIndex, rowIndex, style, ariaAttributes }: any) => {
    const index = rowIndex * dimensions.columnCount + columnIndex;
    
    // Return empty cell if index exceeds diagram count
    if (index >= diagrams.length) {
      return <div style={style} {...ariaAttributes} />;
    }

    const diagram = diagrams[index];
    const isPending = diagram.id.startsWith('temp-');

    return (
      <div style={{ ...style, padding: '8px' }} {...ariaAttributes}>
        <div
          className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border-2 transition h-full ${
            isPending ? 'optimistic-create optimistic-pending' : ''
          } ${
            selectedDiagrams.has(diagram.id)
              ? 'border-blue-500 shadow-md'
              : 'border-gray-200 dark:border-gray-700 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600'
          }`}
        >
          {/* Checkbox Overlay */}
          <div className="relative">
            <div className="absolute top-2 left-2 z-10">
              <input
                type="checkbox"
                checked={selectedDiagrams.has(diagram.id)}
                onChange={(e) => {
                  e.stopPropagation();
                  onToggleSelect(diagram.id);
                }}
                onClick={(e) => e.stopPropagation()}
                className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 bg-white shadow-sm"
              />
            </div>
            
            {/* Thumbnail */}
            <div 
              onClick={() => onDiagramClick(diagram)}
              className="w-full h-48 bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden cursor-pointer"
            >
              {diagram.thumbnail_url ? (
                <OptimizedImage 
                  src={diagram.thumbnail_url} 
                  alt={diagram.title}
                  className="w-full h-full object-cover"
                  fallback={
                    <div className="text-gray-400 dark:text-gray-500 text-center p-4">
                      <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-sm">No preview</p>
                    </div>
                  }
                />
              ) : (
                <div className="text-gray-400 dark:text-gray-500 text-center p-4">
                  <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm">No preview</p>
                </div>
              )}
            </div>
          </div>
        
          {/* Card Content */}
          <div 
            onClick={() => onDiagramClick(diagram)}
            className="p-4 cursor-pointer"
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate flex-1">
                {searchQuery && highlightSearchTerm 
                  ? highlightSearchTerm(diagram.title, searchQuery) 
                  : diagram.title}
              </h3>
              <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-100">
                {diagram.file_type}
              </span>
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <p>Version: {diagram.current_version} ({diagram.version_count || 1} total)</p>
              <p>Updated: {new Date(diagram.updated_at).toLocaleDateString()}</p>
              {diagram.last_activity && (
                <p>Last Activity: {new Date(diagram.last_activity).toLocaleDateString()}</p>
              )}
              <p>Size: {formatBytes(diagram.size_bytes)}</p>
              <div className="flex gap-3 text-xs">
                <span>📤 {diagram.export_count || 0}</span>
                <span>👥 {diagram.collaborator_count || 1}</span>
                <span>💬 {diagram.comment_count || 0}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="virtual-grid-container">
      <Grid
        gridRef={gridRef}
        columnCount={dimensions.columnCount}
        columnWidth={dimensions.columnWidth}
        defaultHeight={dimensions.height}
        rowCount={rowCount}
        rowHeight={dimensions.rowHeight}
        defaultWidth={dimensions.width}
        overscanCount={2}
        className="virtual-grid"
        cellComponent={Cell}
        cellProps={{}}
      />
      
      {/* Virtual scrolling info */}
      <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>
          Showing {diagrams.length.toLocaleString()} diagrams with virtual scrolling
          {diagrams.length > 100 && ' • Only visible items are rendered for optimal performance'}
        </p>
      </div>
    </div>
  );
}
