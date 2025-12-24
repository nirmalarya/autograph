/**
 * IndexedDB wrapper for offline diagram storage
 * Provides a simple API for storing and retrieving diagrams locally
 */

const DB_NAME = 'autograph-offline';
const DB_VERSION = 1;
const DIAGRAMS_STORE = 'diagrams';
const EDITS_STORE = 'pending-edits';

export interface CachedDiagram {
  id: string;
  title: string;
  type: 'canvas' | 'note' | 'mixed';
  canvas_data?: any;
  note_content?: string;
  thumbnail_url?: string;
  updated_at: string;
  cached_at: number;
}

export interface PendingEdit {
  id: string;
  diagram_id: string;
  type: 'update' | 'create' | 'delete';
  data: any;
  timestamp: number;
  retry_count: number;
}

class OfflineDB {
  private db: IDBDatabase | null = null;
  private initPromise: Promise<void> | null = null;

  /**
   * Initialize the IndexedDB database
   */
  async init(): Promise<void> {
    if (this.db) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = new Promise((resolve, reject) => {
      if (typeof window === 'undefined' || !('indexedDB' in window)) {
        reject(new Error('IndexedDB not available'));
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        reject(new Error('Failed to open IndexedDB'));
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create diagrams store
        if (!db.objectStoreNames.contains(DIAGRAMS_STORE)) {
          const diagramStore = db.createObjectStore(DIAGRAMS_STORE, { keyPath: 'id' });
          diagramStore.createIndex('cached_at', 'cached_at', { unique: false });
          diagramStore.createIndex('type', 'type', { unique: false });
        }

        // Create pending edits store
        if (!db.objectStoreNames.contains(EDITS_STORE)) {
          const editsStore = db.createObjectStore(EDITS_STORE, { keyPath: 'id' });
          editsStore.createIndex('diagram_id', 'diagram_id', { unique: false });
          editsStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });

    return this.initPromise;
  }

  /**
   * Cache a diagram for offline access
   */
  async cacheDiagram(diagram: CachedDiagram): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([DIAGRAMS_STORE], 'readwrite');
      const store = transaction.objectStore(DIAGRAMS_STORE);
      
      const diagramWithTimestamp = {
        ...diagram,
        cached_at: Date.now(),
      };

      const request = store.put(diagramWithTimestamp);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to cache diagram'));
    });
  }

  /**
   * Get a cached diagram by ID
   */
  async getCachedDiagram(id: string): Promise<CachedDiagram | null> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([DIAGRAMS_STORE], 'readonly');
      const store = transaction.objectStore(DIAGRAMS_STORE);
      const request = store.get(id);

      request.onsuccess = () => {
        resolve(request.result || null);
      };
      request.onerror = () => reject(new Error('Failed to get cached diagram'));
    });
  }

  /**
   * Get all cached diagrams
   */
  async getAllCachedDiagrams(): Promise<CachedDiagram[]> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([DIAGRAMS_STORE], 'readonly');
      const store = transaction.objectStore(DIAGRAMS_STORE);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result || []);
      };
      request.onerror = () => reject(new Error('Failed to get cached diagrams'));
    });
  }

  /**
   * Remove a cached diagram
   */
  async removeCachedDiagram(id: string): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([DIAGRAMS_STORE], 'readwrite');
      const store = transaction.objectStore(DIAGRAMS_STORE);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove cached diagram'));
    });
  }

  /**
   * Clear all cached diagrams
   */
  async clearCachedDiagrams(): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([DIAGRAMS_STORE], 'readwrite');
      const store = transaction.objectStore(DIAGRAMS_STORE);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to clear cached diagrams'));
    });
  }

  /**
   * Add a pending edit to the queue
   */
  async addPendingEdit(edit: Omit<PendingEdit, 'id' | 'timestamp' | 'retry_count'>): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readwrite');
      const store = transaction.objectStore(EDITS_STORE);
      
      const pendingEdit: PendingEdit = {
        ...edit,
        id: `${edit.diagram_id}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        retry_count: 0,
      };

      const request = store.put(pendingEdit);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to add pending edit'));
    });
  }

  /**
   * Get all pending edits
   */
  async getPendingEdits(): Promise<PendingEdit[]> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readonly');
      const store = transaction.objectStore(EDITS_STORE);
      const request = store.getAll();

      request.onsuccess = () => {
        resolve(request.result || []);
      };
      request.onerror = () => reject(new Error('Failed to get pending edits'));
    });
  }

  /**
   * Get pending edits for a specific diagram
   */
  async getPendingEditsForDiagram(diagramId: string): Promise<PendingEdit[]> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readonly');
      const store = transaction.objectStore(EDITS_STORE);
      const index = store.index('diagram_id');
      const request = index.getAll(diagramId);

      request.onsuccess = () => {
        resolve(request.result || []);
      };
      request.onerror = () => reject(new Error('Failed to get pending edits for diagram'));
    });
  }

  /**
   * Remove a pending edit
   */
  async removePendingEdit(id: string): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readwrite');
      const store = transaction.objectStore(EDITS_STORE);
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to remove pending edit'));
    });
  }

  /**
   * Update retry count for a pending edit
   */
  async updatePendingEditRetryCount(id: string, retryCount: number): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readwrite');
      const store = transaction.objectStore(EDITS_STORE);
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const edit = getRequest.result;
        if (!edit) {
          reject(new Error('Pending edit not found'));
          return;
        }

        edit.retry_count = retryCount;
        const putRequest = store.put(edit);

        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(new Error('Failed to update retry count'));
      };

      getRequest.onerror = () => reject(new Error('Failed to get pending edit'));
    });
  }

  /**
   * Clear all pending edits
   */
  async clearPendingEdits(): Promise<void> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([EDITS_STORE], 'readwrite');
      const store = transaction.objectStore(EDITS_STORE);
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(new Error('Failed to clear pending edits'));
    });
  }

  /**
   * Get database statistics
   */
  async getStats(): Promise<{ cachedDiagrams: number; pendingEdits: number }> {
    await this.init();
    if (!this.db) throw new Error('Database not initialized');

    const [cachedDiagrams, pendingEdits] = await Promise.all([
      this.getAllCachedDiagrams(),
      this.getPendingEdits(),
    ]);

    return {
      cachedDiagrams: cachedDiagrams.length,
      pendingEdits: pendingEdits.length,
    };
  }
}

// Export singleton instance
export const offlineDB = new OfflineDB();
