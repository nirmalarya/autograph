'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '../../components/Button';
import { API_BASE_URL } from '@/lib/api-config';

interface Session {
  token_id: string;
  full_token: string;
  device: string;
  browser: string;
  os: string;
  ip_address: string;
  created_at: string;
  last_activity: string;
  is_current: boolean;
}

export default function SessionsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [revoking, setRevoking] = useState<string | null>(null);

  const fetchSessions = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/sessions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch sessions');
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      setError('Failed to load sessions. Please try again.');
      console.error('Error fetching sessions:', err);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser({ email: payload.sub || payload.email });
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    fetchSessions().finally(() => setLoading(false));
  }, [router]);

  const handleRevokeSession = async (tokenId: string) => {
    setError('');
    setSuccess('');
    setRevoking(tokenId);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/auth/sessions/${tokenId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to revoke session');
      }

      setSuccess('Session revoked successfully');
      // Refresh sessions list
      await fetchSessions();
    } catch (err: any) {
      setError(err.message || 'Failed to revoke session');
      console.error('Error revoking session:', err);
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAllOthers = async () => {
    setError('');
    setSuccess('');
    setRevoking('all');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE_URL}/api/auth/sessions/all/others`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to revoke sessions');
      }

      const data = await response.json();
      setSuccess(`${data.revoked_count} session(s) revoked successfully`);
      // Refresh sessions list
      await fetchSessions();
    } catch (err: any) {
      setError(err.message || 'Failed to revoke sessions');
      console.error('Error revoking sessions:', err);
    } finally {
      setRevoking(null);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  const getRelativeTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now.getTime() - date.getTime();

      const minutes = Math.floor(diff / 60000);
      const hours = Math.floor(diff / 3600000);
      const days = Math.floor(diff / 86400000);

      if (minutes < 1) return 'Just now';
      if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
      if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
      return `${days} day${days !== 1 ? 's' : ''} ago`;
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-4">
              <a href="/dashboard" className="text-xl font-bold text-gray-900 hover:text-gray-700 transition">
                AutoGraph
              </a>
              <span className="text-gray-400">→</span>
              <span className="text-sm text-gray-600">Session Management</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Active Sessions
          </h1>
          <p className="text-gray-600">
            Manage your active sessions across devices. You can revoke any session that you don't recognize.
          </p>
        </div>

        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">{success}</p>
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="mb-6 flex justify-between items-center">
          <p className="text-sm text-gray-600">
            {sessions.length} active session{sessions.length !== 1 ? 's' : ''}
          </p>
          {sessions.length > 1 && (
            <Button
              onClick={handleRevokeAllOthers}
              disabled={revoking !== null}
              variant="secondary"
              size="sm"
              loading={revoking === 'all'}
            >
              Revoke All Other Sessions
            </Button>
          )}
        </div>

        <div className="space-y-4">
          {sessions.map((session) => (
            <div
              key={session.token_id}
              className={`bg-white rounded-lg shadow-sm p-6 border ${
                session.is_current
                  ? 'border-blue-300 bg-blue-50/30'
                  : 'border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="text-2xl">
                      {session.device === 'Mobile' ? '📱' :
                       session.device === 'Tablet' ? '📱' :
                       '💻'}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {session.browser} on {session.os}
                      </h3>
                      {session.is_current && (
                        <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full mt-1">
                          Current Session
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-500">Device Type:</span>
                      <span className="ml-2 text-gray-900 font-medium">{session.device}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">IP Address:</span>
                      <span className="ml-2 text-gray-900 font-mono">{session.ip_address}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Last Activity:</span>
                      <span className="ml-2 text-gray-900" title={formatDate(session.last_activity)}>
                        {getRelativeTime(session.last_activity)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Created:</span>
                      <span className="ml-2 text-gray-900" title={formatDate(session.created_at)}>
                        {getRelativeTime(session.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                {!session.is_current && (
                  <Button
                    onClick={() => handleRevokeSession(session.full_token)}
                    disabled={revoking !== null}
                    variant="danger"
                    size="sm"
                    loading={revoking === session.token_id}
                  >
                    Revoke
                  </Button>
                )}
              </div>
            </div>
          ))}

          {sessions.length === 0 && (
            <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
              <p className="text-gray-600">No active sessions found</p>
            </div>
          )}
        </div>

        <div className="mt-8 flex gap-4">
          <a
            href="/settings"
            className="text-sm text-gray-600 hover:text-gray-900 transition"
          >
            ← Back to settings
          </a>
          <a
            href="/dashboard"
            className="text-sm text-gray-600 hover:text-gray-900 transition"
          >
            ← Back to dashboard
          </a>
        </div>
      </div>
    </main>
  );
}
