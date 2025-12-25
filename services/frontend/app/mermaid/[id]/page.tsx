'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import { API_ENDPOINTS } from '@/lib/api-config';

// Dynamically import components to avoid SSR issues
const MermaidEditor = dynamic(() => import('./MermaidEditor'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
        <p className="text-sm text-gray-600">Loading editor...</p>
      </div>
    </div>
  ),
});

const MermaidPreview = dynamic(() => import('./MermaidPreview'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-white">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
        <p className="text-sm text-gray-600">Loading preview...</p>
      </div>
    </div>
  ),
});

// Default Mermaid code templates
const DEFAULT_CODE = `graph TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[End]
`;

export default function MermaidDiagramPage() {
  const router = useRouter();
  const params = useParams();
  const diagramId = params.id as string;
  
  const [diagram, setDiagram] = useState<any>(null);
  const [code, setCode] = useState(DEFAULT_CODE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [user, setUser] = useState<{ email?: string; sub?: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [splitPosition, setSplitPosition] = useState(50); // Split percentage
  const [mermaidTheme, setMermaidTheme] = useState<'default' | 'dark' | 'forest' | 'neutral'>('default');
  const [showThemeMenu, setShowThemeMenu] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.email, sub: payload.sub });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    // Fetch diagram data
    fetchDiagram();
  }, [diagramId, router]);

  const fetchDiagram = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));
      
      const response = await fetch(API_ENDPOINTS.diagrams.get(diagramId), {
        headers: {
          'X-User-ID': payload.sub,
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Diagram not found');
        } else if (response.status === 403) {
          throw new Error('You do not have permission to access this diagram');
        }
        throw new Error('Failed to load diagram');
      }

      const data = await response.json();
      setDiagram(data);
      
      // Load Mermaid code from note_content
      if (data.note_content) {
        setCode(data.note_content);
      }
    } catch (err: any) {
      console.error('Failed to fetch diagram:', err);
      setError(err.message || 'Failed to load diagram');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = useCallback(async () => {
    if (!diagram) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('access_token');
      const payload = JSON.parse(atob(token!.split('.')[1]));

      const response = await fetch(API_ENDPOINTS.diagrams.update(diagramId), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': payload.sub,
        },
        body: JSON.stringify({
          title: diagram.title,
          canvas_data: diagram.canvas_data,
          note_content: code, // Save Mermaid code in note_content
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save diagram');
      }

      const updated = await response.json();
      setDiagram(updated);
      setLastSaved(new Date());
    } catch (err) {
      console.error('Failed to save diagram:', err);
      alert('Failed to save diagram. Please try again.');
    } finally {
      setSaving(false);
    }
  }, [diagram, diagramId, code]);

  const handleBackToDashboard = () => {
    router.push('/dashboard');
  };

  const handleExportCode = () => {
    try {
      // Create a blob with the Mermaid code
      const blob = new Blob([code], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      
      // Create a temporary link element to trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `${diagram?.title || 'diagram'}.mmd`;
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export code:', err);
      alert('Failed to export code. Please try again.');
    }
  };

  const handleImportCode = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      setCode(text);
      
      // Clear the input so the same file can be imported again if needed
      event.target.value = '';
    } catch (err) {
      console.error('Failed to import code:', err);
      alert('Failed to import code. Please try again.');
    }
  };

  // Add Ctrl+S / Cmd+S keyboard shortcut for manual save
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 's') {
        event.preventDefault();
        if (!saving) {
          handleSave();
        }
      }
    };

    const handleMermaidSave = () => {
      if (!saving) {
        handleSave();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mermaid-save', handleMermaidSave);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mermaid-save', handleMermaidSave);
    };
  }, [handleSave, saving]);

  // Auto-save every 5 minutes
  useEffect(() => {
    if (!diagram) return;

    const autoSaveInterval = setInterval(() => {
      handleSave();
    }, 5 * 60 * 1000); // 5 minutes

    return () => {
      clearInterval(autoSaveInterval);
    };
  }, [diagram, handleSave]);

  // Close theme menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showThemeMenu && !target.closest('.theme-menu-container')) {
        setShowThemeMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showThemeMenu]);

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading diagram...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={handleBackToDashboard}
            className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition"
          >
            Back to Dashboard
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="fixed inset-0 flex flex-col bg-gray-50">
      {/* Header */}
      <nav className="flex-shrink-0 bg-white shadow-sm border-b border-gray-200 z-10">
        <div className="max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={handleBackToDashboard}
                className="text-gray-600 hover:text-gray-900 transition"
                title="Back to Dashboard"
              >
                ← Back
              </button>
              <div className="border-l border-gray-300 h-6"></div>
              <h1 className="text-lg font-semibold text-gray-900">
                {diagram?.title || 'Untitled Diagram'}
              </h1>
              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                Mermaid
              </span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                v{diagram?.current_version || 1}
              </span>
            </div>
            <div className="flex items-center gap-4">
              {lastSaved && (
                <span className="text-xs text-gray-500">
                  Saved at {lastSaved.toLocaleTimeString()}
                </span>
              )}
              <span className="text-sm text-gray-600">{user?.email}</span>
              
              {/* Theme selector */}
              <div className="relative theme-menu-container">
                <button 
                  onClick={() => setShowThemeMenu(!showThemeMenu)}
                  className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition flex items-center gap-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  title="Change theme"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                  </svg>
                  <span className="capitalize">{mermaidTheme}</span>
                </button>
                {showThemeMenu && (
                  <div className="absolute right-0 mt-2 w-40 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                    {['default', 'dark', 'forest', 'neutral'].map((theme) => (
                      <button
                        key={theme}
                        onClick={() => {
                          setMermaidTheme(theme as any);
                          setShowThemeMenu(false);
                        }}
                        className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 first:rounded-t-md last:rounded-b-md ${
                          mermaidTheme === theme ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                        }`}
                      >
                        <span className="capitalize">{theme}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <button 
                onClick={handleExportCode}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition flex items-center gap-2"
                title="Export Mermaid code"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Export
              </button>
              <button 
                onClick={() => document.getElementById('import-file-input')?.click()}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition flex items-center gap-2"
                title="Import Mermaid code"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Import
              </button>
              <input
                id="import-file-input"
                type="file"
                accept=".mmd,.mermaid,.txt"
                onChange={handleImportCode}
                style={{ display: 'none' }}
              />
              <button 
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
                title="Share (coming soon)"
              >
                Share
              </button>
              <button 
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Split View: Code Editor | Preview */}
      <div className="flex-1 flex overflow-hidden">
        {/* Code Editor */}
        <div 
          className="bg-gray-50 border-r border-gray-200 flex flex-col"
          style={{ width: `${splitPosition}%` }}
        >
          <div className="flex-shrink-0 px-4 py-2 bg-white border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-700">Code Editor</h2>
            <p className="text-xs text-gray-500">Write your Mermaid diagram code</p>
          </div>
          <div className="flex-1 overflow-hidden">
            <MermaidEditor value={code} onChange={setCode} />
          </div>
        </div>

        {/* Resizable Divider */}
        <div
          className="w-1 bg-gray-300 cursor-col-resize hover:bg-blue-500 transition-colors"
          onMouseDown={(e) => {
            const startX = e.clientX;
            const startSplit = splitPosition;
            
            const handleMouseMove = (e: MouseEvent) => {
              const deltaX = e.clientX - startX;
              const containerWidth = window.innerWidth;
              const deltaPercent = (deltaX / containerWidth) * 100;
              const newSplit = Math.min(Math.max(startSplit + deltaPercent, 20), 80);
              setSplitPosition(newSplit);
            };
            
            const handleMouseUp = () => {
              document.removeEventListener('mousemove', handleMouseMove);
              document.removeEventListener('mouseup', handleMouseUp);
            };
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
          }}
        />

        {/* Preview */}
        <div 
          className="bg-white flex flex-col"
          style={{ width: `${100 - splitPosition}%` }}
        >
          <div className="flex-shrink-0 px-4 py-2 bg-white border-b border-gray-200">
            <h2 className="text-sm font-semibold text-gray-700">Live Preview</h2>
            <p className="text-xs text-gray-500">Your diagram updates in real-time</p>
          </div>
          <div className="flex-1 overflow-auto">
            <MermaidPreview code={code} theme={mermaidTheme} />
          </div>
        </div>
      </div>
    </main>
  );
}
