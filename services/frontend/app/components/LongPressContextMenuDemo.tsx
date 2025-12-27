'use client';

import { useState } from 'react';
import { useLongPress } from '@/src/hooks/useLongPress';

interface ContextMenuPosition {
  x: number;
  y: number;
}

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  action: () => void;
}

export default function LongPressContextMenuDemo() {
  const [menuPosition, setMenuPosition] = useState<ContextMenuPosition | null>(null);
  const [selectedShape, setSelectedShape] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<string[]>([]);

  const addLog = (message: string) => {
    setActionLog((prev) => [...prev.slice(-4), message]);
  };

  const handleLongPress = (event: TouchEvent | MouseEvent) => {
    // Get position from event
    let x: number, y: number;
    if ('touches' in event) {
      x = event.touches[0].clientX;
      y = event.touches[0].clientY;
    } else {
      x = event.clientX;
      y = event.clientY;
    }

    // Find which shape was pressed
    const target = event.target as HTMLElement;
    const shapeElement = target.closest('[data-shape-id]');
    if (shapeElement) {
      const shapeId = shapeElement.getAttribute('data-shape-id');
      setSelectedShape(shapeId);
      setMenuPosition({ x, y });
      addLog(`Long-press detected on ${shapeId}`);

      // Haptic feedback if available
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
    }
  };

  const handleMenuAction = (action: string) => {
    addLog(`Action: ${action} on ${selectedShape}`);
    setMenuPosition(null);
    setSelectedShape(null);
  };

  const menuItems: MenuItem[] = [
    {
      id: 'edit',
      label: 'Edit',
      icon: '✏️',
      action: () => handleMenuAction('Edit'),
    },
    {
      id: 'duplicate',
      label: 'Duplicate',
      icon: '📋',
      action: () => handleMenuAction('Duplicate'),
    },
    {
      id: 'delete',
      label: 'Delete',
      icon: '🗑️',
      action: () => handleMenuAction('Delete'),
    },
    {
      id: 'properties',
      label: 'Properties',
      icon: '⚙️',
      action: () => handleMenuAction('Properties'),
    },
  ];

  const { isLongPressing } = useLongPress({
    onLongPress: handleLongPress,
    onLongPressStart: () => addLog('Long-press started...'),
    onLongPressEnd: () => addLog('Long-press ended'),
    delay: 500,
    moveThreshold: 10,
  });

  const shapes = [
    { id: 'rectangle', label: 'Rectangle', color: 'bg-blue-500' },
    { id: 'circle', label: 'Circle', color: 'bg-green-500' },
    { id: 'triangle', label: 'Triangle', color: 'bg-purple-500' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-2 text-gray-900">
          Long-Press Context Menu Demo
        </h1>
        <p className="text-gray-600 mb-8">
          Long-press (or click and hold) on any shape to open a context menu
        </p>

        {/* Status Indicator */}
        <div className="mb-6 p-4 bg-white rounded-lg shadow">
          <div className="flex items-center gap-3">
            <div
              className={`w-3 h-3 rounded-full transition-colors ${
                isLongPressing ? 'bg-green-500' : 'bg-gray-300'
              }`}
            />
            <span className="font-medium text-gray-700">
              {isLongPressing ? 'Long-pressing...' : 'Ready'}
            </span>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="relative bg-white rounded-lg shadow-lg p-8 mb-6 min-h-[400px]">
          <h2 className="text-lg font-semibold mb-4 text-gray-700">
            Canvas (Long-press any shape)
          </h2>

          <div className="grid grid-cols-3 gap-8">
            {shapes.map((shape) => (
              <div
                key={shape.id}
                data-shape-id={shape.id}
                className={`${shape.color} rounded-lg p-8 cursor-pointer select-none transition-transform active:scale-95 ${
                  selectedShape === shape.id ? 'ring-4 ring-yellow-400' : ''
                }`}
                style={{ touchAction: 'none' }}
              >
                <div className="text-white text-center font-semibold">
                  {shape.label}
                </div>
              </div>
            ))}
          </div>

          {/* Context Menu */}
          {menuPosition && (
            <>
              {/* Backdrop to close menu */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => {
                  setMenuPosition(null);
                  setSelectedShape(null);
                  addLog('Menu closed');
                }}
              />

              {/* Context Menu */}
              <div
                className="fixed z-50 bg-white rounded-lg shadow-2xl border border-gray-200 overflow-hidden"
                style={{
                  left: `${menuPosition.x}px`,
                  top: `${menuPosition.y}px`,
                  minWidth: '200px',
                }}
              >
                <div className="py-2">
                  {menuItems.map((item, index) => (
                    <button
                      key={item.id}
                      onClick={item.action}
                      className="w-full px-4 py-3 text-left hover:bg-gray-100 active:bg-gray-200 transition-colors flex items-center gap-3 touch-manipulation"
                      style={{
                        minHeight: '48px', // Touch-friendly size
                      }}
                    >
                      <span className="text-2xl">{item.icon}</span>
                      <span className="text-base font-medium text-gray-700">
                        {item.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Action Log */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">Action Log</h3>
          <div className="space-y-2">
            {actionLog.length === 0 ? (
              <p className="text-gray-500 italic">
                No actions yet. Try long-pressing a shape!
              </p>
            ) : (
              actionLog.map((log, index) => (
                <div
                  key={index}
                  className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded"
                >
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-3 text-blue-900">
            How to Use
          </h3>
          <ul className="space-y-2 text-blue-800">
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">1.</span>
              <span>
                <strong>Touch devices:</strong> Long-press (hold for 500ms) on
                any colored shape
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">2.</span>
              <span>
                <strong>Desktop:</strong> Click and hold the mouse button for
                500ms
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">3.</span>
              <span>
                A touch-friendly context menu will appear at your finger/cursor
                position
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">4.</span>
              <span>
                Tap/click any menu item to execute the action
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold mt-0.5">5.</span>
              <span>
                Moving more than 10px during the long-press will cancel it
              </span>
            </li>
          </ul>
        </div>

        {/* Technical Details */}
        <div className="mt-6 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-3 text-gray-700">
            Technical Details
          </h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>
              <strong>Delay:</strong> 500ms (industry standard for long-press)
            </li>
            <li>
              <strong>Move Threshold:</strong> 10px (cancels if finger moves
              beyond this)
            </li>
            <li>
              <strong>Menu Size:</strong> Touch-friendly (48px minimum height per
              item)
            </li>
            <li>
              <strong>Haptic Feedback:</strong> 50ms vibration on long-press
              (supported devices)
            </li>
            <li>
              <strong>Accessibility:</strong> Works with both touch and mouse
              input
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
