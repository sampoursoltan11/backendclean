/**
 * Application Constants
 * Centralizes all magic strings and numbers used throughout the application
 * @module utils/constants
 */

/**
 * Message roles
 */
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system'
};

/**
 * Agent types
 */
export const AGENTS = {
  ORCHESTRATOR: 'orchestrator',
  ASSESSMENT: 'assessment',
  DOCUMENT: 'document',
  QUESTION: 'question',
  STATUS: 'status'
};

/**
 * File status
 */
export const FILE_STATUS = {
  READY: 'ready',
  PROCESSING: 'processing',
  FAILED: 'failed',
  UPLOADING: 'uploading'
};

/**
 * Assessment status
 */
export const ASSESSMENT_STATUS = {
  DRAFT: 'draft',
  IN_PROGRESS: 'in_progress',
  COMPLETE: 'complete',
  ARCHIVED: 'archived'
};

/**
 * Ingestion status
 */
export const INGESTION_STATUS = {
  PENDING: 'PENDING',
  IN_PROGRESS: 'IN_PROGRESS',
  COMPLETE: 'COMPLETE',
  FAILED: 'FAILED'
};

/**
 * Question types
 */
export const QUESTION_TYPES = {
  YES_NO: 'yes_no',
  MULTIPLE_CHOICE: 'multiple_choice',
  FREE_TEXT: 'free_text',
  RISK_AREA_BUTTONS: 'risk_area_buttons'
};

/**
 * Confidence levels
 */
export const CONFIDENCE_LEVELS = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low'
};

/**
 * Risk areas
 */
export const RISK_AREAS = {
  CLOUD_MIGRATION: 'Cloud Migration',
  DATA_PRIVACY: 'Data Privacy',
  CYBERSECURITY: 'Cybersecurity',
  SYSTEM_INTEGRATION: 'System Integration',
  VENDOR_MANAGEMENT: 'Vendor Management',
  COMPLIANCE: 'Compliance',
  BUSINESS_CONTINUITY: 'Business Continuity',
  CHANGE_MANAGEMENT: 'Change Management'
};

/**
 * WebSocket message types
 */
export const WS_MESSAGE_TYPES = {
  MESSAGE: 'message',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  PING: 'ping',
  PONG: 'pong'
};

/**
 * WebSocket connection states
 */
export const WS_STATES = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3
};

/**
 * TRA ID format
 */
export const TRA_ID_FORMAT = {
  PATTERN: /^TRA-\d{4}-[A-Z0-9]{6}$/i,
  PREFIX: 'TRA-',
  YEAR_LENGTH: 4,
  CODE_LENGTH: 6,
  EXAMPLE: 'TRA-2025-XXXXXX'
};

/**
 * HTTP status codes
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_ERROR: 500,
  SERVICE_UNAVAILABLE: 503
};

/**
 * Error messages
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error occurred. Please check your connection.',
  UPLOAD_FAILED: 'File upload failed. Please try again.',
  VALIDATION_FAILED: 'TRA ID validation failed.',
  WEBSOCKET_ERROR: 'WebSocket connection error.',
  FILE_TOO_LARGE: 'File size exceeds maximum allowed size.',
  INVALID_FILE_TYPE: 'Invalid file type. Please upload PDF, DOC, DOCX, or TXT files.',
  SESSION_EXPIRED: 'Your session has expired. Please refresh the page.',
  GENERIC_ERROR: 'An error occurred. Please try again.'
};

/**
 * Success messages
 */
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: 'File uploaded successfully!',
  TRA_ID_VALID: 'TRA ID is valid',
  ASSESSMENT_CREATED: 'Assessment created successfully',
  MESSAGE_SENT: 'Message sent',
  CONNECTION_ESTABLISHED: 'Connected to server'
};

/**
 * UI text
 */
export const UI_TEXT = {
  LOADING: 'Loading...',
  UPLOADING: 'Uploading...',
  PROCESSING: 'Processing...',
  VALIDATING: 'Validating...',
  CONNECTING: 'Connecting...',
  SEARCHING: 'Searching...',
  NO_RESULTS: 'No results found',
  EMPTY_STATE: 'No data available'
};

/**
 * Timeouts (milliseconds)
 */
export const TIMEOUTS = {
  ANIMATION: 50,
  DEBOUNCE: 500,
  SCROLL: 100,
  NOTIFICATION: 3000,
  POLL: 3000,
  RECONNECT: 3000,
  REQUEST: 30000,
  MESSAGE: 60000
};

/**
 * Limits
 */
export const LIMITS = {
  MAX_FILE_SIZE: 10485760, // 10MB in bytes
  MAX_FILES: 10,
  MAX_MESSAGE_LENGTH: 5000,
  MAX_RECONNECT_ATTEMPTS: 10,
  MAX_POLL_ATTEMPTS: 100,
  MESSAGE_HISTORY: 500
};

/**
 * CSS class names
 */
export const CSS_CLASSES = {
  // Messages
  USER_MESSAGE: 'user-message',
  BOT_MESSAGE: 'bot-message',
  SYSTEM_MESSAGE: 'system-message',
  MESSAGE_BUBBLE: 'message-bubble',

  // Agents
  AGENT_BADGE: 'agent-badge',

  // Confidence
  CONFIDENCE_HIGH: 'confidence-high',
  CONFIDENCE_MEDIUM: 'confidence-medium',
  CONFIDENCE_LOW: 'confidence-low',

  // Questions
  QUESTION_CONTAINER: 'question-container',
  QUESTION_TITLE: 'question-title',
  OPTION_ITEM: 'option-item',

  // AI Suggestions
  AI_SUGGESTION_BOX: 'ai-suggestion-box',
  AI_SUGGESTION_HEADER: 'ai-suggestion-header',
  AI_SUGGESTION_CONTENT: 'ai-suggestion-content',
  AI_SUGGESTION_ANSWER: 'ai-suggestion-answer',

  // Progress
  PROGRESS_CONTAINER: 'progress-container',
  PROGRESS_BAR: 'progress-bar-fill',

  // Buttons
  BTN_PRIMARY: 'bg-blue-600 hover:bg-blue-700 text-white',
  BTN_SECONDARY: 'bg-gray-600 hover:bg-gray-700 text-white',
  BTN_SUCCESS: 'bg-green-600 hover:bg-green-700 text-white',
  BTN_DANGER: 'bg-red-600 hover:bg-red-700 text-white'
};

/**
 * Local storage keys
 */
export const STORAGE_KEYS = {
  SESSION_ID: 'tra_session_id',
  SESSION_CONTEXT: 'tra_session_context',
  UPLOADED_FILES: 'tra_uploaded_files',
  TRA_ID: 'tra_current_id',
  USER_PREFERENCES: 'tra_user_prefs'
};

/**
 * Event names
 */
export const EVENTS = {
  MESSAGE_RECEIVED: 'tra:message:received',
  MESSAGE_SENT: 'tra:message:sent',
  FILE_UPLOADED: 'tra:file:uploaded',
  FILE_FAILED: 'tra:file:failed',
  WS_CONNECTED: 'tra:ws:connected',
  WS_DISCONNECTED: 'tra:ws:disconnected',
  WS_ERROR: 'tra:ws:error',
  VALIDATION_SUCCESS: 'tra:validation:success',
  VALIDATION_FAILED: 'tra:validation:failed'
};

/**
 * Regex patterns
 */
export const PATTERNS = {
  TRA_ID: /TRA-\d{4}-[A-Z0-9]{6}/gi,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/.+/i,
  QUESTION_PROGRESS: /Question\s+(\d+)\s+of\s+(\d+)/i,
  RISK_AREAS: /added risk area\(s\):\s*(.+?)\s+to assessment/i,
  PROJECT_NAME: /TRA-\d{4}-[A-Z0-9]+\]\s+(.+?)(?:\n|System ID:)/i
};

/**
 * Animation durations (milliseconds)
 */
export const ANIMATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000
};

/**
 * Notification types
 */
export const NOTIFICATION_TYPES = {
  INFO: 'info',
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error'
};

/**
 * Export all constants
 */
export default {
  MESSAGE_ROLES,
  AGENTS,
  FILE_STATUS,
  ASSESSMENT_STATUS,
  INGESTION_STATUS,
  QUESTION_TYPES,
  CONFIDENCE_LEVELS,
  RISK_AREAS,
  WS_MESSAGE_TYPES,
  WS_STATES,
  TRA_ID_FORMAT,
  HTTP_STATUS,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  UI_TEXT,
  TIMEOUTS,
  LIMITS,
  CSS_CLASSES,
  STORAGE_KEYS,
  EVENTS,
  PATTERNS,
  ANIMATIONS,
  NOTIFICATION_TYPES
};
