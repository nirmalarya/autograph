'use client';

import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastProps {
  message: ToastMessage;
  onClose: (id: string) => void;
}

function Toast({ message, onClose }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    const duration = message.duration || 5000;
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [message.id]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(message.id);
    }, 300); // Match animation duration
  };

  const getIcon = () => {
    switch (message.type) {
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-5 h-5 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'info':
        return (
          <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const getColorClasses = () => {
    switch (message.type) {
      case 'success':
        return 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800';
    }
  };

  const getTitleColorClasses = () => {
    switch (message.type) {
      case 'success':
        return 'text-green-900 dark:text-green-200';
      case 'error':
        return 'text-red-900 dark:text-red-200';
      case 'warning':
        return 'text-yellow-900 dark:text-yellow-200';
      case 'info':
        return 'text-blue-900 dark:text-blue-200';
    }
  };

  const getMessageColorClasses = () => {
    switch (message.type) {
      case 'success':
        return 'text-green-700 dark:text-green-300';
      case 'error':
        return 'text-red-700 dark:text-red-300';
      case 'warning':
        return 'text-yellow-700 dark:text-yellow-300';
      case 'info':
        return 'text-blue-700 dark:text-blue-300';
    }
  };

  return (
    <div
      className={`
        flex items-start gap-3 p-4 rounded-lg border shadow-lg max-w-md w-full
        ${getColorClasses()}
        ${isExiting ? 'slide-out-right' : 'slide-in-right'}
        ${message.type === 'success' ? 'success-bounce' : ''}
        ${message.type === 'error' ? 'error-shake' : ''}
      `}
      role="alert"
      aria-live={message.type === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
    >
      <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-semibold ${getTitleColorClasses()}`}>
          {message.title}
        </p>
        {message.message && (
          <p className={`text-sm mt-1 ${getMessageColorClasses()}`}>
            {message.message}
          </p>
        )}
      </div>
      <button
        onClick={handleClose}
        className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
        aria-label="Close notification"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

interface ToastContainerProps {
  messages: ToastMessage[];
  onClose: (id: string) => void;
}

export function ToastContainer({ messages, onClose }: ToastContainerProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return createPortal(
    <div 
      className="fixed top-4 right-4 z-50 flex flex-col gap-3 pointer-events-none"
      aria-label="Notifications"
      role="region"
    >
      <div className="flex flex-col gap-3 pointer-events-auto">
        {messages.map((message) => (
          <Toast key={message.id} message={message} onClose={onClose} />
        ))}
      </div>
    </div>,
    document.body
  );
}

// Hook for using toasts
export function useToast() {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  const showToast = (
    type: ToastType,
    title: string,
    message?: string,
    duration?: number
  ) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const newMessage: ToastMessage = {
      id,
      type,
      title,
      message,
      duration,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const success = (title: string, message?: string, duration?: number) => {
    showToast('success', title, message, duration);
  };

  const error = (title: string, message?: string, duration?: number) => {
    showToast('error', title, message, duration);
  };

  const warning = (title: string, message?: string, duration?: number) => {
    showToast('warning', title, message, duration);
  };

  const info = (title: string, message?: string, duration?: number) => {
    showToast('info', title, message, duration);
  };

  const closeToast = (id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  };

  return {
    messages,
    success,
    error,
    warning,
    info,
    closeToast,
  };
}
