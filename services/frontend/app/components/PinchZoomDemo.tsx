'use client';

import React, { useRef } from 'react';
import { usePinchZoom } from '@/hooks/usePinchZoom';

export function PinchZoomDemo() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scale, isPinching, zoomIn, zoomOut, resetZoom } = usePinchZoom(
    containerRef,
    {
      minScale: 0.5,
      maxScale: 3,
      step: 0.1,
      smoothing: true,
      enableOnWheel: true,
      onZoomChange: (newScale) => {
        console.log('Zoom changed:', newScale);
      },
    }
  );

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-4">Pinch Zoom Demo</h1>
        <p className="text-gray-600 mb-2">
          Use two fingers to pinch zoom on touch devices
        </p>
        <p className="text-gray-600 mb-4">
          Or Ctrl/Cmd + Scroll on desktop
        </p>

        <div className="flex items-center justify-center gap-4 mb-4">
          <button
            onClick={zoomOut}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            aria-label="Zoom out"
          >
            Zoom Out
          </button>

          <div className="px-4 py-2 bg-gray-100 rounded font-mono">
            {(scale * 100).toFixed(0)}%
          </div>

          <button
            onClick={zoomIn}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            aria-label="Zoom in"
          >
            Zoom In
          </button>

          <button
            onClick={resetZoom}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition"
            aria-label="Reset zoom"
          >
            Reset
          </button>
        </div>

        {isPinching && (
          <div className="text-green-600 font-semibold animate-pulse">
            Pinching detected!
          </div>
        )}
      </div>

      <div
        ref={containerRef}
        className="relative border-4 border-gray-300 rounded-lg overflow-hidden bg-gray-50"
        style={{
          width: '600px',
          height: '400px',
          touchAction: 'none', // Prevent default touch actions
        }}
      >
        <div
          className="absolute inset-0 flex items-center justify-center transition-transform duration-200"
          style={{
            transform: `scale(${scale})`,
            transformOrigin: 'center',
          }}
        >
          <div className="bg-gradient-to-br from-blue-500 to-purple-600 text-white p-12 rounded-lg shadow-2xl">
            <h2 className="text-4xl font-bold mb-4">Zoomable Content</h2>
            <p className="text-xl mb-2">Current Scale: {scale.toFixed(2)}x</p>
            <p className="text-lg">Pinch to zoom in/out</p>

            <div className="mt-8 grid grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                <div
                  key={num}
                  className="w-16 h-16 bg-white bg-opacity-20 rounded flex items-center justify-center text-2xl font-bold"
                >
                  {num}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 p-6 bg-blue-50 rounded-lg max-w-2xl">
        <h3 className="font-semibold text-lg mb-2">How to use:</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-700">
          <li>
            <strong>Touch Device:</strong> Use two fingers to pinch zoom on the
            content area
          </li>
          <li>
            <strong>Desktop:</strong> Hold Ctrl (or Cmd on Mac) and scroll to
            zoom
          </li>
          <li>
            <strong>Buttons:</strong> Use the zoom controls above for precise
            adjustments
          </li>
          <li>
            <strong>Limits:</strong> Zoom range is 50% to 300%
          </li>
        </ul>
      </div>

      <div className="mt-4 p-4 bg-gray-100 rounded font-mono text-sm" data-testid="zoom-info">
        <div>Scale: {scale.toFixed(3)}</div>
        <div>Is Pinching: {isPinching ? 'true' : 'false'}</div>
        <div>Min Scale: 0.5</div>
        <div>Max Scale: 3.0</div>
      </div>
    </div>
  );
}
