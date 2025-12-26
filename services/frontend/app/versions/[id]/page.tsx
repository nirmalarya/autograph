"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import OptimizedImage from "../../components/OptimizedImage";
import { API_ENDPOINTS } from "@/lib/api-config";

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
  searchParams: Promise<{ v1?: string; v2?: string; mode?: string; view?: string }>;
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
  const [pageView, setPageView] = useState<"timeline" | "compare">(
    (unwrappedSearchParams.view as "timeline" | "compare") || "timeline"
  );
  
  // Label editing state
  const [editingLabel, setEditingLabel] = useState<string | null>(null);
  const [labelValue, setLabelValue] = useState<string>("");
  const [savingLabel, setSavingLabel] = useState(false);
  
  // Description editing state
  const [editingDescription, setEditingDescription] = useState<string | null>(null);
  const [descriptionValue, setDescriptionValue] = useState<string>("");
  const [savingDescription, setSavingDescription] = useState(false);
  
  // Share state
  const [sharingVersion, setSharingVersion] = useState<string | null>(null);
  const [shareUrl, setShareUrl] = useState<string>("");
  const [showShareModal, setShowShareModal] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  // Restore state
  const [restoringVersion, setRestoringVersion] = useState<string | null>(null);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [versionToRestore, setVersionToRestore] = useState<Version | null>(null);
  
  // Search/filter state
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [authorFilter, setAuthorFilter] = useState<string>("");
  const [dateFromFilter, setDateFromFilter] = useState<string>("");
  const [dateToFilter, setDateToFilter] = useState<string>("");
  const [showFilters, setShowFilters] = useState(false);

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

        // Build query parameters
        const params = new URLSearchParams();
        if (searchQuery) params.append("search", searchQuery);
        if (authorFilter) params.append("author", authorFilter);
        if (dateFromFilter) params.append("date_from", dateFromFilter);
        if (dateToFilter) params.append("date_to", dateToFilter);

        const queryString = params.toString();
        const url = `${API_ENDPOINTS.diagrams.versions.list(diagramId)}${queryString ? `?${queryString}` : ""}`;

        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        });

        if (!response.ok) throw new Error("Failed to fetch versions");

        const data = await response.json();
        // Sort versions by version_number descending (newest first)
        const sortedVersions = (data.versions || []).sort((a: Version, b: Version) =>
          b.version_number - a.version_number
        );
        setVersions(sortedVersions);
      } catch (err) {
        console.error("Error fetching versions:", err);
        setError("Failed to load versions");
      }
    };

    fetchVersions();
  }, [diagramId, searchQuery, authorFilter, dateFromFilter, dateToFilter]);

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
          API_ENDPOINTS.diagrams.versions.compare(diagramId, selectedV1.toString(), selectedV2.toString()),
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
  
  const handleEditLabel = (versionId: string, currentLabel: string | undefined) => {
    setEditingLabel(versionId);
    setLabelValue(currentLabel || "");
  };
  
  const handleSaveLabel = async (versionId: string) => {
    setSavingLabel(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(
        API_ENDPOINTS.diagrams.versions.updateLabel(diagramId, versionId),
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
          body: JSON.stringify({ label: labelValue || null }),
        }
      );

      if (!response.ok) throw new Error("Failed to update label");

      // Refresh versions list and comparison
      const versionsResponse = await fetch(
        API_ENDPOINTS.diagrams.versions.list(diagramId),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        }
      );

      if (versionsResponse.ok) {
        const data = await versionsResponse.json();
        setVersions(data.versions || []);
      }

      // Also refresh comparison to update labels
      const comparisonResponse = await fetch(
        API_ENDPOINTS.diagrams.versions.compare(diagramId, selectedV1.toString(), selectedV2.toString()),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        }
      );
      
      if (comparisonResponse.ok) {
        const compData = await comparisonResponse.json();
        setComparison(compData);
      }
      
      setEditingLabel(null);
    } catch (err) {
      console.error("Error updating label:", err);
      alert("Failed to update label");
    } finally {
      setSavingLabel(false);
    }
  };
  
  const handleCancelEdit = () => {
    setEditingLabel(null);
    setLabelValue("");
  };
  
  const handleEditDescription = (versionId: string, currentDescription: string | undefined) => {
    setEditingDescription(versionId);
    setDescriptionValue(currentDescription || "");
  };
  
  const handleSaveDescription = async (versionId: string) => {
    setSavingDescription(true);
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setError("Not authenticated");
        return;
      }

      const response = await fetch(
        API_ENDPOINTS.diagrams.versions.updateDescription(diagramId, versionId),
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
          body: JSON.stringify({ description: descriptionValue || null }),
        }
      );

      if (!response.ok) throw new Error("Failed to update description");

      // Refresh versions list and comparison
      const versionsResponse = await fetch(
        API_ENDPOINTS.diagrams.versions.list(diagramId),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        }
      );

      if (versionsResponse.ok) {
        const data = await versionsResponse.json();
        setVersions(data.versions || []);
      }

      // Also refresh comparison to update descriptions
      const comparisonResponse = await fetch(
        API_ENDPOINTS.diagrams.versions.compare(diagramId, selectedV1.toString(), selectedV2.toString()),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": localStorage.getItem("user_id") || "",
          },
        }
      );
      
      if (comparisonResponse.ok) {
        const compData = await comparisonResponse.json();
        setComparison(compData);
      }
      
      setEditingDescription(null);
    } catch (err) {
      console.error("Error updating description:", err);
      alert("Failed to update description");
    } finally {
      setSavingDescription(false);
    }
  };
  
  const handleCancelDescriptionEdit = () => {
    setEditingDescription(null);
    setDescriptionValue("");
  };
  
  const handleClearFilters = () => {
    setSearchQuery("");
    setAuthorFilter("");
    setDateFromFilter("");
    setDateToFilter("");
  };
  
  const handleShareVersion = async (versionId: string, versionNumber: number) => {
    setSharingVersion(versionId);
    try {
      const token = localStorage.getItem("access_token");
      const userId = localStorage.getItem("user_id");
      
      const response = await fetch(
        API_ENDPOINTS.diagrams.versions.share(diagramId, versionId),
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "X-User-ID": userId || "",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({})
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        setShareUrl(data.share_url);
        setShowShareModal(true);
      } else {
        alert("Failed to create share link");
      }
    } catch (error) {
      console.error("Error creating share link:", error);
      alert("Failed to create share link");
    } finally {
      setSharingVersion(null);
    }
  };
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleViewChange = (view: "timeline" | "compare") => {
    setPageView(view);
    const params = new URLSearchParams();
    params.set("view", view);
    if (view === "compare") {
      params.set("v1", selectedV1.toString());
      params.set("v2", selectedV2.toString());
      params.set("mode", viewMode);
    }
    router.push(`/versions/${diagramId}?${params.toString()}`);
  };

  const handleRestoreClick = (version: Version) => {
    setVersionToRestore(version);
    setShowRestoreModal(true);
  };

  const handleRestoreConfirm = async () => {
    if (!versionToRestore) return;

    setRestoringVersion(versionToRestore.id);
    setShowRestoreModal(false);

    try {
      const token = localStorage.getItem("access_token");
      const userId = localStorage.getItem("user_id");

      if (!token || !userId) {
        alert("Not authenticated");
        return;
      }

      const response = await fetch(
        API_ENDPOINTS.diagrams.versions.restore(diagramId, versionToRestore.id),
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": userId,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to restore version");
      }

      const result = await response.json();

      // Show success message
      alert(
        `Successfully restored to version ${versionToRestore.version_number}!\n\n` +
        `A backup of the current state was saved as version ${result.backup_version}.`
      );

      // Refresh the versions list
      const versionsResponse = await fetch(
        API_ENDPOINTS.diagrams.versions.list(diagramId),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-User-ID": userId,
          },
        }
      );

      if (versionsResponse.ok) {
        const data = await versionsResponse.json();
        const sortedVersions = (data.versions || []).sort((a: Version, b: Version) =>
          b.version_number - a.version_number
        );
        setVersions(sortedVersions);
      }
    } catch (err: any) {
      console.error("Error restoring version:", err);
      alert(`Failed to restore version: ${err.message}`);
    } finally {
      setRestoringVersion(null);
      setVersionToRestore(null);
    }
  };

  const handleRestoreCancel = () => {
    setShowRestoreModal(false);
    setVersionToRestore(null);
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
              <div className="flex items-center gap-4">
                <h1 className="text-2xl font-bold">Version History</h1>
                {/* View Switcher */}
                <div className="flex border rounded">
                  <button
                    onClick={() => handleViewChange("timeline")}
                    className={`px-4 py-2 text-sm ${
                      pageView === "timeline"
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Timeline
                  </button>
                  <button
                    onClick={() => handleViewChange("compare")}
                    className={`px-4 py-2 text-sm ${
                      pageView === "compare"
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    Compare
                  </button>
                </div>
              </div>
            </div>

            {/* Search and Filters */}
            <div className="flex-1 mx-8">
              <div className="flex gap-2 items-center">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search versions by content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full border rounded px-3 py-2"
                  />
                </div>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`px-3 py-2 rounded border ${
                    showFilters ? "bg-blue-50 border-blue-500" : "border-gray-300"
                  }`}
                >
                  🔍 Filters
                </button>
                {(searchQuery || authorFilter || dateFromFilter || dateToFilter) && (
                  <button
                    onClick={handleClearFilters}
                    className="px-3 py-2 rounded border border-gray-300 hover:bg-gray-50"
                  >
                    Clear
                  </button>
                )}
              </div>
              
              {/* Advanced Filters */}
              {showFilters && (
                <div className="mt-2 p-4 border rounded bg-white shadow-sm">
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Author
                      </label>
                      <input
                        type="text"
                        placeholder="Search by author name..."
                        value={authorFilter}
                        onChange={(e) => setAuthorFilter(e.target.value)}
                        className="w-full border rounded px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        From Date
                      </label>
                      <input
                        type="date"
                        value={dateFromFilter}
                        onChange={(e) => setDateFromFilter(e.target.value)}
                        className="w-full border rounded px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        To Date
                      </label>
                      <input
                        type="date"
                        value={dateToFilter}
                        onChange={(e) => setDateToFilter(e.target.value)}
                        className="w-full border rounded px-3 py-2"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {versions.length} version(s) found
                  </p>
                </div>
              )}
            </div>

            {/* Version Selectors - Only show in compare mode */}
            {pageView === "compare" && (
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
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {pageView === "timeline" ? (
          /* Timeline View */
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold">Version Timeline</h2>
              <p className="text-sm text-gray-600 mt-1">
                {versions.length} version{versions.length !== 1 ? "s" : ""} • Newest first
              </p>
            </div>

            {/* Timeline List */}
            <div className="divide-y">
              {versions.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  No versions found
                </div>
              ) : (
                versions.map((version, index) => (
                  <div
                    key={version.id}
                    className="p-6 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex gap-6">
                      {/* Timeline Dot */}
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-4 h-4 rounded-full ${
                            index === 0
                              ? "bg-blue-600"
                              : "bg-gray-300"
                          }`}
                        />
                        {index < versions.length - 1 && (
                          <div className="w-0.5 bg-gray-200 flex-1 mt-2" style={{ minHeight: "60px" }} />
                        )}
                      </div>

                      {/* Version Content */}
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-3">
                              <h3 className="text-lg font-semibold">
                                Version {version.version_number}
                              </h3>
                              {version.label && (
                                <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                                  {version.label}
                                </span>
                              )}
                              {index === 0 && (
                                <span className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                                  Latest
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {new Date(version.created_at).toLocaleString()} by{" "}
                              {version.user.full_name}
                            </p>
                            {version.description && (
                              <p className="text-sm text-gray-700 mt-2 bg-gray-50 p-3 rounded">
                                {version.description}
                              </p>
                            )}
                          </div>

                          {/* Thumbnail */}
                          {version.thumbnail_url && (
                            <div className="ml-4">
                              <OptimizedImage
                                src={version.thumbnail_url}
                                alt={`Version ${version.version_number}`}
                                className="w-32 h-24 object-cover border rounded"
                              />
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2 mt-4">
                          <button
                            onClick={() => handleEditLabel(version.id, version.label)}
                            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded border border-blue-200"
                          >
                            {version.label ? "Edit Label" : "+ Add Label"}
                          </button>
                          <button
                            onClick={() => handleEditDescription(version.id, version.description)}
                            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded border border-blue-200"
                          >
                            {version.description ? "Edit Comment" : "+ Add Comment"}
                          </button>
                          <button
                            onClick={() => handleShareVersion(version.id, version.version_number)}
                            disabled={sharingVersion === version.id}
                            className="px-3 py-1 text-sm text-green-600 hover:bg-green-50 rounded border border-green-200 disabled:opacity-50"
                          >
                            {sharingVersion === version.id ? "Sharing..." : "Share"}
                          </button>
                          <button
                            onClick={() => {
                              setSelectedV1(version.version_number);
                              setSelectedV2(version.version_number > 1 ? version.version_number - 1 : 1);
                              handleViewChange("compare");
                            }}
                            className="px-3 py-1 text-sm text-gray-600 hover:bg-gray-100 rounded border border-gray-300"
                          >
                            Compare
                          </button>
                          {index !== 0 && (
                            <button
                              onClick={() => handleRestoreClick(version)}
                              disabled={restoringVersion === version.id}
                              className="px-3 py-1 text-sm text-purple-600 hover:bg-purple-50 rounded border border-purple-200 disabled:opacity-50 font-medium"
                            >
                              {restoringVersion === version.id ? "Restoring..." : "🔄 Restore"}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ) : comparison && (
          /* Comparison View */
          <div>
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
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">
                    Version {comparison.version1.version_number}
                  </h3>
                  {editingLabel === comparison.version1.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={labelValue}
                        onChange={(e) => setLabelValue(e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                        placeholder="Enter label..."
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveLabel(comparison.version1.id)}
                        disabled={savingLabel}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        {savingLabel ? "..." : "Save"}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      {comparison.version1.label && (
                        <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                          {comparison.version1.label}
                        </span>
                      )}
                      <button
                        onClick={() => handleEditLabel(comparison.version1.id, comparison.version1.label)}
                        className="text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
                        title="Edit label"
                      >
                        {comparison.version1.label ? "Edit" : "+ Add Label"}
                      </button>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  {new Date(comparison.version1.created_at).toLocaleString()}
                  {" by "}
                  {comparison.version1.user.full_name}
                </p>
                
                {/* Description/Comment */}
                <div className="mb-4">
                  {editingDescription === comparison.version1.id ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Version Comment
                      </label>
                      <textarea
                        value={descriptionValue}
                        onChange={(e) => setDescriptionValue(e.target.value)}
                        className="w-full border rounded px-3 py-2 text-sm"
                        placeholder="Add a note explaining this version..."
                        rows={3}
                        autoFocus
                      />
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleSaveDescription(comparison.version1.id)}
                          disabled={savingDescription}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          {savingDescription ? "Saving..." : "Save Comment"}
                        </button>
                        <button
                          onClick={handleCancelDescriptionEdit}
                          className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {comparison.version1.description ? (
                        <div className="bg-gray-50 rounded p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-xs text-gray-500 mb-1">Comment:</p>
                              <p className="text-sm text-gray-700">{comparison.version1.description}</p>
                            </div>
                            <button
                              onClick={() => handleEditDescription(comparison.version1.id, comparison.version1.description)}
                              className="text-xs text-blue-600 hover:text-blue-700 ml-2"
                              title="Edit comment"
                            >
                              Edit
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleEditDescription(comparison.version1.id, comparison.version1.description)}
                          className="text-sm text-blue-600 hover:text-blue-700"
                        >
                          + Add Comment
                        </button>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Thumbnail */}
                {comparison.version1.thumbnail_url && (
                  <OptimizedImage
                    src={comparison.version1.thumbnail_url}
                    alt={`Version ${comparison.version1.version_number}`}
                    className="w-full border rounded mb-4"
                  />
                )}
                
                {/* Share Button */}
                <button
                  onClick={() => handleShareVersion(comparison.version1.id, comparison.version1.version_number)}
                  disabled={sharingVersion === comparison.version1.id}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {sharingVersion === comparison.version1.id ? (
                    <>Creating link...</>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                      Share Version
                    </>
                  )}
                </button>
              </div>

              {/* Version 2 */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">
                    Version {comparison.version2.version_number}
                  </h3>
                  {editingLabel === comparison.version2.id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="text"
                        value={labelValue}
                        onChange={(e) => setLabelValue(e.target.value)}
                        className="border rounded px-2 py-1 text-sm"
                        placeholder="Enter label..."
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveLabel(comparison.version2.id)}
                        disabled={savingLabel}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                      >
                        {savingLabel ? "..." : "Save"}
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      {comparison.version2.label && (
                        <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                          {comparison.version2.label}
                        </span>
                      )}
                      <button
                        onClick={() => handleEditLabel(comparison.version2.id, comparison.version2.label)}
                        className="text-sm text-blue-600 hover:text-blue-700 px-2 py-1"
                        title="Edit label"
                      >
                        {comparison.version2.label ? "Edit" : "+ Add Label"}
                      </button>
                    </div>
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-4">
                  {new Date(comparison.version2.created_at).toLocaleString()}
                  {" by "}
                  {comparison.version2.user.full_name}
                </p>
                
                {/* Description/Comment */}
                <div className="mb-4">
                  {editingDescription === comparison.version2.id ? (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Version Comment
                      </label>
                      <textarea
                        value={descriptionValue}
                        onChange={(e) => setDescriptionValue(e.target.value)}
                        className="w-full border rounded px-3 py-2 text-sm"
                        placeholder="Add a note explaining this version..."
                        rows={3}
                        autoFocus
                      />
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleSaveDescription(comparison.version2.id)}
                          disabled={savingDescription}
                          className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          {savingDescription ? "Saving..." : "Save Comment"}
                        </button>
                        <button
                          onClick={handleCancelDescriptionEdit}
                          className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      {comparison.version2.description ? (
                        <div className="bg-gray-50 rounded p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-xs text-gray-500 mb-1">Comment:</p>
                              <p className="text-sm text-gray-700">{comparison.version2.description}</p>
                            </div>
                            <button
                              onClick={() => handleEditDescription(comparison.version2.id, comparison.version2.description)}
                              className="text-xs text-blue-600 hover:text-blue-700 ml-2"
                              title="Edit comment"
                            >
                              Edit
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => handleEditDescription(comparison.version2.id, comparison.version2.description)}
                          className="text-sm text-blue-600 hover:text-blue-700"
                        >
                          + Add Comment
                        </button>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Thumbnail */}
                {comparison.version2.thumbnail_url && (
                  <OptimizedImage
                    src={comparison.version2.thumbnail_url}
                    alt={`Version ${comparison.version2.version_number}`}
                    className="w-full border rounded mb-4"
                  />
                )}
                
                {/* Share Button */}
                <button
                  onClick={() => handleShareVersion(comparison.version2.id, comparison.version2.version_number)}
                  disabled={sharingVersion === comparison.version2.id}
                  className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {sharingVersion === comparison.version2.id ? (
                    <>Creating link...</>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                      Share Version
                    </>
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-4">Overlay View</h3>
              <div className="relative">
                {comparison.version1.thumbnail_url && (
                  <OptimizedImage
                    src={comparison.version1.thumbnail_url}
                    alt={`Version ${comparison.version1.version_number}`}
                    className="w-full border rounded opacity-50"
                  />
                )}
                {comparison.version2.thumbnail_url && (
                  <OptimizedImage
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
      
      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Share Version</h3>
            <p className="text-sm text-gray-600 mb-4">
              Anyone with this link can view this specific version (read-only)
            </p>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={shareUrl}
                readOnly
                className="flex-1 border rounded px-3 py-2 text-sm bg-gray-50"
              />
              <button
                onClick={copyToClipboard}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {copySuccess ? "Copied!" : "Copy"}
              </button>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => {
                  setShowShareModal(false);
                  setShareUrl("");
                  setCopySuccess(false);
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Restore Confirmation Modal */}
      {showRestoreModal && versionToRestore && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                <span className="text-2xl">🔄</span>
              </div>
              <h3 className="text-lg font-semibold">Restore Version</h3>
            </div>

            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                Are you sure you want to restore to <strong>Version {versionToRestore.version_number}</strong>?
              </p>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <div className="flex items-start gap-2">
                  <span className="text-yellow-600 mt-0.5">⚠️</span>
                  <div className="text-sm text-yellow-800">
                    <p className="font-medium mb-1">Important:</p>
                    <ul className="list-disc list-inside space-y-1">
                      <li>This will revert the diagram to the selected version</li>
                      <li>A backup of the current state will be created automatically</li>
                      <li>The backup will appear as a new version in the timeline</li>
                    </ul>
                  </div>
                </div>
              </div>

              {versionToRestore.label && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Label:</span> {versionToRestore.label}
                </p>
              )}
              {versionToRestore.description && (
                <p className="text-sm text-gray-600 mt-1">
                  <span className="font-medium">Description:</span> {versionToRestore.description}
                </p>
              )}
              <p className="text-sm text-gray-500 mt-2">
                Created: {new Date(versionToRestore.created_at).toLocaleString()} by {versionToRestore.user.full_name}
              </p>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={handleRestoreCancel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleRestoreConfirm}
                className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium"
              >
                Restore Version
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
