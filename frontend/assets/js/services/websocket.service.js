/**
 * WebSocket Service
 * Manages WebSocket connections with automatic reconnection
 * @module services/websocket
 */

import { BACKEND_CONFIG, API_ENDPOINTS, WS_CONFIG, debugLog } from '../config/env.js';
import { WS_MESSAGE_TYPES, WS_STATES } from '../utils/constants.js';

/**
 * WebSocket Service Class
 * Handles WebSocket connection, reconnection, and message handling
 */
class WebSocketService {
  constructor() {
    this.socket = null;
    this.sessionId = null;
    this.reconnectAttempts = 0;
    this.reconnectTimeout = null;
    this.isIntentionallyClosed = false;
    this.messageHandlers = new Map();
    this.eventListeners = new Map();
  }

  /**
   * Connect to WebSocket
   * @param {string} sessionId - Session ID
   * @param {string} variant - Variant type ('enterprise' or 'simple')
   * @returns {Promise<void>}
   */
  connect(sessionId, variant = 'enterprise') {
    return new Promise((resolve, reject) => {
      this.sessionId = sessionId;
      this.isIntentionallyClosed = false;

      // In development, use relative path for Vite proxy; in production, use absolute WebSocket URL
      const isDevelopment = window.location.hostname === 'localhost';
      const wsPath = API_ENDPOINTS.ws[variant](sessionId);
      const wsUrl = isDevelopment
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${wsPath}`
        : `${BACKEND_CONFIG.getWsUrl()}${wsPath}`;
      debugLog(`Connecting to WebSocket: ${wsUrl}`);

      try {
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
          debugLog('WebSocket connected');
          this.reconnectAttempts = 0;
          this._emit('connected', { sessionId });
          resolve();
        };

        this.socket.onmessage = (event) => {
          this._handleMessage(event);
        };

        this.socket.onclose = (event) => {
          debugLog('WebSocket closed', event.code, event.reason);
          this._emit('disconnected', { code: event.code, reason: event.reason });

          if (!this.isIntentionallyClosed) {
            this._attemptReconnect(variant);
          }
        };

        this.socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          this._emit('error', { error });
          reject(error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Send message through WebSocket
   * @param {string} content - Message content
   * @param {Object} context - Session context
   */
  sendMessage(content, context = {}) {
    if (!this.isConnected()) {
      console.error('WebSocket not connected');
      return;
    }

    const message = {
      type: WS_MESSAGE_TYPES.MESSAGE,
      content,
      context
    };

    debugLog('Sending WebSocket message:', message);
    this.socket.send(JSON.stringify(message));
  }

  /**
   * Close WebSocket connection
   */
  disconnect() {
    this.isIntentionallyClosed = true;

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    debugLog('WebSocket disconnected intentionally');
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean}
   */
  isConnected() {
    return this.socket && this.socket.readyState === WS_STATES.OPEN;
  }

  /**
   * Register message handler
   * @param {string} type - Message type
   * @param {Function} handler - Handler function
   */
  onMessage(type, handler) {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type).push(handler);
  }

  /**
   * Register event listener
   * @param {string} event - Event name ('connected', 'disconnected', 'error')
   * @param {Function} listener - Listener function
   */
  on(event, listener) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(listener);
  }

  /**
   * Clear all event listeners for a specific event type
   * @param {string} event - Event name
   */
  clearListeners(event) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
  }

  /**
   * Clear all event listeners
   */
  clearAllListeners() {
    this.eventListeners.clear();
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} listener - Listener function
   */
  off(event, listener) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Handle incoming WebSocket message
   * @param {MessageEvent} event - WebSocket message event
   * @private
   */
  _handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      debugLog('WebSocket message received:', data);

      // Call registered handlers for this message type
      const handlers = this.messageHandlers.get(data.type);
      if (handlers) {
        handlers.forEach(handler => handler(data));
      }

      // Emit generic message event
      this._emit('message', data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      this._emit('error', { error });
    }
  }

  /**
   * Emit event to all registered listeners
   * @param {string} event - Event name
   * @param {Object} data - Event data
   * @private
   */
  _emit(event, data) {
    const listeners = this.eventListeners.get(event);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }

  /**
   * Attempt to reconnect WebSocket
   * @param {string} variant - Variant type
   * @private
   */
  _attemptReconnect(variant) {
    if (this.reconnectAttempts >= WS_CONFIG.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this._emit('reconnect_failed', { attempts: this.reconnectAttempts });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), WS_CONFIG.reconnectDelay);

    debugLog(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(() => {
      debugLog(`Reconnection attempt ${this.reconnectAttempts}`);
      this.connect(this.sessionId, variant).catch(error => {
        console.error('Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Get connection state
   * @returns {number} WebSocket ready state
   */
  getState() {
    return this.socket ? this.socket.readyState : WS_STATES.CLOSED;
  }

  /**
   * Get connection state as string
   * @returns {string}
   */
  getStateString() {
    const state = this.getState();
    switch (state) {
      case WS_STATES.CONNECTING: return 'CONNECTING';
      case WS_STATES.OPEN: return 'OPEN';
      case WS_STATES.CLOSING: return 'CLOSING';
      case WS_STATES.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }
  /**
   * Reset the service to initial state (for reconnections)
   */
  reset() {
    debugLog('Resetting WebSocket service...');

    // Close existing connection
    if (this.socket) {
      this.isIntentionallyClosed = true;
      this.socket.close();
      this.socket = null;
    }

    // Clear reconnection timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Reset state
    this.sessionId = null;
    this.reconnectAttempts = 0;
    this.isIntentionallyClosed = false;

    // IMPORTANT: Do NOT clear handlers - they should persist across reconnections
    // The clearAllListeners() method is available if needed for full reset

    debugLog('WebSocket service reset complete');
  }
}

// Singleton instance
let instance = null;

/**
 * Get WebSocket service singleton instance
 * @returns {WebSocketService}
 */
function getWebSocketService() {
  if (!instance) {
    instance = new WebSocketService();
  }
  return instance;
}

// Export singleton instance
export default getWebSocketService();
