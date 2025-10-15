/**
 * Environment Configuration
 * Centralizes all configuration values from environment variables
 * @module config/env
 */

/**
 * Get environment variable with fallback
 * @param {string} key - Environment variable key
 * @param {string} defaultValue - Default value if not found
 * @returns {string}
 */
const getEnv = (key, defaultValue = '') => {
  return (import.meta.env && import.meta.env[key]) || defaultValue;
};

/**
 * Backend configuration
 */
export const BACKEND_CONFIG = {
  host: getEnv('VITE_BACKEND_HOST', 'localhost:8000'),
  protocol: getEnv('VITE_BACKEND_PROTOCOL', 'http'),
  wsProtocol: getEnv('VITE_WS_PROTOCOL', 'ws'),

  /**
   * Get backend URL based on current hostname
   * @returns {string}
   */
  getBackendHost() {
    return window.location.hostname === 'localhost'
      ? this.host
      : window.location.host;
  },

  /**
   * Get HTTP base URL
   * @returns {string}
   */
  getHttpUrl() {
    return `${this.protocol}://${this.getBackendHost()}`;
  },

  /**
   * Get WebSocket base URL
   * @returns {string}
   */
  getWsUrl() {
    return `${this.wsProtocol}://${this.getBackendHost()}`;
  }
};

/**
 * API endpoints configuration
 */
export const API_ENDPOINTS = {
  baseUrl: getEnv('VITE_API_BASE_URL', 'http://localhost:8000/api'),

  // Document endpoints
  documents: {
    upload: '/api/documents/upload',
    ingestionStatus: (jobId) => `/api/documents/ingestion_status/${jobId}`,
    list: '/api/documents/list'
  },

  // Assessment endpoints
  assessments: {
    search: '/api/assessments/search',
    validate: '/api/assessments/validate',
    details: (id) => `/api/assessments/${id}`
  },

  // WebSocket endpoints
  ws: {
    enterprise: (sessionId) => `/ws/enterprise/${sessionId}`,
    simple: (sessionId) => `/ws/simple/${sessionId}`
  },

  // System endpoints
  system: {
    health: '/api/health',
    status: '/api/system/status'
  }
};

/**
 * Upload configuration
 */
export const UPLOAD_CONFIG = {
  maxFileSize: parseInt(getEnv('VITE_MAX_FILE_SIZE', '10485760')), // 10MB
  allowedFileTypes: getEnv('VITE_ALLOWED_FILE_TYPES', '.pdf,.doc,.docx,.txt'),
  maxFilesPerUpload: parseInt(getEnv('VITE_MAX_FILES_PER_UPLOAD', '10')),

  /**
   * Get allowed file extensions as array
   * @returns {string[]}
   */
  getAllowedExtensions() {
    return this.allowedFileTypes.split(',').map(ext => ext.trim());
  },

  /**
   * Format file size for display
   * @param {number} bytes
   * @returns {string}
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
};

/**
 * WebSocket configuration
 */
export const WS_CONFIG = {
  reconnectDelay: parseInt(getEnv('VITE_WS_RECONNECT_DELAY', '3000')),
  maxReconnectAttempts: parseInt(getEnv('VITE_WS_MAX_RECONNECT_ATTEMPTS', '10')),
  heartbeatInterval: 30000,
  messageTimeout: 60000
};

/**
 * Polling configuration
 */
export const POLL_CONFIG = {
  ingestionInterval: parseInt(getEnv('VITE_INGESTION_POLL_INTERVAL', '3000')),
  statusCheckInterval: parseInt(getEnv('VITE_STATUS_CHECK_INTERVAL', '5000')),
  maxPollAttempts: 100
};

/**
 * UI timing configuration
 */
export const UI_CONFIG = {
  messageAnimationDelay: parseInt(getEnv('VITE_MESSAGE_ANIMATION_DELAY', '50')),
  scrollDelay: parseInt(getEnv('VITE_SCROLL_DELAY', '100')),
  debounceDelay: parseInt(getEnv('VITE_DEBOUNCE_DELAY', '500')),
  notificationDuration: 3000,
  tooltipDelay: 500
};

/**
 * Session configuration
 */
export const SESSION_CONFIG = {
  prefix: getEnv('VITE_SESSION_PREFIX', 'enterprise_'),
  storageKey: getEnv('VITE_SESSION_STORAGE_KEY', 'tra_session'),

  /**
   * Generate new session ID
   * @returns {string}
   */
  generateSessionId() {
    return this.prefix + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }
};

/**
 * Feature flags
 */
export const FEATURES = {
  autoAnalysis: getEnv('VITE_ENABLE_AUTO_ANALYSIS', 'true') === 'true',
  documentSummaries: getEnv('VITE_ENABLE_DOCUMENT_SUMMARIES', 'false') === 'true',
  debugMode: getEnv('VITE_ENABLE_DEBUG_MODE', 'false') === 'true'
};

/**
 * Environment info
 */
export const ENV_INFO = {
  environment: getEnv('VITE_ENV', 'development'),
  isDevelopment: getEnv('VITE_ENV', 'development') === 'development',
  isProduction: getEnv('VITE_ENV', 'development') === 'production'
};

/**
 * Debug logger (only logs in development mode)
 * @param {...any} args
 */
export const debugLog = (...args) => {
  if (FEATURES.debugMode) {
    console.log('[TRA Debug]', ...args);
  }
};

/**
 * Export all configuration as single object
 */
export default {
  BACKEND_CONFIG,
  API_ENDPOINTS,
  UPLOAD_CONFIG,
  WS_CONFIG,
  POLL_CONFIG,
  UI_CONFIG,
  SESSION_CONFIG,
  FEATURES,
  ENV_INFO,
  debugLog
};
