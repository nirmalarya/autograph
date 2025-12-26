/**
 * API Configuration
 * Centralizes all API endpoint configuration to use API Gateway
 */

// API Gateway base URL - all requests must go through this
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

// WebSocket URL for collaboration service
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8083';

/**
 * API Endpoints - all routed through API Gateway
 */
export const API_ENDPOINTS = {
  // Auth Service (via /api/auth)
  auth: {
    register: `${API_BASE_URL}/api/auth/register`,
    login: `${API_BASE_URL}/api/auth/login`,
    logout: `${API_BASE_URL}/api/auth/logout`,
    refresh: `${API_BASE_URL}/api/auth/refresh`,
    password: {
      change: `${API_BASE_URL}/api/auth/password/change`,
    },
    mfa: {
      setup: `${API_BASE_URL}/api/auth/mfa/setup`,
      verify: `${API_BASE_URL}/api/auth/mfa/verify`,
      disable: `${API_BASE_URL}/api/auth/mfa/disable`,
    },
    sessions: {
      list: `${API_BASE_URL}/api/auth/sessions`,
      revoke: (tokenId: string) => `${API_BASE_URL}/api/auth/sessions/${tokenId}`,
      revokeAllOthers: `${API_BASE_URL}/api/auth/sessions/all/others`,
    },
    apiKeys: {
      create: `${API_BASE_URL}/api/auth/api-keys`,
      list: `${API_BASE_URL}/api/auth/api-keys`,
      revoke: (keyId: string) => `${API_BASE_URL}/api/auth/api-keys/${keyId}`,
    },
  },

  // Diagram Service (via /api/diagrams)
  diagrams: {
    base: `${API_BASE_URL}/api/diagrams`,
    list: `${API_BASE_URL}/api/diagrams`,
    create: `${API_BASE_URL}/api/diagrams`,
    get: (id: string) => `${API_BASE_URL}/api/diagrams/${id}`,
    update: (id: string) => `${API_BASE_URL}/api/diagrams/${id}`,
    delete: (id: string) => `${API_BASE_URL}/api/diagrams/${id}`,
    recent: `${API_BASE_URL}/api/diagrams/recent`,
    starred: `${API_BASE_URL}/api/diagrams/starred`,
    sharedWithMe: `${API_BASE_URL}/api/diagrams/shared-with-me`,
    team: `${API_BASE_URL}/api/diagrams/team`,
    trash: `${API_BASE_URL}/api/diagrams/trash`,
    folders: {
      breadcrumbs: (folderId: string) => `${API_BASE_URL}/api/diagrams/folders/${folderId}/breadcrumbs`,
    },
    versions: {
      list: (diagramId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/versions`,
      compare: (diagramId: string, v1: string, v2: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/compare?v1=${v1}&v2=${v2}`,
      updateLabel: (diagramId: string, versionId: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/${versionId}/label`,
      updateDescription: (diagramId: string, versionId: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/${versionId}/description`,
      share: (diagramId: string, versionId: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/${versionId}/share`,
      restore: (diagramId: string, versionId: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/${versionId}/restore`,
      fork: (diagramId: string, versionId: string) =>
        `${API_BASE_URL}/api/diagrams/${diagramId}/versions/${versionId}/fork`,
    },
    versionShared: (token: string) => `${API_BASE_URL}/api/diagrams/version-shared/${token}`,
    comments: {
      list: (diagramId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/comments`,
      create: (diagramId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/comments`,
      update: (diagramId: string, commentId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/comments/${commentId}`,
      delete: (diagramId: string, commentId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/comments/${commentId}/delete`,
      resolve: (diagramId: string, commentId: string) => `${API_BASE_URL}/api/diagrams/${diagramId}/comments/${commentId}/resolve`,
    },
  },

  // AI Service (via /api/ai)
  ai: {
    generate: `${API_BASE_URL}/api/ai/generate`,
  },

  // Export Service (via /api/export)
  export: {
    png: (diagramId: string) => `${API_BASE_URL}/api/export/${diagramId}/png`,
    svg: (diagramId: string) => `${API_BASE_URL}/api/export/${diagramId}/svg`,
    pdf: (diagramId: string) => `${API_BASE_URL}/api/export/${diagramId}/pdf`,
  },

  // Collaboration Service (via /api/collaboration)
  collaboration: {
    ws: WS_BASE_URL, // WebSocket uses direct connection
  },
} as const;

/**
 * Helper function to build API URLs
 * @deprecated Use API_ENDPOINTS instead
 */
export function getApiUrl(service: string, path: string = ''): string {
  const base = `${API_BASE_URL}/api/${service}`;
  return path ? `${base}/${path}` : base;
}

/**
 * Check if API is configured correctly
 */
export function validateApiConfig(): boolean {
  if (!API_BASE_URL) {
    console.error('NEXT_PUBLIC_API_URL is not set in environment variables');
    return false;
  }

  // API Gateway should be on port 8080
  if (!API_BASE_URL.includes(':8080')) {
    console.warn(`API_BASE_URL should point to API Gateway on port 8080, got: ${API_BASE_URL}`);
  }

  return true;
}

// Validate on module load (development only)
if (process.env.NODE_ENV === 'development') {
  validateApiConfig();
}
