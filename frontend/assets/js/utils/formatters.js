/**
 * Formatting Utilities
 * Functions for formatting messages, dates, numbers, etc.
 * @module utils/formatters
 */

/**
 * Format timestamp to readable string
 * @param {Date|string|number} timestamp - Timestamp to format
 * @returns {string} Formatted time string
 */
export function formatTime(timestamp) {
  try {
    const date = timestamp instanceof Date ? timestamp : new Date(timestamp);

    if (isNaN(date.getTime())) {
      return '';
    }

    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    // Less than 1 minute
    if (seconds < 60) {
      return 'Just now';
    }

    // Less than 1 hour
    if (minutes < 60) {
      return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
    }

    // Less than 24 hours
    if (hours < 24) {
      return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
    }

    // Less than 7 days
    if (days < 7) {
      return `${days} ${days === 1 ? 'day' : 'days'} ago`;
    }

    // Format as date
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  } catch (error) {
    console.error('Error formatting time:', error);
    return '';
  }
}

/**
 * Format date to full string
 * @param {Date|string|number} date - Date to format
 * @returns {string} Formatted date string
 */
export function formatDate(date) {
  try {
    const d = date instanceof Date ? date : new Date(date);

    if (isNaN(d.getTime())) {
      return '';
    }

    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return '';
  }
}

/**
 * Format file size in bytes to readable string
 * @param {number} bytes - File size in bytes
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted file size
 */
export function formatFileSize(bytes, decimals = 2) {
  if (bytes === 0) return '0 Bytes';
  if (typeof bytes !== 'number' || bytes < 0) return 'Invalid size';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
export function formatNumber(num) {
  if (typeof num !== 'number' || isNaN(num)) {
    return '0';
  }

  return num.toLocaleString('en-US');
}

/**
 * Format percentage
 * @param {number} value - Value (0-100)
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted percentage
 */
export function formatPercentage(value, decimals = 0) {
  if (typeof value !== 'number' || isNaN(value)) {
    return '0%';
  }

  return `${value.toFixed(decimals)}%`;
}

/**
 * Format TRA ID
 * @param {string} traId - TRA ID
 * @returns {string} Formatted TRA ID
 */
export function formatTraId(traId) {
  if (typeof traId !== 'string') {
    return '';
  }

  return traId.toUpperCase().trim();
}

/**
 * Format markdown-style bold text to HTML
 * @param {string} text - Text with **bold** markers
 * @returns {string} HTML with <strong> tags
 */
export function formatBoldText(text) {
  if (typeof text !== 'string') {
    return '';
  }

  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

/**
 * Format line breaks to <br> tags
 * @param {string} text - Text with line breaks
 * @returns {string} HTML with <br> tags
 */
export function formatLineBreaks(text) {
  if (typeof text !== 'string') {
    return '';
  }

  return text.replace(/\n/g, '<br>');
}

/**
 * Format list items (markdown-style)
 * @param {string} text - Text with • or - list markers
 * @returns {string} HTML with proper list structure
 */
export function formatList(text) {
  if (typeof text !== 'string') {
    return '';
  }

  // Split by lines and detect list items
  const lines = text.split('\n');
  let inList = false;
  let result = '';

  lines.forEach(line => {
    const trimmed = line.trim();

    if (trimmed.match(/^[•\-\*]\s+/)) {
      if (!inList) {
        result += '<ul>';
        inList = true;
      }
      const content = trimmed.replace(/^[•\-\*]\s+/, '');
      result += `<li>${content}</li>`;
    } else {
      if (inList) {
        result += '</ul>';
        inList = false;
      }
      if (trimmed) {
        result += trimmed + '<br>';
      }
    }
  });

  if (inList) {
    result += '</ul>';
  }

  return result;
}

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} length - Maximum length
 * @param {string} suffix - Suffix to add (default: '...')
 * @returns {string} Truncated text
 */
export function truncate(text, length = 100, suffix = '...') {
  if (typeof text !== 'string') {
    return '';
  }

  if (text.length <= length) {
    return text;
  }

  return text.substring(0, length).trim() + suffix;
}

/**
 * Format duration in milliseconds to readable string
 * @param {number} ms - Duration in milliseconds
 * @returns {string} Formatted duration
 */
export function formatDuration(ms) {
  if (typeof ms !== 'number' || ms < 0) {
    return '0s';
  }

  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  }

  if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  }

  return `${seconds}s`;
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
export function capitalize(str) {
  if (typeof str !== 'string' || str.length === 0) {
    return '';
  }

  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Convert camelCase to Title Case
 * @param {string} str - camelCase string
 * @returns {string} Title Case string
 */
export function camelToTitle(str) {
  if (typeof str !== 'string') {
    return '';
  }

  return str
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}

/**
 * Format agent name for display
 * @param {string} agent - Agent name
 * @returns {string} Formatted agent name
 */
export function formatAgentName(agent) {
  if (typeof agent !== 'string') {
    return 'AI';
  }

  return capitalize(agent) + ' Agent';
}

/**
 * Format confidence level for display
 * @param {string} confidence - Confidence level (high, medium, low)
 * @returns {Object} Formatted confidence with color
 */
export function formatConfidence(confidence) {
  const lower = String(confidence).toLowerCase();

  const levels = {
    high: { text: 'High', color: 'confidence-high', icon: '✓' },
    medium: { text: 'Medium', color: 'confidence-medium', icon: '~' },
    low: { text: 'Low', color: 'confidence-low', icon: '!' }
  };

  return levels[lower] || levels.medium;
}

// Export all formatters
export default {
  formatTime,
  formatDate,
  formatFileSize,
  formatNumber,
  formatPercentage,
  formatTraId,
  formatBoldText,
  formatLineBreaks,
  formatList,
  truncate,
  formatDuration,
  capitalize,
  camelToTitle,
  formatAgentName,
  formatConfidence
};
