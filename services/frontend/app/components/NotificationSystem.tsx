'use client';

/**
 * Feature: Comprehensive Notification System
 * 
 * This component provides a complete notification infrastructure including:
 * - Notification Center: View all notifications with read/unread status
 * - Notification Preferences: Enable/disable notifications per type
 * - Notification Badges: Unread count display
 * - Multiple notification types: comments, mentions, shares, collaboration, system
 * - Persistence: localStorage for notifications and preferences
 * - Real-time updates: Support for WebSocket integration
 * - Accessibility: Full keyboard navigation and screen reader support
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Bell, X, Settings, Check, CheckCheck, Trash2 } from 'lucide-react';

// Notification types
export type NotificationType = 
  | 'comment'      // Someone commented on your diagram
  | 'mention'      // Someone mentioned you
  | 'share'        // Diagram shared with you
  | 'collaboration' // Collaboration activity (user joined, etc.)
  | 'system'       // System notifications (maintenance, updates, etc.)
  | 'export'       // Export completed
  | 'version';     // New version created

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
  link?: string; // Optional link to navigate to
  metadata?: Record<string, any>; // Additional data
}

export interface NotificationPreferences {
  comment: boolean;
  mention: boolean;
  share: boolean;
  collaboration: boolean;
  system: boolean;
  export: boolean;
  version: boolean;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  preferences: NotificationPreferences;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  deleteNotification: (id: string) => void;
  clearAll: () => void;
  updatePreferences: (preferences: Partial<NotificationPreferences>) => void;
  isOpen: boolean;
  toggleOpen: () => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}

// Default preferences - all enabled
const defaultPreferences: NotificationPreferences = {
  comment: true,
  mention: true,
  share: true,
  collaboration: true,
  system: true,
  export: true,
  version: true,
};

export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [preferences, setPreferences] = useState<NotificationPreferences>(defaultPreferences);
  const [isOpen, setIsOpen] = useState(false);

  // Load notifications and preferences from localStorage
  useEffect(() => {
    const savedNotifications = localStorage.getItem('autograph_notifications');
    const savedPreferences = localStorage.getItem('autograph_notification_preferences');

    if (savedNotifications) {
      try {
        setNotifications(JSON.parse(savedNotifications));
      } catch (error) {
        console.error('Failed to parse notifications from localStorage:', error);
      }
    }

    if (savedPreferences) {
      try {
        setPreferences(JSON.parse(savedPreferences));
      } catch (error) {
        console.error('Failed to parse preferences from localStorage:', error);
      }
    }
  }, []);

  // Save notifications to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('autograph_notifications', JSON.stringify(notifications));
  }, [notifications]);

  // Save preferences to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('autograph_notification_preferences', JSON.stringify(preferences));
  }, [preferences]);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    // Check if notifications of this type are enabled
    if (!preferences[notification.type]) {
      return; // Don't add if disabled
    }

    const newNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      read: false,
    };

    setNotifications((prev) => [newNotification, ...prev]);
  }, [preferences]);

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((notif) =>
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.map((notif) => ({ ...notif, read: true }))
    );
  }, []);

  const deleteNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((notif) => notif.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const updatePreferences = useCallback((newPreferences: Partial<NotificationPreferences>) => {
    setPreferences((prev) => ({ ...prev, ...newPreferences }));
  }, []);

  const toggleOpen = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        preferences,
        addNotification,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        clearAll,
        updatePreferences,
        isOpen,
        toggleOpen,
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

// Notification Center Component
export function NotificationCenter() {
  const {
    notifications,
    unreadCount,
    isOpen,
    toggleOpen,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll,
  } = useNotifications();

  const [showPreferences, setShowPreferences] = useState(false);

  if (!isOpen && !showPreferences) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 dark:bg-black/40 z-40 backdrop-blur-sm"
        onClick={() => {
          toggleOpen();
          setShowPreferences(false);
        }}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className="fixed top-16 right-4 w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-50 max-h-[calc(100vh-5rem)] flex flex-col"
        role="dialog"
        aria-label="Notification center"
        aria-modal="true"
      >
        {showPreferences ? (
          <NotificationPreferencesPanel onClose={() => setShowPreferences(false)} />
        ) : (
          <>
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-gray-700 dark:text-gray-300" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Notifications
                </h2>
                {unreadCount > 0 && (
                  <span className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded-full">
                    {unreadCount}
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    aria-label="Mark all as read"
                    title="Mark all as read"
                  >
                    <CheckCheck className="w-5 h-5" />
                  </button>
                )}

                <button
                  onClick={() => setShowPreferences(true)}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  aria-label="Notification settings"
                  title="Notification settings"
                >
                  <Settings className="w-5 h-5" />
                </button>

                <button
                  onClick={toggleOpen}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  aria-label="Close"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Notifications list */}
            <div className="flex-1 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
                  <Bell className="w-12 h-12 text-gray-400 dark:text-gray-600 mb-3" />
                  <p className="text-gray-600 dark:text-gray-400 font-medium">
                    No notifications
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                    We'll notify you when something important happens
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {notifications.map((notification) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={markAsRead}
                      onDelete={deleteNotification}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            {notifications.length > 0 && (
              <div className="p-3 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={clearAll}
                  className="w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors font-medium"
                >
                  Clear all notifications
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}

// Individual notification item
interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
}

function NotificationItem({ notification, onMarkAsRead, onDelete }: NotificationItemProps) {
  const getIcon = () => {
    switch (notification.type) {
      case 'comment':
        return '💬';
      case 'mention':
        return '@';
      case 'share':
        return '🔗';
      case 'collaboration':
        return '👥';
      case 'system':
        return '⚙️';
      case 'export':
        return '📥';
      case 'version':
        return '🔄';
      default:
        return '📢';
    }
  };

  const formatTime = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  return (
    <div
      className={`
        p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer
        ${!notification.read ? 'bg-blue-50/50 dark:bg-blue-900/10' : ''}
      `}
      onClick={() => {
        if (!notification.read) {
          onMarkAsRead(notification.id);
        }
        if (notification.link) {
          window.location.href = notification.link;
        }
      }}
    >
      <div className="flex items-start gap-3">
        {/* Icon */}
        <div className="flex-shrink-0 text-2xl">{getIcon()}</div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              {notification.title}
            </p>
            {!notification.read && (
              <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1" aria-label="Unread" />
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {notification.message}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-500">
            {formatTime(notification.timestamp)}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {!notification.read && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onMarkAsRead(notification.id);
              }}
              className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
              aria-label="Mark as read"
              title="Mark as read"
            >
              <Check className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(notification.id);
            }}
            className="p-1.5 text-gray-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
            aria-label="Delete notification"
            title="Delete"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Notification Preferences Panel
function NotificationPreferencesPanel({ onClose }: { onClose: () => void }) {
  const { preferences, updatePreferences } = useNotifications();

  const notificationTypes: { key: keyof NotificationPreferences; label: string; description: string }[] = [
    { key: 'comment', label: 'Comments', description: 'When someone comments on your diagram' },
    { key: 'mention', label: 'Mentions', description: 'When someone mentions you with @' },
    { key: 'share', label: 'Shares', description: 'When a diagram is shared with you' },
    { key: 'collaboration', label: 'Collaboration', description: 'When users join or edit your diagrams' },
    { key: 'export', label: 'Exports', description: 'When your export is ready' },
    { key: 'version', label: 'Versions', description: 'When a new version is created' },
    { key: 'system', label: 'System', description: 'Important system updates and maintenance' },
  ];

  return (
    <>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Notification Preferences
        </h2>
        <button
          onClick={onClose}
          className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Preferences list */}
      <div className="flex-1 overflow-y-auto p-4">
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Choose which notifications you want to receive
        </p>

        <div className="space-y-4">
          {notificationTypes.map((type) => (
            <div
              key={type.key}
              className="flex items-start justify-between gap-4 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
            >
              <div className="flex-1 min-w-0">
                <label
                  htmlFor={`notif-${type.key}`}
                  className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-1 cursor-pointer"
                >
                  {type.label}
                </label>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {type.description}
                </p>
              </div>

              <label className="relative inline-flex items-center cursor-pointer flex-shrink-0">
                <input
                  id={`notif-${type.key}`}
                  type="checkbox"
                  checked={preferences[type.key]}
                  onChange={(e) => updatePreferences({ [type.key]: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={onClose}
          className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
        >
          Done
        </button>
      </div>
    </>
  );
}

// Notification Bell Icon with Badge
export function NotificationBellIcon() {
  const { unreadCount, toggleOpen } = useNotifications();

  return (
    <button
      onClick={toggleOpen}
      className="relative p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
      aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      title="Notifications"
    >
      <Bell className="w-6 h-6" />
      {unreadCount > 0 && (
        <span
          className="absolute -top-1 -right-1 flex items-center justify-center min-w-[20px] h-5 px-1 text-xs font-bold text-white bg-red-600 rounded-full"
          aria-label={`${unreadCount} unread notifications`}
        >
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  );
}
