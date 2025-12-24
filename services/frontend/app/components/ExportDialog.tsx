'use client';

import { useState } from 'react';
import { X } from 'lucide-react';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  diagramId: string;
  canvasData: any;
  selectedShapes?: string[]; // IDs of selected shapes
}

type BackgroundType = 'transparent' | 'white' | 'custom';
type ExportFormat = 'png' | 'svg' | 'pdf' | 'json' | 'markdown' | 'html';
type Resolution = '1x' | '2x' | '3x' | '4x';
type Quality = 'low' | 'medium' | 'high' | 'ultra';
type ExportScope = 'full' | 'selection';

export default function ExportDialog({ isOpen, onClose, diagramId, canvasData, selectedShapes }: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>('png');
  const [backgroundType, setBackgroundType] = useState<BackgroundType>('white');
  const [customColor, setCustomColor] = useState('#f0f0f0');
  const [resolution, setResolution] = useState<Resolution>('2x');
  const [quality, setQuality] = useState<Quality>('high');
  const [exportScope, setExportScope] = useState<ExportScope>('full');
  const [exporting, setExporting] = useState(false);
  
  const hasSelection = selectedShapes && selectedShapes.length > 0;

  if (!isOpen) return null;

  const getBackgroundValue = (): string => {
    if (backgroundType === 'transparent') return 'transparent';
    if (backgroundType === 'white') return 'white';
    return customColor;
  };

  const getScaleValue = (): number => {
    const scaleMap: Record<Resolution, number> = {
      '1x': 1,
      '2x': 2,
      '3x': 3,
      '4x': 4,
    };
    return scaleMap[resolution];
  };

  const handleExport = async () => {
    try {
      setExporting(true);

      const exportRequest = {
        diagram_id: diagramId,
        canvas_data: canvasData || {},
        format,
        width: 1920,
        height: 1080,
        quality,
        background: getBackgroundValue(),
        scale: getScaleValue(),
        export_scope: exportScope,
        selected_shapes: exportScope === 'selection' ? selectedShapes : undefined,
      };

      const response = await fetch(`http://localhost:8097/export/${format}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(exportRequest),
      });

      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }

      // Get the filename from Content-Disposition header or generate one
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `diagram_${diagramId}.${format}`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?(.+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // Close dialog after successful export
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Export Diagram</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Format Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['png', 'svg', 'pdf', 'json', 'markdown', 'html'] as ExportFormat[]).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => setFormat(fmt)}
                  className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition ${
                    format === fmt
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {fmt.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Export Scope - Full Canvas or Selection Only */}
          {hasSelection && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Export Scope
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setExportScope('full')}
                  className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition ${
                    exportScope === 'full'
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold">Full Canvas</div>
                  <div className="text-xs text-gray-500 mt-1">Export entire diagram</div>
                </button>
                <button
                  onClick={() => setExportScope('selection')}
                  className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition ${
                    exportScope === 'selection'
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold">Selection Only</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {selectedShapes?.length || 0} shape{selectedShapes?.length !== 1 ? 's' : ''} selected
                  </div>
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {exportScope === 'selection' 
                  ? 'Export will be tightly cropped to selected shapes'
                  : 'Export will include the entire canvas'
                }
              </p>
            </div>
          )}

          {/* Background Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Background
            </label>
            <div className="space-y-3">
              {/* Transparent */}
              <label className="flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer hover:border-gray-300 transition">
                <input
                  type="radio"
                  name="background"
                  checked={backgroundType === 'transparent'}
                  onChange={() => setBackgroundType('transparent')}
                  className="w-4 h-4 text-blue-600"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Transparent</div>
                  <div className="text-sm text-gray-500">No background (PNG only)</div>
                </div>
                <div className="w-12 h-12 rounded border border-gray-300 bg-transparent" 
                     style={{ backgroundImage: 'linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%)', backgroundSize: '10px 10px', backgroundPosition: '0 0, 0 5px, 5px -5px, -5px 0px' }}>
                </div>
              </label>

              {/* White */}
              <label className="flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer hover:border-gray-300 transition">
                <input
                  type="radio"
                  name="background"
                  checked={backgroundType === 'white'}
                  onChange={() => setBackgroundType('white')}
                  className="w-4 h-4 text-blue-600"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">White</div>
                  <div className="text-sm text-gray-500">Clean white background</div>
                </div>
                <div className="w-12 h-12 rounded border border-gray-300 bg-white"></div>
              </label>

              {/* Custom Color */}
              <label className="flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer hover:border-gray-300 transition">
                <input
                  type="radio"
                  name="background"
                  checked={backgroundType === 'custom'}
                  onChange={() => setBackgroundType('custom')}
                  className="w-4 h-4 text-blue-600"
                />
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Custom Color</div>
                  <div className="text-sm text-gray-500">Choose any color</div>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={customColor}
                    onChange={(e) => {
                      setCustomColor(e.target.value);
                      setBackgroundType('custom');
                    }}
                    className="w-12 h-12 rounded border border-gray-300 cursor-pointer"
                  />
                  <input
                    type="text"
                    value={customColor}
                    onChange={(e) => {
                      setCustomColor(e.target.value);
                      setBackgroundType('custom');
                    }}
                    placeholder="#f0f0f0"
                    className="w-24 px-2 py-1 text-sm border border-gray-300 rounded"
                  />
                </div>
              </label>
            </div>
          </div>

          {/* Resolution (for PNG/raster formats) */}
          {(format === 'png') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Resolution
              </label>
              <div className="grid grid-cols-4 gap-3">
                {(['1x', '2x', '3x', '4x'] as Resolution[]).map((res) => (
                  <button
                    key={res}
                    onClick={() => setResolution(res)}
                    className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition ${
                      resolution === res
                        ? 'border-blue-600 bg-blue-50 text-blue-700'
                        : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {res}
                    <div className="text-xs text-gray-500 mt-1">
                      {res === '1x' && 'Low'}
                      {res === '2x' && 'Medium'}
                      {res === '3x' && 'High'}
                      {res === '4x' && 'Ultra'}
                    </div>
                  </button>
                ))}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                Higher resolution = better quality but larger file size
              </p>
            </div>
          )}

          {/* Quality */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Quality
            </label>
            <div className="grid grid-cols-4 gap-3">
              {(['low', 'medium', 'high', 'ultra'] as Quality[]).map((qual) => (
                <button
                  key={qual}
                  onClick={() => setQuality(qual)}
                  className={`px-4 py-3 text-sm font-medium rounded-lg border-2 transition capitalize ${
                    quality === qual
                      ? 'border-blue-600 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {qual}
                </button>
              ))}
            </div>
          </div>

          {/* Export Preview */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Export Settings</h3>
            <div className="space-y-1 text-sm text-gray-600">
              <div className="flex justify-between">
                <span>Format:</span>
                <span className="font-medium">{format.toUpperCase()}</span>
              </div>
              <div className="flex justify-between">
                <span>Scope:</span>
                <span className="font-medium">
                  {exportScope === 'full' ? 'Full Canvas' : `Selection (${selectedShapes?.length || 0} shapes)`}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Background:</span>
                <span className="font-medium">
                  {backgroundType === 'transparent' && 'Transparent'}
                  {backgroundType === 'white' && 'White'}
                  {backgroundType === 'custom' && customColor}
                </span>
              </div>
              {format === 'png' && (
                <div className="flex justify-between">
                  <span>Resolution:</span>
                  <span className="font-medium">{resolution}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span>Quality:</span>
                <span className="font-medium capitalize">{quality}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
            disabled={exporting}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="px-6 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {exporting ? 'Exporting...' : 'Export'}
          </button>
        </div>
      </div>
    </div>
  );
}
