'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Button from '../components/Button';
import Input from '../components/Input';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    fullName: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate password confirmation
    if (formData.password !== formData.passwordConfirm) {
      setError('Passwords do not match');
      return;
    }

    // Validate password length (client-side check)
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (formData.password.length > 128) {
      setError('Password must not exceed 128 characters');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('http://localhost:8085/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          full_name: formData.fullName || undefined,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle validation errors
        if (response.status === 422 && data.detail) {
          if (Array.isArray(data.detail)) {
            setError(data.detail[0].msg || 'Validation error');
          } else {
            setError(data.detail);
          }
        } else if (data.detail) {
          setError(data.detail);
        } else {
          setError('Registration failed. Please try again.');
        }
        return;
      }

      // Success! Redirect to login
      router.push('/login?registered=true');
    } catch (err) {
      setError('Network error. Please check if the auth service is running.');
      console.error('Registration error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-6 sm:px-6 sm:py-8 md:p-8 bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 sm:p-8">
          <div className="text-center mb-6 sm:mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Create Account
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
              Sign up for AutoGraph
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
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
              type="text"
              id="fullName"
              name="fullName"
              label="Full Name (Optional)"
              value={formData.fullName}
              onChange={handleChange}
              maxLength={255}
              placeholder="John Doe"
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
              minLength={8}
              maxLength={128}
              placeholder="At least 8 characters"
              helperText="Must be 8-128 characters long"
              fullWidth
            />

            <Input
              type="password"
              id="passwordConfirm"
              name="passwordConfirm"
              label="Confirm Password"
              required
              value={formData.passwordConfirm}
              onChange={handleChange}
              minLength={8}
              maxLength={128}
              placeholder="Confirm your password"
              fullWidth
            />

            <Button
              type="submit"
              disabled={loading}
              variant="primary"
              size="lg"
              fullWidth
              loading={loading}
            >
              Create Account
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Already have an account?{' '}
              <a
                href="/login"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Sign in
              </a>
            </p>
          </div>
        </div>

        <div className="mt-4 text-center">
          <a
            href="/"
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            ← Back to home
          </a>
        </div>
      </div>
    </main>
  );
}
