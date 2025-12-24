"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface Version {
  id: string;
  version_number: number;
  description?: string;
  label?: string;
  thumbnail_url?: string;
  created_at: string;
  created_by: string;
  user: {
    id: string;
    full_name: string;
  };
  canvas_data?: any;
  note_content?: string;
}

interface Comparison {
  diagram_id: string;
  version1: Version;
  version2: Version;
  differences: {
    additions: any[];
    deletions: any[];
    modifications: any[];
    note_changed: boolean;
    summary: {
      total_changes: number;
      added_count: number;
      deleted_count: number;
      modified_count: number;
    };
  };
}

export default function VersionComparePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ v1?: string; v2?: string; mode?: string }>;
}) {
  const unwrappedParams = use(params);
  const unwrappedSearchParams = use(searchParams);
  const router = useRouter();
  
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedV1, setSelectedV1] = useState<number>(
    parseInt(unwrappedSearchParams.v1 || "1")
  );
  const [selectedV2, setSelectedV2] = useState<number>(
    parseInt(unwrappedSearchParams.v2 || "2")
  );
  const [viewMode, setViewMode] = useState<"side-by-side" | "overlay">(
    (unwrappedSearchParams.mode as "side-by-side" | "overlay") || "side-by-side"
  );

  const diagramId = unwrappedParams.id;

  // Fetch versions list
  useEffect(() => {
    const fetchVersions = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("Not authenticated");
          return;
        }

        const response = await fetch(
          `http://localhost:8082/${diagramId}/versions`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-User-ID": localStorage.getItem("user_id") || "",
            },
          }
        );

        if (!response.ok) throw new Error("Failed to fetch versions");

        const data = await response.json();
        setVersions(data.versions || []);
      } catch (err) {
        console.error("Error fetching versions:", err);
        setError("Failed to load versions");
      }
    };

    fetchVersions();
  }, [diagramId]);

  // Fetch comparison
  useEffect(() => {
    const fetchComparison = async () => {
      if (!selectedV1 || !selectedV2) return;

      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          setError("Not authenticated");
          setLoading(false);
          return;
        }

        const response = await fetch(
          `http://localhost:8082/${diagramId}/versions/compare?v1=${selectedV1}&v2=${selectedV2}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "X-User-ID": localStorage.getItem("user_id") || "",
            },
          }
        );

        if (!response.ok) throw new Error("Failed to compare versions");

        const data = await response.json();
        setComparison(data);
      } catch (err) {
        console.error("Error comparing versions:", err);
        setError("Failed to load comparison");
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [diagramId, selectedV1, selectedV2]);

  const handleVersionChange = (v1: number, v2: number) => {
    setSelectedV1(v1);
    setSelectedV2(v2);
    router.push(
      `/versions/${diagramId}?v1=${v1}&v2=${v2}&mode=${viewMode}`
    );
  };

  const handleModeChange = (mode: "side-by-side" | "overlay") => {
    setViewMode(mode);
    router.push(
      `/versions/${diagramId}?v1=${selectedV1}&v2=${selectedV2}&mode=${mode}`
    );
  };

  if (loading && !comparison) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading comparison...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md">
          <h2 className="text-xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700">{error}</p>
          <button
            onClick={() => router.back()}
            className="mt-4 px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
          >
            Go Back
          </button>
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
              <button
                onClick={() => router.back()}
                className="text-gray-600 hover:text-gray-900 mb-2"
              >
                ← Back
              </button>
              <h1 className="text-2xl font-bold">Version Comparison</h1>
            </div>

            {/* Version Selectors */}
            <div className="flex gap-4 items-center">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version 1
                </label>
                <select
                  value={selectedV1}
                  onChange={(e) =>
                    handleVersionChange(parseInt(e.target.value), selectedV2)
                  }
                  className="border rounded px-3 py-2"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      v{v.version_number}
                      {v.label ? ` - ${v.label}` : ""}
                    </option>
                  ))}
                </select>
              </div>

              <span className="text-gray-400 mt-6">vs</span>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Version 2
                </label>
                <select
                  value={selectedV2}
                  onChange={(e) =>
                    handleVersionChange(selectedV1, parseInt(e.target.value))
                  }
                  className="border rounded px-3 py-2"
                >
                  {versions.map((v) => (
                    <option key={v.id} value={v.version_number}>
                      v{v.version_number}
                      {v.label ? ` - ${v.label}` : ""}
                    </option>
                  ))}
                </select>
              </div>

              {/* View Mode Toggle */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  View Mode
                </label>
                <div className="flex border rounded">
                  <button
                    onClick={() => handleModeChange("side-by-side")}
                    className={`px-4 py-2 ${
                      viewMode === "side-by-side"
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Side-by-Side
                  </button>
                  <button
                    onClick={() => handleModeChange("overlay")}
                    className={`px-4 py-2 ${
                      viewMode === "overlay"
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Overlay
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      {comparison && (
        <div className="max-w-7xl mx-auto px-4 py-6">
          {/* Summary */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold mb-4">Summary</h2>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-gray-50 rounded">
                <div className="text-2xl font-bold text-gray-900">
                  {comparison.differences.summary.total_changes}
                </div>
                <div className="text-sm text-gray-600">Total Changes</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded">
                <div className="text-2xl font-bold text-green-600">
                  {comparison.differences.summary.added_count}
                </div>
                <div className="text-sm text-green-700">Added</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded">
                <div className="text-2xl font-bold text-red-600">
                  {comparison.differences.summary.deleted_count}
                </div>
                <div className="text-sm text-red-700">Deleted</div>
              </div>
              <div className="text-center p-4 bg-yellow-50 rounded">
                <div className="text-2xl font-bold text-yellow-600">
                  {comparison.differences.summary.modified_count}
                </div>
                <div className="text-sm text-yellow-700">Modified</div>
              </div>
            </div>
          </div>

          {/* Main Comparison View */}
          {viewMode === "side-by-side" ? (
            <div className="grid grid-cols-2 gap-6">
              {/* Version 1 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Version {comparison.version1.version_number}
                  {comparison.version1.label && ` - ${comparison.version1.label}`}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {new Date(comparison.version1.created_at).toLocaleString()}
                  {" by "}
                  {comparison.version1.user.full_name}
                </p>
                
                {/* Thumbnail */}
                {comparison.version1.thumbnail_url && (
                  <img
                    src={comparison.version1.thumbnail_url}
                    alt={`Version ${comparison.version1.version_number}`}
                    className="w-full border rounded mb-4"
                  />
                )}
              </div>

              {/* Version 2 */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Version {comparison.version2.version_number}
                  {comparison.version2.label && ` - ${comparison.version2.label}`}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {new Date(comparison.version2.created_at).toLocaleString()}
                  {" by "}
                  {comparison.version2.user.full_name}
                </p>
                
                {/* Thumbnail */}
                {comparison.version2.thumbnail_url && (
                  <img
                    src={comparison.version2.thumbnail_url}
                    alt={`Version ${comparison.version2.version_number}`}
                    className="w-full border rounded mb-4"
                  />
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Overlay View</h3>
              <div className="relative">
                {comparison.version1.thumbnail_url && (
                  <img
                    src={comparison.version1.thumbnail_url}
                    alt={`Version ${comparison.version1.version_number}`}
                    className="w-full border rounded opacity-50"
                  />
                )}
                {comparison.version2.thumbnail_url && (
                  <img
                    src={comparison.version2.thumbnail_url}
                    alt={`Version ${comparison.version2.version_number}`}
                    className="w-full border rounded absolute top-0 left-0 opacity-50"
                  />
                )}
              </div>
            </div>
          )}

          {/* Detailed Changes */}
          <div className="mt-6 space-y-4">
            {/* Additions */}
            {comparison.differences.additions.length > 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-green-800 mb-4">
                  ✅ Added Elements ({comparison.differences.additions.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {comparison.differences.additions.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-4 rounded border border-green-300"
                    >
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(item, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deletions */}
            {comparison.differences.deletions.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-red-800 mb-4">
                  ❌ Deleted Elements ({comparison.differences.deletions.length})
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {comparison.differences.deletions.map((item, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-4 rounded border border-red-300 line-through opacity-75"
                    >
                      <pre className="text-xs overflow-auto">
                        {JSON.stringify(item, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Modifications */}
            {comparison.differences.modifications.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-yellow-800 mb-4">
                  ⚠️ Modified Elements ({comparison.differences.modifications.length})
                </h3>
                <div className="space-y-4">
                  {comparison.differences.modifications.map((mod, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-4 rounded border border-yellow-300"
                    >
                      <div className="font-medium text-yellow-900 mb-2">
                        Element ID: {mod.id}
                      </div>
                      <div className="text-sm text-yellow-700 mb-2">
                        Changes: {mod.changes.join(", ")}
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">
                            Before:
                          </div>
                          <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                            {JSON.stringify(mod.before, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <div className="text-xs font-medium text-gray-700 mb-1">
                            After:
                          </div>
                          <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded">
                            {JSON.stringify(mod.after, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Changes */}
            {comparison.differences.summary.total_changes === 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-gray-600">
                  No differences found between these versions.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
