'use client';

/**
 * Feature: Notification Preferences Settings Page
 * 
 * Provides a dedicated settings page for managing notification preferences.
 * Users can enable/disable notifications per type and test notifications.
 */

import { useNotifications } from '../../components/NotificationSystem';
import { Bell, Check, X } from 'lucide-react';
import Link from 'next/link';

export default function NotificationSettingsPage() {
  const { preferences, updatePreferences, addNotification } = useNotifications();

  const notificationTypes: { 
    key: keyof typeof preferences;
    label: string;
    description: string;
    icon: string;
  }[] = [
    { 
      key: 'comment', 
      label: 'Comments', 
      description: 'Receive notifications when someone comments on your diagrams',
      icon: '💬'
    },
    { 
      key: 'mention', 
      label: 'Mentions', 
      description: 'Get notified when someone mentions you with @ in comments or notes',
      icon: '@'
    },
    { 
      key: 'share', 
      label: 'Shares', 
      description: 'Know when a diagram is shared with you or your team',
      icon: '🔗'
    },
    { 
      key: 'collaboration', 
      label: 'Collaboration', 
      description: 'Updates when users join your diagram or make edits in real-time',
      icon: '👥'
    },
    { 
      key: 'export', 
      label: 'Exports', 
      description: 'Get notified when your export (PNG, SVG, PDF) is ready',
      icon: '📥'
    },
    { 
      key: 'version', 
      label: 'Version History', 
      description: 'Alerts when a new version of a diagram is created',
      icon: '🔄'
    },
    { 
      key: 'system', 
      label: 'System Updates', 
      description: 'Important system notifications, maintenance, and feature updates',
      icon: '⚙️'
    },
  ];

  const handleToggle = (key: keyof typeof preferences) => {
    updatePreferences({ [key]: !preferences[key] });
  };

  const handleTestNotification = (type: keyof typeof preferences) => {
    const messages = {
      comment: {
        title: 'New Comment',
        message: 'Alice commented on "System Architecture Diagram"',
      },
      mention: {
        title: 'You were mentioned',
        message: 'Bob mentioned you in "API Design Review"',
      },
      share: {
        title: 'Diagram Shared',
        message: 'Carol shared "Database ERD" with you',
      },
      collaboration: {
        title: 'User Joined',
        message: 'Dave is now editing "User Flow Diagram"',
      },
      export: {
        title: 'Export Ready',
        message: 'Your PNG export of "Architecture Diagram" is ready',
      },
      version: {
        title: 'New Version',
        message: 'Version 5 of "System Design" was created by Eve',
      },
      system: {
        title: 'System Update',
        message: 'AutoGraph has been updated to v3.1 with new features',
      },
    };

    const msg = messages[type];
    addNotification({
      type,
      title: msg.title,
      message: msg.message,
    });
  };

  const handleEnableAll = () => {
    updatePreferences({
      comment: true,
      mention: true,
      share: true,
      collaboration: true,
      export: true,
      version: true,
      system: true,
    });
  };

  const handleDisableAll = () => {
    updatePreferences({
      comment: false,
      mention: false,
      share: false,
      collaboration: false,
      export: false,
      version: false,
      system: false,
    });
  };

  const enabledCount = Object.values(preferences).filter(Boolean).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <Link
              href="/settings"
              className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Back to settings"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </Link>

            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Notification Settings
                </h1>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Manage how you receive notifications about activity in AutoGraph
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Card */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                Notification Status
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {enabledCount} of {notificationTypes.length} notification types enabled
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleEnableAll}
                className="px-4 py-2 text-sm font-medium text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                Enable All
              </button>
              <button
                onClick={handleDisableAll}
                className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                Disable All
              </button>
            </div>
          </div>

          {/* Progress bar */}
          <div className="relative w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${(enabledCount / notificationTypes.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Notification Types */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 divide-y divide-gray-200 dark:divide-gray-700">
          {notificationTypes.map((type) => (
            <div
              key={type.key}
              className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className="flex-shrink-0 text-3xl mt-1">{type.icon}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    {type.label}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {type.description}
                  </p>

                  {/* Test notification button */}
                  {preferences[type.key] && (
                    <button
                      onClick={() => handleTestNotification(type.key)}
                      className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                    >
                      Send test notification
                    </button>
                  )}
                </div>

                {/* Toggle Switch */}
                <div className="flex-shrink-0">
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={preferences[type.key]}
                      onChange={() => handleToggle(type.key)}
                      className="sr-only peer"
                      aria-label={`Toggle ${type.label} notifications`}
                    />
                    <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Info Box */}
        <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <div className="flex gap-3">
            <svg
              className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-1">
                About Notifications
              </h4>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Notifications appear in the notification center (bell icon in the header) and can
                also be sent as browser push notifications. You can view all your notifications
                and mark them as read from the notification center.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
