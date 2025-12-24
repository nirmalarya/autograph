'use client';

import React from 'react';

interface BreadcrumbItem {
  id: string;
  name: string;
  color?: string;
  icon?: string;
}

interface BreadcrumbsProps {
  breadcrumbs: BreadcrumbItem[];
  onNavigate: (folderId: string | null) => void;
}

export default function Breadcrumbs({ breadcrumbs, onNavigate }: BreadcrumbsProps) {
  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 py-3 px-4 bg-white border-b border-gray-200">
      {/* Home/Root */}
      <button
        onClick={() => onNavigate(null)}
        className="flex items-center hover:text-blue-600 transition font-medium"
        title="Go to root"
      >
        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        Home
      </button>

      {/* Breadcrumb trail */}
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.id}>
          {/* Separator */}
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>

          {/* Breadcrumb item */}
          <button
            onClick={() => onNavigate(crumb.id)}
            className={`flex items-center hover:text-blue-600 transition ${
              index === breadcrumbs.length - 1 ? 'font-semibold text-gray-900' : 'font-medium'
            }`}
            title={`Go to ${crumb.name}`}
          >
            {/* Icon if provided */}
            {crumb.icon && (
              <span className="mr-1" role="img" aria-label="folder icon">
                {getFolderIcon(crumb.icon)}
              </span>
            )}
            
            {/* Folder name with color dot */}
            {crumb.color && (
              <span
                className="w-2 h-2 rounded-full mr-1.5"
                style={{ backgroundColor: crumb.color }}
                aria-hidden="true"
              />
            )}
            
            <span className="truncate max-w-xs">{crumb.name}</span>
          </button>
        </React.Fragment>
      ))}
    </nav>
  );
}

// Helper function to get folder icon
function getFolderIcon(iconName: string): string {
  const iconMap: { [key: string]: string } = {
    'folder': '📁',
    'folder-open': '📂',
    'folder-star': '⭐',
    'folder-lock': '🔒',
    'folder-cloud': '☁️',
    'folder-code': '💻',
    'folder-docs': '📄',
    'folder-images': '🖼️',
    'folder-music': '🎵',
    'folder-video': '🎬',
  };
  
  return iconMap[iconName] || '📁';
}
