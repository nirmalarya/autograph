'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface Diagram {
  id: string;
  title: string;
  file_type: 'canvas' | 'note' | 'mixed';
  created_at: string;
  updated_at: string;
  current_version: number;
  thumbnail_url?: string;
  owner_email?: string;
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

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [diagramTitle, setDiagramTitle] = useState('');
  const [diagramType, setDiagramType] = useState<'canvas' | 'note' | 'mixed'>('canvas');
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

  // Fetch diagrams when user, page, filterType, searchQuery, sortBy, or sortOrder changes
  useEffect(() => {
    if (user?.sub) {
      fetchDiagrams();
    }
  }, [user, page, filterType, searchQuery, sortBy, sortOrder]);

  const fetchDiagrams = async () => {
    if (!user?.sub) return;

    setLoadingDiagrams(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '20',
      });

      if (filterType) {
        params.append('file_type', filterType);
      }

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      if (sortBy) {
        params.append('sort_by', sortBy);
      }

      if (sortOrder) {
        params.append('sort_order', sortOrder);
      }

      const response = await fetch(`http://localhost:8082/?${params.toString()}`, {
        headers: {
          'X-User-ID': user.sub,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch diagrams');
      }

      const data: DiagramsResponse = await response.json();
      setDiagrams(data.diagrams);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setHasNext(data.has_next);
      setHasPrev(data.has_prev);
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
      router.push(`/note/${diagram.id}`);
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
      const response = await fetch('http://localhost:8082/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': user?.sub || '',
        },
        body: JSON.stringify({
          title: diagramTitle,
          file_type: diagramType,
          canvas_data: diagramType === 'canvas' || diagramType === 'mixed' ? { shapes: [] } : null,
          note_content: diagramType === 'note' || diagramType === 'mixed' ? '' : null,
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
      if (diagramType === 'canvas') {
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

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">AutoGraph v3</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              My Diagrams
            </h2>
            <p className="text-gray-600">
              {total} diagram{total !== 1 ? 's' : ''} total
            </p>
          </div>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
          >
            + Create Diagram
          </button>
        </div>

        {/* Search and Filter */}
        <div className="mb-6 bg-white rounded-lg shadow-sm p-4 border border-gray-200">
          <div className="flex flex-col gap-4">
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="flex-1">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder="Search diagrams by title..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
                >
                  Search
                </button>
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
            </form>
            
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
          </div>
        </div>

        {/* Diagrams List */}
        {loadingDiagrams ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading diagrams...</p>
          </div>
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {diagrams.map((diagram) => (
                  <div
                    key={diagram.id}
                    onClick={() => handleDiagramClick(diagram)}
                    className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200 cursor-pointer hover:shadow-md hover:border-blue-300 transition"
                  >
                    {/* Thumbnail */}
                    <div className="w-full h-48 bg-gray-100 flex items-center justify-center overflow-hidden">
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
                    
                    {/* Card Content */}
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="text-lg font-semibold text-gray-900 truncate flex-1">
                          {diagram.title}
                        </h3>
                        <span className="ml-2 px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                          {diagram.file_type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Version: {diagram.current_version}</p>
                        <p>Updated: {new Date(diagram.updated_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* List View */}
            {viewMode === 'list' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
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
                        Version
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {diagrams.map((diagram) => (
                      <tr
                        key={diagram.id}
                        onClick={() => handleDiagramClick(diagram)}
                        className="cursor-pointer hover:bg-gray-50 transition"
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
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
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{diagram.title}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                            {diagram.file_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{diagram.owner_email || user?.email || 'Unknown'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">
                            {new Date(diagram.updated_at).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">v{diagram.current_version}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
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
    </main>
  );
}
