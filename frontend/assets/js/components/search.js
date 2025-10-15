/**
 * Search Component
 * Handles assessment search functionality with debouncing and result management
 * @module components/search
 */

import { validateTraId } from '../utils/validators.js';
import { BACKEND_CONFIG, API_ENDPOINTS } from '../config/env.js';
import { debugLog } from '../config/env.js';

/**
 * Search Component Class
 * Provides search functionality for assessments and TRA IDs
 */
export class Search {
  constructor() {
    this.searchQuery = '';
    this.searchResults = [];
    this.isSearching = false;
    this.showNotification = false;
    this.debounceTimer = null;
    this.debounceDelay = 300; // milliseconds
    this.searchCallbacks = {
      onStart: null,
      onResults: null,
      onError: null,
      onClear: null
    };
  }

  /**
   * Set callbacks for search events
   * @param {Object} callbacks - Event callbacks
   */
  setCallbacks(callbacks) {
    this.searchCallbacks = { ...this.searchCallbacks, ...callbacks };
  }

  /**
   * Perform search for assessments
   * @param {string} query - Search query
   * @param {boolean} debounce - Whether to debounce the search
   * @returns {Promise<Array>} Search results
   */
  async searchAssessments(query, debounce = true) {
    this.searchQuery = query;

    debugLog(`[SEARCH] Searching for: "${query}"`);

    if (!query || !query.trim()) {
      this.clearResults();
      return [];
    }

    // Debounce search if requested
    if (debounce) {
      return this.debounceSearch(query);
    }

    this.isSearching = true;
    this.showNotification = false;

    if (this.searchCallbacks.onStart) {
      this.searchCallbacks.onStart(query);
    }

    try {
      const backendHost = BACKEND_CONFIG.getBackendHost();
      const url = `http://${backendHost}${API_ENDPOINTS.assessments.search}?query=${encodeURIComponent(query)}&limit=10`;

      debugLog(`[SEARCH] Making request to: ${url}`);

      const response = await fetch(url);
      debugLog(`[SEARCH] Response status: ${response.status}`);

      if (response.ok) {
        const results = await response.json();
        debugLog(`[SEARCH] Search results:`, results);

        if (results && results.success === true) {
          this.searchResults = results.assessments || [];
          debugLog(`[SEARCH] Found ${this.searchResults.length} results`);

          // Show notification when results are received
          if (this.searchResults.length > 0) {
            this.showNotification = true;
            setTimeout(() => {
              this.showNotification = false;
            }, 5000);
          }

          if (this.searchCallbacks.onResults) {
            this.searchCallbacks.onResults(this.searchResults);
          }

          return this.searchResults;
        } else {
          debugLog(`[SEARCH] No assessments in results:`, results);
          this.searchResults = [];
          return [];
        }
      } else {
        debugLog(`[SEARCH] Error response:`, response);
        throw new Error(`Search error: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('Search error:', error);
      this.searchResults = [];

      if (this.searchCallbacks.onError) {
        this.searchCallbacks.onError(error);
      }

      throw error;
    } finally {
      this.isSearching = false;
    }
  }

  /**
   * Debounced search
   * @param {string} query - Search query
   * @returns {Promise<Array>} Search results (wrapped in promise for debounce)
   */
  debounceSearch(query) {
    return new Promise((resolve) => {
      // Clear existing timer
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
      }

      // Set new timer
      this.debounceTimer = setTimeout(async () => {
        const results = await this.searchAssessments(query, false);
        resolve(results);
      }, this.debounceDelay);
    });
  }

  /**
   * Validate TRA ID format and check if it exists
   * @param {string} traId - TRA ID to validate
   * @returns {Promise<Object>} Validation result
   */
  async validateTraId(traId) {
    const trimmedId = traId.trim();

    if (!trimmedId) {
      return {
        valid: null,
        message: '',
        details: null
      };
    }

    // Check format first
    if (!validateTraId(trimmedId)) {
      return {
        valid: false,
        message: 'Invalid format. Use: TRA-2025-XXXXXX',
        details: null
      };
    }

    // Check if TRA ID exists
    try {
      const backendHost = BACKEND_CONFIG.getBackendHost();
      const response = await fetch(`http://${backendHost}${API_ENDPOINTS.assessments.details(trimmedId)}`);

      if (response.ok) {
        const data = await response.json();
        debugLog('[TRA ID] Validated:', data);

        return {
          valid: true,
          message: `Valid: ${data.title || trimmedId}`,
          details: data
        };
      } else {
        debugLog('[TRA ID] Not found:', trimmedId);

        return {
          valid: false,
          message: 'TRA ID not found',
          details: null
        };
      }
    } catch (error) {
      console.error('[TRA ID] Validation error:', error);

      return {
        valid: false,
        message: 'Error validating TRA ID',
        details: null
      };
    }
  }

  /**
   * Clear search results
   * @returns {void}
   */
  clearResults() {
    this.searchResults = [];
    this.showNotification = false;
    this.searchQuery = '';

    if (this.searchCallbacks.onClear) {
      this.searchCallbacks.onClear();
    }
  }

  /**
   * Get current search results
   * @returns {Array} Search results
   */
  getResults() {
    return [...this.searchResults];
  }

  /**
   * Check if currently searching
   * @returns {boolean} True if searching
   */
  isSearchingNow() {
    return this.isSearching;
  }

  /**
   * Get search query
   * @returns {string} Current search query
   */
  getQuery() {
    return this.searchQuery;
  }

  /**
   * Display search results (for UI integration)
   * @param {Array} results - Search results to display
   * @returns {string} HTML for search results
   */
  displayResults(results = null) {
    const resultsToDisplay = results || this.searchResults;

    if (!resultsToDisplay || resultsToDisplay.length === 0) {
      return '<div class="text-gray-500 text-sm p-4">No results found</div>';
    }

    let html = '<div class="search-results">';

    resultsToDisplay.forEach(result => {
      html += `
        <div class="search-result-item" onclick="window.selectSearchResult('${result.assessment_id}')">
          <div class="font-semibold text-gray-900">${result.assessment_id}</div>
          <div class="text-sm text-gray-600">${result.title || 'Untitled Assessment'}</div>
          ${result.created_at ? `<div class="text-xs text-gray-400">${new Date(result.created_at).toLocaleDateString()}</div>` : ''}
        </div>
      `;
    });

    html += '</div>';

    return html;
  }

  /**
   * Filter results by criteria
   * @param {Object} criteria - Filter criteria
   * @returns {Array} Filtered results
   */
  filterResults(criteria) {
    let filtered = [...this.searchResults];

    if (criteria.status) {
      filtered = filtered.filter(r => r.status === criteria.status);
    }

    if (criteria.dateFrom) {
      filtered = filtered.filter(r => new Date(r.created_at) >= new Date(criteria.dateFrom));
    }

    if (criteria.dateTo) {
      filtered = filtered.filter(r => new Date(r.created_at) <= new Date(criteria.dateTo));
    }

    if (criteria.title) {
      const titleLower = criteria.title.toLowerCase();
      filtered = filtered.filter(r => r.title && r.title.toLowerCase().includes(titleLower));
    }

    return filtered;
  }

  /**
   * Sort results by field
   * @param {string} field - Field to sort by
   * @param {string} order - Sort order ('asc' or 'desc')
   * @returns {Array} Sorted results
   */
  sortResults(field, order = 'asc') {
    const sorted = [...this.searchResults];

    sorted.sort((a, b) => {
      let aVal = a[field];
      let bVal = b[field];

      // Handle dates
      if (field === 'created_at' || field === 'updated_at') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }

      // Handle strings
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (order === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

    return sorted;
  }

  /**
   * Get result by assessment ID
   * @param {string} assessmentId - Assessment ID
   * @returns {Object|null} Result or null
   */
  getResultById(assessmentId) {
    return this.searchResults.find(r => r.assessment_id === assessmentId) || null;
  }

  /**
   * Set debounce delay
   * @param {number} delay - Delay in milliseconds
   * @returns {void}
   */
  setDebounceDelay(delay) {
    this.debounceDelay = delay;
  }

  /**
   * Cancel pending search
   * @returns {void}
   */
  cancelPendingSearch() {
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
  }
}

// Export singleton instance
export default new Search();
