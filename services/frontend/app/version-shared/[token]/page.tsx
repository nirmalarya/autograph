"use client";

import { use, useEffect, useState } from "react";
import { API_ENDPOINTS } from "@/lib/api-config";

interface SharedVersion {
  id: string;
  title: string;
  type: string;
  version_number: number;
  version_label?: string;
  version_description?: string;
  canvas_data?: any;
  note_content?: string;
  created_at: string;
  permission: string;
  is_read_only: boolean;
}

export default function SharedVersionPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const unwrappedParams = use(params);
  const [version, setVersion] = useState<SharedVersion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const token = unwrappedParams.token;

  useEffect(() => {
    const fetchSharedVersion = async () => {
      try {
        const response = await fetch(
          API_ENDPOINTS.diagrams.versionShared(token)
        );

        if (!response.ok) {
          throw new Error("Failed to load shared version");
        }

        const data = await response.json();
        setVersion(data);
      } catch (err: any) {
        setError(err.message || "Failed to load shared version");
      } finally {
        setLoading(false);
      }
    };

    fetchSharedVersion();
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading shared version...</p>
        </div>
      </div>
    );
  }

  if (error || !version) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md text-center">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Invalid Share Link
          </h2>
          <p className="text-gray-600 mb-4">
            {error || "This shared version link is invalid or has expired."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {version.title}
              </h1>
              <div className="flex items-center gap-3 mt-2">
                <span className="px-3 py-1 bg-purple-100 text-purple-800 text-sm rounded-full">
                  Version {version.version_number}
                </span>
                {version.version_label && (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                    {version.version_label}
                  </span>
                )}
                <span className="px-3 py-1 bg-gray-100 text-gray-600 text-sm rounded-full">
                  Read-Only
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">
                Created: {new Date(version.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          {/* Description */}
          {version.version_description && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm font-medium text-blue-900 mb-1">
                Version Notes:
              </p>
              <p className="text-sm text-blue-800">{version.version_description}</p>
            </div>
          )}

          {/* Canvas Data */}
          {version.canvas_data && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Canvas Content</h3>
              <div className="bg-gray-50 rounded p-4 border">
                <pre className="text-xs overflow-auto max-h-96">
                  {JSON.stringify(version.canvas_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Note Content */}
          {version.note_content && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Notes</h3>
              <div className="prose max-w-none bg-gray-50 rounded p-4 border">
                <div
                  dangerouslySetInnerHTML={{ __html: version.note_content }}
                />
              </div>
            </div>
          )}

          {/* Info Box */}
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-yellow-600 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="text-sm font-medium text-yellow-900">
                  This is a read-only snapshot
                </p>
                <p className="text-sm text-yellow-700 mt-1">
                  You are viewing version {version.version_number} of this
                  diagram. This is a historical snapshot and cannot be edited.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
