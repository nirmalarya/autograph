'use client';

import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidPreviewProps {
  code: string;
  theme?: 'default' | 'dark' | 'forest' | 'neutral';
  onErrorLineClick?: (lineNumber: number) => void;
  onCodeUpdate?: (newCode: string) => void;
}

export default function MermaidPreview({ code, theme = 'default', onErrorLineClick, onCodeUpdate }: MermaidPreviewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string>('');
  const [errorLine, setErrorLine] = useState<number | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const [draggableEnabled, setDraggableEnabled] = useState(false);
  const [nodePositions, setNodePositions] = useState<Record<string, { x: number; y: number }>>({});

  // Reinitialize mermaid when theme changes
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: theme,
      securityLevel: 'loose',
      fontFamily: 'Inter, system-ui, sans-serif',
      themeVariables: {
        fontSize: '16px',
      },
    });
  }, [theme]);

  // Helper function to extract line number from error message
  const extractLineNumber = (errorMessage: string): number | null => {
    // Try various patterns to extract line numbers
    const patterns = [
      /line\s+(\d+)/i,
      /at\s+line\s+(\d+)/i,
      /on\s+line\s+(\d+)/i,
      /:(\d+):/,
      /\[line\s+(\d+)\]/i,
    ];

    for (const pattern of patterns) {
      const match = errorMessage.match(pattern);
      if (match && match[1]) {
        return parseInt(match[1], 10);
      }
    }

    return null;
  };

  // Helper function to format error message with line number
  const formatErrorMessage = (errorMessage: string, lineNum: number | null): string => {
    if (lineNum !== null) {
      // If error doesn't already start with line number, add it
      if (!errorMessage.toLowerCase().startsWith('line')) {
        return `Line ${lineNum}: ${errorMessage}`;
      }
    }
    return errorMessage;
  };

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
      setErrorLine(null);

      try {
        // Clear previous content
        containerRef.current.innerHTML = '';

        // Generate unique ID for this diagram
        const id = `mermaid-${Date.now()}`;

        // Render the diagram
        const { svg } = await mermaid.render(id, code);

        if (containerRef.current) {
          containerRef.current.innerHTML = svg;

          // Enable draggable functionality for nodes (Beta feature)
          if (draggableEnabled) {
            enableNodeDragging();
          }
        }
      } catch (err: any) {
        console.error('Mermaid rendering error:', err);
        const errorMessage = err.message || 'Failed to render diagram';
        const lineNum = extractLineNumber(errorMessage);

        setErrorLine(lineNum);
        setError(formatErrorMessage(errorMessage, lineNum));

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
  }, [code, theme]);

  // Function to enable drag-and-drop on SVG nodes
  const enableNodeDragging = () => {
    if (!containerRef.current) return;

    const svgElement = containerRef.current.querySelector('svg');
    if (!svgElement) return;

    // Find all flowchart nodes (typically <g> elements with class "node")
    const nodes = svgElement.querySelectorAll('g.node');

    nodes.forEach((node) => {
      const nodeElement = node as SVGGElement;

      // Add visual feedback
      nodeElement.style.cursor = 'move';

      // Extract node ID from the element
      const nodeId = nodeElement.id || nodeElement.getAttribute('id') || '';

      let isDragging = false;
      let startX = 0;
      let startY = 0;
      let initialTransform = { x: 0, y: 0 };

      const handleMouseDown = (e: MouseEvent) => {
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;

        // Get current transform
        const transform = nodeElement.getAttribute('transform') || '';
        const match = transform.match(/translate\(([^,]+),([^)]+)\)/);
        if (match) {
          initialTransform = { x: parseFloat(match[1]), y: parseFloat(match[2]) };
        }

        e.preventDefault();
        e.stopPropagation();
      };

      const handleMouseMove = (e: MouseEvent) => {
        if (!isDragging) return;

        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;

        const newX = initialTransform.x + deltaX;
        const newY = initialTransform.y + deltaY;

        nodeElement.setAttribute('transform', `translate(${newX}, ${newY})`);

        // Update node positions state
        setNodePositions(prev => ({
          ...prev,
          [nodeId]: { x: newX, y: newY }
        }));
      };

      const handleMouseUp = (e: MouseEvent) => {
        if (isDragging) {
          isDragging = false;

          // Notify code update (Beta: add comment about position)
          if (onCodeUpdate && nodeId) {
            const updatedCode = code + `\n%% Node ${nodeId} repositioned to (${nodePositions[nodeId]?.x?.toFixed(0) || 0}, ${nodePositions[nodeId]?.y?.toFixed(0) || 0})`;
            onCodeUpdate(updatedCode);
          }
        }
      };

      nodeElement.addEventListener('mousedown', handleMouseDown as any);
      document.addEventListener('mousemove', handleMouseMove as any);
      document.addEventListener('mouseup', handleMouseUp as any);
    });
  };

  return (
    <div className={`h-full flex flex-col ${
      theme === 'dark' ? 'bg-gray-900' : 'bg-white'
    }`}>
      {/* Draggable Mode Toggle (Beta) */}
      <div className="flex-shrink-0 px-4 py-2 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setDraggableEnabled(!draggableEnabled);
              if (!draggableEnabled && containerRef.current) {
                // Re-render to apply draggable handlers
                setTimeout(() => {
                  if (containerRef.current) {
                    const event = new CustomEvent('mermaid-re-render');
                    window.dispatchEvent(event);
                  }
                }, 100);
              }
            }}
            className={`px-3 py-1 text-xs font-medium rounded transition ${
              draggableEnabled
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
            title="Enable drag-and-drop mode (Beta)"
          >
            {draggableEnabled ? '🎯 Drag Mode: ON (Beta)' : '🎯 Drag Mode: OFF'}
          </button>
          {draggableEnabled && (
            <span className="text-xs text-gray-500">Drag nodes to reposition</span>
          )}
        </div>
      </div>

      {/* Diagram Content */}
      <div className="flex-1 flex items-center justify-center overflow-auto">
      {error ? (
        <div className="text-center p-6 max-w-2xl">
          <div className="text-red-600 mb-2 text-xl">⚠️ Syntax Error</div>
          <div
            className={`text-sm text-gray-600 bg-red-50 border border-red-200 rounded p-4 ${
              errorLine !== null ? 'cursor-pointer hover:bg-red-100 transition' : ''
            }`}
            onClick={() => {
              if (errorLine !== null && onErrorLineClick) {
                onErrorLineClick(errorLine);
              }
            }}
            title={errorLine !== null ? `Click to jump to line ${errorLine}` : ''}
          >
            <pre className="whitespace-pre-wrap font-mono text-left">{error}</pre>
            {errorLine !== null && (
              <div className="mt-2 text-xs text-blue-600 font-semibold">
                📍 Click to jump to line {errorLine}
              </div>
            )}
          </div>
          <div className="mt-4 text-xs text-gray-500">
            Check your Mermaid syntax and try again
          </div>
        </div>
      ) : !code.trim() ? (
        <div className={`text-center p-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-400'}`}>
          <div className="text-6xl mb-4">📊</div>
          <div className="text-lg">Start typing Mermaid code to see preview</div>
          <div className="text-sm mt-2">Try: <code className="bg-gray-100 px-2 py-1 rounded">graph TD</code></div>
        </div>
      ) : isRendering ? (
        <div className={`text-center p-6 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
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
    </div>
  );
}
