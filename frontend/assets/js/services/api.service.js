/**
 * API Service
 * Handles all HTTP requests to the backend API
 * @module services/api
 */

import { BACKEND_CONFIG, API_ENDPOINTS, debugLog } from '../config/env.js';
import { HTTP_STATUS, ERROR_MESSAGES } from '../utils/constants.js';

/**
 * API Service Class
 * Provides methods for making API calls with error handling
 */
class APIService {
  constructor() {
    this.baseUrl = BACKEND_CONFIG.getHttpUrl();
    this.requestTimeout = 30000; // 30 seconds
  }

  /**
   * Generic fetch wrapper with error handling
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise<any>}
   * @private
   */
  async _fetch(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.requestTimeout);

    try {
      debugLog(`API Request: ${options.method || 'GET'} ${url}`);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          ...options.headers
        }
      });

      clearTimeout(timeout);

      // Handle non-OK responses
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      debugLog(`API Response: ${url}`, data);

      return data;
    } catch (error) {
      clearTimeout(timeout);

      if (error.name === 'AbortError') {
        throw new Error('Request timeout - please try again');
      }

      debugLog(`API Error: ${url}`, error);
      throw error;
    }
  }

  /**
   * Upload file to backend
   * @param {File} file - File to upload
   * @param {string} sessionId - Session ID
   * @param {string} assessmentId - TRA ID
   * @param {Function} onProgress - Progress callback
   * @returns {Promise<Object>}
   */
  async uploadFile(file, sessionId, assessmentId, onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    formData.append('assessment_id', assessmentId);

    try {
      const xhr = new XMLHttpRequest();

      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && onProgress) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch (e) {
              reject(new Error('Invalid JSON response'));
            }
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        });

        xhr.addEventListener('error', () => {
          reject(new Error('Network error during upload'));
        });

        xhr.addEventListener('abort', () => {
          reject(new Error('Upload cancelled'));
        });

        const url = `${this.baseUrl}${API_ENDPOINTS.documents.upload}`;
        xhr.open('POST', url);
        xhr.send(formData);
      });
    } catch (error) {
      console.error('Upload error:', error);
      throw new Error(ERROR_MESSAGES.UPLOAD_FAILED);
    }
  }

  /**
   * Get ingestion status for uploaded file
   * @param {string} ingestionJobId - Ingestion job ID
   * @returns {Promise<Object>}
   */
  async getIngestionStatus(ingestionJobId) {
    try {
      const endpoint = API_ENDPOINTS.documents.ingestionStatus(ingestionJobId);
      return await this._fetch(endpoint);
    } catch (error) {
      console.error('Failed to get ingestion status:', error);
      throw error;
    }
  }

  /**
   * Search assessments
   * @param {string} query - Search query
   * @returns {Promise<Array>}
   */
  async searchAssessments(query) {
    try {
      const params = new URLSearchParams({ q: query });
      const endpoint = `${API_ENDPOINTS.assessments.search}?${params}`;
      const data = await this._fetch(endpoint);
      return data.results || [];
    } catch (error) {
      console.error('Search failed:', error);
      throw error;
    }
  }

  /**
   * Validate TRA ID
   * @param {string} traId - TRA ID to validate
   * @returns {Promise<Object>}
   */
  async validateTraId(traId) {
    try {
      const endpoint = API_ENDPOINTS.assessments.validate;
      const data = await this._fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tra_id: traId })
      });

      return {
        valid: data.valid || false,
        message: data.message || '',
        details: data.details || null
      };
    } catch (error) {
      console.error('TRA ID validation failed:', error);
      throw new Error(ERROR_MESSAGES.VALIDATION_FAILED);
    }
  }

  /**
   * Get assessment details
   * @param {string} assessmentId - Assessment ID
   * @returns {Promise<Object>}
   */
  async getAssessmentDetails(assessmentId) {
    try {
      const endpoint = API_ENDPOINTS.assessments.details(assessmentId);
      return await this._fetch(endpoint);
    } catch (error) {
      console.error('Failed to get assessment details:', error);
      throw error;
    }
  }

  /**
   * List documents for session
   * @param {string} sessionId - Session ID
   * @returns {Promise<Array>}
   */
  async listDocuments(sessionId) {
    try {
      const params = new URLSearchParams({ session_id: sessionId });
      const endpoint = `${API_ENDPOINTS.documents.list}?${params}`;
      const data = await this._fetch(endpoint);
      return data.documents || [];
    } catch (error) {
      console.error('Failed to list documents:', error);
      throw error;
    }
  }

  /**
   * Get system health status
   * @returns {Promise<Object>}
   */
  async getHealthStatus() {
    try {
      return await this._fetch(API_ENDPOINTS.system.health);
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }

  /**
   * Get system status
   * @returns {Promise<Object>}
   */
  async getSystemStatus() {
    try {
      return await this._fetch(API_ENDPOINTS.system.status);
    } catch (error) {
      console.error('System status check failed:', error);
      throw error;
    }
  }

  /**
   * Generic POST request
   * @param {string} endpoint - Endpoint path
   * @param {Object} data - Request body
   * @returns {Promise<Object>}
   */
  async post(endpoint, data) {
    return await this._fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }

  /**
   * Generic GET request
   * @param {string} endpoint - Endpoint path
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>}
   */
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return await this._fetch(url);
  }

  /**
   * Generic PUT request
   * @param {string} endpoint - Endpoint path
   * @param {Object} data - Request body
   * @returns {Promise<Object>}
   */
  async put(endpoint, data) {
    return await this._fetch(endpoint, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
  }

  /**
   * Generic DELETE request
   * @param {string} endpoint - Endpoint path
   * @returns {Promise<Object>}
   */
  async delete(endpoint) {
    return await this._fetch(endpoint, {
      method: 'DELETE'
    });
  }
}

// Export singleton instance
export default new APIService();
