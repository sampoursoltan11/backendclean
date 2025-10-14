/**
 * File Uploader Component
 * Handles file upload logic with validation, progress tracking, and status polling
 * @module components/file-uploader
 */

import { validateFile } from '../utils/validators.js';
import { sanitizeFilename } from '../utils/sanitizers.js';
import apiService from '../services/api.service.js';
import { debugLog } from '../config/env.js';

/**
 * File Uploader Class
 * Manages file upload operations with comprehensive error handling
 */
export class FileUploader {
  constructor() {
    this.uploadedFiles = [];
    this.uploadCallbacks = {
      onStart: null,
      onProgress: null,
      onSuccess: null,
      onError: null,
      onStatusChange: null
    };
  }

  /**
   * Set callbacks for upload events
   * @param {Object} callbacks - Event callbacks
   */
  setCallbacks(callbacks) {
    this.uploadCallbacks = { ...this.uploadCallbacks, ...callbacks };
  }

  /**
   * Handle file input change event
   * @param {Event} event - File input change event
   * @param {string} sessionId - Session ID
   * @param {string} assessmentId - TRA ID
   * @returns {Promise<void>}
   */
  async handleFileUpload(event, sessionId, assessmentId) {
    const files = Array.from(event.target.files);

    for (const file of files) {
      await this.uploadFile(file, sessionId, assessmentId);
    }

    // Clear input to allow re-uploading the same file
    event.target.value = '';
  }

  /**
   * Validate file before upload
   * @param {File} file - File to validate
   * @returns {Object} Validation result
   */
  validateFile(file) {
    return validateFile(file);
  }

  /**
   * Upload a single file
   * @param {File} file - File to upload
   * @param {string} sessionId - Session ID
   * @param {string} assessmentId - TRA ID
   * @returns {Promise<Object>} Upload result
   */
  async uploadFile(file, sessionId, assessmentId) {
    // Validate file first
    const validation = this.validateFile(file);
    if (!validation.valid) {
      const error = new Error(validation.message);
      this.handleUploadError(file, error);
      return { success: false, error: validation.message };
    }

    try {
      const tempId = Date.now().toString();
      const sanitizedFilename = sanitizeFilename(file.name);

      // Track file in uploaded files list
      const fileEntry = {
        filename: sanitizedFilename,
        file_id: tempId,
        status: 'uploading',
        progress: 0
      };

      this.uploadedFiles.push(fileEntry);

      // Notify upload start
      if (this.uploadCallbacks.onStart) {
        this.uploadCallbacks.onStart(file, fileEntry);
      }

      debugLog(`Starting upload: ${sanitizedFilename}`);

      // Upload file with progress tracking
      const result = await apiService.uploadFile(
        file,
        sessionId,
        assessmentId,
        (progress) => {
          fileEntry.progress = Math.round(progress);
          if (this.uploadCallbacks.onProgress) {
            this.uploadCallbacks.onProgress(file, fileEntry);
          }
        }
      );

      // Update file entry with real file ID and status
      this.updateFileStatus(tempId, {
        file_id: result.file_id,
        status: 'processing',
        progress: 100
      });

      debugLog(`Upload complete: ${sanitizedFilename}`, result);

      // Handle auto-analysis if it happened
      if (result.auto_analyzed && result.risk_areas_added) {
        this.handleAutoAnalysis(file, result);
      } else {
        // Poll ingestion status if needed
        if (result.ingestion_job_id) {
          this.pollIngestionStatus(result.file_id, result.ingestion_job_id, sanitizedFilename);
        } else {
          // Mark as ready immediately
          this.updateFileStatus(result.file_id, { status: 'ready' });
        }
      }

      // Notify success
      this.handleUploadSuccess(file, result);

      return { success: true, result };

    } catch (error) {
      debugLog(`Upload error: ${file.name}`, error);
      this.handleUploadError(file, error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Poll ingestion status for uploaded file
   * @param {string} fileId - File ID
   * @param {string} ingestionJobId - Ingestion job ID
   * @param {string} filename - Filename for logging
   * @returns {void}
   */
  pollIngestionStatus(fileId, ingestionJobId, filename) {
    debugLog(`Starting ingestion polling for: ${filename}`);

    const poll = async () => {
      try {
        const status = await apiService.getIngestionStatus(ingestionJobId);

        if (status.ready || status.complete || status.status === 'COMPLETE') {
          debugLog(`Ingestion complete: ${filename}`);
          this.updateFileStatus(fileId, { status: 'ready' });

          if (this.uploadCallbacks.onStatusChange) {
            this.uploadCallbacks.onStatusChange(fileId, 'ready');
          }
          return;
        } else if (status.status === 'FAILED') {
          debugLog(`Ingestion failed: ${filename}`);
          this.updateFileStatus(fileId, { status: 'failed' });

          if (this.uploadCallbacks.onStatusChange) {
            this.uploadCallbacks.onStatusChange(fileId, 'failed');
          }
          return;
        }

        // Poll again after 3 seconds
        setTimeout(poll, 3000);
      } catch (error) {
        debugLog(`Ingestion poll error: ${filename}`, error);
        // Continue polling even on errors
        setTimeout(poll, 3000);
      }
    };

    poll();
  }

  /**
   * Handle successful upload
   * @param {File} file - Uploaded file
   * @param {Object} result - Upload result
   * @returns {void}
   */
  handleUploadSuccess(file, result) {
    debugLog('Upload success:', file.name, result);

    if (this.uploadCallbacks.onSuccess) {
      this.uploadCallbacks.onSuccess(file, result);
    }
  }

  /**
   * Handle upload error
   * @param {File} file - File that failed to upload
   * @param {Error} error - Error object
   * @returns {void}
   */
  handleUploadError(file, error) {
    console.error('Upload error:', file.name, error);

    // Update file status to failed
    const fileEntry = this.uploadedFiles.find(f => f.filename === file.name);
    if (fileEntry) {
      this.updateFileStatus(fileEntry.file_id, { status: 'failed' });
    }

    if (this.uploadCallbacks.onError) {
      this.uploadCallbacks.onError(file, error);
    }
  }

  /**
   * Handle auto-analysis result
   * @param {File} file - Uploaded file
   * @param {Object} result - Upload result with auto-analysis data
   * @returns {void}
   */
  handleAutoAnalysis(file, result) {
    debugLog('Auto-analysis complete:', file.name, result);

    // Update file status to ready
    this.updateFileStatus(result.file_id, { status: 'ready' });

    // Trigger additional callback for auto-analysis
    if (this.uploadCallbacks.onAutoAnalysis) {
      this.uploadCallbacks.onAutoAnalysis(file, result);
    }
  }

  /**
   * Update file status
   * @param {string} fileId - File ID
   * @param {Object} updates - Status updates
   * @returns {void}
   */
  updateFileStatus(fileId, updates) {
    this.uploadedFiles = this.uploadedFiles.map(f =>
      f.file_id === fileId ? { ...f, ...updates } : f
    );

    if (this.uploadCallbacks.onStatusChange && updates.status) {
      this.uploadCallbacks.onStatusChange(fileId, updates.status);
    }
  }

  /**
   * Get uploaded files
   * @returns {Array} List of uploaded files
   */
  getUploadedFiles() {
    return [...this.uploadedFiles];
  }

  /**
   * Get file by ID
   * @param {string} fileId - File ID
   * @returns {Object|null} File entry or null
   */
  getFile(fileId) {
    return this.uploadedFiles.find(f => f.file_id === fileId) || null;
  }

  /**
   * Remove file from list
   * @param {string} fileId - File ID
   * @returns {boolean} Success status
   */
  removeFile(fileId) {
    const initialLength = this.uploadedFiles.length;
    this.uploadedFiles = this.uploadedFiles.filter(f => f.file_id !== fileId);
    return this.uploadedFiles.length < initialLength;
  }

  /**
   * Clear all uploaded files
   * @returns {void}
   */
  clearFiles() {
    this.uploadedFiles = [];
  }

  /**
   * Get files by status
   * @param {string} status - Status to filter by
   * @returns {Array} Filtered files
   */
  getFilesByStatus(status) {
    return this.uploadedFiles.filter(f => f.status === status);
  }

  /**
   * Check if any files are uploading
   * @returns {boolean} True if any files are uploading
   */
  hasUploadingFiles() {
    return this.uploadedFiles.some(f => f.status === 'uploading');
  }

  /**
   * Check if any files are processing
   * @returns {boolean} True if any files are processing
   */
  hasProcessingFiles() {
    return this.uploadedFiles.some(f => f.status === 'processing');
  }

  /**
   * Get upload progress summary
   * @returns {Object} Progress summary
   */
  getProgressSummary() {
    const total = this.uploadedFiles.length;
    const uploading = this.getFilesByStatus('uploading').length;
    const processing = this.getFilesByStatus('processing').length;
    const ready = this.getFilesByStatus('ready').length;
    const failed = this.getFilesByStatus('failed').length;

    return {
      total,
      uploading,
      processing,
      ready,
      failed,
      inProgress: uploading + processing,
      completed: ready + failed
    };
  }

  /**
   * Generate system message for upload status
   * @param {File} file - File object
   * @param {string} status - Upload status
   * @param {Object} result - Upload result (optional)
   * @returns {string} System message HTML
   */
  generateStatusMessage(file, status, result = null) {
    const filename = sanitizeFilename(file.name);

    switch (status) {
      case 'uploading':
        return `⬆ Uploading <strong>${filename}</strong>...`;

      case 'success':
        if (result && result.auto_analyzed && result.risk_areas_added) {
          const riskAreas = result.risk_areas_added.join(', ');
          return `✅ <strong>${filename}</strong> uploaded and analyzed!<br>` +
                 `🤖 AI Summary generated (${result.word_count || 0} words)<br>` +
                 `🏷️ Topics: ${(result.key_topics?.slice(0, 3).join(', ') || 'N/A')}<br>` +
                 `💾 Saved to DynamoDB<br>` +
                 `🎯 <strong>Auto-assigned Risk Areas: ${riskAreas}</strong><br>` +
                 `✨ Ready to answer questions for these risk areas!`;
        } else if (result) {
          const wordCount = result.word_count || 0;
          const topics = result.key_topics?.slice(0, 3).join(', ') || 'N/A';

          return `✅ <strong>${filename}</strong> uploaded successfully!<br>` +
                 `🤖 AI Summary generated (${wordCount} words)<br>` +
                 `🏷️ Topics: ${topics}<br>` +
                 `💾 Saved to DynamoDB - Ready for analysis!`;
        } else {
          return `✅ <strong>${filename}</strong> uploaded successfully!`;
        }

      case 'ready':
        return `✓ <strong>${filename}</strong> is ready for analysis.`;

      case 'failed':
        return `❌ Upload failed for <strong>${filename}</strong>`;

      case 'error':
        return `❌ Upload error: <strong>${filename}</strong>`;

      default:
        return `Processing <strong>${filename}</strong>...`;
    }
  }
}

// Export singleton instance
export default new FileUploader();
