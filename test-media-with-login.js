const { chromium } = require('playwright');

async function testWithStoredLogin() {
  console.log('🚀 Starting media library test (using stored session)...\n');

  const browser = await chromium.launch({
    headless: false,
    args: [
      '--no-sandbox',
      '--force-device-scale-factor=1'  // Fix zoom issue
    ]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    storageState: {
      cookies: [],
      origins: []
    }
  });

  const page = await context.newPage();

  // Capture everything
  const logs = {
    console: [],
    network: [],
    api: []
  };

  page.on('console', msg => {
    const text = msg.text();
    const type = msg.type();
    logs.console.push({ type, text, time: new Date().toISOString() });

    const color = { 'error': '\x1b[31m', 'warning': '\x1b[33m', 'log': '\x1b[37m' }[type] || '\x1b[37m';
    console.log(`${color}[CONSOLE ${type.toUpperCase()}]\x1b[0m ${text}`);
  });

  page.on('requestfailed', request => {
    const failure = request.failure();
    logs.network.push({
      url: request.url(),
      error: failure ? failure.errorText : 'Unknown',
      time: new Date().toISOString()
    });
    console.log(`\x1b[31m[NETWORK FAIL]\x1b[0m ${request.url()}`);
  });

  page.on('response', async response => {
    const url = response.url();
    const status = response.status();

    if (url.includes('/library') || url.includes('/cloud-storage') || url.includes('orla3-marketing')) {
      const log = { url, status, time: new Date().toISOString() };

      if (status >= 400) {
        try {
          log.body = (await response.text()).substring(0, 300);
        } catch (e) {
          log.body = 'Could not read';
        }
      }

      logs.api.push(log);
      const color = status >= 400 ? '\x1b[31m' : '\x1b[32m';
      console.log(`${color}[API ${status}]\x1b[0m ${url.substring(0, 80)}`);
    }
  });

  try {
    console.log('📍 Loading https://marketing.orla3.com\n');
    await page.goto('https://marketing.orla3.com', { waitUntil: 'networkidle', timeout: 30000 });

    console.log('✅ Page loaded\n');
    console.log('ℹ️  INSTRUCTIONS:');
    console.log('   1. Log in if needed');
    console.log('   2. Navigate to Social Manager or Media Library');
    console.log('   3. Try opening "Browse Media"');
    console.log('   4. Click "Generated Content" and "Cloud Storage" tabs');
    console.log('   5. Wait for logs to appear here\n');
    console.log('⏰ Test will run for 90 seconds then auto-close\n');
    console.log('─'.repeat(80) + '\n');

    // Wait 90 seconds for user interaction
    await page.waitForTimeout(90000);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  } finally {
    console.log('\n\n' + '='.repeat(80));
    console.log('📊 TEST RESULTS');
    console.log('='.repeat(80));

    const consoleErrors = logs.console.filter(l => l.type === 'error');
    const apiErrors = logs.api.filter(l => l.status >= 400);

    console.log(`\nTotal Console Messages: ${logs.console.length}`);
    console.log(`Console Errors: ${consoleErrors.length}`);
    console.log(`Network Failures: ${logs.network.length}`);
    console.log(`API Errors: ${apiErrors.length}`);

    if (consoleErrors.length > 0) {
      console.log('\n🔴 CONSOLE ERRORS:');
      consoleErrors.forEach(e => {
        console.log(`\n  [${e.time}]`);
        console.log(`  ${e.text}`);
      });
    }

    if (apiErrors.length > 0) {
      console.log('\n🔴 API ERRORS:');
      apiErrors.forEach(e => {
        console.log(`\n  [${e.status}] ${e.url}`);
        if (e.body) console.log(`  Response: ${e.body}`);
      });
    }

    if (logs.network.length > 0) {
      console.log('\n🔴 NETWORK FAILURES:');
      logs.network.forEach(e => {
        console.log(`\n  ${e.url}`);
        console.log(`  Error: ${e.error}`);
      });
    }

    // Look for specific issues
    const jsonErrors = logs.console.filter(l =>
      l.text.toLowerCase().includes('json') ||
      l.text.toLowerCase().includes('unterminated')
    );

    if (jsonErrors.length > 0) {
      console.log('\n⚠️  JSON PARSING ISSUES:');
      jsonErrors.forEach(e => console.log(`  - ${e.text}`));
    }

    console.log('\n' + '='.repeat(80));
    console.log('\n✅ Closing browser in 3 seconds...');
    await page.waitForTimeout(3000);
    await browser.close();
    console.log('✅ Done!\n');
  }
}

testWithStoredLogin().catch(console.error);
