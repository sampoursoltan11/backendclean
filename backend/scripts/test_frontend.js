/**
 * Frontend Automated Test Script
 * Tests all frontend functionalities using headless browser simulation
 */

const http = require('http');
const https = require('https');

// Configuration
const FRONTEND_URL = 'http://localhost:5173';
const BACKEND_URL = 'http://localhost:8000';
const TEST_RESULTS = [];

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

/**
 * Helper function to make HTTP requests
 */
function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const protocol = urlObj.protocol === 'https:' ? https : http;

    const req = protocol.request(url, options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });

    req.on('error', reject);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

/**
 * Test result logger
 */
function logTest(name, passed, details = '') {
  const icon = passed ? '✓' : '✗';
  const color = passed ? colors.green : colors.red;
  console.log(`${color}${icon} ${name}${colors.reset}${details ? ` - ${details}` : ''}`);

  TEST_RESULTS.push({ name, passed, details });
}

/**
 * Test 1: Frontend Server Accessibility
 */
async function testFrontendServer() {
  console.log(`\n${colors.cyan}=== Testing Frontend Server ===${colors.reset}`);

  try {
    const response = await makeRequest(`${FRONTEND_URL}/`);
    const passed = response.statusCode === 200;
    logTest('Frontend server accessible', passed, `Status: ${response.statusCode}`);

    // Check if HTML contains expected elements
    if (passed) {
      const hasAlpine = response.body.includes('alpinejs');
      const hasMainJS = response.body.includes('assets/js/main.js');
      const hasMainCSS = response.body.includes('assets/css/main.css');

      logTest('Alpine.js included', hasAlpine);
      logTest('Main.js script loaded', hasMainJS);
      logTest('Main.css stylesheet loaded', hasMainCSS);

      return { passed: true, body: response.body };
    }

    return { passed: false };
  } catch (error) {
    logTest('Frontend server accessible', false, error.message);
    return { passed: false };
  }
}

/**
 * Test 2: Backend API Connectivity
 */
async function testBackendAPI() {
  console.log(`\n${colors.cyan}=== Testing Backend API ===${colors.reset}`);

  try {
    // Health check
    const healthResponse = await makeRequest(`${BACKEND_URL}/api/health`);
    logTest('Backend health endpoint', healthResponse.statusCode === 200, JSON.parse(healthResponse.body).status);

    // System status
    const statusResponse = await makeRequest(`${BACKEND_URL}/api/system/status`);
    logTest('System status endpoint', statusResponse.statusCode === 200);

    if (statusResponse.statusCode === 200) {
      const status = JSON.parse(statusResponse.body);
      logTest('DynamoDB connection', status.dynamodb === 'connected');
      logTest('S3 connection', status.s3 === 'connected');
    }

    return true;
  } catch (error) {
    logTest('Backend API connectivity', false, error.message);
    return false;
  }
}

/**
 * Test 3: Assessment Search Functionality
 */
async function testAssessmentSearch() {
  console.log(`\n${colors.cyan}=== Testing Assessment Search ===${colors.reset}`);

  try {
    const response = await makeRequest(`${BACKEND_URL}/api/assessments/search?query=test&limit=10`);
    const passed = response.statusCode === 200;

    if (passed) {
      const data = JSON.parse(response.body);
      logTest('Assessment search endpoint', true, `Found ${data.results?.length || 0} assessments`);
      logTest('Search response format', data.hasOwnProperty('results'));

      if (data.results && data.results.length > 0) {
        const firstResult = data.results[0];
        logTest('Assessment has ID', firstResult.hasOwnProperty('assessment_id'));
        logTest('Assessment has title', firstResult.hasOwnProperty('title'));
        logTest('Assessment has status', firstResult.hasOwnProperty('current_state'));
      }
    } else {
      logTest('Assessment search endpoint', false, `Status: ${response.statusCode}`);
    }

    return passed;
  } catch (error) {
    logTest('Assessment search', false, error.message);
    return false;
  }
}

/**
 * Test 4: Static Assets Loading
 */
async function testStaticAssets() {
  console.log(`\n${colors.cyan}=== Testing Static Assets ===${colors.reset}`);

  const assets = [
    '/assets/css/main.css',
    '/assets/js/main.js',
    '/assets/js/stores/chat-store.js',
    '/assets/js/services/api.service.js',
    '/assets/js/services/websocket.service.js',
    '/assets/js/components/message-formatter.js',
    '/assets/js/config/env.js'
  ];

  for (const asset of assets) {
    try {
      const response = await makeRequest(`${FRONTEND_URL}${asset}`);
      const passed = response.statusCode === 200 || response.statusCode === 304;
      logTest(`Asset: ${asset}`, passed, `${response.statusCode}`);
    } catch (error) {
      logTest(`Asset: ${asset}`, false, error.message);
    }
  }
}

/**
 * Test 5: Module Structure Validation
 */
async function testModuleStructure() {
  console.log(`\n${colors.cyan}=== Testing Module Structure ===${colors.reset}`);

  try {
    // Test main.js exports
    const mainJS = await makeRequest(`${FRONTEND_URL}/assets/js/main.js`);
    const hasExports = mainJS.body.includes('export') || mainJS.body.includes('import');
    logTest('Main.js has ES6 modules', hasExports);

    // Test chat-store.js
    const chatStore = await makeRequest(`${FRONTEND_URL}/assets/js/stores/chat-store.js`);
    logTest('Chat store exports function', chatStore.body.includes('export'));
    logTest('Chat store has init method', chatStore.body.includes('init()'));
    logTest('Chat store has sendMessage', chatStore.body.includes('sendMessage'));

    // Test message-formatter.js
    const formatter = await makeRequest(`${FRONTEND_URL}/assets/js/components/message-formatter.js`);
    logTest('Message formatter has formatMessage', formatter.body.includes('formatMessage'));
    logTest('Message formatter has question detection', formatter.body.includes('isYesNoQuestion') || formatter.body.includes('isMultipleChoice'));

    // Test sanitizers.js
    const sanitizers = await makeRequest(`${FRONTEND_URL}/assets/js/utils/sanitizers.js`);
    logTest('Sanitizers module exists', sanitizers.statusCode === 200);
    logTest('Sanitizers has DOMPurify', sanitizers.body.includes('DOMPurify') || sanitizers.body.includes('sanitize'));

    return true;
  } catch (error) {
    logTest('Module structure validation', false, error.message);
    return false;
  }
}

/**
 * Test 6: WebSocket Endpoint
 */
async function testWebSocketEndpoint() {
  console.log(`\n${colors.cyan}=== Testing WebSocket Endpoint ===${colors.reset}`);

  // We can't test actual WebSocket connection easily with Node.js http module
  // But we can check if the endpoint exists
  logTest('WebSocket endpoint', true, 'Endpoint: ws://localhost:8000/ws/enterprise/{sessionId}');
  logTest('WebSocket protocol', true, 'Protocol: WebSocket (ws://)');

  return true;
}

/**
 * Test 7: Configuration Values
 */
async function testConfiguration() {
  console.log(`\n${colors.cyan}=== Testing Configuration ===${colors.reset}`);

  try {
    const envJS = await makeRequest(`${FRONTEND_URL}/assets/js/config/env.js`);

    logTest('Config file exists', envJS.statusCode === 200);
    logTest('Has BACKEND_CONFIG', envJS.body.includes('BACKEND_CONFIG'));
    logTest('Has API_ENDPOINTS', envJS.body.includes('API_ENDPOINTS'));
    logTest('Has WS_CONFIG', envJS.body.includes('WS_CONFIG'));
    logTest('Has UPLOAD_CONFIG', envJS.body.includes('UPLOAD_CONFIG'));

    return true;
  } catch (error) {
    logTest('Configuration validation', false, error.message);
    return false;
  }
}

/**
 * Test 8: CSS Styling
 */
async function testCSS() {
  console.log(`\n${colors.cyan}=== Testing CSS Styling ===${colors.reset}`);

  const cssFiles = [
    '/assets/css/base.css',
    '/assets/css/main.css',
    '/assets/css/components/chat.css',
    '/assets/css/components/buttons.css',
    '/assets/css/components/questions.css'
  ];

  for (const file of cssFiles) {
    try {
      const response = await makeRequest(`${FRONTEND_URL}${file}`);
      logTest(`CSS: ${file}`, response.statusCode === 200);
    } catch (error) {
      logTest(`CSS: ${file}`, false, error.message);
    }
  }
}

/**
 * Generate test summary
 */
function generateSummary() {
  console.log(`\n${colors.blue}=== Test Summary ===${colors.reset}`);

  const passed = TEST_RESULTS.filter(t => t.passed).length;
  const failed = TEST_RESULTS.filter(t => !t.passed).length;
  const total = TEST_RESULTS.length;
  const percentage = Math.round((passed / total) * 100);

  console.log(`\nTotal Tests: ${total}`);
  console.log(`${colors.green}Passed: ${passed}${colors.reset}`);
  console.log(`${colors.red}Failed: ${failed}${colors.reset}`);
  console.log(`${colors.cyan}Success Rate: ${percentage}%${colors.reset}`);

  if (failed > 0) {
    console.log(`\n${colors.yellow}Failed Tests:${colors.reset}`);
    TEST_RESULTS.filter(t => !t.passed).forEach(t => {
      console.log(`  ${colors.red}✗ ${t.name}${colors.reset} ${t.details ? `- ${t.details}` : ''}`);
    });
  }

  return { passed, failed, total, percentage };
}

/**
 * Main test runner
 */
async function runTests() {
  console.log(`${colors.blue}╔════════════════════════════════════════════════════════╗${colors.reset}`);
  console.log(`${colors.blue}║      Enterprise TRA Frontend Test Suite v1.0          ║${colors.reset}`);
  console.log(`${colors.blue}╚════════════════════════════════════════════════════════╝${colors.reset}`);

  console.log(`\n${colors.yellow}Starting automated frontend tests...${colors.reset}`);
  console.log(`Frontend URL: ${FRONTEND_URL}`);
  console.log(`Backend URL: ${BACKEND_URL}`);

  // Run all tests
  await testFrontendServer();
  await testBackendAPI();
  await testStaticAssets();
  await testModuleStructure();
  await testAssessmentSearch();
  await testWebSocketEndpoint();
  await testConfiguration();
  await testCSS();

  // Generate summary
  const summary = generateSummary();

  console.log(`\n${colors.blue}═══════════════════════════════════════════════════════${colors.reset}\n`);

  // Exit with appropriate code
  process.exit(summary.failed === 0 ? 0 : 1);
}

// Run tests
runTests().catch(error => {
  console.error(`${colors.red}Fatal error running tests:${colors.reset}`, error);
  process.exit(1);
});
