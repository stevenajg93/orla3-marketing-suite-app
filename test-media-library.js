const { chromium } = require('playwright');

async function testMediaLibrary() {
  console.log('🚀 Starting Playwright browser test...\n');

  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();

  // Capture console messages
  const consoleMessages = [];
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push({ type: msg.type(), text });
    console.log(`[${msg.type().toUpperCase()}] ${text}`);
  });

  // Capture network errors
  const networkErrors = [];
  page.on('requestfailed', request => {
    const failure = request.failure();
    const error = `${request.url()} - ${failure ? failure.errorText : 'Unknown error'}`;
    networkErrors.push(error);
    console.log(`[NETWORK ERROR] ${error}`);
  });

  // Capture response errors
  const apiErrors = [];
  page.on('response', response => {
    const url = response.url();
    const status = response.status();

    if (status >= 400) {
      const error = `${status} ${url}`;
      apiErrors.push(error);
      console.log(`[API ERROR] ${error}`);
    }

    // Log specific API calls
    if (url.includes('/library/content') || url.includes('/cloud-storage')) {
      console.log(`[API CALL] ${status} ${url}`);
    }
  });

  try {
    console.log('\n📍 Navigating to https://marketing.orla3.com\n');
    await page.goto('https://marketing.orla3.com', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('✅ Page loaded\n');

    // Wait a bit for any initial requests
    await page.waitForTimeout(3000);

    console.log('\n📊 Summary Report:');
    console.log('==================');
    console.log(`Console Messages: ${consoleMessages.length}`);
    console.log(`Network Errors: ${networkErrors.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (networkErrors.length > 0) {
      console.log('\n🔴 Network Errors:');
      networkErrors.forEach(err => console.log(`  - ${err}`));
    }

    if (apiErrors.length > 0) {
      console.log('\n🔴 API Errors:');
      apiErrors.forEach(err => console.log(`  - ${err}`));
    }

    // Check for specific errors in console
    const jsonErrors = consoleMessages.filter(m => m.text.includes('Unterminated string in JSON'));
    if (jsonErrors.length > 0) {
      console.log('\n🔴 JSON Parsing Errors Found:');
      jsonErrors.forEach(err => console.log(`  - ${err.text}`));
    }

    const driveErrors = consoleMessages.filter(m => m.text.toLowerCase().includes('google drive') || m.text.toLowerCase().includes('cloud storage'));
    if (driveErrors.length > 0) {
      console.log('\n☁️  Cloud Storage Related Messages:');
      driveErrors.forEach(err => console.log(`  - ${err.text}`));
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
  } finally {
    await browser.close();
    console.log('\n✅ Browser closed');
  }
}

testMediaLibrary().catch(console.error);
