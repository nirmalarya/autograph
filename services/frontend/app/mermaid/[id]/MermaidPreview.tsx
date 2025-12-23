'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidPreviewProps {
  code: string;
}

// Initialize mermaid with configuration
mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  fontFamily: 'Inter, system-ui, sans-serif',
  themeVariables: {
    fontSize: '16px',
  },
});

export default function MermaidPreview({ code }: MermaidPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string>('');
  const [isRendering, setIsRendering] = useState(false);

  useEffect(() => {
    const renderDiagram = async () => {
      if (!containerRef.current || !code.trim()) {
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }
        return;
      }

      setIsRendering(true);
      setError('');

      try {
        // Clear previous content
        containerRef.current.innerHTML = '';

        // Generate unique ID for this diagram
        const id = `mermaid-${Date.now()}`;

        // Render the diagram
        const { svg } = await mermaid.render(id, code);
        
        if (containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch (err: any) {
        console.error('Mermaid rendering error:', err);
        setError(err.message || 'Failed to render diagram');
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
        }
      } finally {
        setIsRendering(false);
      }
    };

    // Debounce rendering to avoid too many updates
    const timeoutId = setTimeout(renderDiagram, 300);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [code]);

  return (
    <div className="h-full flex items-center justify-center bg-white overflow-auto">
      {error ? (
        <div className="text-center p-6 max-w-2xl">
          <div className="text-red-600 mb-2 text-xl">⚠️ Syntax Error</div>
          <div className="text-sm text-gray-600 bg-red-50 border border-red-200 rounded p-4">
            <pre className="whitespace-pre-wrap font-mono text-left">{error}</pre>
          </div>
          <div className="mt-4 text-xs text-gray-500">
            Check your Mermaid syntax and try again
          </div>
        </div>
      ) : !code.trim() ? (
        <div className="text-center p-6 text-gray-400">
          <div className="text-6xl mb-4">📊</div>
          <div className="text-lg">Start typing Mermaid code to see preview</div>
          <div className="text-sm mt-2">Try: <code className="bg-gray-100 px-2 py-1 rounded">graph TD</code></div>
        </div>
      ) : isRendering ? (
        <div className="text-center p-6 text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <div className="text-sm">Rendering diagram...</div>
        </div>
      ) : (
        <div 
          ref={containerRef} 
          className="p-6 w-full h-full flex items-center justify-center"
        />
      )}
    </div>
  );
}
