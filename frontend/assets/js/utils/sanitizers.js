/**
 * Sanitization Utilities
 * HTML sanitization using DOMPurify
 * @module utils/sanitizers
 */

// DOMPurify is loaded via CDN in HTML, use global variable
const DOMPurify = window.DOMPurify;

/**
 * Default DOMPurify configuration
 */
const DEFAULT_CONFIG = {
  ALLOWED_TAGS: [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i',
    'ul', 'ol', 'li', 'a', 'span', 'div',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'code', 'pre', 'blockquote',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'svg', 'path'  // Allow SVG for icons
  ],
  ALLOWED_ATTR: [
    'href', 'title', 'target', 'rel',
    'class', 'id', 'style',
    'data-*',  // Allow data attributes
    'onclick', 'onmouseover', 'onmouseout',  // For interactive buttons (temporary)
    // SVG attributes
    'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'd',
    'width', 'height'
  ],
  ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  ALLOW_DATA_ATTR: true,
  KEEP_CONTENT: true,
  RETURN_DOM: false,
  RETURN_DOM_FRAGMENT: false,
  RETURN_DOM_IMPORT: false
};

/**
 * Strict configuration (for user input)
 */
const STRICT_CONFIG = {
  ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a'],
  ALLOWED_ATTR: ['href', 'title', 'target', 'rel'],
  ALLOW_DATA_ATTR: false
};

/**
 * Sanitize HTML content
 * @param {string} html - HTML string to sanitize
 * @param {Object} config - Custom DOMPurify configuration
 * @returns {string} Sanitized HTML
 */
export function sanitizeHtml(html, config = {}) {
  if (typeof html !== 'string') {
    return '';
  }

  const finalConfig = { ...DEFAULT_CONFIG, ...config };

  try {
    return DOMPurify.sanitize(html, finalConfig);
  } catch (error) {
    console.error('Sanitization error:', error);
    return escapeHtml(html);  // Fallback to escaping
  }
}

/**
 * Sanitize HTML with strict rules (for user input)
 * @param {string} html - HTML string to sanitize
 * @returns {string} Sanitized HTML
 */
export function sanitizeUserInput(html) {
  return sanitizeHtml(html, STRICT_CONFIG);
}

/**
 * Escape HTML special characters
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
  if (typeof text !== 'string') {
    return '';
  }

  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Unescape HTML entities
 * @param {string} text - Text with HTML entities
 * @returns {string} Unescaped text
 */
export function unescapeHtml(text) {
  if (typeof text !== 'string') {
    return '';
  }

  const div = document.createElement('div');
  div.innerHTML = text;
  return div.textContent || '';
}

/**
 * Strip all HTML tags
 * @param {string} html - HTML string
 * @returns {string} Plain text
 */
export function stripHtml(html) {
  if (typeof html !== 'string') {
    return '';
  }

  const div = document.createElement('div');
  div.innerHTML = html;
  return div.textContent || div.innerText || '';
}

/**
 * Sanitize URL
 * @param {string} url - URL to sanitize
 * @returns {string} Sanitized URL or empty string if invalid
 */
export function sanitizeUrl(url) {
  if (typeof url !== 'string') {
    return '';
  }

  // Allow only http, https, and mailto protocols
  const allowedProtocols = ['http:', 'https:', 'mailto:'];

  try {
    const parsed = new URL(url, window.location.origin);
    if (allowedProtocols.includes(parsed.protocol)) {
      return parsed.toString();
    }
  } catch (error) {
    // Invalid URL
  }

  return '';
}

/**
 * Sanitize filename
 * @param {string} filename - Filename to sanitize
 * @returns {string} Sanitized filename
 */
export function sanitizeFilename(filename) {
  if (typeof filename !== 'string') {
    return 'file';
  }

  // Remove path separators and dangerous characters
  return filename
    .replace(/[/\\]/g, '')
    .replace(/[<>:"|?*]/g, '')
    .replace(/\.\./g, '')
    .trim()
    .substring(0, 255);  // Limit length
}

/**
 * Clean text for display (remove extra whitespace, normalize line breaks)
 * @param {string} text - Text to clean
 * @returns {string} Cleaned text
 */
export function cleanText(text) {
  if (typeof text !== 'string') {
    return '';
  }

  return text
    .replace(/\r\n/g, '\n')  // Normalize line breaks
    .replace(/\r/g, '\n')
    .replace(/\n{3,}/g, '\n\n')  // Max 2 consecutive line breaks
    .replace(/[ \t]+/g, ' ')  // Normalize spaces
    .trim();
}

/**
 * Sanitize CSS class name
 * @param {string} className - Class name to sanitize
 * @returns {string} Sanitized class name
 */
export function sanitizeClassName(className) {
  if (typeof className !== 'string') {
    return '';
  }

  // Keep only valid CSS class name characters
  return className
    .replace(/[^a-zA-Z0-9_-]/g, '')
    .replace(/^[0-9-]/, '')  // Can't start with number or hyphen
    .substring(0, 100);  // Limit length
}

/**
 * Sanitize JSON for safe embedding in HTML
 * @param {any} obj - Object to sanitize
 * @returns {string} Sanitized JSON string
 */
export function sanitizeJson(obj) {
  try {
    const json = JSON.stringify(obj);
    // Escape for safe embedding in HTML attributes
    return json
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');
  } catch (error) {
    console.error('JSON sanitization error:', error);
    return '{}';
  }
}

/**
 * Fix malformed HTML tags (specifically <br> tags)
 * @param {string} html - HTML with potential malformed tags
 * @returns {string} Fixed HTML
 */
export function fixMalformedTags(html) {
  if (typeof html !== 'string') {
    return '';
  }

  return html
    // Fix HTML-encoded br tags
    .replace(/&lt;(\s*)br(\s*)&gt;/gi, '<br>')
    // Fix br tags with spaces
    .replace(/<(\s*)br(\s*)>/gi, '<br>')
    // Fix newline + malformed br
    .replace(/\n(\s*)<(\s*)br(\s*)>/gi, '\n<br>')
    // Fix whitespace before opening bracket
    .replace(/\s+<(\s+)br>/gi, ' <br>');
}

/**
 * Create DOMPurify hook for custom sanitization
 * @param {string} hookName - Hook name
 * @param {Function} callback - Hook callback
 */
export function addSanitizationHook(hookName, callback) {
  DOMPurify.addHook(hookName, callback);
}

/**
 * Remove DOMPurify hook
 * @param {string} hookName - Hook name
 */
export function removeSanitizationHook(hookName) {
  DOMPurify.removeHook(hookName);
}

/**
 * Check if content is safe (returns boolean, doesn't modify)
 * @param {string} html - HTML to check
 * @returns {boolean} True if content is safe
 */
export function isSafeHtml(html) {
  const sanitized = sanitizeHtml(html);
  return sanitized === html;
}

// Export default sanitizer
export default {
  sanitizeHtml,
  sanitizeUserInput,
  escapeHtml,
  unescapeHtml,
  stripHtml,
  sanitizeUrl,
  sanitizeFilename,
  cleanText,
  sanitizeClassName,
  sanitizeJson,
  fixMalformedTags,
  addSanitizationHook,
  removeSanitizationHook,
  isSafeHtml
};
