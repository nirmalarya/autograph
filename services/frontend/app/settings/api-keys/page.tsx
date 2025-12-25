'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '../../components/Button';
import Input from '../../components/Input';
import { API_ENDPOINTS } from '@/lib/api-config';
import { Key, Copy, Trash2, AlertCircle, CheckCircle } from 'lucide-react';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  last_used_at: string | null;
  created_at: string;
}

interface ApiKeyCreated {
  id: string;
  name: string;
  api_key: string; // Full key - only shown once
  key_prefix: string;
  scopes: string[];
  expires_at: string | null;
  created_at: string;
}

export default function ApiKeysPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    // Decode JWT to get user info
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.sub || payload.email });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    // Load existing API keys
    loadApiKeys();
  }, [router]);

  const loadApiKeys = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.auth.apiKeys.list, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Failed to load API keys');
        return;
      }

      setApiKeys(data.api_keys || []);
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('Load API keys error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setCreating(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.auth.apiKeys.create, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: keyName,
          scopes: [], // Default scopes - same as user permissions
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Failed to create API key');
        return;
      }

      // Show the created key (only shown once!)
      setCreatedKey(data);
      setShowCreateForm(false);
      setKeyName('');

      // Reload the list
      await loadApiKeys();
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('Create API key error:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleRevokeKey = async (keyId: string, keyName: string) => {
    if (!confirm(`Are you sure you want to revoke "${keyName}"? This cannot be undone.`)) {
      return;
    }

    setError('');
    setSuccess('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(API_ENDPOINTS.auth.apiKeys.revoke(keyId), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        setError(data.detail || 'Failed to revoke API key');
        return;
      }

      setSuccess(`API key "${keyName}" revoked successfully`);
      await loadApiKeys();
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('Revoke API key error:', err);
    }
  };

  const handleCopyKey = async (key: string, keyId: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedKeyId(keyId);
      setTimeout(() => setCopiedKeyId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
      setError('Failed to copy to clipboard');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading && apiKeys.length === 0) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <a href="/dashboard" className="text-xl font-bold text-gray-900 dark:text-gray-100 hover:text-gray-700 dark:hover:text-gray-300 transition">
                AutoGraph
              </a>
              <span className="text-gray-400">→</span>
              <a href="/settings" className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition">
                Settings
              </a>
              <span className="text-gray-400">→</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">API Keys</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Key className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              API Keys
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Generate API keys for programmatic access to AutoGraph. API keys have the same permissions as your user account.
          </p>
        </div>

        {success && (
          <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
            <p className="text-sm text-green-800 dark:text-green-200">{success}</p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5" />
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Show newly created key - ONE TIME ONLY */}
        {createdKey && (
          <div className="mb-6 p-6 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-300 dark:border-blue-700 rounded-lg">
            <div className="flex items-start gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
                  API Key Created Successfully
                </h3>
                <p className="text-sm text-blue-800 dark:text-blue-200 mb-4">
                  <strong>Important:</strong> Copy your API key now. You won't be able to see it again!
                </p>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-md border border-blue-200 dark:border-blue-700">
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Your API Key:
                  </label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-sm font-mono bg-gray-100 dark:bg-gray-900 px-3 py-2 rounded border border-gray-300 dark:border-gray-700 select-all overflow-x-auto">
                      {createdKey.api_key}
                    </code>
                    <Button
                      onClick={() => handleCopyKey(createdKey.api_key, 'new')}
                      variant="secondary"
                      size="sm"
                    >
                      {copiedKeyId === 'new' ? '✓ Copied' : <><Copy className="w-4 h-4 mr-1" /> Copy</>}
                    </Button>
                  </div>
                </div>
                <div className="mt-4 text-sm text-blue-800 dark:text-blue-200">
                  <p className="font-medium mb-1">To use this API key:</p>
                  <code className="block bg-white dark:bg-gray-800 px-3 py-2 rounded border border-blue-200 dark:border-blue-700 overflow-x-auto">
                    Authorization: Bearer {createdKey.api_key}
                  </code>
                </div>
              </div>
              <button
                onClick={() => setCreatedKey(null)}
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-medium"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Create Key Form */}
        {!showCreateForm && (
          <div className="mb-6">
            <Button
              onClick={() => setShowCreateForm(true)}
              variant="primary"
              size="lg"
            >
              <Key className="w-4 h-4 mr-2" />
              Generate New API Key
            </Button>
          </div>
        )}

        {showCreateForm && (
          <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Create New API Key
            </h2>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <Input
                type="text"
                id="key_name"
                name="key_name"
                label="Key Name"
                required
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder="e.g., CI/CD Pipeline, Production Server, Mobile App"
                maxLength={255}
              />
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Choose a descriptive name to help you remember what this key is used for.
              </p>
              <div className="flex gap-4">
                <Button
                  type="submit"
                  disabled={creating || !keyName}
                  variant="primary"
                  size="lg"
                  loading={creating}
                >
                  Generate API Key
                </Button>
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setKeyName('');
                    setError('');
                  }}
                  variant="secondary"
                  size="lg"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* API Keys List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Your API Keys
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {apiKeys.length} {apiKeys.length === 1 ? 'key' : 'keys'} active
            </p>
          </div>

          {apiKeys.length === 0 ? (
            <div className="p-12 text-center">
              <Key className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-2">
                No API keys yet
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Generate your first API key to get started with programmatic access.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {apiKeys.map((key) => (
                <div key={key.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                          {key.name}
                        </h3>
                        <code className="text-xs font-mono bg-gray-100 dark:bg-gray-900 px-2 py-1 rounded text-gray-600 dark:text-gray-400">
                          {key.key_prefix}...
                        </code>
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                        <p>
                          <span className="font-medium">Created:</span> {formatDate(key.created_at)}
                        </p>
                        <p>
                          <span className="font-medium">Last used:</span>{' '}
                          {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                        </p>
                        {key.scopes && key.scopes.length > 0 && (
                          <p>
                            <span className="font-medium">Scopes:</span> {key.scopes.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                    <Button
                      onClick={() => handleRevokeKey(key.id, key.name)}
                      variant="secondary"
                      size="sm"
                      className="ml-4"
                    >
                      <Trash2 className="w-4 h-4 mr-1" />
                      Revoke
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8">
          <a
            href="/settings"
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition"
          >
            ← Back to settings
          </a>
        </div>
      </div>
    </main>
  );
}
