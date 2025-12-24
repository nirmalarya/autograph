'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import OptimizedImage from '../../components/OptimizedImage';
import Button from '../../components/Button';
import Input from '../../components/Input';

export default function SecuritySettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [showMfaSetup, setShowMfaSetup] = useState(false);
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [setupLoading, setSetupLoading] = useState(false);

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
      
      // Check if MFA is enabled (you could add an API call here to check actual status)
      // For now, we'll assume it's not enabled unless we get confirmation
      setMfaEnabled(false);
    } catch (err) {
      console.error('Failed to decode token:', err);
      router.push('/login');
      return;
    }

    setLoading(false);
  }, [router]);

  const handleStartMfaSetup = async () => {
    setError('');
    setSuccess('');
    setSetupLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8085/mfa/setup', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Failed to setup MFA. Please try again.');
        return;
      }

      setQrCode(data.qr_code);
      setSecret(data.secret);
      setShowMfaSetup(true);
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('MFA setup error:', err);
    } finally {
      setSetupLoading(false);
    }
  };

  const handleEnableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSetupLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('http://localhost:8085/mfa/enable', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          code: verificationCode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Invalid code. Please try again.');
        return;
      }

      setSuccess('MFA enabled successfully! You will need to use your authenticator app on your next login.');
      setMfaEnabled(true);
      setShowMfaSetup(false);
      setQrCode('');
      setSecret('');
      setVerificationCode('');
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('MFA enable error:', err);
    } finally {
      setSetupLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
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
              <span className="text-sm text-gray-600">Security Settings</span>
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

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Security Settings
          </h1>
          <p className="text-gray-600">
            Manage your account security and authentication methods
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

        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Two-Factor Authentication (2FA)
              </h2>
              <p className="text-gray-600">
                Add an extra layer of security to your account
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              mfaEnabled 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              {mfaEnabled ? 'Enabled' : 'Disabled'}
            </div>
          </div>

          {!showMfaSetup && !mfaEnabled && (
            <div>
              <p className="text-gray-700 mb-6">
                Two-factor authentication adds an extra layer of security to your account. 
                You'll need to enter a code from your authenticator app each time you log in.
              </p>
              <Button
                onClick={handleStartMfaSetup}
                disabled={setupLoading}
                variant="primary"
                size="lg"
                loading={setupLoading}
              >
                Enable Two-Factor Authentication
              </Button>
            </div>
          )}

          {showMfaSetup && (
            <div className="space-y-6">
              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Step 1: Scan QR Code
                </h3>
                <p className="text-gray-600 mb-4">
                  Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
                </p>
                {qrCode && (
                  <div className="flex justify-center mb-4">
                    <OptimizedImage 
                      src={`data:image/png;base64,${qrCode}`} 
                      alt="MFA QR Code" 
                      className="border border-gray-300 rounded-lg p-4 bg-white"
                      priority={true}
                    />
                  </div>
                )}
                {secret && (
                  <div className="bg-gray-50 p-4 rounded-md">
                    <p className="text-sm text-gray-700 mb-2">
                      Or enter this code manually:
                    </p>
                    <code className="text-sm font-mono bg-white px-3 py-2 rounded border border-gray-300 inline-block">
                      {secret}
                    </code>
                  </div>
                )}
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Step 2: Verify Code
                </h3>
                <form onSubmit={handleEnableMfa} className="space-y-4">
                  <Input
                    type="text"
                    id="verification_code"
                    name="verification_code"
                    label="Enter the 6-digit code from your app"
                    required
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="000000"
                    maxLength={6}
                    // @ts-ignore - pattern is a valid HTML attribute
                    pattern="[0-9]{6}"
                    autoComplete="off"
                    className="text-center text-2xl tracking-widest max-w-xs"
                  />

                  <div className="flex gap-4">
                    <Button
                      type="submit"
                      disabled={setupLoading || verificationCode.length !== 6}
                      variant="primary"
                      size="lg"
                      loading={setupLoading}
                    >
                      Verify and Enable
                    </Button>
                    <Button
                      type="button"
                      onClick={() => {
                        setShowMfaSetup(false);
                        setQrCode('');
                        setSecret('');
                        setVerificationCode('');
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
            </div>
          )}

          {mfaEnabled && (
            <div>
              <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
                <p className="text-sm text-green-800">
                  ✓ Two-factor authentication is enabled for your account. 
                  You'll need to enter a code from your authenticator app each time you log in.
                </p>
              </div>
              <p className="text-gray-700">
                To disable two-factor authentication, please contact support.
              </p>
            </div>
          )}
        </div>

        <div className="mt-8">
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
