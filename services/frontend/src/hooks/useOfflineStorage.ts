/**
 * React hook for offline diagram storage and synchronization
 */

import { useState, useEffect, useCallback } from 'react';
import { offlineDB, CachedDiagram, PendingEdit } from '@/lib/db';

export interface UseOfflineStorageReturn {
  // State
  isOnline: boolean;
  isSyncing: boolean;
  cachedDiagrams: CachedDiagram[];
  pendingEdits: PendingEdit[];
  syncError: string | null;
  
  // Methods
  cacheDiagram: (diagram: CachedDiagram) => Promise<void>;
  getCachedDiagram: (id: string) => Promise<CachedDiagram | null>;
  removeCachedDiagram: (id: string) => Promise<void>;
  addPendingEdit: (edit: Omit<PendingEdit, 'id' | 'timestamp' | 'retry_count'>) => Promise<void>;
  syncPendingEdits: () => Promise<void>;
  clearCache: () => Promise<void>;
  refreshCache: () => Promise<void>;
}

export function useOfflineStorage(): UseOfflineStorageReturn {
  const [isOnline, setIsOnline] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [cachedDiagrams, setCachedDiagrams] = useState<CachedDiagram[]>([]);
  const [pendingEdits, setPendingEdits] = useState<PendingEdit[]>([]);
  const [syncError, setSyncError] = useState<string | null>(null);

  // Initialize IndexedDB
  useEffect(() => {
    offlineDB.init().catch(console.error);
  }, []);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Auto-sync when coming back online
      syncPendingEdits();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    // Set initial state
    setIsOnline(navigator.onLine);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load cached diagrams on mount
  useEffect(() => {
    refreshCache();
  }, []);

  /**
   * Refresh the cached diagrams list
   */
  const refreshCache = useCallback(async () => {
    try {
      const [diagrams, edits] = await Promise.all([
        offlineDB.getAllCachedDiagrams(),
        offlineDB.getPendingEdits(),
      ]);
      setCachedDiagrams(diagrams);
      setPendingEdits(edits);
    } catch (error) {
      console.error('Failed to refresh cache:', error);
    }
  }, []);

  /**
   * Cache a diagram for offline access
   */
  const cacheDiagram = useCallback(async (diagram: CachedDiagram) => {
    try {
      await offlineDB.cacheDiagram(diagram);
      await refreshCache();
    } catch (error) {
      console.error('Failed to cache diagram:', error);
      throw error;
    }
  }, [refreshCache]);

  /**
   * Get a cached diagram by ID
   */
  const getCachedDiagram = useCallback(async (id: string): Promise<CachedDiagram | null> => {
    try {
      return await offlineDB.getCachedDiagram(id);
    } catch (error) {
      console.error('Failed to get cached diagram:', error);
      return null;
    }
  }, []);

  /**
   * Remove a cached diagram
   */
  const removeCachedDiagram = useCallback(async (id: string) => {
    try {
      await offlineDB.removeCachedDiagram(id);
      await refreshCache();
    } catch (error) {
      console.error('Failed to remove cached diagram:', error);
      throw error;
    }
  }, [refreshCache]);

  /**
   * Add a pending edit to the queue
   */
  const addPendingEdit = useCallback(async (edit: Omit<PendingEdit, 'id' | 'timestamp' | 'retry_count'>) => {
    try {
      await offlineDB.addPendingEdit(edit);
      await refreshCache();
    } catch (error) {
      console.error('Failed to add pending edit:', error);
      throw error;
    }
  }, [refreshCache]);

  /**
   * Sync all pending edits to the server
   */
  const syncPendingEdits = useCallback(async () => {
    if (!isOnline || isSyncing) return;

    setIsSyncing(true);
    setSyncError(null);

    try {
      const edits = await offlineDB.getPendingEdits();
      
      if (edits.length === 0) {
        setIsSyncing(false);
        return;
      }

      console.log(`Syncing ${edits.length} pending edits...`);

      // Sort edits by timestamp (oldest first)
      const sortedEdits = edits.sort((a, b) => a.timestamp - b.timestamp);

      let successCount = 0;
      let failCount = 0;

      for (const edit of sortedEdits) {
        try {
          // Determine API endpoint based on edit type
          let endpoint = '';
          let method = '';

          switch (edit.type) {
            case 'create':
              endpoint = '/api/diagrams';
              method = 'POST';
              break;
            case 'update':
              endpoint = `/api/diagrams/${edit.diagram_id}`;
              method = 'PUT';
              break;
            case 'delete':
              endpoint = `/api/diagrams/${edit.diagram_id}`;
              method = 'DELETE';
              break;
          }

          // Get auth token from localStorage
          const token = localStorage.getItem('token');
          if (!token) {
            throw new Error('No authentication token found');
          }

          // Send the edit to the server
          const response = await fetch(`http://localhost:8080${endpoint}`, {
            method,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: edit.type !== 'delete' ? JSON.stringify(edit.data) : undefined,
          });

          if (response.ok) {
            // Success - remove from pending edits
            await offlineDB.removePendingEdit(edit.id);
            successCount++;
          } else if (response.status === 409) {
            // Conflict - handle conflict resolution
            console.warn(`Conflict detected for edit ${edit.id}`);
            
            // For now, server wins - remove the pending edit
            // In a production app, you might want to show a conflict resolution UI
            await offlineDB.removePendingEdit(edit.id);
            failCount++;
          } else if (response.status >= 400 && response.status < 500) {
            // Client error - remove invalid edit
            console.error(`Client error for edit ${edit.id}:`, response.status);
            await offlineDB.removePendingEdit(edit.id);
            failCount++;
          } else {
            // Server error - increment retry count
            const newRetryCount = edit.retry_count + 1;
            
            if (newRetryCount >= 3) {
              // Max retries reached - remove edit
              console.error(`Max retries reached for edit ${edit.id}`);
              await offlineDB.removePendingEdit(edit.id);
              failCount++;
            } else {
              // Increment retry count
              await offlineDB.updatePendingEditRetryCount(edit.id, newRetryCount);
              failCount++;
            }
          }
        } catch (error) {
          console.error(`Failed to sync edit ${edit.id}:`, error);
          
          // Increment retry count
          const newRetryCount = edit.retry_count + 1;
          
          if (newRetryCount >= 3) {
            // Max retries reached - remove edit
            await offlineDB.removePendingEdit(edit.id);
          } else {
            await offlineDB.updatePendingEditRetryCount(edit.id, newRetryCount);
          }
          
          failCount++;
        }
      }

      console.log(`Sync complete: ${successCount} succeeded, ${failCount} failed`);

      if (failCount > 0) {
        setSyncError(`${failCount} edit(s) failed to sync`);
      }

      // Refresh cache
      await refreshCache();
    } catch (error) {
      console.error('Failed to sync pending edits:', error);
      setSyncError('Failed to sync edits');
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing, refreshCache]);

  /**
   * Clear all cached data
   */
  const clearCache = useCallback(async () => {
    try {
      await Promise.all([
        offlineDB.clearCachedDiagrams(),
        offlineDB.clearPendingEdits(),
      ]);
      await refreshCache();
    } catch (error) {
      console.error('Failed to clear cache:', error);
      throw error;
    }
  }, [refreshCache]);

  return {
    isOnline,
    isSyncing,
    cachedDiagrams,
    pendingEdits,
    syncError,
    cacheDiagram,
    getCachedDiagram,
    removeCachedDiagram,
    addPendingEdit,
    syncPendingEdits,
    clearCache,
    refreshCache,
  };
}
