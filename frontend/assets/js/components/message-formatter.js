/**
 * Message Formatter Component
 * Handles formatting of messages for display in the chat interface
 * Breaks down the massive formatMessage function into modular, testable methods
 * @module components/message-formatter
 */

import { fixMalformedTags, sanitizeHtml } from '../utils/sanitizers.js';

/**
 * Message Formatter Class
 * Provides methods for formatting different types of messages and questions
 */
export class MessageFormatter {
  constructor() {
    this.questionCounter = 0;
  }

  /**
   * Main entry point for formatting messages
   * @param {string} content - Message content to format
   * @param {string} role - Message role (assistant, user, system)
   * @returns {string} Formatted HTML
   */
  formatMessage(content, role = 'assistant') {
    // Enhanced logging for debugging
    if (content.includes('< br>') || content.includes('<br >') || content.includes('&lt;br')) {
      console.warn('⚠️ MALFORMED BR TAG DETECTED IN CONTENT!');
      console.log('Full problematic content:', content);
    }

    // Skip question formatting for system messages
    if (role === 'system') {
      console.log('Detected system message, skipping question formatting');
      return this.formatSystemMessage(content);
    }

    // Clean up malformed HTML tags at the very start
    const originalContent = content;
    content = this.cleanMalformedTags(content);

    if (content !== originalContent) {
      console.log('🔧 Fixed malformed br tags!');
      console.log('Before:', originalContent);
      console.log('After:', content);
    }

    // First, detect and format AI suggestions
    let formatted = content;

    // Remove generic helper sentence globally
    formatted = formatted.replace(/(?:<br>|<br>)?\s*You can accept the suggestion, pick an option, or provide your own answer\.?(?:\s*(?:<br>|<br>))?/gi, '');

    // Check for risk area selection (checkboxes - must be before buttons check)
    if (this.isRiskAreaSelection(content)) {
      return this.formatRiskAreaSelection(content);
    }

    // Check for risk area buttons
    if (this.isRiskAreaButtons(content)) {
      return this.formatRiskAreaButtons(content);
    }

    // Check for editable review
    if (content.includes('[EDITABLE_REVIEW]')) {
      return this.formatEditableReview(content);
    }

    // Apply AI Analysis formatting
    formatted = this.formatAIAnalysis(formatted);

    // Clean up any malformed tags after AI box creation
    formatted = this.cleanMalformedTags(formatted);

    // Remove textual "Question X of Y" headers to avoid duplication
    formatted = formatted
      .replace(/\*\*Question\s+\d+\s+of\s+\d+\*\*:?\s*(?:<br>\s*)*/gi, '')
      .replace(/<strong>Question\s+\d+\s+of\s+\d+<\/strong>:?\s*(?:<br>\s*)*/gi, '')
      .replace(/(?:^|\n|<br>\s*)Question\s+\d+\s+of\s+\d+[:\s]*(?:<br>\s*)*/gi, '')
      .replace(/(?:^|\n|<br>\s*)Please\s+provide\s+your\s+answer:?\s*(?:<br>\s*)*/gi, '');

    // Check for Yes/No question
    if (this.isYesNoQuestion(content)) {
      return this.formatYesNoQuestion(content, formatted);
    }

    // Check for multiple choice question
    const isActualQuestion = content.match(/Question\s+\d+\s+of\s+\d+/i);
    if (this.isMultipleChoice(formatted) && isActualQuestion) {
      return this.formatMultipleChoice(formatted);
    }

    // Check for free text question
    if (this.isFreeTextQuestion(content, formatted, isActualQuestion)) {
      return this.formatFreeTextQuestion(content, formatted);
    }

    // Check for all risk areas completed message
    if (content.includes('You have completed all risk areas for this assessment')) {
      return this.formatCompletionMessage(content);
    }

    // Check for option buttons (A, B, C)
    if (this.isOptionButtons(content)) {
      return this.formatOptionButtons(content);
    }

    // Regular message formatting - remove markers before display
    formatted = this.removeQuestionTypeMarkers(formatted);
    return this.formatRegularMessage(formatted);
  }

  /**
   * Check if message contains risk area selection checkboxes
   * @param {string} content - Message content
   * @returns {boolean}
   */
  isRiskAreaSelection(content) {
    return content.match(/RISK_AREA_SELECTION:(.+?)(?:\n|$)/) !== null;
  }

  /**
   * Check if message contains risk area buttons
   * @param {string} content - Message content
   * @returns {boolean}
   */
  isRiskAreaButtons(content) {
    return content.match(/RISK_AREA_BUTTONS:(.+?)(?:\n|$)/) !== null;
  }

  /**
   * Check if message is a Yes/No question
   * @param {string} content - Message content
   * @returns {boolean}
   */
  isYesNoQuestion(content) {
    const hasPleasAnswerPattern = content.match(/Please answer:\s*Yes or No/i);
    const hasYesOption = content.match(/•\s*Yes\s*$/im);
    const hasNoOption = content.match(/•\s*No\s*$/im);
    const hasOptionsPattern = hasYesOption && hasNoOption && content.match(/Your options are:/i);

    return hasPleasAnswerPattern || hasOptionsPattern;
  }

  /**
   * Check if message contains multiple choice options
   * @param {string} formatted - Formatted message content
   * @returns {boolean}
   */
  isMultipleChoice(formatted) {
    return formatted.match(/Your options are:<br>•/i) || formatted.match(/Your options are:\n•/i);
  }

  /**
   * Check if message is a free text question
   * @param {string} content - Original message content
   * @param {string} formatted - Formatted message content
   * @param {boolean} isActualQuestion - Whether it has "Question X of Y"
   * @returns {boolean}
   */
  isFreeTextQuestion(content, formatted, isActualQuestion) {
    // Check for explicit question type marker from backend
    const questionTypeMatch = content.match(/\[QUESTION_TYPE:(text|textarea|select|multiselect)\]/);
    const backendQuestionType = questionTypeMatch ? questionTypeMatch[1] : null;

    // Check if this is a question with options
    const hasOptions = formatted.match(/Your options are:<br>•/i) || formatted.match(/Your options are:\n•/i);
    const hasRiskAreaOptions = content.match(/A\)\s+Upload documents.*B\)\s+Select from standard.*C\)\s+Answer AI questions/is);
    const hasPostQualifyingOptions = content.match(/A\)\s+Start answering questions.*B\)\s+Add more risk areas.*C\)\s+View assessment status/is);

    // Use backend marker if available, otherwise fall back to heuristics
    return backendQuestionType === 'text' || backendQuestionType === 'textarea' ||
           (!backendQuestionType && !hasOptions && !hasRiskAreaOptions && !hasPostQualifyingOptions &&
            (isActualQuestion || this.looksLikeAQuestion(content)));
  }

  /**
   * Remove backend question type markers from content
   * @param {string} content - Content with potential markers
   * @returns {string} Content with markers removed
   */
  removeQuestionTypeMarkers(content) {
    return content.replace(/\[QUESTION_TYPE:(text|textarea|select|multiselect)\]/gi, '');
  }

  /**
   * Check if message contains option buttons (A, B, C)
   * @param {string} content - Message content
   * @returns {boolean}
   */
  isOptionButtons(content) {
    const hasRiskAreaOptions = content.match(/A\)\s+Upload documents.*B\)\s+Select from standard.*C\)\s+Answer AI questions/is);
    const hasPostQualifyingOptions = content.match(/A\)\s+Start answering questions.*B\)\s+Add more risk areas.*C\)\s+View assessment status/is);
    return hasRiskAreaOptions || hasPostQualifyingOptions;
  }

  /**
   * Format system message (basic formatting only)
   * @param {string} content - Message content
   * @returns {string} Formatted HTML
   */
  formatSystemMessage(content) {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  /**
   * Format regular message (default formatting)
   * @param {string} formatted - Formatted message content
   * @returns {string} Formatted HTML
   */
  formatRegularMessage(formatted) {
    return formatted;
  }

  /**
   * Format risk area buttons
   * @param {string} content - Message content
   * @returns {string} Formatted HTML with buttons
   */
  formatRiskAreaButtons(content) {
    const riskAreaButtonMatch = content.match(/RISK_AREA_BUTTONS:(.+?)(?:\n|$)/);
    const riskAreas = riskAreaButtonMatch[1].split('|').map(ra => ra.trim());
    const introText = content.split('RISK_AREA_BUTTONS:')[0]
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    // Simple neutral icon for all risk areas
    const neutralIcon = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>';

    let buttonsHtml = `
      <div style="width: 100%;">
        <div style="margin-bottom: 16px;">${introText}</div>
        <div style="margin-bottom: 12px; font-size: 1rem; font-weight: 600; color: #111827;">Choose a risk area to start with:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
    `;

    riskAreas.forEach((riskArea) => {
      buttonsHtml += `
        <button onclick="window.populateInput('start answering ${riskArea}'); setTimeout(() => Alpine.\$data(document.querySelector('[x-data]')).sendMessage(), 100);"
                style="flex: 1 1 calc(50% - 5px); min-width: 200px; padding: 14px 16px; background: white; border: 2px solid #d1d5db; border-radius: 10px; cursor: pointer; text-align: left; font-size: 0.9rem; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);"
                onmouseover="this.style.borderColor='#6b7280'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 6px rgba(0, 0, 0, 0.1)'; this.style.background='#f9fafb'"
                onmouseout="this.style.borderColor='#d1d5db'; this.style.transform=''; this.style.boxShadow='0 1px 3px rgba(0, 0, 0, 0.05)'; this.style.background='white'">
          <div style="display: flex; align-items: center;">
            <div style="flex-shrink: 0; width: 32px; height: 32px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 16px; height: 16px; color: #6b7280;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${neutralIcon}
              </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 600; color: #111827; font-size: 0.95rem;">${riskArea}</div>
            </div>
          </div>
        </button>
      `;
    });

    buttonsHtml += `
        </div>
        <div style="margin-top: 14px; padding: 10px 14px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 6px; font-size: 0.85rem; color: #1e40af;">
          <strong>💡 Tip:</strong> Click a risk area above to start answering questions for that area
        </div>
      </div>
    `;

    return buttonsHtml;
  }

  /**
   * Format risk area selection with checkboxes (for manual selection before adding)
   * @param {string} content - Message content
   * @returns {string} Formatted HTML with checkboxes
   */
  formatRiskAreaSelection(content) {
    const riskAreaSelectionMatch = content.match(/RISK_AREA_SELECTION:(.+?)(?:\n|$)/);
    const riskAreas = riskAreaSelectionMatch[1].split('|').map(ra => ra.trim());
    const introText = content.split('RISK_AREA_SELECTION:')[0]
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    // Generate unique ID for this selection group
    const selectionId = 'risk-area-selection-' + Date.now();

    // Simple neutral icon for all risk areas
    const neutralIcon = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>';

    let buttonsHtml = `
      <div style="width: 100%;" id="${selectionId}">
        <div style="margin-bottom: 16px;">${introText}</div>
        <div style="margin-bottom: 12px; font-size: 1rem; font-weight: 600; color: #111827;">Select one or more risk areas:</div>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
    `;

    riskAreas.forEach((riskArea, index) => {
      const checkboxId = `${selectionId}-checkbox-${index}`;
      buttonsHtml += `
        <label for="${checkboxId}"
               class="risk-area-checkbox-label"
               style="flex: 1 1 calc(50% - 5px); min-width: 200px; padding: 14px 16px; background: white; border: 2px solid #d1d5db; border-radius: 10px; cursor: pointer; text-align: left; font-size: 0.9rem; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); display: block;"
               onmouseover="this.style.borderColor='#6b7280'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 6px rgba(0, 0, 0, 0.1)'; this.style.background='#f9fafb'"
               onmouseout="if (!this.querySelector('input').checked) { this.style.borderColor='#d1d5db'; this.style.transform=''; this.style.boxShadow='0 1px 3px rgba(0, 0, 0, 0.05)'; this.style.background='white'; }">
          <div style="display: flex; align-items: center;">
            <input type="checkbox"
                   id="${checkboxId}"
                   name="risk-area-selection"
                   value="${riskArea}"
                   style="width: 18px; height: 18px; margin-right: 12px; cursor: pointer; accent-color: #3b82f6;"
                   onchange="
                     const label = this.parentElement.parentElement;
                     if (this.checked) {
                       label.style.borderColor = '#3b82f6';
                       label.style.background = '#eff6ff';
                       label.style.borderWidth = '2px';
                     } else {
                       label.style.borderColor = '#d1d5db';
                       label.style.background = 'white';
                     }
                   ">
            <div style="flex-shrink: 0; width: 32px; height: 32px; background: #f3f4f6; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 16px; height: 16px; color: #6b7280;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${neutralIcon}
              </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 600; color: #111827; font-size: 0.95rem;">${riskArea}</div>
            </div>
          </div>
        </label>
      `;
    });

    buttonsHtml += `
        </div>
        <div style="margin-top: 16px;">
          <button onclick="
            const container = document.getElementById('${selectionId}');
            const checkboxes = container.querySelectorAll('input[name=\\'risk-area-selection\\']:checked');
            const selected = Array.from(checkboxes).map(cb => cb.value);
            if (selected.length === 0) {
              alert('Please select at least one risk area');
              return;
            }
            const message = selected.join(', ');
            window.populateInput(message);
            setTimeout(() => Alpine.\$data(document.querySelector('[x-data]')).sendMessage(), 100);
          "
          style="width: 100%; padding: 14px 20px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 10px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: all 0.2s; box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);"
          onmouseover="this.style.background='linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.4)'"
          onmouseout="this.style.background='linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'; this.style.transform=''; this.style.boxShadow='0 2px 6px rgba(59, 130, 246, 0.3)'">
            <svg style="width: 18px; height: 18px; display: inline; vertical-align: middle; margin-right: 8px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            Add Selected Risk Areas
          </button>
        </div>
        <div style="margin-top: 14px; padding: 10px 14px; background: #f0f9ff; border-left: 3px solid #3b82f6; border-radius: 6px; font-size: 0.85rem; color: #1e40af;">
          <strong>💡 Tip:</strong> Select multiple risk areas by checking the boxes, then click "Add Selected Risk Areas"
        </div>
      </div>
    `;

    return buttonsHtml;
  }

  /**
   * Format Yes/No question
   * @param {string} content - Original message content
   * @param {string} formatted - Formatted message content
   * @returns {string} Formatted HTML with Yes/No buttons
   */
  formatYesNoQuestion(content, formatted) {
    const hasPleasAnswerPattern = content.match(/Please answer:\s*Yes or No/i);
    const parts = hasPleasAnswerPattern ?
      formatted.split(/Please answer:\s*Yes or No/i) :
      formatted.split(/Your options are:/i);

    if (parts.length >= 1) {
      let questionPart = parts[0];

      // Remove duplicate "Question X of Y" text
      questionPart = questionPart.replace(/\*\*Question\s+\d+\s+of\s+\d+\*\*/gi, '');
      questionPart = questionPart.replace(/<strong>Question\s+\d+\s+of\s+\d+<\/strong>/gi, '');
      questionPart = questionPart.replace(/Question\s+\d+\s+of\s+\d+[:\s]*/gi, '');

      const progressBarHtml = this.extractProgressBar(content);

      let result = `<div class="question-container">
        ${progressBarHtml}
        <span class="question-type-badge question-type-multiple">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Yes/No
        </span>
        <div class="question-title">${questionPart}</div>
        <div style="display: flex; gap: 16px; justify-content: center; margin-top: 20px;">
          <button onclick="(function(){ const c = Alpine.\$data(document.querySelector('[x-data]')); c.currentMessage = 'Yes'; c.sendMessage(); })();"
                  style="min-width: 160px; padding: 14px 28px; background: #10b981; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2); transition: all 0.2s;"
                  onmouseover="this.style.background='#059669'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(16, 185, 129, 0.3)'"
                  onmouseout="this.style.background='#10b981'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(16, 185, 129, 0.2)'">
            <svg style="width: 16px; height: 16px; display: inline; margin-right: 8px; vertical-align: middle;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path>
            </svg>
            Yes
          </button>
          <button onclick="(function(){ const c = Alpine.\$data(document.querySelector('[x-data]')); c.currentMessage = 'No'; c.sendMessage(); })();"
                  style="min-width: 160px; padding: 14px 28px; background: #ef4444; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2); transition: all 0.2s;"
                  onmouseover="this.style.background='#dc2626'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(239, 68, 68, 0.3)'"
                  onmouseout="this.style.background='#ef4444'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(239, 68, 68, 0.2)'">
            <svg style="width: 16px; height: 16px; display: inline; margin-right: 8px; vertical-align: middle;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            No
          </button>
        </div>
        <p style="margin-top: 16px; font-size: 0.875rem; color: #9ca3af; text-align: center;">
          💡 <strong>Tip:</strong> Click Yes or No to automatically proceed to the next question
        </p>
      </div>`;

      return result;
    }

    return formatted;
  }

  /**
   * Format multiple choice question
   * @param {string} formatted - Formatted message content
   * @returns {string} Formatted HTML with options
   */
  formatMultipleChoice(formatted) {
    const parts = formatted.split(/Your options are:/i);
    if (parts.length === 2) {
      let questionPart = parts[0];
      let optionsPart = parts[1];

      // Remove duplicate "Question X of Y" text
      questionPart = questionPart.replace(/Question\s+\d+\s+of\s+\d+[:\s]*/gi, '');

      // Parse options
      const optionLines = optionsPart.split(/\n|<br>/gi).filter(line => line.trim().startsWith('•'));
      const options = optionLines.map(line => line.replace('•', '').trim()).filter(o => o);

      const progressBarHtml = this.extractProgressBar(formatted);

      let result = `<div class="question-container">
        ${progressBarHtml}
        <span class="question-type-badge question-type-multiple">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Multiple Choice
        </span>
        <div>${questionPart}</div>
        <div style="margin-top: 16px;">`;

      options.forEach((option, idx) => {
        result += `<div class="option-item">
          <span class="option-label" style="flex: 1; color: #374151;">${option}</span>
          <button onclick="window.populateInput('${option.replace(/'/g, "\\'")}')"
                  style="padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.75rem; margin-left: 8px; flex-shrink: 0;"
                  title="Copy to input">
            <svg style="width: 14px; height: 14px; display: inline;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </button>
        </div>`;
      });

      result += `</div>
        <p style="margin-top: 12px; font-size: 0.875rem; color: #6b7280;">
          <strong>Tip:</strong> Click an option above or type your answer below
        </p>
      </div>`;

      return result;
    }

    return formatted;
  }

  /**
   * Format free text question
   * @param {string} content - Original message content
   * @param {string} formatted - Formatted message content
   * @returns {string} Formatted HTML with text input
   */
  formatFreeTextQuestion(content, formatted) {
    // Extract AI suggested answer if available
    let aiSuggestedAnswer = '';
    const aiMatch = content.match(/💡 AI Suggestion:\s*(.+?)\s*\(Confidence:/i);
    if (aiMatch) {
      aiSuggestedAnswer = aiMatch[1].trim();
    }

    // Create unique ID for this text area
    const textAreaId = 'freetext_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Style the main question line
    let contentStyled = this.styleQuestionTitle(content, formatted);

    // Remove question type markers before display
    contentStyled = this.removeQuestionTypeMarkers(contentStyled);

    const progressBarHtml = this.extractProgressBar(content);

    // Wrap in question container with text badge and text input area
    return `<div class="question-container">
      ${progressBarHtml}
      <span class="question-type-badge question-type-text">
        <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
        </svg>
        Free Text
      </span>
      <div>${contentStyled}</div>

      <div style="margin-top: 10px; background: #f9fafb; padding: 12px; border-radius: 8px; border: 2px solid #e5e7eb;">
        <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 6px; font-size: 0.9rem;">
          <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
          </svg>
          Your Answer:
        </label>
        <textarea
          id="${textAreaId}"
          class="text-input-area"
          placeholder="Type your detailed answer here..."
          rows="1"
          style="width: 100%; min-height: 44px; padding: 10px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 0.95rem; resize: vertical; font-family: inherit;"
          onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';"
          onblur="this.style.borderColor='#d1d5db'; this.style.boxShadow='none';"
          onkeydown="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); window.submitFreeText('${textAreaId}'); }"
        ></textarea>
        <div style="margin-top: 8px; display: flex; gap: 8px; justify-content: flex-end;">
          ${aiSuggestedAnswer ? `<button onclick="document.getElementById('${textAreaId}').value='${aiSuggestedAnswer.replace(/'/g, "\\'")}'"
            style="padding: 8px 16px; background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 500;"
            onmouseover="this.style.background='#e5e7eb'"
            onmouseout="this.style.background='#f3f4f6'">
            <svg style="width: 14px; height: 14px; display: inline; margin-right: 4px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Use AI Suggestion
          </button>` : ''}
          <button onclick="window.submitFreeText('${textAreaId}')"
            style="padding: 8px 20px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600; box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);"
            onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 6px rgba(59, 130, 246, 0.4)'"
            onmouseout="this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(59, 130, 246, 0.3)'">
            <svg style="width: 14px; height: 14px; display: inline; margin-right: 4px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
            </svg>
            Submit Answer
          </button>
        </div>
        <p style="margin-top: 8px; font-size: 0.75rem; color: #6b7280; text-align: right;">
          💡 Tip: Press Enter to submit, or Shift+Enter for a new line
        </p>
      </div>
    </div>`;
  }

  /**
   * Format option buttons (A, B, C)
   * @param {string} content - Message content
   * @returns {string} Formatted HTML with option buttons
   */
  formatOptionButtons(content) {
    const hasRiskAreaOptions = content.match(/A\)\s+Upload documents.*B\)\s+Select from standard.*C\)\s+Answer AI questions/is);
    const hasPostQualifyingOptions = content.match(/A\)\s+Start answering questions.*B\)\s+Add more risk areas.*C\)\s+View assessment status/is);

    // Extract the intro text before options
    const splitPattern = hasPostQualifyingOptions ? /(?=A\)\s+Start answering questions)/i : /(?=A\)\s+Upload documents)/i;
    const parts = content.split(splitPattern);
    let introText = parts[0] || '';

    // Format intro text
    introText = introText
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    // Determine button labels based on which pattern matched
    // Order: A = Upload Documents, B = Answer Qualifying Questions, C = Select Risk Areas
    const buttonA = hasPostQualifyingOptions ?
      {
        label: 'Start Answering Questions',
        desc: 'Begin answering questions for identified risk areas',
        value: 'start questions',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>',
        bgColor: '#3b82f6',
        hoverColor: '#2563eb'
      } :
      {
        label: 'Upload Documents',
        desc: 'AI analyzes documents to recommend risk areas',
        value: 'A',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>',
        bgColor: '#10b981',
        hoverColor: '#059669'
      };
    const buttonB = hasPostQualifyingOptions ?
      {
        label: 'Add More Risk Areas',
        desc: 'Manually add additional risk areas',
        value: 'add more risk areas',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>',
        bgColor: '#8b5cf6',
        hoverColor: '#7c3aed'
      } :
      {
        label: 'Answer Qualifying Questions',
        desc: 'AI asks qualifying questions to identify areas',
        value: 'C',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path>',
        bgColor: '#ec4899',
        hoverColor: '#db2777'
      };
    const buttonC = hasPostQualifyingOptions ?
      {
        label: 'View Assessment Status',
        desc: 'See your assessment progress',
        value: 'status',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>',
        bgColor: '#06b6d4',
        hoverColor: '#0891b2'
      } :
      {
        label: 'Select from Standard Risk Areas',
        desc: 'Manual selection from predefined list',
        value: 'B',
        icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"></path>',
        bgColor: '#f59e0b',
        hoverColor: '#d97706'
      };

    // Button A handler: if post-qualifying, send message; otherwise open file dialog
    const buttonAOnclick = hasPostQualifyingOptions ?
      "window.populateInput('start questions'); setTimeout(() => Alpine.\$data(document.querySelector('[x-data]')).sendMessage(), 100);" :
      "Alpine.\$data(document.querySelector('[x-data]')).\$refs.fileInput.click();";

    return `
      <div>${introText}</div>
      <div style="margin-top: 20px; display: flex; flex-wrap: wrap; gap: 12px;">
        <button onclick="${buttonAOnclick}"
                class="option-button"
                style="flex: 1 1 calc(50% - 6px); min-width: 280px; padding: 16px 18px; background: white; border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; text-align: left; font-size: 0.95rem; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);"
                onmouseover="this.style.borderColor='${buttonA.bgColor}'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'"
                onmouseout="this.style.borderColor='#e5e7eb'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.05)'">
          <div style="display: flex; align-items: start;">
            <div style="flex-shrink: 0; width: 36px; height: 36px; background: ${buttonA.bgColor}; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 18px; height: 18px; color: white;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${buttonA.icon}
              </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 700; color: #111827; margin-bottom: 4px; font-size: 0.95rem;">${buttonA.label}</div>
              <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.4;">${buttonA.desc}</div>
            </div>
          </div>
        </button>

        <button onclick="window.populateInput('${buttonB.value}'); setTimeout(() => Alpine.\$data(document.querySelector('[x-data]')).sendMessage(), 100);"
                class="option-button"
                style="flex: 1 1 calc(50% - 6px); min-width: 280px; padding: 16px 18px; background: white; border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; text-align: left; font-size: 0.95rem; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);"
                onmouseover="this.style.borderColor='${buttonB.bgColor}'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'"
                onmouseout="this.style.borderColor='#e5e7eb'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.05)'">
          <div style="display: flex; align-items: start;">
            <div style="flex-shrink: 0; width: 36px; height: 36px; background: ${buttonB.bgColor}; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 18px; height: 18px; color: white;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${buttonB.icon}
              </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 700; color: #111827; margin-bottom: 4px; font-size: 0.95rem;">${buttonB.label}</div>
              <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.4;">${buttonB.desc}</div>
            </div>
          </div>
        </button>

        <button onclick="window.populateInput('${buttonC.value}'); setTimeout(() => Alpine.\$data(document.querySelector('[x-data]')).sendMessage(), 100);"
                class="option-button"
                style="flex: 1 1 calc(50% - 6px); min-width: 280px; padding: 16px 18px; background: white; border: 2px solid #e5e7eb; border-radius: 12px; cursor: pointer; text-align: left; font-size: 0.95rem; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);"
                onmouseover="this.style.borderColor='${buttonC.bgColor}'; this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(0, 0, 0, 0.1)'"
                onmouseout="this.style.borderColor='#e5e7eb'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.05)'">
          <div style="display: flex; align-items: start;">
            <div style="flex-shrink: 0; width: 36px; height: 36px; background: ${buttonC.bgColor}; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 18px; height: 18px; color: white;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${buttonC.icon}
              </svg>
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 700; color: #111827; margin-bottom: 4px; font-size: 0.95rem;">${buttonC.label}</div>
              <div style="font-size: 0.8rem; color: #6b7280; line-height: 1.4;">${buttonC.desc}</div>
            </div>
          </div>
        </button>
      </div>
      <div style="margin-top: 16px; padding: 12px 16px; background: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 8px; font-size: 0.875rem; color: #1e40af;">
        <strong>💡 Tip:</strong> Click any option above to proceed with that method
      </div>
    `;
  }

  /**
   * Convert URLs to clickable links
   * @param {string} text - Text with potential URLs
   * @returns {string} Text with clickable links
   */
  linkifyUrls(text) {
    // URL regex pattern - matches http://, https://, and www. URLs
    const urlPattern = /(https?:\/\/[^\s<]+|www\.[^\s<]+)/gi;

    return text.replace(urlPattern, (url) => {
      // Add http:// to www. URLs
      const href = url.startsWith('www.') ? 'http://' + url : url;

      // Return clickable link with styling
      return `<a href="${href}" target="_blank" rel="noopener noreferrer" style="color: #3b82f6; text-decoration: underline; font-weight: 500; cursor: pointer;" onmouseover="this.style.color='#2563eb'" onmouseout="this.style.color='#3b82f6'">${url}</a>`;
    });
  }

  /**
   * Format AI analysis box
   * @param {string} content - Message content
   * @returns {string} Formatted HTML
   */
  formatAIAnalysis(content) {
    // Step 1: Basic formatting
    let formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');

    // Step 1.5: Convert URLs to clickable links
    formatted = this.linkifyUrls(formatted);

    // Simple styling for assessment creation message
    if (formatted.includes('Assessment Created Successfully')) {
      // Just make the text bold and slightly larger
      formatted = formatted.replace(
        /✅\s*Assessment Created Successfully!/g,
        '<strong style="font-size: 1.1em; color: #10b981;">✅ Assessment Created Successfully!</strong>'
      );

      formatted = formatted.replace(
        /(📋\s*TRA Number:)/g,
        '<strong>$1</strong>'
      );

      formatted = formatted.replace(
        /(📁\s*Project Name:)/g,
        '<strong>$1</strong>'
      );

      formatted = formatted.replace(
        /(🏢\s*Business Unit:)/g,
        '<strong>$1</strong>'
      );
    }

    // Step 2: Handle "No confident AI suggestion" case
    formatted = formatted.replace(
      /No confident AI suggestion found for this question\.(?:\s*<br>\s*|\s*< br>\s*|\s*<br >\s*)*(?=\S|$)/gi,
      '<div class="ai-suggestion-box" style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); border-color: #9ca3af;">' +
        '<div class="ai-suggestion-header" style="color: #6b7280;">' +
          '<svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>' +
          '</svg>' +
          'AI Analysis' +
        '</div>' +
        '<div class="ai-suggestion-content" style="color: #4b5563;">' +
          'No confident AI suggestion found for this question. Please review the available options or provide your own answer based on your system architecture.' +
        '</div>' +
      '</div><br>'
    );

    // Step 3: Handle AI suggestions with confidence
    formatted = formatted.replace(
      /💡 AI Suggestion:\s*(.+?)\s*\(Confidence:\s*(\w+)\)(?:\s*<br>\s*)*(?:\s*<br>\s*)*/gi,
      (match, answer, confidence) => {
        const confLower = confidence.toLowerCase();
        const confClass = confLower === 'high' ? 'confidence-high' :
                        confLower === 'medium' ? 'confidence-medium' :
                        'confidence-low';

        return `<div class="ai-suggestion-box">
          <div class="ai-suggestion-header">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            AI Suggestion
            <span class="ai-confidence ${confClass}">${confidence}</span>
          </div>
          <div class="ai-suggestion-answer">${answer}</div>
        </div><br>`;
      }
    );

    return formatted;
  }

  /**
   * Clean malformed HTML tags
   * @param {string} html - HTML with potential malformed tags
   * @returns {string} Cleaned HTML
   */
  cleanMalformedTags(html) {
    return html
      .replace(/&lt;(\s*)br(\s*)&gt;/gi, '<br>')
      .replace(/<(\s*)br(\s*)>/gi, '<br>')
      .replace(/\n(\s*)<(\s*)br(\s*)>/gi, '\n<br>')
      .replace(/\s+<(\s+)br>/gi, ' <br>');
  }

  /**
   * Extract progress bar HTML from content
   * @param {string} content - Message content
   * @returns {string} Progress bar HTML
   */
  extractProgressBar(content) {
    const progressMatch = content.match(/Question\s+(\d+)\s+of\s+(\d+)/i);
    if (progressMatch) {
      const current = parseInt(progressMatch[1]);
      const total = parseInt(progressMatch[2]);
      const percentage = Math.round((current / total) * 100);

      return `
        <div class="progress-container">
          <div class="progress-info">Question ${current} of ${total}</div>
          <div class="progress-bar-track">
            <div class="progress-bar-fill" style="width: ${percentage}%"></div>
          </div>
          <div class="progress-percentage">${percentage}%</div>
        </div>
      `;
    }
    return '';
  }

  /**
   * Format completion message
   * @param {string} content - Message content
   * @returns {string} Formatted HTML
   */
  formatCompletionMessage(content) {
    // Parse the completion message into sections
    const lines = content.split('\n').filter(line => line.trim());

    let header = '';
    let subheader = '';
    let nextSteps = [];
    let note = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Find main header (contains "You have completed all risk areas")
      if (line.includes('You have completed all risk areas')) {
        header = line.replace(/🎉\s*/, '').replace(/\*\*/g, '');
      }
      // Find subheader (first line before "Next Steps")
      else if (line.includes('All questions for') && line.includes('are complete')) {
        subheader = line.replace(/✅\s*/, '');
      }
      // Find next steps items (lines starting with •)
      else if (line.startsWith('•')) {
        nextSteps.push(line.substring(1).trim());
      }
      // Find note section
      else if (line.includes('Note:') || line.includes('Finalizing will change')) {
        note += line.replace(/\*\*Note:\*\*/, '<strong>Note:</strong>').replace(/\*\*/g, '') + ' ';
      }
    }

    return `
      <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 2px solid #10b981; border-radius: 16px; padding: 24px; margin: 16px 0; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);">
        <!-- Party icon and header -->
        <div style="text-align: center; margin-bottom: 20px;">
          <div style="font-size: 48px; margin-bottom: 8px;">🎉</div>
          <h3 style="font-size: 1.25rem; font-weight: 700; color: #065f46; margin: 0;">
            ${header || 'Assessment Complete!'}
          </h3>
          ${subheader ? `<p style="color: #047857; margin-top: 8px; font-size: 0.95rem;">${subheader}</p>` : ''}
        </div>

        <!-- Divider -->
        <div style="height: 2px; background: linear-gradient(90deg, transparent, #10b981, transparent); margin: 20px 0;"></div>

        <!-- Next Steps Section -->
        ${nextSteps.length > 0 ? `
          <div style="margin-bottom: 20px;">
            <h4 style="font-size: 1rem; font-weight: 600; color: #065f46; margin-bottom: 12px; display: flex; align-items: center;">
              <svg style="width: 20px; height: 20px; margin-right: 8px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
              Next Steps:
            </h4>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
              ${nextSteps.map((step, idx) => {
                // Determine the command and button text based on the step content
                let command = '';
                let buttonText = '';
                // Check for finalize FIRST before review (more specific)
                if (step.toLowerCase().includes('finalize assessment') || step.toLowerCase().includes('finalize')) {
                  command = 'finalize assessment';
                  buttonText = 'Finalize the current assessment';
                } else if (step.toLowerCase().includes('review my answers') || step.toLowerCase().includes('see all your responses')) {
                  command = 'review my answers';
                  buttonText = 'Review the Answers';
                } else {
                  buttonText = step;
                  command = step.toLowerCase();
                }

                return `
                  <button onclick="window.populateInput('${command}'); setTimeout(() => Alpine.$data(document.querySelector('[x-data]')).sendMessage(), 100);"
                          style="flex: 1 1 calc(50% - 5px); min-width: 200px; padding: 14px 16px; background: white; border: 2px solid #10b981; border-radius: 10px; cursor: pointer; text-align: left; font-size: 0.9rem; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);"
                          onmouseover="this.style.borderColor='#059669'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 6px rgba(16, 185, 129, 0.2)'; this.style.background='#f0fdf4'"
                          onmouseout="this.style.borderColor='#10b981'; this.style.transform=''; this.style.boxShadow='0 1px 3px rgba(0, 0, 0, 0.05)'; this.style.background='white'">
                    <div style="display: flex; align-items: center;">
                      <div style="flex-shrink: 0; width: 32px; height: 32px; background: #d1fae5; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                        <div style="width: 24px; height: 24px; background: #10b981; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.85rem;">
                          ${idx + 1}
                        </div>
                      </div>
                      <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; color: #111827; font-size: 0.95rem;">${buttonText}</div>
                      </div>
                    </div>
                  </button>
                `;
              }).join('')}
            </div>
          </div>
        ` : ''}

        <!-- Note Section -->
        ${note ? `
          <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px 16px; display: flex; align-items-start;">
            <svg style="width: 20px; height: 20px; color: #f59e0b; margin-right: 12px; flex-shrink: 0; margin-top: 2px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <div style="color: #92400e; font-size: 0.9rem; line-height: 1.5;">
              ${note}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  /**
   * Format editable review with form inputs for each Q&A
   * @param {string} content - Message content with [EDITABLE_REVIEW] marker
   * @returns {string} Formatted HTML with editable form
   */
  formatEditableReview(content) {
    // Remove the marker
    let cleanContent = content.replace('[EDITABLE_REVIEW]', '').trim();

    // Extract assessment ID
    const traIdMatch = cleanContent.match(/TRA-\d{4}-[A-Z0-9]+/);
    const assessmentId = traIdMatch ? traIdMatch[0] : '';

    // Parse Q&A pairs
    const qaPairs = this.parseQAPairs(cleanContent);

    if (qaPairs.length === 0) {
      // Fallback to regular formatting if parsing fails
      return this.formatRegularMessage(cleanContent);
    }

    // Extract header information
    const projectMatch = cleanContent.match(/\*\*Project:\*\*\s*(.+)/);
    const progressMatch = cleanContent.match(/\*\*Overall Progress:\*\*\s*(.+)/);
    const statusMatch = cleanContent.match(/\*\*Status:\*\*\s*(.+)/);

    const projectName = projectMatch ? projectMatch[1].trim() : '';
    const progress = progressMatch ? progressMatch[1].trim() : '';
    const status = statusMatch ? statusMatch[1].trim() : '';

    // Group Q&A by risk area
    const riskAreas = {};
    let currentRiskArea = '';

    for (const qa of qaPairs) {
      if (qa.riskArea) {
        currentRiskArea = qa.riskArea;
        if (!riskAreas[currentRiskArea]) {
          riskAreas[currentRiskArea] = { name: qa.riskAreaName, pairs: [] };
        }
      }
      if (currentRiskArea) {
        riskAreas[currentRiskArea].pairs.push(qa);
      }
    }

    // Generate unique form ID
    const formId = `editable-review-form-${Date.now()}`;

    // Build HTML
    let html = `
      <div style="background: #f9fafb; border: 2px solid #3b82f6; border-radius: 16px; padding: 24px; margin: 16px 0;">
        <!-- Header -->
        <div style="margin-bottom: 20px;">
          <h3 style="font-size: 1.25rem; font-weight: 700; color: #1e40af; margin: 0 0 8px 0;">
            Assessment Review: ${assessmentId}
          </h3>
          ${projectName ? `<p style="color: #6b7280; margin: 4px 0;"><strong>Project:</strong> ${projectName}</p>` : ''}
          ${progress ? `<p style="color: #6b7280; margin: 4px 0;"><strong>Overall Progress:</strong> ${progress}</p>` : ''}
        </div>

        <!-- Divider -->
        <div style="height: 2px; background: linear-gradient(90deg, transparent, #3b82f6, transparent); margin: 20px 0;"></div>

        <form id="${formId}">
    `;

    // Render each risk area
    for (const [riskAreaId, riskAreaData] of Object.entries(riskAreas)) {
      html += `
        <div style="margin-bottom: 24px;">
          <h4 style="font-size: 1.1rem; font-weight: 600; color: #1e40af; margin-bottom: 16px;">
            ${riskAreaData.name}
          </h4>
      `;

      // Render each Q&A pair
      for (const qa of riskAreaData.pairs) {
        const textareaId = `answer-${qa.questionId}-${Date.now()}`;
        html += `
          <div style="background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
            <!-- Question -->
            <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 8px;">
              <span style="color: #3b82f6;">${qa.questionId}:</span> ${qa.question}
            </label>

            <!-- Answer Input -->
            <textarea
              id="${textareaId}"
              name="${qa.questionId}"
              data-risk-area="${riskAreaId}"
              style="width: 100%; min-height: 60px; padding: 10px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 0.95rem; resize: vertical; font-family: inherit;"
              onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';"
              onblur="this.style.borderColor='#d1d5db'; this.style.boxShadow='none';"
            >${this.escapeHtml(qa.answer)}</textarea>
          </div>
        `;
      }

      html += `</div>`;
    }

    // Submit button
    html += `
          <div style="margin-top: 24px; display: flex; gap: 12px; justify-content: flex-end;">
            <button type="button"
                    onclick="window.submitEditableReview('${formId}', '${assessmentId}')"
                    style="padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: all 0.2s;"
                    onmouseover="this.style.background='#2563eb'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 12px rgba(59, 130, 246, 0.3)'"
                    onmouseout="this.style.background='#3b82f6'; this.style.transform=''; this.style.boxShadow='none'">
              📝 Update Answers
            </button>
          </div>
        </form>

        ${status ? `
          <div style="margin-top: 20px; padding: 12px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px;">
            <strong style="color: #92400e;">Status:</strong> <span style="color: #78350f;">${status}</span>
          </div>
        ` : ''}
      </div>
    `;

    return html;
  }

  /**
   * Parse Q&A pairs from review content
   * @param {string} content - Review content
   * @returns {Array} Array of {questionId, question, answer, riskArea, riskAreaName}
   */
  parseQAPairs(content) {
    const pairs = [];
    const lines = content.split('\n');

    let currentRiskArea = '';
    let currentRiskAreaName = '';
    let currentQuestion = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Match risk area header (e.g., "**Data Privacy Risk:** 8/8 questions answered")
      const riskAreaMatch = line.match(/\*\*(.+?Risk):\*\*\s*\d+\/\d+\s*questions?\s*answered/i);
      if (riskAreaMatch) {
        currentRiskAreaName = riskAreaMatch[1].trim();
        // Convert name to ID (e.g., "Data Privacy Risk" -> "data_privacy")
        currentRiskArea = currentRiskAreaName
          .toLowerCase()
          .replace(/\s+risk$/i, '')
          .replace(/\s+/g, '_');
        continue;
      }

      // Match question line (e.g., "• **Q (DP-01):** Question text..." or "• **Q (C8 Q 3.01):** Question text...")
      // Pattern matches both simple (AI-04, IP-01) and complex (C8 Q 3.01, D1 Q 4.01) formats
      const questionMatch = line.match(/^[•·]\s*\*\*Q\s*\(([A-Z0-9 Q.-]+)\):\*\*\s*(.+)$/i);
      if (questionMatch) {
        if (currentQuestion) {
          // Save previous question before starting new one
          pairs.push(currentQuestion);
        }
        currentQuestion = {
          questionId: questionMatch[1],
          question: questionMatch[2].trim(),
          answer: '',
          riskArea: currentRiskArea,
          riskAreaName: currentRiskAreaName
        };
        continue;
      }

      // Match answer line (e.g., "  **A:** Answer text")
      const answerMatch = line.match(/^\s*\*\*A:\*\*\s*(.+)$/i);
      if (answerMatch && currentQuestion) {
        currentQuestion.answer = answerMatch[1].trim();
        // Save the completed Q&A pair
        pairs.push(currentQuestion);
        currentQuestion = null;
        continue;
      }
    }

    // Save last question if exists
    if (currentQuestion) {
      pairs.push(currentQuestion);
    }

    return pairs;
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Style question title for better visibility
   * @param {string} content - Original content
   * @param {string} formatted - Formatted content
   * @returns {string} Styled content
   */
  styleQuestionTitle(content, formatted) {
    let contentStyled = formatted;
    try {
      // Identify a candidate question line
      const prunedContent = content.replace(/^\s*Please\s+provide\s+your\s+answer:?\s*$/gmi, '');
      const plainLines = prunedContent.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      const phraseList = [
        'please provide','provide a brief','brief summary','summary','summarize','summarise',
        'please describe','provide details','briefly explain','describe','your own answer',
        'select','choose'
      ];
      let candidate = plainLines.slice().reverse().find(l => /[?:]\s*$/.test(l))
                     || plainLines.find(l => phraseList.some(p => l.toLowerCase().includes(p)))
                     || '';

      if (candidate && !contentStyled.includes('<div class="question-title">')) {
        const esc = candidate.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let applied = false;

        // Case A: candidate is between <br> ... <br>
        contentStyled = contentStyled.replace(new RegExp(`(<br>\\s*)(${esc})(\\s*<br>)`, 'i'),
          (m, pre, mid, post) => { applied = true; return `${pre}<div class="question-title">${mid}</div>${post}`; });

        // Case B: candidate at start followed by <br> or end
        if (!applied) {
          contentStyled = contentStyled.replace(new RegExp(`^\\s*(${esc})(\\s*(?:<br>|$))`, 'i'),
            (m, mid, post) => { applied = true; return `<div class="question-title">${mid}</div>${post}`; });
        }

        // Case C: candidate right after AI Analysis box
        if (!applied) {
          contentStyled = contentStyled.replace(new RegExp(`(ai-suggestion-(?:box|content)">.*?</div>\\s*</div>\\s*)(?:<br>\\s*)*(${esc})(\\s*(?:<br>|$))`, 'is'),
            (m, close, mid, post) => { applied = true; return `${close}<div class="question-title">${mid}</div>${post}`; });
        }

        // Case D: candidate before next block <div> or end
        if (!applied) {
          contentStyled = contentStyled.replace(new RegExp(`(${esc})(\\s*)(?=<div|$)`, 'i'),
            (m, mid, space) => { applied = true; return `<div class="question-title">${mid}</div>${space}`; });
        }

        // Case E: final fallback
        if (!applied && !contentStyled.includes('<div class="question-title">')) {
          contentStyled = contentStyled.replace(/([^<][^<]*?)(\s*(?:<br>\s*)*)$/i, '<div class="question-title">$1</div>$2');
        }
      }
    } catch (e) {
      console.error('Error styling question title:', e);
      contentStyled = formatted;
    }

    return contentStyled;
  }

  /**
   * Heuristic to detect if content looks like a question
   * @param {string} text - Text to analyze
   * @returns {boolean}
   */
  looksLikeAQuestion(text) {
    const t = (text || '').toLowerCase();
    const lines = t.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
    const last = lines[lines.length - 1] || '';

    // EXCLUDE system messages
    const systemMessagePatterns = [
      /uploaded successfully/i,
      /upload failed/i,
      /saved to dynamodb/i,
      /ready for analysis/i,
      /ai summary generated/i,
      /topics:/i,
      /uploading/i,
      /processing/i,
      /✅|❌|⬆|💾|🤖|🏷️/,
      /assessment created/i,
      /session.*created/i,
      /status:/i
    ];

    if (systemMessagePatterns.some(pattern => pattern.test(text))) {
      return false;
    }

    // Heuristic phrases
    const phrases = [
      'please describe',
      'provide details',
      'enter your answer',
      'briefly explain',
      'give details',
      'add your explanation',
      'explain your answer',
      'please provide',
      'provide a brief',
      'brief summary',
      'provide your answer',
      'your own answer',
      'required information'
    ];

    const lastEndsWithQuestion = /[?]\s*$/.test(last);
    const hasPromptColon = lines.some(line => /:\s*$/.test(line) && phrases.some(p => line.toLowerCase().includes(p)));
    const containsQuestionPhrase = phrases.some(p => t.includes(p));
    const hasListItems = /^[\s]*[-•]\s+/m.test(text);
    const isSimpleFieldQuestion = lines.length >= 1 && lines.length <= 3 &&
                                  /\b(name|email|address|contact|phone|number|date|location|title|description|url|id)\b/i.test(last);

    return lastEndsWithQuestion ||
           (containsQuestionPhrase && (hasPromptColon || hasListItems)) ||
           isSimpleFieldQuestion;
  }
}

// Export singleton instance
export default new MessageFormatter();
