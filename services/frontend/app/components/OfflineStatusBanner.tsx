'use client';

import { useOfflineStorage } from '@/hooks/useOfflineStorage';
import { useEffect, useState } from 'react';

export default function OfflineStatusBanner() {
  const { isOnline, isSyncing, pendingEdits, syncError, cachedDiagrams } = useOfflineStorage();
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    // Show banner if offline, syncing, or there's an error
    setShowBanner(!isOnline || isSyncing || !!syncError);
  }, [isOnline, isSyncing, syncError]);

  if (!showBanner) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50">
      {/* Offline Banner */}
      {!isOnline && (
        <div className="bg-amber-500 text-white px-4 py-2 text-center text-sm">
          <div className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
            </svg>
            <span className="font-medium">You&apos;re offline</span>
            <span className="text-amber-100">•</span>
            <span className="text-amber-100">
              {cachedDiagrams.length} diagram{cachedDiagrams.length !== 1 ? 's' : ''} available
            </span>
            {pendingEdits.length > 0 && (
              <>
                <span className="text-amber-100">•</span>
                <span className="text-amber-100">
                  {pendingEdits.length} pending change{pendingEdits.length !== 1 ? 's' : ''} will sync when online
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Syncing Banner */}
      {isOnline && isSyncing && (
        <div className="bg-blue-500 text-white px-4 py-2 text-center text-sm">
          <div className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span className="font-medium">Syncing changes...</span>
            <span className="text-blue-100">
              {pendingEdits.length} change{pendingEdits.length !== 1 ? 's' : ''} remaining
            </span>
          </div>
        </div>
      )}

      {/* Sync Error Banner */}
      {isOnline && syncError && !isSyncing && (
        <div className="bg-red-500 text-white px-4 py-2 text-center text-sm">
          <div className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="font-medium">Sync error:</span>
            <span className="text-red-100">{syncError}</span>
          </div>
        </div>
      )}
    </div>
  );
}
