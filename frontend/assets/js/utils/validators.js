/**
 * Validation Utilities
 * Functions for validating user input
 * @module utils/validators
 */

import { UPLOAD_CONFIG } from '../config/env.js';
import { TRA_ID_FORMAT } from './constants.js';

/**
 * Validate TRA ID format
 * @param {string} traId - TRA ID to validate
 * @returns {boolean} True if valid
 */
export function validateTraId(traId) {
  if (typeof traId !== 'string' || !traId) {
    return false;
  }

  return TRA_ID_FORMAT.PATTERN.test(traId.trim());
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid
 */
export function validateEmail(email) {
  if (typeof email !== 'string' || !email) {
    return false;
  }

  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return pattern.test(email.trim());
}

/**
 * Validate URL format
 * @param {string} url - URL to validate
 * @returns {boolean} True if valid
 */
export function validateUrl(url) {
  if (typeof url !== 'string' || !url) {
    return false;
  }

  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Validate file for upload
 * @param {File} file - File to validate
 * @returns {Object} Validation result with valid flag and message
 */
export function validateFile(file) {
  if (!file || !(file instanceof File)) {
    return {
      valid: false,
      message: 'Invalid file object'
    };
  }

  // Check file size
  if (file.size > UPLOAD_CONFIG.maxFileSize) {
    return {
      valid: false,
      message: `File size exceeds maximum allowed size (${UPLOAD_CONFIG.formatFileSize(UPLOAD_CONFIG.maxFileSize)})`
    };
  }

  // Check file type
  const extension = '.' + file.name.split('.').pop().toLowerCase();
  const allowedExtensions = UPLOAD_CONFIG.getAllowedExtensions();

  if (!allowedExtensions.includes(extension)) {
    return {
      valid: false,
      message: `File type not allowed. Allowed types: ${UPLOAD_CONFIG.allowedFileTypes}`
    };
  }

  return {
    valid: true,
    message: 'File is valid'
  };
}

/**
 * Validate text input (not empty, within length limits)
 * @param {string} text - Text to validate
 * @param {number} minLength - Minimum length
 * @param {number} maxLength - Maximum length
 * @returns {Object} Validation result
 */
export function validateText(text, minLength = 1, maxLength = 5000) {
  if (typeof text !== 'string') {
    return {
      valid: false,
      message: 'Text must be a string'
    };
  }

  const trimmed = text.trim();

  if (trimmed.length < minLength) {
    return {
      valid: false,
      message: `Text must be at least ${minLength} characters`
    };
  }

  if (trimmed.length > maxLength) {
    return {
      valid: false,
      message: `Text must not exceed ${maxLength} characters`
    };
  }

  return {
    valid: true,
    message: 'Text is valid'
  };
}

/**
 * Validate phone number (basic validation)
 * @param {string} phone - Phone number to validate
 * @returns {boolean} True if valid
 */
export function validatePhone(phone) {
  if (typeof phone !== 'string' || !phone) {
    return false;
  }

  // Remove common separators
  const cleaned = phone.replace(/[\s\-\(\)\.]/g, '');

  // Check if it's a valid phone number (10-15 digits, optional + prefix)
  const pattern = /^\+?[0-9]{10,15}$/;
  return pattern.test(cleaned);
}

/**
 * Validate date string
 * @param {string} dateString - Date string to validate
 * @returns {boolean} True if valid
 */
export function validateDate(dateString) {
  if (typeof dateString !== 'string' || !dateString) {
    return false;
  }

  const date = new Date(dateString);
  return !isNaN(date.getTime());
}

/**
 * Validate number within range
 * @param {number} value - Value to validate
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {Object} Validation result
 */
export function validateNumber(value, min = -Infinity, max = Infinity) {
  if (typeof value !== 'number' || isNaN(value)) {
    return {
      valid: false,
      message: 'Value must be a number'
    };
  }

  if (value < min) {
    return {
      valid: false,
      message: `Value must be at least ${min}`
    };
  }

  if (value > max) {
    return {
      valid: false,
      message: `Value must not exceed ${max}`
    };
  }

  return {
    valid: true,
    message: 'Number is valid'
  };
}

/**
 * Validate required field
 * @param {any} value - Value to validate
 * @returns {Object} Validation result
 */
export function validateRequired(value) {
  const isEmpty = value === null ||
                  value === undefined ||
                  value === '' ||
                  (Array.isArray(value) && value.length === 0) ||
                  (typeof value === 'object' && Object.keys(value).length === 0);

  return {
    valid: !isEmpty,
    message: isEmpty ? 'This field is required' : 'Field is valid'
  };
}

/**
 * Validate JSON string
 * @param {string} jsonString - JSON string to validate
 * @returns {Object} Validation result
 */
export function validateJson(jsonString) {
  if (typeof jsonString !== 'string' || !jsonString) {
    return {
      valid: false,
      message: 'Invalid JSON string'
    };
  }

  try {
    JSON.parse(jsonString);
    return {
      valid: true,
      message: 'Valid JSON'
    };
  } catch (error) {
    return {
      valid: false,
      message: `Invalid JSON: ${error.message}`
    };
  }
}

/**
 * Validate password strength
 * @param {string} password - Password to validate
 * @returns {Object} Validation result with strength score
 */
export function validatePassword(password) {
  if (typeof password !== 'string' || !password) {
    return {
      valid: false,
      strength: 0,
      message: 'Password is required'
    };
  }

  let strength = 0;
  const checks = {
    length: password.length >= 8,
    lowercase: /[a-z]/.test(password),
    uppercase: /[A-Z]/.test(password),
    numbers: /[0-9]/.test(password),
    special: /[^a-zA-Z0-9]/.test(password)
  };

  // Calculate strength
  Object.values(checks).forEach(passed => {
    if (passed) strength++;
  });

  const messages = {
    0: 'Very weak password',
    1: 'Weak password',
    2: 'Fair password',
    3: 'Good password',
    4: 'Strong password',
    5: 'Very strong password'
  };

  return {
    valid: strength >= 3,
    strength,
    checks,
    message: messages[strength]
  };
}

/**
 * Validate form data object
 * @param {Object} data - Form data to validate
 * @param {Object} rules - Validation rules
 * @returns {Object} Validation results
 */
export function validateForm(data, rules) {
  const errors = {};
  let isValid = true;

  Object.keys(rules).forEach(field => {
    const rule = rules[field];
    const value = data[field];

    if (rule.required) {
      const result = validateRequired(value);
      if (!result.valid) {
        errors[field] = result.message;
        isValid = false;
        return;
      }
    }

    if (rule.type === 'email' && value) {
      if (!validateEmail(value)) {
        errors[field] = 'Invalid email format';
        isValid = false;
      }
    }

    if (rule.type === 'url' && value) {
      if (!validateUrl(value)) {
        errors[field] = 'Invalid URL format';
        isValid = false;
      }
    }

    if (rule.type === 'tra_id' && value) {
      if (!validateTraId(value)) {
        errors[field] = 'Invalid TRA ID format';
        isValid = false;
      }
    }

    if (rule.minLength && value && value.length < rule.minLength) {
      errors[field] = `Minimum length is ${rule.minLength} characters`;
      isValid = false;
    }

    if (rule.maxLength && value && value.length > rule.maxLength) {
      errors[field] = `Maximum length is ${rule.maxLength} characters`;
      isValid = false;
    }

    if (rule.pattern && value && !rule.pattern.test(value)) {
      errors[field] = rule.patternMessage || 'Invalid format';
      isValid = false;
    }

    if (rule.custom && value) {
      const result = rule.custom(value);
      if (!result.valid) {
        errors[field] = result.message;
        isValid = false;
      }
    }
  });

  return {
    valid: isValid,
    errors
  };
}

// Export all validators
export default {
  validateTraId,
  validateEmail,
  validateUrl,
  validateFile,
  validateText,
  validatePhone,
  validateDate,
  validateNumber,
  validateRequired,
  validateJson,
  validatePassword,
  validateForm
};
