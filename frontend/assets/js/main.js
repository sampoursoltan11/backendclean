/**
 * Main Entry Point
 * Initializes the application and sets up Alpine.js with all stores and services
 * @module main
 */

// Import Alpine.js (assumes it's loaded via CDN in HTML)
// If using npm/bundler, uncomment: import Alpine from 'alpinejs';

// Import stores
import createChatStore from './stores/chat-store.js';

// Import services (for initialization)
import apiService from './services/api.service.js';
import websocketService from './services/websocket.service.js';
import storageService from './services/storage.service.js';

// Import components (for availability)
import messageFormatter from './components/message-formatter.js';
import questionRenderer from './components/question-renderer.js';
import fileUploader from './components/file-uploader.js';
import search from './components/search.js';

// Import utilities
import * as sanitizers from './utils/sanitizers.js';
import * as validators from './utils/validators.js';
import * as formatters from './utils/formatters.js';
import * as constants from './utils/constants.js';

// Import config
import { BACKEND_CONFIG, debugLog, setDebugMode } from './config/env.js';

/**
 * Application initialization
 */
function initializeApp() {
  debugLog('🚀 Initializing Enterprise TRA Application...');

  // Enable debug mode in development
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    setDebugMode(true);
    debugLog('Debug mode enabled (development environment)');
  }

  // Check if Alpine is loaded
  if (typeof window.Alpine === 'undefined') {
    console.error('❌ Alpine.js not found! Make sure Alpine.js is loaded before main.js');
    return;
  }

  debugLog('✓ Alpine.js detected');

  // Register Alpine stores
  registerAlpineStores();

  // Set up global error handlers
  setupErrorHandlers();

  // Initialize services
  initializeServices();

  // Start Alpine (use startAlpine callback if available, otherwise direct start)
  if (typeof window.startAlpine === 'function') {
    window.startAlpine();
    debugLog('✓ Alpine.js started (deferred)');
  } else if (window.Alpine && !window.Alpine.version) {
    window.Alpine.start();
    debugLog('✓ Alpine.js started (direct)');
  } else {
    debugLog('✓ Alpine.js already started');
  }

  // Perform health check
  performHealthCheck();

  debugLog('✓ Application initialized successfully');
}

/**
 * Register Alpine.js stores
 */
function registerAlpineStores() {
  debugLog('Registering Alpine stores...');

  // Register chat store
  window.Alpine.store('chat', createChatStore());
  debugLog('✓ Chat store registered');

  // You can register additional stores here
  // window.Alpine.store('otherStore', createOtherStore());
}

/**
 * Set up global error handlers
 */
function setupErrorHandlers() {
  debugLog('Setting up global error handlers...');

  // Handle uncaught errors
  window.addEventListener('error', (event) => {
    console.error('Uncaught error:', event.error);

    // Log to backend if available
    if (apiService) {
      apiService.post('/api/logs/error', {
        message: event.error?.message || 'Unknown error',
        stack: event.error?.stack,
        url: window.location.href,
        timestamp: new Date().toISOString()
      }).catch(err => {
        debugLog('Failed to log error to backend:', err);
      });
    }
  });

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);

    // Log to backend if available
    if (apiService) {
      apiService.post('/api/logs/error', {
        message: event.reason?.message || 'Unhandled promise rejection',
        stack: event.reason?.stack,
        url: window.location.href,
        timestamp: new Date().toISOString()
      }).catch(err => {
        debugLog('Failed to log error to backend:', err);
      });
    }
  });

  debugLog('✓ Error handlers set up');
}

/**
 * Initialize services
 */
function initializeServices() {
  debugLog('Initializing services...');

  // Storage service initialization
  try {
    storageService.init();
    debugLog('✓ Storage service initialized');
  } catch (error) {
    console.error('Failed to initialize storage service:', error);
  }

  // API service is initialized automatically on import
  debugLog('✓ API service ready');

  // WebSocket service will be initialized by the chat store
  debugLog('✓ WebSocket service ready');
}

/**
 * Perform health check
 */
async function performHealthCheck() {
  debugLog('Performing health check...');

  try {
    const health = await apiService.getHealthStatus();
    debugLog('✓ Backend health check passed:', health);
  } catch (error) {
    console.warn('⚠ Backend health check failed:', error);
    console.warn('Application will continue, but backend may be unavailable');
  }
}

/**
 * Expose utilities and services globally for debugging (development only)
 */
function exposeGlobals() {
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.__TRA_DEBUG__ = {
      services: {
        api: apiService,
        websocket: websocketService,
        storage: storageService
      },
      components: {
        messageFormatter,
        questionRenderer,
        fileUploader,
        search
      },
      utils: {
        sanitizers,
        validators,
        formatters,
        constants
      },
      config: {
        backend: BACKEND_CONFIG
      }
    };

    console.log('🔧 Debug utilities available at window.__TRA_DEBUG__');
  }
}

/**
 * Export utilities for use in other modules
 */
export {
  // Services
  apiService,
  websocketService,
  storageService,

  // Components
  messageFormatter,
  questionRenderer,
  fileUploader,
  search,

  // Utilities
  sanitizers,
  validators,
  formatters,
  constants,

  // Config
  BACKEND_CONFIG
};

// Initialize the application when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    exposeGlobals();
  });
} else {
  // DOM already loaded
  initializeApp();
  exposeGlobals();
}

// Export initialization function for manual use
export { initializeApp };

// Make initialization function available globally
window.initializeEnterpriseTRA = initializeApp;

debugLog('Main module loaded');
