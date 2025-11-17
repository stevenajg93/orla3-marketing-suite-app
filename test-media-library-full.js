const { chromium } = require('playwright');

async function testMediaLibraryFull() {
  console.log('🚀 Starting comprehensive media library test...\n');

  const browser = await chromium.launch({
    headless: false, // Show browser for debugging
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
    const type = msg.type();
    consoleMessages.push({ type, text, timestamp: new Date().toISOString() });

    // Color code console output
    const color = {
      'error': '\x1b[31m', // Red
      'warning': '\x1b[33m', // Yellow
      'info': '\x1b[36m', // Cyan
      'log': '\x1b[37m' // White
    }[type] || '\x1b[37m';

    console.log(`${color}[${type.toUpperCase()}]\x1b[0m ${text}`);
  });

  // Capture network errors
  const networkErrors = [];
  page.on('requestfailed', request => {
    const failure = request.failure();
    const error = {
      url: request.url(),
      error: failure ? failure.errorText : 'Unknown error',
      timestamp: new Date().toISOString()
    };
    networkErrors.push(error);
    console.log(`\x1b[31m[NETWORK ERROR]\x1b[0m ${error.url} - ${error.error}`);
  });

  // Capture ALL API responses
  const apiCalls = [];
  page.on('response', async response => {
    const url = response.url();
    const status = response.status();

    // Track library and cloud storage calls
    if (url.includes('/library') || url.includes('/cloud-storage') || url.includes('orla3-marketing-suite-app-production')) {
      const call = {
        url,
        status,
        timestamp: new Date().toISOString()
      };

      // Try to get response body for errors
      if (status >= 400) {
        try {
          const body = await response.text();
          call.body = body.substring(0, 500); // First 500 chars
        } catch (e) {
          call.body = 'Could not read body';
        }
      }

      apiCalls.push(call);

      const statusColor = status >= 400 ? '\x1b[31m' : status >= 300 ? '\x1b[33m' : '\x1b[32m';
      console.log(`${statusColor}[${status}]\x1b[0m ${url.substring(0, 100)}`);

      if (status >= 400 && call.body) {
        console.log(`  └─ Body: ${call.body}`);
      }
    }
  });

  try {
    console.log('\n📍 Step 1: Loading https://marketing.orla3.com\n');
    await page.goto('https://marketing.orla3.com', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('\n✅ Page loaded');
    console.log('\n⏳ Waiting 5 seconds for any background requests...\n');
    await page.waitForTimeout(5000);

    console.log('\n📍 Step 2: Checking if user is logged in...\n');

    // Check localStorage for tokens
    const hasToken = await page.evaluate(() => {
      return localStorage.getItem('access_token') !== null;
    });

    if (hasToken) {
      console.log('✅ Found access token in localStorage\n');

      console.log('📍 Step 3: Looking for media library or dashboard navigation...\n');
      await page.waitForTimeout(2000);

      // Try to find and click media library or dashboard links
      const dashboardLink = await page.$('a[href*="dashboard"]').catch(() => null);
      const mediaLink = await page.$('a[href*="media"]').catch(() => null);
      const socialLink = await page.$('a[href*="social"]').catch(() => null);

      if (socialLink) {
        console.log('🎯 Found social/media link, clicking...\n');
        await socialLink.click();
        await page.waitForTimeout(3000);
      } else if (dashboardLink) {
        console.log('🎯 Found dashboard link, clicking...\n');
        await dashboardLink.click();
        await page.waitForTimeout(3000);
      } else {
        console.log('⚠️  Could not find navigation links\n');
      }

      // Wait for any API calls to finish
      console.log('⏳ Waiting 10 seconds for API calls to complete...\n');
      await page.waitForTimeout(10000);

    } else {
      console.log('⚠️  No access token found - user not logged in');
      console.log('ℹ️  Please log in manually in the browser window that opened\n');
      console.log('⏳ Waiting 60 seconds for you to log in and navigate to media library...\n');
      await page.waitForTimeout(60000);
    }

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
  } finally {
    console.log('\n\n' + '='.repeat(80));
    console.log('📊 FINAL SUMMARY REPORT');
    console.log('='.repeat(80));

    console.log(`\n📝 Console Messages: ${consoleMessages.length}`);
    if (consoleMessages.length > 0) {
      const errors = consoleMessages.filter(m => m.type === 'error');
      const warnings = consoleMessages.filter(m => m.type === 'warning');
      console.log(`   - Errors: ${errors.length}`);
      console.log(`   - Warnings: ${warnings.length}`);

      if (errors.length > 0) {
        console.log('\n🔴 Console Errors:');
        errors.forEach(err => console.log(`   ${err.timestamp} - ${err.text}`));
      }
    }

    console.log(`\n🌐 Network Errors: ${networkErrors.length}`);
    if (networkErrors.length > 0) {
      networkErrors.forEach(err => {
        console.log(`   ${err.timestamp} - ${err.url}`);
        console.log(`      └─ ${err.error}`);
      });
    }

    console.log(`\n🔌 API Calls Tracked: ${apiCalls.length}`);
    if (apiCalls.length > 0) {
      const errors = apiCalls.filter(c => c.status >= 400);
      console.log(`   - Errors (4xx/5xx): ${errors.length}`);

      if (errors.length > 0) {
        console.log('\n🔴 API Errors:');
        errors.forEach(call => {
          console.log(`   [${call.status}] ${call.url}`);
          if (call.body) {
            console.log(`      └─ ${call.body.substring(0, 200)}`);
          }
        });
      }
    }

    // Check for specific error patterns
    const jsonErrors = consoleMessages.filter(m =>
      m.text.toLowerCase().includes('json') ||
      m.text.toLowerCase().includes('unterminated')
    );

    if (jsonErrors.length > 0) {
      console.log('\n🔴 JSON Parsing Issues:');
      jsonErrors.forEach(err => console.log(`   - ${err.text}`));
    }

    const libraryErrors = consoleMessages.filter(m =>
      m.text.toLowerCase().includes('library') ||
      m.text.toLowerCase().includes('cloud storage') ||
      m.text.toLowerCase().includes('google drive')
    );

    if (libraryErrors.length > 0) {
      console.log('\n☁️  Library/Cloud Storage Messages:');
      libraryErrors.forEach(err => console.log(`   - ${err.text}`));
    }

    console.log('\n' + '='.repeat(80));
    console.log('\n✅ Browser will close in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
    console.log('✅ Test complete\n');
  }
}

testMediaLibraryFull().catch(console.error);
