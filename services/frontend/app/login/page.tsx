'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Button from '../components/Button';
import Input from '../components/Input';
import { API_ENDPOINTS } from '@/lib/api-config';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    remember_me: false,
  });
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaCode, setMfaCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Show success message if redirected from registration
    if (searchParams.get('registered') === 'true') {
      setSuccess('Account created successfully! Please log in.');
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.auth.login, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          remember_me: formData.remember_me,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Login failed. Please check your credentials.');
        return;
      }

      // Check if MFA is required
      if (data.mfa_required) {
        setMfaRequired(true);
        setSuccess(data.message || 'Please enter your MFA code from your authenticator app.');
        return;
      }

      // Store tokens
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      // Redirect to dashboard or home
      router.push('/dashboard');
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await fetch(API_ENDPOINTS.auth.mfa.verify, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          code: mfaCode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || 'Invalid MFA code. Please try again.');
        return;
      }

      // Store tokens
      if (data.access_token) {
        localStorage.setItem('access_token', data.access_token);
      }
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token);
      }

      // Redirect to dashboard
      router.push('/dashboard');
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('MFA verification error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setFormData({
      ...formData,
      [e.target.name]: value,
    });
  };

  return (
    <main id="main-content" role="main" aria-label="Login page" className="flex min-h-screen flex-col items-center justify-center px-4 py-6 sm:px-6 sm:py-8 md:p-8 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 sm:p-8">
          <header className="text-center mb-6 sm:mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {mfaRequired ? 'Two-Factor Authentication' : 'Welcome Back'}
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              {mfaRequired ? 'Enter your 6-digit code' : 'Sign in to AutoGraph'}
            </p>
          </header>

          {success && (
            <div role="status" aria-live="polite" className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
              <p className="text-sm text-green-800 dark:text-green-300">{success}</p>
            </div>
          )}

          {error && (
            <div role="alert" aria-live="assertive" className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          {!mfaRequired ? (
            <form onSubmit={handleSubmit} className="space-y-6" aria-label="Login form">
              <Input
                type="email"
                id="email"
                name="email"
                label="Email Address"
                required
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                fullWidth
              />

              <Input
                type="password"
                id="password"
                name="password"
                label="Password"
                required
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                fullWidth
              />

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="remember_me"
                  name="remember_me"
                  checked={formData.remember_me}
                  onChange={handleChange}
                  className="h-4 w-4 text-blue-600 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500"
                />
                <label
                  htmlFor="remember_me"
                  className="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                >
                  Remember me for 30 days
                </label>
              </div>

              <Button
                type="submit"
                disabled={loading}
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
              >
                Sign In
              </Button>
            </form>
          ) : (
            <form onSubmit={handleMfaSubmit} className="space-y-6" aria-label="Two-factor authentication form">
              <Input
                type="text"
                id="mfa_code"
                name="mfa_code"
                label="Authentication Code"
                required
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                placeholder="000000"
                maxLength={6}
                // @ts-ignore - pattern is a valid HTML attribute
                pattern="[0-9]{6}"
                autoComplete="off"
                autoFocus
                className="text-center text-2xl tracking-widest"
                helperText="Enter the 6-digit code from your authenticator app"
                fullWidth
              />

              <Button
                type="submit"
                disabled={loading || mfaCode.length !== 6}
                variant="primary"
                size="lg"
                fullWidth
                loading={loading}
              >
                Verify Code
              </Button>

              <Button
                type="button"
                onClick={() => {
                  setMfaRequired(false);
                  setMfaCode('');
                  setError('');
                  setSuccess('');
                }}
                variant="ghost"
                size="md"
                fullWidth
              >
                ← Back to login
              </Button>
            </form>
          )}

          {!mfaRequired && (
            <nav aria-label="Account navigation" className="mt-6 text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Don't have an account?{' '}
                <a
                  href="/register"
                  aria-label="Sign up for a new account"
                  className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
                >
                  Sign up
                </a>
              </p>
            </nav>
          )}
        </div>

        <nav aria-label="Back navigation" className="mt-4 text-center">
          <a
            href="/"
            aria-label="Go back to home page"
            className="text-sm text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          >
            ← Back to home
          </a>
        </nav>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </main>
    }>
      <LoginForm />
    </Suspense>
  );
}
