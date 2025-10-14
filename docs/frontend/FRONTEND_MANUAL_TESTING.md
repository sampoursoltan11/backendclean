# Frontend Manual Testing Guide

**Quick Start Guide for Testing the Enterprise TRA Frontend**

---

## Prerequisites

Before you begin testing, ensure:
- ✅ Backend server is running: `./scripts/run_backend.sh`
- ✅ Frontend dev server is running: `cd frontend && npm run dev`
- ✅ Browser is open: [http://localhost:5173/enterprise_tra_home_clean.html](http://localhost:5173/enterprise_tra_home_clean.html)

---

## 1. Initial Load Test (2 minutes)

### Steps:
1. Open [http://localhost:5173/enterprise_tra_home_clean.html](http://localhost:5173/enterprise_tra_home_clean.html)
2. Open browser DevTools (F12)
3. Check Console tab for errors

### Expected Results:
- ✅ Page loads without errors
- ✅ Connection indicator shows green "Connected"
- ✅ Session ID appears in left sidebar
- ✅ Welcome message displays in chat area
- ✅ Console shows: `"🚀 Initializing Enterprise TRA Application..."`
- ✅ Console shows: `"✓ Application initialized successfully"`

### Screenshot Checklist:
- [ ] Green connection indicator (top left)
- [ ] Generated session ID displayed
- [ ] Welcome message with suggested commands
- [ ] Clean console (no red errors)

---

## 2. Chat Functionality Test (3 minutes)

### Test A: Send Simple Message
**Steps:**
1. Type: `"Hello"` in the message input
2. Press Enter or click Send button

**Expected:**
- ✅ Message appears with "User" badge (dark background)
- ✅ Message sent to backend (check backend terminal logs)
- ✅ Bot response appears with "Agent" badge (light background)
- ✅ Chat auto-scrolls to bottom

### Test B: Multi-line Message
**Steps:**
1. Type: `"Line 1"`
2. Press Shift+Enter
3. Type: `"Line 2"`
4. Press Enter

**Expected:**
- ✅ Message preserves line breaks
- ✅ Multi-line message sent correctly

### Test C: Create Assessment
**Steps:**
1. Type: `"Create new assessment for Test Project"`
2. Press Enter

**Expected:**
- ✅ Backend creates assessment
- ✅ Response shows TRA-YYYY-XXXXXX format ID
- ✅ TRA ID is automatically populated in upload section
- ✅ Response formatted with markdown/sections

---

## 3. Assessment Search Test (2 minutes)

### Steps:
1. Locate search box in left sidebar ("Search Assessments")
2. Type: `"test"` (or any keyword)
3. Wait 300ms for debounced search

### Expected Results:
- ✅ Search triggers automatically after typing stops
- ✅ Notification appears: "Found X result(s)"
- ✅ Results display below search box with:
  - Assessment ID (blue text)
  - Title (bold)
  - Completion percentage
  - Updated date
  - Copy button

### Test Copy Function:
1. Click the copy button (📋 icon) on any result
2. Check for toast notification: "Copied ID: TRA-YYYY-XXXXXX"

**Expected:**
- ✅ ID copied to clipboard
- ✅ Toast notification appears bottom-right
- ✅ Toast fades out after 2 seconds

---

## 4. TRA ID Validation Test (2 minutes)

### Test A: Invalid Format
**Steps:**
1. Locate "TRA ID for Document Upload" section (bottom left)
2. Enter: `"invalid-id"`
3. Click "Validate TRA ID"

**Expected:**
- ✅ Red border appears around input
- ✅ Red error message: "Invalid TRA ID format"
- ✅ File upload button remains disabled

### Test B: Valid Format (No Assessment)
**Steps:**
1. Enter: `"TRA-2025-ABC123"`
2. Click "Validate TRA ID"

**Expected:**
- ✅ Backend checks if assessment exists
- ✅ Red error if not found: "TRA ID not found"
- ✅ Green success if found: "Valid TRA ID"

### Test C: Valid Format (Existing Assessment)
**Steps:**
1. Copy an assessment ID from search results
2. Paste into TRA ID field
3. Click "Validate TRA ID" or press Enter

**Expected:**
- ✅ Green border appears
- ✅ Green success message: "Valid TRA ID"
- ✅ File upload section becomes enabled
- ✅ Upload button changes from gray to black

---

## 5. File Upload Test (3 minutes)

### Prerequisites:
- Must validate a TRA ID first (see Test 4)

### Test A: Valid File Upload
**Steps:**
1. Click "Choose Files" button
2. Select a PDF file (test.pdf)
3. Observe upload progress

**Expected:**
- ✅ System message appears: "📄 Uploading test.pdf..."
- ✅ File appears in uploaded files list with status
- ✅ Status changes: "⟳ Processing" → "✓ Ready"
- ✅ Chat message shows file analysis result
- ✅ Backend logs show upload and ingestion

### Test B: Invalid File Type
**Steps:**
1. Click "Choose Files"
2. Try to select an image file (test.png)

**Expected:**
- ✅ File picker only shows .pdf, .doc, .docx, .txt
- ✅ Or error message if file type rejected

### Test C: Multiple Files
**Steps:**
1. Click "Choose Files"
2. Select multiple PDFs (Ctrl/Cmd + Click)
3. Observe batch upload

**Expected:**
- ✅ All files appear in list
- ✅ Each file processed independently
- ✅ Status updates for each file

---

## 6. Question Flow Test (5 minutes)

### Test A: Trigger Questions
**Steps:**
1. Type: `"start questions"` or `"begin assessment"`
2. Press Enter

**Expected:**
- ✅ Bot responds with first question
- ✅ Question formatted with progress indicator: "Question 1 of X"
- ✅ Question type detected and rendered correctly

### Test B: Yes/No Question
**Expected Display:**
- ✅ Question text displayed
- ✅ Two buttons: "Yes" and "No"
- ✅ AI Suggestion box (if available): "💡 AI Suggestion: Yes (Confidence: High)"
- ✅ Progress bar or indicator

**Actions:**
1. Click "Yes" button

**Expected:**
- ✅ Answer sent to backend
- ✅ User message shows: "Yes"
- ✅ Next question appears

### Test C: Multiple Choice Question
**Expected Display:**
- ✅ Question text
- ✅ Multiple option buttons (A, B, C, D, etc.)
- ✅ Each option clickable
- ✅ AI suggestion (if present)

**Actions:**
1. Click any option button

**Expected:**
- ✅ Selected option sent as answer
- ✅ Next question or completion message

### Test D: Free Text Question
**Expected Display:**
- ✅ Question text
- ✅ Large textarea for answer
- ✅ "Submit Answer" button

**Actions:**
1. Type: `"This is my detailed answer"`
2. Click "Submit Answer"

**Expected:**
- ✅ Text sent to backend
- ✅ Next question or assessment complete message

---

## 7. Message Formatting Test (3 minutes)

### Test Markdown Rendering
**Steps:**
Type the following in chat:

```
**Bold Text**
*Italic Text*
- List item 1
- List item 2
1. Numbered item
```

**Expected:**
- ✅ Bold text renders in bold
- ✅ Italic text renders in italic
- ✅ Lists render correctly
- ✅ Proper spacing and indentation

### Test Code Blocks
**Steps:**
Type:
```python
def hello():
    print("Hello World")
```

**Expected:**
- ✅ Code block has background color
- ✅ Syntax highlighting applied
- ✅ Monospace font used
- ✅ Proper indentation preserved

---

## 8. Security Testing (3 minutes)

### Test A: XSS Prevention
**Steps:**
1. Type: `<script>alert('XSS')</script>`
2. Press Enter

**Expected:**
- ✅ NO alert popup appears
- ✅ Script tag displayed as text (sanitized)
- ✅ No JavaScript execution

### Test B: HTML Injection
**Steps:**
1. Type: `<img src=x onerror=alert(1)>`
2. Press Enter

**Expected:**
- ✅ NO alert popup
- ✅ Image tag stripped or sanitized
- ✅ No malicious code execution

### Test C: Malformed Tags
**Steps:**
1. Type: `Hello< br>World` (space before br)
2. Press Enter

**Expected:**
- ✅ Tag fixed to proper `<br>`
- ✅ Line break renders correctly
- ✅ Console shows: "🔧 Fixed malformed br tags!"

---

## 9. WebSocket Connection Test (3 minutes)

### Test A: Normal Connection
**Steps:**
1. Open browser DevTools Console
2. Check for: `"WebSocket connected successfully"`

**Expected:**
- ✅ Connection indicator green
- ✅ Console shows successful connection
- ✅ Messages send/receive correctly

### Test B: Reconnection
**Steps:**
1. Stop backend server: `Ctrl+C` in backend terminal
2. Observe frontend behavior
3. Restart backend: `./scripts/run_backend.sh`

**Expected:**
- ✅ Connection indicator turns red "Disconnected"
- ✅ Console shows: "WebSocket closed"
- ✅ Frontend attempts reconnection (up to 10 times)
- ✅ When backend restarts, auto-reconnects
- ✅ Connection indicator turns green again

---

## 10. Responsive Design Test (2 minutes)

### Test Different Screen Sizes
**Steps:**
1. Open DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Test these sizes:
   - Desktop: 1920x1080
   - Laptop: 1366x768
   - Tablet: 768x1024
   - Mobile: 375x667

**Expected for Each Size:**
- ✅ Layout adjusts appropriately
- ✅ Sidebar scrollable on small screens
- ✅ Chat messages wrap correctly
- ✅ Buttons remain accessible
- ✅ No horizontal scrolling
- ✅ Text remains readable

---

## 11. Performance Test (2 minutes)

### Test A: Message Load
**Steps:**
1. Send 50 messages rapidly
2. Observe rendering performance

**Expected:**
- ✅ Messages render smoothly
- ✅ Auto-scroll works for all messages
- ✅ No lag or stuttering
- ✅ Memory usage remains stable

### Test B: Large Message
**Steps:**
1. Send a message with 500+ words
2. Observe rendering

**Expected:**
- ✅ Long message renders correctly
- ✅ Proper line wrapping
- ✅ Scrolling works smoothly

---

## 12. Error Handling Test (3 minutes)

### Test A: Network Error
**Steps:**
1. Open DevTools Network tab
2. Set throttling to "Offline"
3. Try to send a message

**Expected:**
- ✅ User-friendly error message
- ✅ No crash or undefined errors
- ✅ Console logs meaningful error

### Test B: API Timeout
**Steps:**
1. Stop backend
2. Try to upload a file

**Expected:**
- ✅ Error message: "Request timeout - please try again"
- ✅ Upload status shows "✗ Failed"
- ✅ Graceful error handling

---

## Debugging Tools

### Browser Console Commands
```javascript
// Access debug utilities
window.__TRA_DEBUG__

// View chat store state
Alpine.store('chat')

// Check connection status
Alpine.store('chat').connected

// View messages
Alpine.store('chat').messages

// Send test message
Alpine.store('chat').sendMessageDirect('test')

// View session ID
Alpine.store('chat').sessionId

// Check uploaded files
Alpine.store('chat').uploadedFiles

// Check search results
Alpine.store('chat').searchResults

// Test message formatter
const formatter = window.__TRA_DEBUG__.components.messageFormatter;
formatter.formatMessage("Test message");

// Test API service
const api = window.__TRA_DEBUG__.services.api;
await api.getHealthStatus();
```

---

## Common Issues & Solutions

### Issue: Connection Indicator Shows Red
**Cause:** Backend not running or WebSocket connection failed

**Solution:**
1. Check backend is running: `ps aux | grep uvicorn`
2. Restart backend: `./scripts/run_backend.sh`
3. Check WebSocket URL in browser console
4. Verify port 8000 is not blocked by firewall

### Issue: Messages Not Sending
**Cause:** WebSocket disconnected or frontend error

**Solution:**
1. Check browser console for errors
2. Verify connection status in UI
3. Refresh page to reinitialize
4. Check backend logs for errors

### Issue: Files Not Uploading
**Cause:** TRA ID not validated or backend issue

**Solution:**
1. Validate TRA ID first (green checkmark)
2. Check file type is allowed (.pdf, .doc, .docx, .txt)
3. Check file size < 10MB
4. Verify S3 bucket is accessible (backend logs)

### Issue: Search Returns No Results
**Cause:** No assessments in database

**Solution:**
1. Create test assessment: "Create new assessment"
2. Wait for assessment creation confirmation
3. Try search again

---

## Test Completion Checklist

Mark each section when tested:

- [ ] 1. Initial Load Test
- [ ] 2. Chat Functionality Test
- [ ] 3. Assessment Search Test
- [ ] 4. TRA ID Validation Test
- [ ] 5. File Upload Test
- [ ] 6. Question Flow Test
- [ ] 7. Message Formatting Test
- [ ] 8. Security Testing
- [ ] 9. WebSocket Connection Test
- [ ] 10. Responsive Design Test
- [ ] 11. Performance Test
- [ ] 12. Error Handling Test

---

## Test Report Template

After completing all tests, fill out this report:

```
FRONTEND TEST REPORT
====================

Date: _______________
Tester: _______________
Browser: _______________
OS: _______________

Test Results:
- Initial Load: [ ] PASS [ ] FAIL
- Chat Functionality: [ ] PASS [ ] FAIL
- Assessment Search: [ ] PASS [ ] FAIL
- TRA ID Validation: [ ] PASS [ ] FAIL
- File Upload: [ ] PASS [ ] FAIL
- Question Flow: [ ] PASS [ ] FAIL
- Message Formatting: [ ] PASS [ ] FAIL
- Security: [ ] PASS [ ] FAIL
- WebSocket: [ ] PASS [ ] FAIL
- Responsive Design: [ ] PASS [ ] FAIL
- Performance: [ ] PASS [ ] FAIL
- Error Handling: [ ] PASS [ ] FAIL

Issues Found:
1. _____________________________
2. _____________________________
3. _____________________________

Overall Assessment:
[ ] APPROVED FOR PRODUCTION
[ ] NEEDS MINOR FIXES
[ ] NEEDS MAJOR FIXES

Comments:
_________________________________
_________________________________
_________________________________

Signature: _______________
```

---

## Next Steps After Testing

If all tests pass:
1. ✅ Build production version: `npm run build`
2. ✅ Test production build: `npm run preview`
3. ✅ Review [FRONTEND_TEST_RESULTS.md](./FRONTEND_TEST_RESULTS.md)
4. ✅ Deploy to staging environment
5. ✅ User acceptance testing (UAT)
6. ✅ Production deployment

---

**Testing Time Estimate:** 30-40 minutes for complete manual testing

**Automated Testing:** Run `node scripts/test_frontend.js` for quick validation (2 minutes)

**Questions?** Check the [FRONTEND_TEST_RESULTS.md](./FRONTEND_TEST_RESULTS.md) for detailed technical information.
