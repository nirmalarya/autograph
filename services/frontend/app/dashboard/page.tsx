'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Breadcrumbs from '../components/Breadcrumbs';
import FolderTree from '../components/FolderTree';
import CommandPalette from '../components/CommandPalette';
import KeyboardShortcutsDialog from '../components/KeyboardShortcutsDialog';
import ThemeToggle from '../components/ThemeToggle';
import MobileBottomNav from '../components/MobileBottomNav';
import { SkeletonCard, SkeletonListItem } from '../components/SkeletonLoader';
import { useSwipeGesture } from '../../src/hooks/useSwipeGesture';

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

interface DiagramsResponse {
  diagrams: Diagram[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// Helper function to format bytes into human-readable size
function formatBytes(bytes?: number): string {
  if (!bytes || bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [diagramTitle, setDiagramTitle] = useState('');
  const [diagramType, setDiagramType] = useState<'canvas' | 'note' | 'mixed' | 'mermaid'>('canvas');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  
  // Diagram list state
  const [diagrams, setDiagrams] = useState<Diagram[]>([]);
  const [loadingDiagrams, setLoadingDiagrams] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const [filterType, setFilterType] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [sortBy, setSortBy] = useState<string>('updated_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [activeTab, setActiveTab] = useState<'all' | 'recent' | 'starred' | 'shared' | 'trash'>('all');
  
  // Advanced filter state
  const [filterAuthor, setFilterAuthor] = useState<string>('');
  const [filterDateRange, setFilterDateRange] = useState<'all' | 'today' | 'week' | 'month' | 'year'>('all');
  const [filterFolder, setFilterFolder] = useState<string>('');
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  
  // Folder navigation state
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<any[]>([]);
  const [showFolderSidebar, setShowFolderSidebar] = useState(true);
  
  // Batch operations state
  const [selectedDiagrams, setSelectedDiagrams] = useState<Set<string>>(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [deletingBatch, setDeletingBatch] = useState(false);
  const [movingBatch, setMovingBatch] = useState(false);
  
  // Command palette state
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  
  // Keyboard shortcuts dialog state
  const [showKeyboardShortcuts, setShowKeyboardShortcuts] = useState(false);

  // Swipe gesture for sidebar on mobile
  useSwipeGesture({
    onSwipeRight: () => {
      // Only on mobile (screen width < 768px)
      if (window.innerWidth < 768) {
        setShowFolderSidebar(true);
      }
    },
    onSwipeLeft: () => {
      // Only on mobile (screen width < 768px)
      if (window.innerWidth < 768 && showFolderSidebar) {
        setShowFolderSidebar(false);
      }
    },
    minSwipeDistance: 50,
    maxSwipeTime: 300,
  });

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info (simple decode, not verification)
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.email, sub: payload.sub });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    setLoading(false);
  }, [router]);

  // Command Palette keyboard shortcut (Cmd+K or Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Keyboard Shortcuts dialog shortcut (Cmd+? or Ctrl+?)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for Cmd+? or Ctrl+? (Shift+/ produces '?')
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === '?') {
        e.preventDefault();
        setShowKeyboardShortcuts((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Instant search: debounce search input to trigger search automatically
  useEffect(() => {
    // Debounce search to avoid too many API calls
    const timeoutId = setTimeout(() => {
      if (searchInput !== searchQuery) {
        setSearchQuery(searchInput);
        setPage(1); // Reset to first page on new search
      }
    }, 300); // 300ms debounce - fast enough to feel instant, slow enough to avoid excessive API calls

    return () => clearTimeout(timeoutId);
  }, [searchInput, searchQuery]);

  // Fetch diagrams when user, page, filterType, searchQuery, sortBy, sortOrder, or activeTab changes
  useEffect(() => {
    if (user?.sub) {
      fetchDiagrams();
    }
  }, [user, page, filterType, searchQuery, sortBy, sortOrder, activeTab, currentFolderId, filterAuthor, filterDateRange, filterFolder]);

  // Fetch breadcrumbs when folder changes
  useEffect(() => {
    if (user?.sub && currentFolderId) {
      fetchBreadcrumbs();
    } else {
      setBreadcrumbs([]);
    }
  }, [user, currentFolderId]);

  const fetchBreadcrumbs = async () => {
    if (!currentFolderId || !user?.sub) return;

    try {
      const response = await fetch(`http://localhost:8082/folders/${currentFolderId}/breadcrumbs`, {
        headers: {
          'X-User-ID': user.sub,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBreadcrumbs(data.breadcrumbs || []);
      }
    } catch (err) {
      console.error('Failed to fetch breadcrumbs:', err);
    }
  };

  const fetchDiagrams = async () => {
    if (!user?.sub) return;

    setLoadingDiagrams(true);
    try {
      let url = 'http://localhost:8082/';
      let params = new URLSearchParams();

      // If Recent tab is active, use the /recent endpoint
      if (activeTab === 'recent') {
        url = 'http://localhost:8082/recent';
        params.append('limit', '10');
      } else if (activeTab === 'starred') {
        // For "Starred" tab, use the /starred endpoint
        url = 'http://localhost:8082/starred';
      } else if (activeTab === 'shared') {
        // For "Shared with me" tab, use the /shared-with-me endpoint
        url = 'http://localhost:8082/shared-with-me';
      } else if (activeTab === 'trash') {
        // For "Trash" tab, use the /trash endpoint
        url = 'http://localhost:8082/trash';
      } else {
        // For "All" tab, use regular list endpoint with pagination
        params.append('page', page.toString());
        params.append('page_size', '20');

        if (filterType) {
          params.append('file_type', filterType);
        }

        // Build search query with advanced filters
        let finalSearchQuery = searchQuery;
        
        // Add author filter to search query
        if (filterAuthor) {
          finalSearchQuery = finalSearchQuery 
            ? `${finalSearchQuery} author:${filterAuthor}`
            : `author:${filterAuthor}`;
        }
        
        // Add date range filter
        if (filterDateRange && filterDateRange !== 'all') {
          const now = new Date();
          let startDate = new Date();
          
          switch (filterDateRange) {
            case 'today':
              startDate.setHours(0, 0, 0, 0);
              break;
            case 'week':
              startDate.setDate(now.getDate() - 7);
              break;
            case 'month':
              startDate.setDate(now.getDate() - 30);
              break;
            case 'year':
              startDate.setDate(now.getDate() - 365);
              break;
          }
          
          // Add date filter to search query
          finalSearchQuery = finalSearchQuery 
            ? `${finalSearchQuery} after:${startDate.toISOString().split('T')[0]}`
            : `after:${startDate.toISOString().split('T')[0]}`;
        }

        if (finalSearchQuery) {
          params.append('search', finalSearchQuery);
        }

        if (sortBy) {
          params.append('sort_by', sortBy);
        }

        if (sortOrder) {
          params.append('sort_order', sortOrder);
        }

        // Add folder filter if a folder is selected (either from sidebar or filter dropdown)
        if (filterFolder) {
          params.append('folder_id', filterFolder);
        } else if (currentFolderId) {
          params.append('folder_id', currentFolderId);
        }
      }

      const response = await fetch(`${url}?${params.toString()}`, {
        headers: {
          'X-User-ID': user.sub,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch diagrams');
      }

      const data = await response.json();
      setDiagrams(data.diagrams);
      setTotal(data.total);
      
      // Recent, Starred, Shared, and Trash endpoints don't have pagination
      if (activeTab === 'recent' || activeTab === 'starred' || activeTab === 'shared' || activeTab === 'trash') {
        setTotalPages(1);
        setHasNext(false);
        setHasPrev(false);
      } else {
        setTotalPages(data.total_pages);
        setHasNext(data.has_next);
        setHasPrev(data.has_prev);
      }
    } catch (err) {
      console.error('Failed to fetch diagrams:', err);
    } finally {
      setLoadingDiagrams(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput);
    setPage(1); // Reset to first page on new search
  };

  const handleFilterChange = (type: string) => {
    setFilterType(type);
    setPage(1); // Reset to first page on filter change
  };

  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      // Toggle sort order if same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to desc for dates, asc for name
      setSortBy(field);
      setSortOrder(field === 'title' ? 'asc' : 'desc');
    }
    setPage(1); // Reset to first page on sort change
  };

  const handleDiagramClick = (diagram: Diagram) => {
    if (diagram.file_type === 'note') {
      // Check if it's a Mermaid diagram by looking at note_content pattern
      // For simplicity, we'll route to mermaid editor if title contains "Mermaid" or note_content starts with mermaid keywords
      // In a real app, we'd have a separate field or check the content
      if (diagram.title.toLowerCase().includes('mermaid') || 
          diagram.title.toLowerCase().includes('diagram-as-code')) {
        router.push(`/mermaid/${diagram.id}`);
      } else {
        router.push(`/note/${diagram.id}`);
      }
    } else {
      router.push(`/canvas/${diagram.id}`);
    }
  };

  const handleCreateDiagram = async () => {
    if (!diagramTitle.trim()) {
      setError('Please enter a diagram title');
      return;
    }

    setCreating(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      
      // For Mermaid diagrams, store as 'note' type with default Mermaid code
      const actualType = diagramType === 'mermaid' ? 'note' : diagramType;
      const defaultMermaidCode = `graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]`;
      
      const response = await fetch('http://localhost:8082/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user?.sub || '',
        },
        body: JSON.stringify({
          title: diagramType === 'mermaid' ? `${diagramTitle} (Mermaid)` : diagramTitle,
          file_type: actualType,
          canvas_data: actualType === 'canvas' || actualType === 'mixed' ? { shapes: [] } : null,
          note_content: diagramType === 'mermaid' ? defaultMermaidCode : (actualType === 'note' || actualType === 'mixed' ? '' : null),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create diagram');
      }

      const diagram = await response.json();
      
      // Close modal and refresh list
      setShowCreateModal(false);
      setDiagramTitle('');
      setDiagramType('canvas');
      fetchDiagrams();
      
      // Redirect to the appropriate editor
      if (diagramType === 'mermaid') {
        router.push(`/mermaid/${diagram.id}`);
      } else if (diagramType === 'canvas') {
        router.push(`/canvas/${diagram.id}`);
      } else if (diagramType === 'note') {
        router.push(`/note/${diagram.id}`);
      } else {
        router.push(`/canvas/${diagram.id}`); // Mixed defaults to canvas view
      }
    } catch (err: any) {
      console.error('Failed to create diagram:', err);
      setError(err.message || 'Failed to create diagram');
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  // Folder navigation handlers
  const handleFolderSelect = (folderId: string | null) => {
    setCurrentFolderId(folderId);
    setPage(1); // Reset to first page when changing folders
  };

  const handleBreadcrumbNavigate = (folderId: string | null) => {
    setCurrentFolderId(folderId);
    setPage(1);
  };

  // Helper function to highlight search terms in text
  const highlightSearchTerm = (text: string, searchTerm: string) => {
    if (!searchTerm || !text) return text;
    
    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'));
    return (
      <>
        {parts.map((part, index) => 
          part.toLowerCase() === searchTerm.toLowerCase() ? (
            <mark key={index} className="bg-yellow-200 px-1 rounded">{part}</mark>
          ) : (
            part
          )
        )}
      </>
    );
  };

  // Batch operations handlers
  const toggleSelectDiagram = (diagramId: string) => {
    const newSelected = new Set(selectedDiagrams);
    if (newSelected.has(diagramId)) {
      newSelected.delete(diagramId);
    } else {
      newSelected.add(diagramId);
    }
    setSelectedDiagrams(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedDiagrams.size === diagrams.length) {
      setSelectedDiagrams(new Set());
    } else {
      setSelectedDiagrams(new Set(diagrams.map(d => d.id)));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedDiagrams.size === 0) return;

    setDeletingBatch(true);
    try {
      // Delete each selected diagram
      const deletePromises = Array.from(selectedDiagrams).map(diagramId =>
        fetch(`http://localhost:8082/${diagramId}`, {
          method: 'DELETE',
          headers: {
            'X-User-ID': user?.sub || '',
          },
        })
      );

      await Promise.all(deletePromises);

      // Clear selection and refresh list
      setSelectedDiagrams(new Set());
      setShowDeleteConfirm(false);
      fetchDiagrams();
    } catch (err) {
      console.error('Failed to delete diagrams:', err);
      alert('Failed to delete some diagrams. Please try again.');
    } finally {
      setDeletingBatch(false);
    }
  };

  const handleBulkMove = async (folderId: string | null) => {
    if (selectedDiagrams.size === 0) return;

    setMovingBatch(true);
    try {
      // Move each selected diagram
      const movePromises = Array.from(selectedDiagrams).map(diagramId =>
        fetch(`http://localhost:8082/${diagramId}/move`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': user?.sub || '',
          },
          body: JSON.stringify({ folder_id: folderId }),
        })
      );

      await Promise.all(movePromises);

      // Clear selection and refresh list
      setSelectedDiagrams(new Set());
      setShowMoveDialog(false);
      fetchDiagrams();
    } catch (err) {
      console.error('Failed to move diagrams:', err);
      alert('Failed to move some diagrams. Please try again.');
    } finally {
      setMovingBatch(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Navigation skeleton */}
        <nav className="bg-white dark:bg-gray-800 shadow-sm">
          <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
            <div className="flex justify-between items-center h-14 sm:h-16">
              <div className="flex items-center gap-2 sm:gap-4">
                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                <div className="w-32 h-6 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              </div>
              <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                <div className="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              </div>
            </div>
          </div>
        </nav>

        {/* Content skeleton */}
        <div className="flex-1 flex">
          {/* Sidebar skeleton */}
          <aside className="hidden md:block w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4">
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-8 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
              ))}
            </div>
          </aside>

          {/* Main content skeleton */}
          <div className="flex-1 p-4 sm:p-6">
            {/* Header skeleton */}
            <div className="mb-6 space-y-4">
              <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 animate-pulse"></div>
              <div className="flex gap-4">
                <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-64 animate-pulse"></div>
                <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse"></div>
              </div>
            </div>

            {/* Grid skeleton */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Responsive Navigation */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => setShowFolderSidebar(!showFolderSidebar)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition touch-manipulation"
                title={showFolderSidebar ? 'Hide sidebar' : 'Show sidebar'}
              >
                <svg className="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 dark:text-gray-100">AutoGraph v3</h1>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
              {/* Hide email on mobile */}
              <span className="hidden sm:inline text-xs sm:text-sm text-gray-600 dark:text-gray-300">{user?.email}</span>
              <ThemeToggle />
              {/* Hide keyboard shortcuts button on mobile */}
              <button
                onClick={() => setShowKeyboardShortcuts(true)}
                className="hidden sm:block p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-gray-100 dark:hover:bg-gray-700 rounded-md transition"
                title="Keyboard shortcuts (⌘?)"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 sm:px-4 sm:py-2 text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 transition touch-manipulation"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Breadcrumbs - only show when in a folder */}
      {currentFolderId && breadcrumbs.length > 0 && (
        <Breadcrumbs 
          breadcrumbs={breadcrumbs} 
          onNavigate={handleBreadcrumbNavigate}
        />
      )}

      {/* Main content area with sidebar */}
      <div className="flex flex-1 overflow-hidden">
        {/* Folder Sidebar */}
        {showFolderSidebar && user?.sub && (
          <FolderTree
            userId={user.sub}
            currentFolderId={currentFolderId}
            onFolderSelect={handleFolderSelect}
            onRefresh={fetchDiagrams}
          />
        )}

        {/* Main Content - Responsive */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-4 sm:py-6 md:py-8 lg:py-12">
        <div className="mb-4 sm:mb-6 md:mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
          <div>
            <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1 sm:mb-2">
              My Diagrams
            </h2>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              {total} diagram{total !== 1 ? 's' : ''} total
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
            <button 
              onClick={() => router.push('/ai-generate')}
              className="px-4 sm:px-6 py-2.5 sm:py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-md font-medium hover:from-purple-700 hover:to-blue-700 transition shadow-sm text-sm sm:text-base touch-manipulation"
            >
              ✨ AI Generate
            </button>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="px-4 sm:px-6 py-2.5 sm:py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition text-sm sm:text-base touch-manipulation"
            >
              + Create Diagram
            </button>
          </div>
        </div>

        {/* Tabs - Responsive with horizontal scroll on mobile */}
        <div className="mb-4 sm:mb-6 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
          <nav className="-mb-px flex space-x-4 sm:space-x-8 min-w-max sm:min-w-0" aria-label="Tabs">
            <button
              onClick={() => {
                setActiveTab('all');
                setPage(1);
              }}
              className={`${
                activeTab === 'all'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm transition touch-manipulation`}
            >
              All Diagrams
            </button>
            <button
              onClick={() => {
                setActiveTab('recent');
                setPage(1);
              }}
              className={`${
                activeTab === 'recent'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
              } whitespace-nowrap py-3 sm:py-4 px-1 border-b-2 font-medium text-xs sm:text-sm transition touch-manipulation`}
            >
              Recent
            </button>
            <button
              onClick={() => {
                setActiveTab('starred');
                setPage(1);
              }}
              className={`${
                activeTab === 'starred'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition`}
            >
              ⭐ Starred
            </button>
            <button
              onClick={() => {
                setActiveTab('shared');
                setPage(1);
              }}
              className={`${
                activeTab === 'shared'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition`}
            >
              Shared with me
            </button>
            <button
              onClick={() => {
                setActiveTab('trash');
                setPage(1);
              }}
              className={`${
                activeTab === 'trash'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition`}
            >
              🗑️ Trash
            </button>
          </nav>
        </div>

        {/* Search and Filter - Only show for "All" tab */}
        {activeTab === 'all' && (
          <div className="mb-6 bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="flex flex-col gap-4">
              {/* Search Bar - Instant Search */}
              <div className="flex-1">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    placeholder="Search diagrams... (instant results as you type)"
                    className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {/* Search icon */}
                  <svg
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
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
                  <p className="mt-1 text-xs text-gray-500">
                    <span className="inline-flex items-center gap-1">
                      <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Instant search
                    </span>
                    {' • '}
                    Use <code className="px-1 bg-gray-100 rounded">type:</code> or <code className="px-1 bg-gray-100 rounded">author:</code> to filter
                  </p>
                </div>
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchInput('');
                      setSearchQuery('');
                      setPage(1);
                    }}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md font-medium hover:bg-gray-300 transition"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
            
            {/* Filter and Sort Controls */}
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
              {/* Type Filter */}
              <div className="flex gap-2 items-center">
                <span className="text-sm font-medium text-gray-700 mr-2">Filter:</span>
                <button
                  onClick={() => handleFilterChange('')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    filterType === '' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => handleFilterChange('canvas')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    filterType === 'canvas' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Canvas
                </button>
                <button
                  onClick={() => handleFilterChange('note')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    filterType === 'note' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Note
                </button>
                <button
                  onClick={() => handleFilterChange('mixed')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    filterType === 'mixed' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Mixed
                </button>
              </div>

              {/* Advanced Filters Toggle */}
              <div className="flex gap-2 items-center">
                <button
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition flex items-center gap-1 ${
                    showAdvancedFilters || filterAuthor || filterDateRange !== 'all' || filterFolder
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  Advanced Filters
                  {(filterAuthor || filterDateRange !== 'all' || filterFolder) && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-white text-blue-600 rounded-full">
                      {[filterAuthor, filterDateRange !== 'all', filterFolder].filter(Boolean).length}
                    </span>
                  )}
                </button>
              </div>

              {/* Sort Controls */}
              <div className="flex gap-2 items-center">
                <span className="text-sm font-medium text-gray-700 mr-2">Sort by:</span>
                <button
                  onClick={() => handleSortChange('title')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'title'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Name {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
                <button
                  onClick={() => handleSortChange('created_at')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'created_at'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Created {sortBy === 'created_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
                <button
                  onClick={() => handleSortChange('updated_at')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'updated_at'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Updated {sortBy === 'updated_at' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
                <button
                  onClick={() => handleSortChange('last_viewed')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'last_viewed'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Last Viewed {sortBy === 'last_viewed' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
                <button
                  onClick={() => handleSortChange('last_activity')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'last_activity'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Last Activity {sortBy === 'last_activity' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
                <button
                  onClick={() => handleSortChange('size_bytes')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    sortBy === 'size_bytes'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Size {sortBy === 'size_bytes' && (sortOrder === 'asc' ? '↑' : '↓')}
                </button>
              </div>

              {/* View Mode Toggle */}
              <div className="flex gap-2 items-center ml-auto">
                <span className="text-sm font-medium text-gray-700 mr-2">View:</span>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    viewMode === 'grid'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  title="Grid view with thumbnails"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-1.5 text-sm rounded-md font-medium transition ${
                    viewMode === 'list'
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  title="List view with details"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
              </div>
            </div>
            
            {/* Advanced Filters Panel */}
            {showAdvancedFilters && (
              <div className="mt-4 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Filter by Author */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Filter by Author
                    </label>
                    <input
                      type="text"
                      value={filterAuthor}
                      onChange={(e) => {
                        setFilterAuthor(e.target.value);
                        setPage(1);
                      }}
                      placeholder="Enter author email or name"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    {filterAuthor && (
                      <button
                        onClick={() => {
                          setFilterAuthor('');
                          setPage(1);
                        }}
                        className="mt-1 text-xs text-blue-600 hover:text-blue-800"
                      >
                        Clear
                      </button>
                    )}
                  </div>

                  {/* Filter by Date Range */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Filter by Date Range
                    </label>
                    <select
                      value={filterDateRange}
                      onChange={(e) => {
                        setFilterDateRange(e.target.value as 'all' | 'today' | 'week' | 'month' | 'year');
                        setPage(1);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                      <option value="all">All Time</option>
                      <option value="today">Today</option>
                      <option value="week">Last 7 Days</option>
                      <option value="month">Last 30 Days</option>
                      <option value="year">Last Year</option>
                    </select>
                  </div>

                  {/* Filter by Folder */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Filter by Folder
                    </label>
                    <select
                      value={filterFolder}
                      onChange={(e) => {
                        setFilterFolder(e.target.value);
                        setPage(1);
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    >
                      <option value="">All Folders</option>
                      {/* TODO: Load folders dynamically */}
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Use sidebar to navigate folders
                    </p>
                  </div>
                </div>

                {/* Clear All Filters */}
                {(filterAuthor || filterDateRange !== 'all' || filterFolder) && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <button
                      onClick={() => {
                        setFilterAuthor('');
                        setFilterDateRange('all');
                        setFilterFolder('');
                        setPage(1);
                      }}
                      className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition"
                    >
                      Clear All Filters
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
        )}

        {/* Batch Actions Toolbar */}
        {selectedDiagrams.size > 0 && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-medium text-blue-900">
                  {selectedDiagrams.size} diagram{selectedDiagrams.size !== 1 ? 's' : ''} selected
                </span>
                <button
                  onClick={() => setSelectedDiagrams(new Set())}
                  className="text-sm text-blue-700 hover:text-blue-900 font-medium"
                >
                  Clear Selection
                </button>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowMoveDialog(true)}
                  className="px-4 py-2 bg-white border border-blue-300 text-blue-700 rounded-md font-medium hover:bg-blue-50 transition"
                >
                  Move Selected
                </button>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 bg-red-600 text-white rounded-md font-medium hover:bg-red-700 transition"
                >
                  Delete Selected
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Diagrams List */}
        {loadingDiagrams ? (
          viewMode === 'grid' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <SkeletonListItem key={i} />
              ))}
            </div>
          )
        ) : diagrams.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
            <p className="text-gray-600 text-lg mb-4">
              {searchQuery || filterType 
                ? 'No diagrams found matching your criteria' 
                : 'No diagrams yet'}
            </p>
            <button 
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
            >
              Create Your First Diagram
            </button>
          </div>
        ) : (
          <>
            {/* Grid View */}
            {viewMode === 'grid' && (
              <>
                {/* Select All Checkbox */}
                <div className="mb-4 flex items-center gap-2 px-2">
                  <input
                    type="checkbox"
                    checked={diagrams.length > 0 && selectedDiagrams.size === diagrams.length}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label className="text-sm text-gray-700 font-medium">
                    Select All
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                  {diagrams.map((diagram) => (
                    <div
                      key={diagram.id}
                      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border-2 transition ${
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
                              toggleSelectDiagram(diagram.id);
                            }}
                            onClick={(e) => e.stopPropagation()}
                            className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 bg-white shadow-sm"
                          />
                        </div>
                        
                        {/* Thumbnail */}
                        <div 
                          onClick={() => handleDiagramClick(diagram)}
                          className="w-full h-48 bg-gray-100 flex items-center justify-center overflow-hidden cursor-pointer"
                        >
                      {diagram.thumbnail_url ? (
                        <img 
                          src={diagram.thumbnail_url} 
                          alt={diagram.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="text-gray-400 text-center p-4">
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
                        onClick={() => handleDiagramClick(diagram)}
                        className="p-4 cursor-pointer"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 truncate flex-1">
                            {searchQuery ? highlightSearchTerm(diagram.title, searchQuery) : diagram.title}
                          </h3>
                          <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                            {diagram.file_type}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>Version: {diagram.current_version} ({diagram.version_count || 1} total)</p>
                          <p>Updated: {new Date(diagram.updated_at).toLocaleDateString()}</p>
                          {diagram.last_activity && (
                            <p>Last Activity: {new Date(diagram.last_activity).toLocaleDateString()}</p>
                          )}
                          <p>Size: {formatBytes(diagram.size_bytes)}</p>
                          <p>Exports: {diagram.export_count || 0}</p>
                          <p>Collaborators: {diagram.collaborator_count || 1}</p>
                          <p>Comments: {diagram.comment_count || 0}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* List View */}
            {viewMode === 'list' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={diagrams.length > 0 && selectedDiagrams.size === diagrams.length}
                          onChange={toggleSelectAll}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Preview
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Title
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Owner
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Updated
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Activity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Version
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Versions
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Size
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Exports
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Collaborators
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Comments
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {diagrams.map((diagram) => (
                      <tr
                        key={diagram.id}
                        className={`transition ${
                          selectedDiagrams.has(diagram.id)
                            ? 'bg-blue-50'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedDiagrams.has(diagram.id)}
                            onChange={() => toggleSelectDiagram(diagram.id)}
                            onClick={(e) => e.stopPropagation()}
                            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="w-16 h-16 bg-gray-100 rounded flex items-center justify-center overflow-hidden">
                            {diagram.thumbnail_url ? (
                              <img 
                                src={diagram.thumbnail_url} 
                                alt={diagram.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            )}
                          </div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm font-medium text-gray-900">
                            {searchQuery ? highlightSearchTerm(diagram.title, searchQuery) : diagram.title}
                          </div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                            {diagram.file_type}
                          </span>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{diagram.owner_email || user?.email || 'Unknown'}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">
                            {new Date(diagram.updated_at).toLocaleDateString()}
                          </div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">
                            {diagram.last_activity ? new Date(diagram.last_activity).toLocaleDateString() : '-'}
                          </div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">v{diagram.current_version}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{diagram.version_count || 1}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{formatBytes(diagram.size_bytes)}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{diagram.export_count || 0}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{diagram.collaborator_count || 1}</div>
                        </td>
                        <td 
                          onClick={() => handleDiagramClick(diagram)}
                          className="px-6 py-4 whitespace-nowrap cursor-pointer"
                        >
                          <div className="text-sm text-gray-600">{diagram.comment_count || 0}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination - Only show for "All" tab */}
            {activeTab === 'all' && totalPages > 1 && (
              <div className="mt-8 flex justify-center items-center gap-4">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={!hasPrev}
                  className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <span className="text-gray-700">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={!hasNext}
                  className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
          </div>
          {/* End of max-w-7xl container */}
        </div>
        {/* End of flex-1 overflow-y-auto (main content) */}
      </div>
      {/* End of flex container with sidebar */}

      {/* Create Diagram Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Create New Diagram</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Diagram Title
                </label>
                <input
                  id="title"
                  type="text"
                  value={diagramTitle}
                  onChange={(e) => setDiagramTitle(e.target.value)}
                  placeholder="My Architecture Diagram"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={creating}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Diagram Type
                </label>
                <div className="space-y-2">
                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="canvas"
                      checked={diagramType === 'canvas'}
                      onChange={(e) => setDiagramType(e.target.value as 'canvas')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Canvas</div>
                      <div className="text-sm text-gray-600">Visual diagram with shapes and connections</div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="note"
                      checked={diagramType === 'note'}
                      onChange={(e) => setDiagramType(e.target.value as 'note')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Note</div>
                      <div className="text-sm text-gray-600">Markdown document with text</div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="type"
                      value="mixed"
                      checked={diagramType === 'mixed'}
                      onChange={(e) => setDiagramType(e.target.value as 'mixed')}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Mixed</div>
                      <div className="text-sm text-gray-600">Canvas and notes combined</div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-purple-300 rounded-md cursor-pointer hover:bg-purple-50 bg-purple-25">
                    <input
                      type="radio"
                      name="type"
                      value="mermaid"
                      checked={diagramType === 'mermaid' as any}
                      onChange={(e) => setDiagramType(e.target.value as any)}
                      className="mr-3"
                      disabled={creating}
                    />
                    <div>
                      <div className="font-medium text-gray-900">Diagram-as-Code (Mermaid)</div>
                      <div className="text-sm text-gray-600">Code-based diagrams with Mermaid.js</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setDiagramTitle('');
                  setDiagramType('canvas');
                  setError('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition"
                disabled={creating}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateDiagram}
                disabled={creating || !diagramTitle.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {creating ? 'Creating...' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Delete Diagrams?</h2>
            <p className="text-gray-700 mb-6">
              Are you sure you want to delete {selectedDiagrams.size} diagram{selectedDiagrams.size !== 1 ? 's' : ''}? 
              They will be moved to trash and can be restored within 30 days.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition"
                disabled={deletingBatch}
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={deletingBatch}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md font-medium hover:bg-red-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {deletingBatch ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Move Dialog */}
      {showMoveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Move Diagrams</h2>
            <p className="text-gray-700 mb-4">
              Move {selectedDiagrams.size} diagram{selectedDiagrams.size !== 1 ? 's' : ''} to:
            </p>
            <div className="space-y-2 mb-6">
              <button
                onClick={() => handleBulkMove(null)}
                disabled={movingBatch}
                className="w-full px-4 py-3 text-left border border-gray-300 rounded-md hover:bg-gray-50 transition disabled:opacity-50"
              >
                <div className="font-medium text-gray-900">Root Folder</div>
                <div className="text-sm text-gray-600">Move to main workspace</div>
              </button>
              <div className="text-sm text-gray-500 italic p-2">
                Note: Folder management will be implemented in a future update. For now, diagrams can only be moved to the root folder.
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowMoveDialog(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 transition"
                disabled={movingBatch}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Command Palette */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={() => setShowCommandPalette(false)}
        onCreateDiagram={(type) => {
          setDiagramType(type);
          setShowCreateModal(true);
        }}
        diagrams={diagrams}
      />

      {/* Keyboard Shortcuts Dialog */}
      <KeyboardShortcutsDialog
        isOpen={showKeyboardShortcuts}
        onClose={() => setShowKeyboardShortcuts(false)}
      />

      {/* Mobile Bottom Navigation */}
      <MobileBottomNav onCreateClick={() => setShowCreateModal(true)} />
    </main>
  );
}
