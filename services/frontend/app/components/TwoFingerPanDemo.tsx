'use client';

import React, { useRef } from 'react';
import { useTwoFingerPan } from '@/hooks/useTwoFingerPan';

export function TwoFingerPanDemo() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { isPanning, panOffset, resetPan } = useTwoFingerPan(containerRef, {
    threshold: 5,
    smoothing: true,
    onPan: (deltaX, deltaY) => {
      console.log('Pan delta:', deltaX, deltaY);
    },
    onPanStart: () => {
      console.log('Pan started');
    },
    onPanEnd: () => {
      console.log('Pan ended');
    },
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold mb-4">Two-Finger Pan Demo</h1>
        <p className="text-gray-600 mb-2">
          Use two fingers to drag and pan the canvas
        </p>
        <p className="text-gray-600 mb-4">
          Works on touch devices with multi-touch support
        </p>

        <div className="flex items-center justify-center gap-4 mb-4">
          <button
            onClick={resetPan}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
            aria-label="Reset pan position"
          >
            Reset Position
          </button>

          <div className="px-4 py-2 bg-gray-100 rounded font-mono text-sm">
            X: {panOffset.x.toFixed(0)}px, Y: {panOffset.y.toFixed(0)}px
          </div>
        </div>

        {isPanning && (
          <div className="text-green-600 font-semibold animate-pulse">
            Panning in progress!
          </div>
        )}
      </div>

      <div className="mb-8 relative">
        <div
          ref={containerRef}
          className="border-4 border-gray-300 rounded-lg bg-gray-100 overflow-hidden cursor-move"
          style={{
            width: '600px',
            height: '400px',
            touchAction: 'none', // Prevent default touch actions
          }}
        >
          <div
            className="relative w-[1200px] h-[800px] transition-transform duration-200"
            style={{
              transform: `translate(${panOffset.x}px, ${panOffset.y}px)`,
              transformOrigin: 'top left',
            }}
          >
            {/* Grid background */}
            <div
              className="absolute inset-0"
              style={{
                backgroundImage: `
                  linear-gradient(rgba(0, 0, 0, 0.1) 1px, transparent 1px),
                  linear-gradient(90deg, rgba(0, 0, 0, 0.1) 1px, transparent 1px)
                `,
                backgroundSize: '50px 50px',
              }}
            />

            {/* Content items */}
            <div className="absolute top-20 left-20 w-40 h-40 bg-blue-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 1
            </div>

            <div className="absolute top-60 left-80 w-40 h-40 bg-green-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 2
            </div>

            <div className="absolute top-40 left-[360px] w-40 h-40 bg-purple-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 3
            </div>

            <div className="absolute top-[280px] left-[200px] w-40 h-40 bg-red-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 4
            </div>

            <div className="absolute top-[100px] left-[500px] w-40 h-40 bg-yellow-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 5
            </div>

            <div className="absolute top-[320px] left-[440px] w-40 h-40 bg-pink-500 rounded-lg shadow-lg flex items-center justify-center text-white font-bold text-2xl">
              Item 6
            </div>

            {/* Origin marker */}
            <div className="absolute top-0 left-0 w-4 h-4 bg-black rounded-full" />
            <div className="absolute top-0 left-5 text-xs font-mono text-black">
              (0, 0)
            </div>
          </div>
        </div>

        {/* Visual feedback overlay */}
        {isPanning && (
          <div className="absolute top-0 left-0 right-0 bottom-0 border-4 border-green-500 rounded-lg pointer-events-none animate-pulse" />
        )}
      </div>

      <div className="p-6 bg-blue-50 rounded-lg max-w-2xl">
        <h3 className="font-semibold text-lg mb-2">How to use:</h3>
        <ul className="list-disc list-inside space-y-1 text-gray-700">
          <li>
            <strong>Two-Finger Drag:</strong> Place two fingers on the canvas
            and drag to pan
          </li>
          <li>
            <strong>Smooth Panning:</strong> The canvas follows your fingers
            smoothly
          </li>
          <li>
            <strong>Reset Button:</strong> Returns the canvas to the origin (0,
            0)
          </li>
          <li>
            <strong>Position Display:</strong> Shows current pan offset in
            pixels
          </li>
          <li>
            <strong>Visual Feedback:</strong> Green border appears while
            panning
          </li>
        </ul>
      </div>

      <div
        className="mt-4 p-4 bg-gray-100 rounded font-mono text-sm"
        data-testid="pan-info"
      >
        <div>Pan Offset X: {panOffset.x.toFixed(2)}px</div>
        <div>Pan Offset Y: {panOffset.y.toFixed(2)}px</div>
        <div>Is Panning: {isPanning ? 'true' : 'false'}</div>
        <div>Threshold: 5px</div>
        <div>
          Total Distance:{' '}
          {Math.sqrt(
            panOffset.x * panOffset.x + panOffset.y * panOffset.y
          ).toFixed(2)}
          px
        </div>
      </div>
    </div>
  );
}
