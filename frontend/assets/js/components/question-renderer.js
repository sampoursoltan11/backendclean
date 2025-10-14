/**
 * Question Renderer Component
 * Specialized rendering for different question types
 * @module components/question-renderer
 */

/**
 * Question Renderer Class
 * Provides methods for rendering specific question types
 */
export class QuestionRenderer {
  constructor() {
    this.renderedQuestions = new Set();
  }

  /**
   * Render Yes/No question with buttons
   * @param {Object} questionData - Question data
   * @returns {string} HTML for Yes/No question
   */
  renderYesNo(questionData) {
    const { question, progress, aiSuggestion } = questionData;

    return `
      <div class="question-container">
        ${this.renderProgressBar(progress)}
        <span class="question-type-badge question-type-multiple">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Yes/No
        </span>
        <div class="question-title">${question}</div>
        ${aiSuggestion ? this.renderAISuggestion(aiSuggestion) : ''}
        <div style="display: flex; gap: 16px; justify-content: center; margin-top: 20px;">
          ${this.renderYesNoButtons()}
        </div>
        <p style="margin-top: 16px; font-size: 0.875rem; color: #9ca3af; text-align: center;">
          💡 <strong>Tip:</strong> Click Yes or No to automatically proceed to the next question
        </p>
      </div>
    `;
  }

  /**
   * Render multiple choice question with options
   * @param {Object} questionData - Question data
   * @returns {string} HTML for multiple choice question
   */
  renderMultipleChoice(questionData) {
    const { question, options, progress, aiSuggestion } = questionData;

    return `
      <div class="question-container">
        ${this.renderProgressBar(progress)}
        <span class="question-type-badge question-type-multiple">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          Multiple Choice
        </span>
        <div class="question-title">${question}</div>
        ${aiSuggestion ? this.renderAISuggestion(aiSuggestion) : ''}
        <div style="margin-top: 16px;">
          ${options.map(option => this.renderOption(option)).join('')}
        </div>
        <p style="margin-top: 12px; font-size: 0.875rem; color: #6b7280;">
          <strong>Tip:</strong> Click an option above or type your answer below
        </p>
      </div>
    `;
  }

  /**
   * Render free text question with textarea
   * @param {Object} questionData - Question data
   * @returns {string} HTML for free text question
   */
  renderFreeText(questionData) {
    const { question, progress, aiSuggestion, placeholder = 'Type your detailed answer here...' } = questionData;
    const textAreaId = 'freetext_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    return `
      <div class="question-container">
        ${this.renderProgressBar(progress)}
        <span class="question-type-badge question-type-text">
          <svg class="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
          </svg>
          Free Text
        </span>
        <div class="question-title">${question}</div>
        ${aiSuggestion ? this.renderAISuggestion(aiSuggestion) : ''}

        <div style="margin-top: 16px; background: #f9fafb; padding: 16px; border-radius: 8px; border: 2px solid #e5e7eb;">
          <label style="display: block; font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 0.9rem;">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
            </svg>
            Your Answer:
          </label>
          ${this.renderTextArea(textAreaId, placeholder)}
          ${this.renderTextAreaActions(textAreaId, aiSuggestion)}
          <p style="margin-top: 8px; font-size: 0.75rem; color: #6b7280; text-align: right;">
            💡 Tip: Press Enter to submit, or Shift+Enter for a new line
          </p>
        </div>
      </div>
    `;
  }

  /**
   * Extract question data from content
   * @param {string} content - Message content
   * @param {string} type - Question type (yesno, multiple, freetext)
   * @returns {Object} Question data
   */
  extractQuestionData(content, type) {
    const data = {
      question: '',
      options: [],
      progress: this.extractProgress(content),
      aiSuggestion: this.extractAISuggestion(content),
      type
    };

    // Extract question text
    if (type === 'yesno') {
      const match = content.match(/(.+?)(?:Please answer:\s*Yes or No|Your options are:)/is);
      if (match) {
        data.question = match[1].trim()
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br>');
      }
    } else if (type === 'multiple') {
      const match = content.match(/(.+?)Your options are:/is);
      if (match) {
        data.question = match[1].trim()
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br>');
        data.options = this.extractOptions(content);
      }
    } else if (type === 'freetext') {
      data.question = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    }

    return data;
  }

  /**
   * Extract options from multiple choice content
   * @param {string} content - Message content
   * @returns {Array<string>} Array of options
   */
  extractOptions(content) {
    const match = content.match(/Your options are:(.+?)$/is);
    if (!match) return [];

    const optionsText = match[1];
    const optionLines = optionsText.split(/\n/).filter(line => line.trim().startsWith('•'));

    return optionLines
      .map(line => line.replace('•', '').trim())
      .filter(o => o);
  }

  /**
   * Extract progress information
   * @param {string} content - Message content
   * @returns {Object|null} Progress data or null
   */
  extractProgress(content) {
    const match = content.match(/Question\s+(\d+)\s+of\s+(\d+)/i);
    if (match) {
      return {
        current: parseInt(match[1]),
        total: parseInt(match[2]),
        percentage: Math.round((parseInt(match[1]) / parseInt(match[2])) * 100)
      };
    }
    return null;
  }

  /**
   * Extract AI suggestion from content
   * @param {string} content - Message content
   * @returns {Object|null} AI suggestion data or null
   */
  extractAISuggestion(content) {
    const match = content.match(/💡 AI Suggestion:\s*(.+?)\s*\(Confidence:\s*(\w+)\)/i);
    if (match) {
      return {
        answer: match[1].trim(),
        confidence: match[2].toLowerCase()
      };
    }

    if (content.includes('No confident AI suggestion')) {
      return {
        answer: null,
        confidence: 'none',
        message: 'No confident AI suggestion found for this question.'
      };
    }

    return null;
  }

  /**
   * Render progress bar
   * @param {Object|null} progress - Progress data
   * @returns {string} Progress bar HTML
   */
  renderProgressBar(progress) {
    if (!progress) return '';

    return `
      <div class="progress-container">
        <div class="progress-info">Question ${progress.current} of ${progress.total}</div>
        <div class="progress-bar-track">
          <div class="progress-bar-fill" style="width: ${progress.percentage}%"></div>
        </div>
        <div class="progress-percentage">${progress.percentage}%</div>
      </div>
    `;
  }

  /**
   * Render AI suggestion box
   * @param {Object} suggestion - AI suggestion data
   * @returns {string} AI suggestion HTML
   */
  renderAISuggestion(suggestion) {
    if (!suggestion) return '';

    if (!suggestion.answer) {
      return `
        <div class="ai-suggestion-box" style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); border-color: #9ca3af;">
          <div class="ai-suggestion-header" style="color: #6b7280;">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            AI Analysis
          </div>
          <div class="ai-suggestion-content" style="color: #4b5563;">
            ${suggestion.message || 'No confident AI suggestion found for this question.'}
          </div>
        </div>
      `;
    }

    const confClass = suggestion.confidence === 'high' ? 'confidence-high' :
                     suggestion.confidence === 'medium' ? 'confidence-medium' :
                     'confidence-low';

    return `
      <div class="ai-suggestion-box">
        <div class="ai-suggestion-header">
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
          AI Suggestion
          <span class="ai-confidence ${confClass}">${suggestion.confidence}</span>
        </div>
        <div class="ai-suggestion-answer">${suggestion.answer}</div>
      </div>
    `;
  }

  /**
   * Render Yes/No buttons
   * @returns {string} Buttons HTML
   */
  renderYesNoButtons() {
    return `
      <button onclick="(function(){ const c = Alpine.\$data(document.querySelector('[x-data]')); c.currentMessage = 'Yes'; c.sendMessage(); })();"
              style="min-width: 160px; padding: 14px 28px; background: #6b7280; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); transition: all 0.2s;"
              onmouseover="this.style.background='#4b5563'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(0, 0, 0, 0.15)'"
              onmouseout="this.style.background='#6b7280'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.1)'">
        <svg style="width: 16px; height: 16px; display: inline; margin-right: 8px; vertical-align: middle;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"></path>
        </svg>
        Yes
      </button>
      <button onclick="(function(){ const c = Alpine.\$data(document.querySelector('[x-data]')); c.currentMessage = 'No'; c.sendMessage(); })();"
              style="min-width: 160px; padding: 14px 28px; background: #6b7280; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); transition: all 0.2s;"
              onmouseover="this.style.background='#4b5563'; this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 8px rgba(0, 0, 0, 0.15)'"
              onmouseout="this.style.background='#6b7280'; this.style.transform=''; this.style.boxShadow='0 2px 4px rgba(0, 0, 0, 0.1)'">
        <svg style="width: 16px; height: 16px; display: inline; margin-right: 8px; vertical-align: middle;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
        No
      </button>
    `;
  }

  /**
   * Render a single option
   * @param {string} option - Option text
   * @returns {string} Option HTML
   */
  renderOption(option) {
    const escapedOption = option.replace(/'/g, "\\'");
    return `
      <div class="option-item">
        <span class="option-label" style="flex: 1; color: #374151;">${option}</span>
        <button onclick="window.populateInput('${escapedOption}')"
                style="padding: 6px 12px; background: #3b82f6; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.75rem; margin-left: 8px; flex-shrink: 0;"
                title="Copy to input">
          <svg style="width: 14px; height: 14px; display: inline;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
          </svg>
        </button>
      </div>
    `;
  }

  /**
   * Render text area for free text input
   * @param {string} id - Textarea ID
   * @param {string} placeholder - Placeholder text
   * @returns {string} Textarea HTML
   */
  renderTextArea(id, placeholder) {
    return `
      <textarea
        id="${id}"
        class="text-input-area"
        placeholder="${placeholder}"
        rows="1"
        style="width: 100%; min-height: 44px; padding: 12px; border: 2px solid #d1d5db; border-radius: 8px; font-size: 0.95rem; resize: vertical; font-family: inherit;"
        onfocus="this.style.borderColor='#3b82f6'; this.style.boxShadow='0 0 0 3px rgba(59, 130, 246, 0.1)';"
        onblur="this.style.borderColor='#d1d5db'; this.style.boxShadow='none';"
        onkeydown="if(event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); window.submitFreeText('${id}'); }"
      ></textarea>
    `;
  }

  /**
   * Render text area action buttons
   * @param {string} textAreaId - Textarea ID
   * @param {Object|null} aiSuggestion - AI suggestion data
   * @returns {string} Actions HTML
   */
  renderTextAreaActions(textAreaId, aiSuggestion) {
    const useSuggestionBtn = aiSuggestion && aiSuggestion.answer ? `
      <button onclick="document.getElementById('${textAreaId}').value='${aiSuggestion.answer.replace(/'/g, "\\'")}')"
        style="padding: 8px 16px; background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 500;"
        onmouseover="this.style.background='#e5e7eb'"
        onmouseout="this.style.background='#f3f4f6'">
        <svg style="width: 14px; height: 14px; display: inline; margin-right: 4px;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        Use AI Suggestion
      </button>
    ` : '';

    return `
      <div style="margin-top: 12px; display: flex; gap: 8px; justify-content: flex-end;">
        ${useSuggestionBtn}
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
    `;
  }
}

// Export singleton instance
export default new QuestionRenderer();
