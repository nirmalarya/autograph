'use client';

import React, { useState, useEffect } from 'react';
import { API_ENDPOINTS } from '@/lib/api-config';

interface Folder {
  id: string;
  name: string;
  parent_id: string | null;
  color?: string;
  icon?: string;
  subfolder_count?: number;
  file_count?: number;
  subfolders?: Folder[];
}

interface FolderTreeProps {
  userId: string;
  currentFolderId: string | null;
  onFolderSelect: (folderId: string | null) => void;
  onRefresh?: () => void;
}

export default function FolderTree({ userId, currentFolderId, onFolderSelect, onRefresh }: FolderTreeProps) {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderParentId, setNewFolderParentId] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const [selectedIcon, setSelectedIcon] = useState('folder');
  const [creating, setCreating] = useState(false);

  const colors = [
    { name: 'Blue', value: '#3B82F6' },
    { name: 'Green', value: '#10B981' },
    { name: 'Red', value: '#EF4444' },
    { name: 'Yellow', value: '#F59E0B' },
    { name: 'Purple', value: '#8B5CF6' },
    { name: 'Pink', value: '#EC4899' },
    { name: 'Gray', value: '#6B7280' },
    { name: 'Orange', value: '#F97316' },
  ];

  const icons = [
    { name: 'Folder', value: 'folder', emoji: '📁' },
    { name: 'Open', value: 'folder-open', emoji: '📂' },
    { name: 'Star', value: 'folder-star', emoji: '⭐' },
    { name: 'Lock', value: 'folder-lock', emoji: '🔒' },
    { name: 'Cloud', value: 'folder-cloud', emoji: '☁️' },
    { name: 'Code', value: 'folder-code', emoji: '💻' },
    { name: 'Docs', value: 'folder-docs', emoji: '📄' },
    { name: 'Images', value: 'folder-images', emoji: '🖼️' },
  ];

  useEffect(() => {
    fetchFolders();
  }, [userId]);

  const fetchFolders = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_ENDPOINTS.diagrams.base}/folders`, {
        headers: {
          'X-User-ID': userId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFolders(data.folders || []);
        
        // Load subfolders for each root folder
        for (const folder of data.folders || []) {
          if (folder.subfolder_count && folder.subfolder_count > 0) {
            await loadSubfolders(folder.id);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch folders:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSubfolders = async (folderId: string) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.diagrams.base}/folders?parent_id=${folderId}`, {
        headers: {
          'X-User-ID': userId,
        },
      });

      if (response.ok) {
        const data = await response.json();
        // Update the folder tree with subfolders
        setFolders(prevFolders => updateFolderTree(prevFolders, folderId, data.folders || []));
      }
    } catch (error) {
      console.error('Failed to load subfolders:', error);
    }
  };

  const updateFolderTree = (folders: Folder[], parentId: string, subfolders: Folder[]): Folder[] => {
    return folders.map(folder => {
      if (folder.id === parentId) {
        return { ...folder, subfolders };
      }
      if (folder.subfolders && folder.subfolders.length > 0) {
        return { ...folder, subfolders: updateFolderTree(folder.subfolders, parentId, subfolders) };
      }
      return folder;
    });
  };

  const toggleExpand = async (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
      // Load subfolders if not already loaded
      await loadSubfolders(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    setCreating(true);
    try {
      const response = await fetch(`${API_ENDPOINTS.diagrams.base}/folders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({
          name: newFolderName,
          parent_id: newFolderParentId,
          color: selectedColor,
          icon: selectedIcon,
        }),
      });

      if (response.ok) {
        setShowCreateModal(false);
        setNewFolderName('');
        setNewFolderParentId(null);
        setSelectedColor('#3B82F6');
        setSelectedIcon('folder');
        await fetchFolders();
        if (onRefresh) onRefresh();
      } else {
        alert('Failed to create folder');
      }
    } catch (error) {
      console.error('Failed to create folder:', error);
      alert('Failed to create folder');
    } finally {
      setCreating(false);
    }
  };

  const renderFolder = (folder: Folder, level: number = 0) => {
    const isExpanded = expandedFolders.has(folder.id);
    const isSelected = currentFolderId === folder.id;
    const hasSubfolders = folder.subfolder_count && folder.subfolder_count > 0;

    return (
      <div key={folder.id}>
        <div
          className={`flex items-center py-2 px-2 rounded-md cursor-pointer transition group ${
            isSelected
              ? 'bg-blue-100 text-blue-900'
              : 'hover:bg-gray-100 text-gray-700'
          }`}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
        >
          {/* Expand/Collapse Button */}
          {hasSubfolders ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleExpand(folder.id);
              }}
              className="mr-1 p-0.5 hover:bg-gray-200 rounded"
            >
              <svg
                className={`w-3 h-3 transition-transform ${isExpanded ? 'transform rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ) : (
            <span className="w-4 mr-1" />
          )}

          {/* Folder Icon and Name */}
          <button
            onClick={() => onFolderSelect(folder.id)}
            className="flex-1 flex items-center text-left"
          >
            {/* Color Dot */}
            {folder.color && (
              <span
                className="w-2 h-2 rounded-full mr-2"
                style={{ backgroundColor: folder.color }}
              />
            )}

            {/* Icon */}
            <span className="mr-2 text-base">{getFolderIcon(folder.icon || 'folder')}</span>

            {/* Name */}
            <span className="truncate text-sm font-medium">{folder.name}</span>

            {/* File Count Badge */}
            {folder.file_count !== undefined && folder.file_count > 0 && (
              <span className="ml-auto mr-2 px-2 py-0.5 text-xs rounded-full bg-gray-200 text-gray-600">
                {folder.file_count}
              </span>
            )}
          </button>

          {/* Actions (visible on hover) */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setNewFolderParentId(folder.id);
              setShowCreateModal(true);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded transition"
            title="Create subfolder"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        {/* Render Subfolders */}
        {isExpanded && folder.subfolders && folder.subfolders.length > 0 && (
          <div>
            {folder.subfolders.map(subfolder => renderFolder(subfolder, level + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-900">Folders</h3>
          <button
            onClick={() => {
              setNewFolderParentId(null);
              setShowCreateModal(true);
            }}
            className="p-1 hover:bg-gray-100 rounded transition"
            title="Create new folder"
          >
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>

        {/* Root/All Files Button */}
        <button
          onClick={() => onFolderSelect(null)}
          className={`w-full flex items-center py-2 px-3 rounded-md transition ${
            currentFolderId === null
              ? 'bg-blue-100 text-blue-900 font-medium'
              : 'hover:bg-gray-100 text-gray-700'
          }`}
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          <span className="text-sm">All Files</span>
        </button>
      </div>

      {/* Folder Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {loading ? (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
          </div>
        ) : folders.length === 0 ? (
          <div className="text-center py-4 px-2">
            <p className="text-sm text-gray-500">No folders yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-2 text-xs text-blue-600 hover:text-blue-700"
            >
              Create your first folder
            </button>
          </div>
        ) : (
          <div className="space-y-0.5">
            {folders.map(folder => renderFolder(folder))}
          </div>
        )}
      </div>

      {/* Create Folder Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-xl font-bold text-gray-900 mb-4">
              {newFolderParentId ? 'Create Subfolder' : 'Create Folder'}
            </h3>

            <div className="space-y-4">
              {/* Folder Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Folder Name
                </label>
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="My Folder"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              {/* Color Picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Color
                </label>
                <div className="flex flex-wrap gap-2">
                  {colors.map(color => (
                    <button
                      key={color.value}
                      onClick={() => setSelectedColor(color.value)}
                      className={`w-8 h-8 rounded-full transition ${
                        selectedColor === color.value
                          ? 'ring-2 ring-offset-2 ring-blue-500'
                          : 'hover:scale-110'
                      }`}
                      style={{ backgroundColor: color.value }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>

              {/* Icon Picker */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Icon
                </label>
                <div className="flex flex-wrap gap-2">
                  {icons.map(icon => (
                    <button
                      key={icon.value}
                      onClick={() => setSelectedIcon(icon.value)}
                      className={`w-10 h-10 flex items-center justify-center rounded-md transition ${
                        selectedIcon === icon.value
                          ? 'bg-blue-100 ring-2 ring-blue-500'
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                      title={icon.name}
                    >
                      <span className="text-xl">{icon.emoji}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewFolderName('');
                  setNewFolderParentId(null);
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateFolder}
                disabled={creating || !newFolderName.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition disabled:bg-gray-400"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper function to get folder icon emoji
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
  };
  
  return iconMap[iconName] || '📁';
}
