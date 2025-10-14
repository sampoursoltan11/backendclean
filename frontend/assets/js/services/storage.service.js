/**
 * Storage Service
 * Wrapper for localStorage with error handling and type safety
 * @module services/storage
 */

import { STORAGE_KEYS } from '../utils/constants.js';
import { debugLog } from '../config/env.js';

/**
 * Storage Service Class
 * Provides safe access to localStorage with automatic serialization
 */
class StorageService {
  constructor() {
    this.available = this._checkAvailability();
  }

  /**
   * Check if localStorage is available
   * @returns {boolean}
   * @private
   */
  _checkAvailability() {
    try {
      const test = '__storage_test__';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch (e) {
      console.warn('localStorage is not available:', e);
      return false;
    }
  }

  /**
   * Set item in localStorage
   * @param {string} key - Storage key
   * @param {any} value - Value to store (will be JSON stringified)
   * @returns {boolean} Success status
   */
  set(key, value) {
    if (!this.available) {
      console.warn('localStorage not available');
      return false;
    }

    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(key, serialized);
      debugLog(`Storage set: ${key}`, value);
      return true;
    } catch (error) {
      console.error(`Failed to set storage item ${key}:`, error);
      return false;
    }
  }

  /**
   * Get item from localStorage
   * @param {string} key - Storage key
   * @param {any} defaultValue - Default value if key doesn't exist
   * @returns {any} Stored value or default value
   */
  get(key, defaultValue = null) {
    if (!this.available) {
      return defaultValue;
    }

    try {
      const item = localStorage.getItem(key);
      if (item === null) {
        return defaultValue;
      }

      const parsed = JSON.parse(item);
      debugLog(`Storage get: ${key}`, parsed);
      return parsed;
    } catch (error) {
      console.error(`Failed to get storage item ${key}:`, error);
      return defaultValue;
    }
  }

  /**
   * Remove item from localStorage
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  remove(key) {
    if (!this.available) {
      return false;
    }

    try {
      localStorage.removeItem(key);
      debugLog(`Storage remove: ${key}`);
      return true;
    } catch (error) {
      console.error(`Failed to remove storage item ${key}:`, error);
      return false;
    }
  }

  /**
   * Clear all items from localStorage
   * @returns {boolean} Success status
   */
  clear() {
    if (!this.available) {
      return false;
    }

    try {
      localStorage.clear();
      debugLog('Storage cleared');
      return true;
    } catch (error) {
      console.error('Failed to clear storage:', error);
      return false;
    }
  }

  /**
   * Check if key exists in localStorage
   * @param {string} key - Storage key
   * @returns {boolean}
   */
  has(key) {
    if (!this.available) {
      return false;
    }

    return localStorage.getItem(key) !== null;
  }

  /**
   * Get all keys from localStorage
   * @returns {string[]}
   */
  keys() {
    if (!this.available) {
      return [];
    }

    return Object.keys(localStorage);
  }

  /**
   * Get storage size (approximate, in characters)
   * @returns {number}
   */
  getSize() {
    if (!this.available) {
      return 0;
    }

    let total = 0;
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        total += localStorage[key].length + key.length;
      }
    }
    return total;
  }

  // Convenience methods for TRA-specific storage

  /**
   * Save session ID
   * @param {string} sessionId
   * @returns {boolean}
   */
  setSessionId(sessionId) {
    return this.set(STORAGE_KEYS.SESSION_ID, sessionId);
  }

  /**
   * Get session ID
   * @returns {string|null}
   */
  getSessionId() {
    return this.get(STORAGE_KEYS.SESSION_ID);
  }

  /**
   * Save session context
   * @param {Object} context
   * @returns {boolean}
   */
  setSessionContext(context) {
    return this.set(STORAGE_KEYS.SESSION_CONTEXT, context);
  }

  /**
   * Get session context
   * @returns {Object}
   */
  getSessionContext() {
    return this.get(STORAGE_KEYS.SESSION_CONTEXT, {});
  }

  /**
   * Save uploaded files list
   * @param {Array} files
   * @returns {boolean}
   */
  setUploadedFiles(files) {
    return this.set(STORAGE_KEYS.UPLOADED_FILES, files);
  }

  /**
   * Get uploaded files list
   * @returns {Array}
   */
  getUploadedFiles() {
    return this.get(STORAGE_KEYS.UPLOADED_FILES, []);
  }

  /**
   * Save current TRA ID
   * @param {string} traId
   * @returns {boolean}
   */
  setTraId(traId) {
    return this.set(STORAGE_KEYS.TRA_ID, traId);
  }

  /**
   * Get current TRA ID
   * @returns {string|null}
   */
  getTraId() {
    return this.get(STORAGE_KEYS.TRA_ID);
  }

  /**
   * Save user preferences
   * @param {Object} preferences
   * @returns {boolean}
   */
  setUserPreferences(preferences) {
    return this.set(STORAGE_KEYS.USER_PREFERENCES, preferences);
  }

  /**
   * Get user preferences
   * @returns {Object}
   */
  getUserPreferences() {
    return this.get(STORAGE_KEYS.USER_PREFERENCES, {});
  }

  /**
   * Clear session data (keeps user preferences)
   * @returns {boolean}
   */
  clearSession() {
    this.remove(STORAGE_KEYS.SESSION_ID);
    this.remove(STORAGE_KEYS.SESSION_CONTEXT);
    this.remove(STORAGE_KEYS.UPLOADED_FILES);
    this.remove(STORAGE_KEYS.TRA_ID);
    debugLog('Session data cleared');
    return true;
  }
}

// Export singleton instance
export default new StorageService();
