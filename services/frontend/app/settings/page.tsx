'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWelcomeTour } from '../components/WelcomeTour';
import { useInteractiveTutorial } from '../components/InteractiveTutorial';
import Button from '../components/Button';
import { Play, Shield, Bell, User, GraduationCap } from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ email?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const { restartTour, hasCompletedTour } = useWelcomeTour();
  const { restartTutorial, hasCompletedTutorial } = useInteractiveTutorial();
  const [tourCompleted, setTourCompleted] = useState(false);
  const [tutorialCompleted, setTutorialCompleted] = useState(false);

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

    setTourCompleted(hasCompletedTour());
    setTutorialCompleted(hasCompletedTutorial());
    setLoading(false);
  }, [router, hasCompletedTour, hasCompletedTutorial]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    router.push('/');
  };

  if (loading) {
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
                AutoGraph v3
              </a>
              <span className="text-gray-400">→</span>
              <span className="text-sm text-gray-600 dark:text-gray-400">Settings</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600 dark:text-gray-400">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition touch-target-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account preferences and application settings
          </p>
        </div>

        {/* Settings Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Onboarding & Help */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-4 mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <GraduationCap className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Onboarding & Help
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Get help with using AutoGraph v3
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Welcome Tour
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {tourCompleted ? 'Completed' : 'Not completed'}
                  </p>
                </div>
                <Button
                  onClick={restartTour}
                  variant="secondary"
                  size="sm"
                >
                  {tourCompleted ? 'Show Again' : 'Start Tour'}
                </Button>
              </div>
              
              <div className="flex items-center justify-between py-2 border-t border-gray-200 dark:border-gray-700 pt-3">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Interactive Tutorial
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {tutorialCompleted ? 'Completed' : 'Not completed'}
                  </p>
                </div>
                <Button
                  onClick={restartTutorial}
                  variant="secondary"
                  size="sm"
                >
                  {tutorialCompleted ? 'Restart' : 'Start Tutorial'}
                </Button>
              </div>
              
              <div className="border-t border-gray-200 dark:border-gray-700 pt-3">
                <a
                  href="/help"
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition"
                >
                  View Documentation →
                </a>
              </div>
            </div>
          </div>

          {/* Security */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-4 mb-4">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Shield className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Security
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Manage your account security
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <a
                href="/settings/security"
                className="block py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition"
              >
                Two-Factor Authentication →
              </a>
              <a
                href="/settings/security"
                className="block py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition"
              >
                Password & Login →
              </a>
            </div>
          </div>

          {/* Notifications */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-4 mb-4">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <Bell className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Notifications
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Control your notification preferences
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Coming soon: Customize email, push, and in-app notifications
              </p>
            </div>
          </div>

          {/* Profile */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
            <div className="flex items-start gap-4 mb-4">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <User className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Profile
                </h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Manage your profile information
                </p>
              </div>
            </div>
            
            <div className="space-y-3">
              <a
                href="/profile"
                className="block py-2 text-sm text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition"
              >
                Edit Profile →
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <a
            href="/dashboard"
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition"
          >
            ← Back to dashboard
          </a>
        </div>
      </div>
    </main>
  );
}
