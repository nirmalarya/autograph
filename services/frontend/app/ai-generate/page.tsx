'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '../components/Button';
import { API_ENDPOINTS } from '@/lib/api-config';

interface GenerateResponse {
  mermaid_code: string;
  diagram_type: string;
  explanation: string;
  provider: string;
  model: string;
  tokens_used: number;
  timestamp: string;
}

interface ProvidersStatus {
  primary_provider: string;
  available_providers: string[];
  fallback_chain: string[];
  mga_configured: boolean;
  openai_configured: boolean;
  anthropic_configured: boolean;
  gemini_configured: boolean;
}

export default function AIGeneratePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [diagramType, setDiagramType] = useState<string>('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [providersStatus, setProvidersStatus] = useState<ProvidersStatus | null>(null);
  const [savingToDashboard, setSavingToDashboard] = useState(false);

  // Example prompts for quick testing
  const examplePrompts = [
    {
      title: "E-commerce Architecture",
      prompt: "Create an e-commerce architecture with frontend, backend, payment gateway, and database",
      type: "architecture"
    },
    {
      title: "User Login Flow",
      prompt: "Create a sequence diagram for user login with email and password",
      type: "sequence"
    },
    {
      title: "Blog Database Schema",
      prompt: "Create a database schema for a blog with users, posts, comments, and tags",
      type: "erd"
    },
    {
      title: "Order Processing Flowchart",
      prompt: "Create a flowchart for order processing from cart to delivery",
      type: "flowchart"
    }
  ];

  // Load providers status on mount
  useState(() => {
    loadProvidersStatus();
  });

  async function loadProvidersStatus() {
    try {
      const response = await fetch(`${API_ENDPOINTS.ai.generate.replace('/generate', '/providers')}`);
      if (response.ok) {
        const data = await response.json();
        setProvidersStatus(data);
      }
    } catch (err) {
      console.error('Failed to load providers status:', err);
    }
  }

  async function handleGenerate() {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setError('');
    setGenerating(true);
    setResult(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.ai.generate, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          diagram_type: diagramType || undefined
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate diagram');
      }

      const data: GenerateResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to generate diagram');
      console.error('Generation error:', err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveToDashboard() {
    if (!result) return;

    setSavingToDashboard(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      // Create a new Mermaid diagram
      const response = await fetch(API_ENDPOINTS.diagrams.create, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: `AI Generated - ${result.diagram_type} (${new Date().toLocaleString()})`,
          file_type: 'note',  // Mermaid diagrams are stored as 'note' type
          note_content: result.mermaid_code
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save diagram');
      }

      const diagram = await response.json();
      
      // Redirect to the Mermaid editor
      router.push(`/mermaid/${diagram.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to save diagram');
      console.error('Save error:', err);
    } finally {
      setSavingToDashboard(false);
    }
  }

  function useExamplePrompt(example: typeof examplePrompts[0]) {
    setPrompt(example.prompt);
    setDiagramType(example.type);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-2xl font-bold text-gray-900">
                AI Diagram Generator
              </h1>
            </div>
            {providersStatus && (
              <div className="text-sm text-gray-600">
                Primary: <span className="font-semibold">{providersStatus.primary_provider || 'None'}</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Input Form */}
          <div className="space-y-6">
            {/* Provider Status */}
            {providersStatus && (
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-2">AI Providers</h3>
                <div className="space-y-1 text-sm">
                  {providersStatus.fallback_chain.map((provider, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <span className="text-green-600">✓</span>
                      <span className="text-gray-700">{provider}</span>
                    </div>
                  ))}
                </div>
                {providersStatus.available_providers.length === 0 && (
                  <p className="text-sm text-red-600">No providers configured</p>
                )}
              </div>
            )}

            {/* Example Prompts */}
            <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-3">Example Prompts</h3>
              <div className="grid grid-cols-1 gap-2">
                {examplePrompts.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => useExamplePrompt(example)}
                    className="text-left p-3 rounded border border-gray-200 hover:border-blue-500 hover:bg-blue-50 transition-colors"
                  >
                    <div className="font-medium text-sm text-gray-900">{example.title}</div>
                    <div className="text-xs text-gray-600 mt-1">{example.prompt}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Generation Form */}
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="font-semibold text-gray-900 mb-4">Generate Diagram</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Describe your diagram
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="E.g., Create a microservices architecture with API gateway, auth service, and database"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[120px]"
                    disabled={generating}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Diagram Type (optional)
                  </label>
                  <select
                    value={diagramType}
                    onChange={(e) => setDiagramType(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={generating}
                  >
                    <option value="">Auto-detect</option>
                    <option value="architecture">Architecture</option>
                    <option value="sequence">Sequence</option>
                    <option value="erd">ER Diagram</option>
                    <option value="flowchart">Flowchart</option>
                    <option value="class_diagram">Class Diagram</option>
                    <option value="state_diagram">State Diagram</option>
                  </select>
                </div>

                {error && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
                    {error}
                  </div>
                )}

                <Button
                  onClick={handleGenerate}
                  disabled={generating || !prompt.trim()}
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={generating}
                >
                  Generate Diagram
                </Button>
              </div>
            </div>
          </div>

          {/* Right: Preview/Result */}
          <div className="space-y-6">
            {result ? (
              <>
                {/* Result Info */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900">Generated Diagram</h3>
                    <Button
                      onClick={handleSaveToDashboard}
                      disabled={savingToDashboard}
                      variant="success"
                      size="sm"
                      loading={savingToDashboard}
                    >
                      Save to Dashboard
                    </Button>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium text-gray-900">{result.diagram_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Provider:</span>
                      <span className="font-medium text-gray-900">{result.provider}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Model:</span>
                      <span className="font-medium text-gray-900">{result.model}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Tokens:</span>
                      <span className="font-medium text-gray-900">{result.tokens_used}</span>
                    </div>
                  </div>
                </div>

                {/* Mermaid Code */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900">Mermaid Code</h3>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(result.mermaid_code);
                      }}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Copy
                    </button>
                  </div>
                  <pre className="bg-gray-50 p-3 rounded border border-gray-200 overflow-x-auto text-xs font-mono">
                    <code>{result.mermaid_code}</code>
                  </pre>
                </div>

                {/* Explanation */}
                <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-2">Explanation</h3>
                  <p className="text-sm text-gray-700">{result.explanation}</p>
                </div>
              </>
            ) : (
              <div className="bg-white p-12 rounded-lg shadow-sm border border-gray-200 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">No diagram generated yet</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Enter a prompt and click Generate to create your diagram
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
