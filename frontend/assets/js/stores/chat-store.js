/**
 * Chat Store for Alpine.js
 * Central state management for the chat interface
 * @module stores/chat-store
 */

import messageFormatter from '../components/message-formatter.js';
import fileUploader from '../components/file-uploader.js';
import search from '../components/search.js';
import websocketService from '../services/websocket.service.js';
import { debugLog } from '../config/env.js';

/**
 * Create chat store for Alpine.js
 * This function returns the Alpine store configuration
 */
export function createChatStore() {
  return {
    // Connection state
    connected: false,
    socket: null,
    sessionId: '',
    sessionContext: {},

    // Message state
    messages: [],
    currentMessage: '',

    // File upload state
    uploadedFiles: [],
    traIdForUpload: '',
    traIdValid: null,
    traIdValidationMessage: '',
    isValidatingTraId: false,
    selectedTraDetails: null,

    // Search state
    searchQuery: '',
    searchResults: [],
    isSearching: false,
    showNotification: false,

    // Document summary query state
    docQueryTraId: '',
    documentSummaries: [],
    docQueryResult: {},
    isQueryingDocs: false,
    docQueryMessage: '',

    /**
     * Initialize the chat store
     */
    init() {
      this.sessionId = 'enterprise_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();

      debugLog('Initializing chat store with session ID:', this.sessionId);

      // Set up file uploader callbacks
      this.initFileUploader();

      // Set up search callbacks
      this.initSearch();

      // Connect WebSocket
      this.connectWebSocket();

      // Set up global helper functions
      this.setupGlobalHelpers();
    },

    /**
     * Initialize file uploader with callbacks
     */
    initFileUploader() {
      fileUploader.setCallbacks({
        onStart: (file, entry) => {
          this.addMessage('system', fileUploader.generateStatusMessage(file, 'uploading'));
          this.uploadedFiles = fileUploader.getUploadedFiles();
        },
        onProgress: (file, entry) => {
          this.uploadedFiles = fileUploader.getUploadedFiles();
        },
        onSuccess: (file, result) => {
          this.addMessage('system', fileUploader.generateStatusMessage(file, 'success', result));
          this.uploadedFiles = fileUploader.getUploadedFiles();

          // Auto-trigger question flow if auto-analyzed
          if (result.auto_analyzed && result.risk_areas_added) {
            setTimeout(() => {
              if (this.connected) {
                this.sendMessageDirect('start questions');
              }
            }, 1000);
          }
        },
        onError: (file, error) => {
          this.addMessage('system', fileUploader.generateStatusMessage(file, 'error'));
          this.uploadedFiles = fileUploader.getUploadedFiles();
        },
        onStatusChange: (fileId, status) => {
          this.uploadedFiles = fileUploader.getUploadedFiles();
        }
      });
    },

    /**
     * Initialize search with callbacks
     */
    initSearch() {
      search.setCallbacks({
        onStart: (query) => {
          this.isSearching = true;
        },
        onResults: (results) => {
          this.searchResults = results;
          this.isSearching = false;
          this.showNotification = results.length > 0;
        },
        onError: (error) => {
          this.isSearching = false;
          console.error('Search error:', error);
        },
        onClear: () => {
          this.searchResults = [];
          this.showNotification = false;
        }
      });
    },

    /**
     * Connect to WebSocket
     */
    async connectWebSocket() {
      try {
        await websocketService.connect(this.sessionId, 'enterprise');
        this.connected = true;

        // Set up message handler
        websocketService.on('message', (data) => {
          this.handleWebSocketMessage(data);
        });

        // Set up connection events
        websocketService.on('disconnected', () => {
          this.connected = false;
        });

        websocketService.on('connected', () => {
          this.connected = true;
        });

        debugLog('WebSocket connected successfully');
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        this.connected = false;
      }
    },

    /**
     * Handle incoming WebSocket message
     * @param {Object} data - Message data
     */
    handleWebSocketMessage(data) {
      if (data.type === 'message') {
        // Capture context from backend response
        if (data.context) {
          this.sessionContext = data.context;
          debugLog('[FRONTEND] Updated session context:', this.sessionContext);
        }

        // Detect which agent handled this
        const agent = this.detectAgent(data.content);
        this.addMessage('assistant', data.content, { agent });

        // Auto-populate TRA ID when assessment is created
        if (data.content.includes('Assessment Created Successfully')) {
          const traMatch = data.content.match(/TRA-\d{4}-[A-Z0-9]{6}/i);
          if (traMatch) {
            this.traIdForUpload = traMatch[0];
            this.traIdValid = true;
            this.traIdValidationMessage = 'Auto-populated from created assessment';
          }
        }

        // Scroll to bottom after message
        this.$nextTick(() => this.scrollToBottom());
      }
    },

    /**
     * Detect which agent sent the message
     * @param {string} content - Message content
     * @returns {string} Agent name
     */
    detectAgent(content) {
      const lower = content.toLowerCase();

      if (lower.includes('choose a risk area') || lower.includes('risk_area_buttons')) return 'question';
      if (lower.includes('assessment') && (lower.includes('created') || lower.includes('tra-'))) return 'assessment';
      if (lower.includes('uploaded') || lower.includes('upload') || lower.includes('document analyzed')) return 'document';
      if (lower.includes('question') || lower.includes('answer') || lower.includes('progress') || lower.includes('ai suggestion')) return 'question';
      if (lower.includes('status') || lower.includes('export') || lower.includes('report')) return 'status';

      return 'orchestrator';
    },

    /**
     * Handle file upload
     * @param {Event} event - File input event
     */
    async handleFileUpload(event) {
      if (!this.traIdValid) {
        this.addMessage('system', '❌ Please enter and validate a TRA ID before uploading documents.');
        return;
      }

      await fileUploader.handleFileUpload(event, this.sessionId, this.traIdForUpload);
    },

    /**
     * Send message through WebSocket
     */
    sendMessage() {
      if (!this.currentMessage.trim() || !this.connected) return;

      this.addMessage('user', this.currentMessage);

      websocketService.sendMessage(this.currentMessage, this.sessionContext);

      debugLog('[FRONTEND] Sent message with context:', this.sessionContext);

      this.currentMessage = '';
      this.$nextTick(() => this.scrollToBottom());
    },

    /**
     * Send message directly (for programmatic use)
     * @param {string} content - Message content
     */
    sendMessageDirect(content) {
      if (!content.trim() || !this.connected) return;

      this.addMessage('user', content);
      websocketService.sendMessage(content, this.sessionContext);

      debugLog('[FRONTEND] Sent direct message:', content);

      this.$nextTick(() => this.scrollToBottom());
    },

    /**
     * Add message to chat
     * @param {string} role - Message role (user, assistant, system)
     * @param {string} content - Message content
     * @param {Object} metadata - Additional metadata
     */
    addMessage(role, content, metadata = {}) {
      this.messages.push({
        id: Date.now() + Math.random(),
        role: role,
        content: content,
        timestamp: new Date(),
        metadata: metadata
      });

      this.$nextTick(() => this.scrollToBottom());
    },

    /**
     * Format message for display
     * @param {string} content - Message content
     * @param {string} role - Message role
     * @returns {string} Formatted HTML
     */
    formatMessage(content, role = 'assistant') {
      return messageFormatter.formatMessage(content, role);
    },

    /**
     * Scroll chat to bottom
     */
    scrollToBottom() {
      const container = document.getElementById('chat-messages');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },

    /**
     * Search assessments
     * @param {string} query - Search query
     */
    async searchAssessments(query = null) {
      const searchQuery = query !== null ? query : this.searchQuery;

      if (!searchQuery) {
        search.clearResults();
        this.searchResults = [];
        this.showNotification = false;
        return;
      }

      try {
        await search.searchAssessments(searchQuery, true);
        this.searchResults = search.getResults();
        this.isSearching = search.isSearchingNow();
      } catch (error) {
        console.error('Search failed:', error);
      }
    },

    /**
     * Validate TRA ID
     */
    async validateTraId() {
      const traId = this.traIdForUpload.trim();

      if (!traId) {
        this.traIdValid = null;
        this.traIdValidationMessage = '';
        return;
      }

      this.isValidatingTraId = true;

      try {
        const result = await search.validateTraId(traId);

        this.traIdValid = result.valid;
        this.traIdValidationMessage = result.message;
        this.selectedTraDetails = result.details;

        debugLog('[TRA ID] Validation result:', result);
      } catch (error) {
        this.traIdValid = false;
        this.traIdValidationMessage = 'Error validating TRA ID';
        console.error('[TRA ID] Validation error:', error);
      } finally {
        this.isValidatingTraId = false;
      }
    },

    /**
     * Copy assessment ID to clipboard
     * @param {string} assessmentId - Assessment ID
     * @param {Event} event - Click event
     */
    copyAssessmentToClipboard(assessmentId, event) {
      navigator.clipboard.writeText(assessmentId)
        .then(() => {
          this.showToast(`Copied ID: ${assessmentId}`, 'success');
          debugLog(`Copied assessment ID ${assessmentId} to clipboard`);
        })
        .catch(err => {
          console.error('Failed to copy assessment ID:', err);
          this.showToast('Failed to copy ID', 'error');
        });

      if (event) {
        event.stopPropagation();
      }
    },

    /**
     * Query document summaries for a TRA ID
     */
    async queryDocumentSummaries() {
      const traId = this.docQueryTraId.trim();

      if (!traId) {
        this.documentSummaries = [];
        this.docQueryMessage = '';
        return;
      }

      // Validate TRA ID format
      const validation = await search.validateTraId(traId);
      if (!validation.valid) {
        this.docQueryMessage = validation.message;
        this.documentSummaries = [];
        return;
      }

      this.isQueryingDocs = true;
      this.docQueryMessage = '';
      this.documentSummaries = [];

      try {
        const backendHost = window.location.hostname === 'localhost' ? 'localhost:8000' : window.location.host;
        const url = `http://${backendHost}/api/assessments/${traId}/documents`;

        debugLog(`[DOC QUERY] Making request to: ${url}`);

        const response = await fetch(url);
        debugLog(`[DOC QUERY] Response status: ${response.status}`);

        if (response.ok) {
          const result = await response.json();
          debugLog(`[DOC QUERY] Document query result:`, result);

          if (result && result.success === true) {
            this.documentSummaries = result.documents || [];
            this.docQueryResult = result;

            if (this.documentSummaries.length === 0) {
              this.docQueryMessage = `No documents found for TRA ${traId}`;
            }

            debugLog(`[DOC QUERY] Found ${this.documentSummaries.length} documents`);
          } else {
            this.docQueryMessage = result.error || 'Failed to retrieve documents';
            this.documentSummaries = [];
          }
        } else if (response.status === 404) {
          this.docQueryMessage = `TRA ID ${traId} not found`;
          this.documentSummaries = [];
        } else {
          this.docQueryMessage = `Error: ${response.status} ${response.statusText}`;
          this.documentSummaries = [];
        }
      } catch (error) {
        console.error('Document query error:', error);
        this.docQueryMessage = `Network error: ${error.message}`;
        this.documentSummaries = [];
      } finally {
        this.isQueryingDocs = false;
      }
    },

    /**
     * Show toast notification
     * @param {string} message - Toast message
     * @param {string} type - Toast type (success, error, info)
     */
    showToast(message, type = 'info') {
      const toast = document.createElement('div');
      const bgColor = type === 'success' ? 'bg-green-100 border-green-400 text-green-700' :
                      type === 'error' ? 'bg-red-100 border-red-400 text-red-700' :
                      'bg-blue-100 border-blue-400 text-blue-700';

      const icon = type === 'success' ?
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' :
        type === 'error' ?
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>' :
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>';

      toast.className = `fixed bottom-4 right-4 ${bgColor} border px-4 py-2 rounded-lg shadow-lg transition-opacity duration-500`;
      toast.innerHTML = `<div class="flex items-center">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          ${icon}
        </svg>
        <span>${message}</span>
      </div>`;

      document.body.appendChild(toast);

      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
          document.body.removeChild(toast);
        }, 500);
      }, 2000);
    },

    /**
     * Set up global helper functions for inline event handlers
     */
    setupGlobalHelpers() {
      // Populate input field
      window.populateInput = (text) => {
        this.currentMessage = text;
      };

      // Submit free text answer
      window.submitFreeText = (textAreaId) => {
        const textarea = document.getElementById(textAreaId);
        if (textarea && textarea.value.trim()) {
          this.currentMessage = textarea.value.trim();
          this.sendMessage();
        }
      };

      // Select search result
      window.selectSearchResult = (assessmentId) => {
        this.traIdForUpload = assessmentId;
        this.validateTraId();
      };

      debugLog('Global helpers set up');
    }
  };
}

// Export the store creator
export default createChatStore;
