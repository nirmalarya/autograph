'use client';

import React from 'react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
}: EmptyStateProps) {
  const defaultIcon = (
    <svg
      className="w-16 h-16 text-gray-400 dark:text-gray-600"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
      />
    </svg>
  );

  return (
    <div className="empty-state fade-in">
      <div className="empty-state-icon">{icon || defaultIcon}</div>
      <h3 className="empty-state-title">{title}</h3>
      {description && (
        <p className="empty-state-description">{description}</p>
      )}
      {(action || secondaryAction) && (
        <div className="flex gap-3">
          {action && (
            <button
              onClick={action.onClick}
              className="btn-primary"
            >
              {action.label}
            </button>
          )}
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="btn-outline"
            >
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Preset empty states for common scenarios
export function NoResultsEmptyState({ onClear }: { onClear?: () => void }) {
  return (
    <EmptyState
      icon={
        <svg
          className="w-16 h-16 text-gray-400 dark:text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      }
      title="No results found"
      description="Try adjusting your search or filter criteria to find what you're looking for."
      action={onClear ? { label: 'Clear filters', onClick: onClear } : undefined}
    />
  );
}

export function NoDiagramsEmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <EmptyState
      icon={
        <svg
          className="w-16 h-16 text-gray-400 dark:text-gray-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
      }
      title="No diagrams yet"
      description="Get started by creating your first diagram. Choose from canvas, note, or diagram-as-code."
      action={{ label: 'Create Diagram', onClick: onCreate }}
    />
  );
}

export function ErrorEmptyState({
  title = 'Something went wrong',
  description = 'We encountered an error loading this content. Please try again.',
  onRetry,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <EmptyState
      icon={
        <svg
          className="w-16 h-16 text-red-400 dark:text-red-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      }
      title={title}
      description={description}
      action={onRetry ? { label: 'Try Again', onClick: onRetry } : undefined}
    />
  );
}

export function LoadingEmptyState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="empty-state">
      <div className="spinner-lg text-blue-600 dark:text-blue-400 mb-4"></div>
      <p className="text-gray-600 dark:text-gray-400">{message}</p>
    </div>
  );
}
