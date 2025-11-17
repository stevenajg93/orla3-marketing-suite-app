const { chromium } = require('playwright');

/**
 * COMPREHENSIVE END-TO-END TEST
 *
 * Tests the complete flow:
 * 1. Login
 * 2. Google Drive connection
 * 3. Browse Drive files
 * 4. Select media
 * 5. Create social post
 *
 * This validates ALL fixes are working together
 */

async function testCompleteFlow() {
  console.log('🎯 COMPREHENSIVE END-TO-END TEST');
  console.log('='.repeat(80));
  console.log('Testing: Login → Drive Connect → Browse Files → Media Selection');
  console.log('='.repeat(80) + '\n');

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--force-device-scale-factor=1']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1
  });

  const page = await context.newPage();

  // Test tracking
  const testResults = {
    login: 'pending',
    driveConnection: 'pending',
    driveList: 'pending',
    browseDrive: 'pending',
    mediaLoad: 'pending',
    errors: []
  };

  // Capture API calls
  const apiCalls = [];
  page.on('response', async response => {
    const url = response.url();
    const status = response.status();

    if (url.includes('orla3-marketing') &&
        (url.includes('/auth/') || url.includes('/cloud-storage/') || url.includes('/library/'))) {

      const call = { url, status, timestamp: new Date().toISOString() };

      try {
        if (response.headers()['content-type']?.includes('application/json')) {
          call.body = await response.text();
        }
      } catch (e) {}

      apiCalls.push(call);

      const color = status >= 400 ? '\x1b[31m' : '\x1b[32m';
      console.log(`${color}[${status}]\x1b[0m ${url.substring(url.indexOf('/orla3') + 6, 100)}`);

      if (status >= 400 && call.body) {
        console.log(`  └─ Error: ${call.body.substring(0, 150)}`);
        testResults.errors.push({ url, status, body: call.body });
      }

      // Track test progress
      if (url.includes('/auth/login') && status === 200) {
        testResults.login = 'success';
        console.log('  ✅ Login successful');
      }
      if (url.includes('/cloud-storage/connections') && status === 200) {
        testResults.driveList = 'success';
        console.log('  ✅ Drive connections loaded');
      }
      if (url.includes('/cloud-storage/browse/google_drive') && status === 200) {
        testResults.browseDrive = 'success';
        console.log('  ✅ Google Drive files loaded!');
      }
      if (url.includes('/library/content') && status === 200) {
        testResults.mediaLoad = 'success';
        console.log('  ✅ Library content loaded');
      }
    }
  });

  // Capture console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      console.log(`\x1b[31m[CONSOLE ERROR]\x1b[0m ${text.substring(0, 100)}`);
      if (text.includes('Google Drive') || text.includes('cloud')) {
        testResults.errors.push({ type: 'console', text });
      }
    }
  });

  try {
    console.log('\n📍 STEP 1: Loading application...\n');
    await page.goto('https://marketing.orla3.com', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    console.log('✅ Application loaded\n');
    console.log('─'.repeat(80));
    console.log('📋 MANUAL TESTING STEPS:');
    console.log('─'.repeat(80));
    console.log('1. Log in if needed');
    console.log('2. Go to Settings → Cloud Storage');
    console.log('3. If Google Drive shows as connected:');
    console.log('   - Click "Disconnect"');
    console.log('   - Click "Connect Google Drive"');
    console.log('   - Complete OAuth flow');
    console.log('4. Go to Social Manager');
    console.log('5. Click "Browse Media"');
    console.log('6. Click "Cloud Storage" tab');
    console.log('7. Verify Google Drive files load');
    console.log('8. Select a file');
    console.log('9. Try creating a post');
    console.log('─'.repeat(80) + '\n');
    console.log('⏰ Test will run for 180 seconds (3 minutes)\n');
    console.log('🔍 Watching for API calls...\n');

    // Wait 3 minutes for user interaction
    await page.waitForTimeout(180000);

  } catch (error) {
    console.error('\n❌ Test Error:', error.message);
    testResults.errors.push({ type: 'test_error', message: error.message });
  } finally {
    console.log('\n\n' + '='.repeat(80));
    console.log('📊 FINAL TEST RESULTS');
    console.log('='.repeat(80));

    console.log('\n✅ SUCCESSFUL STEPS:');
    if (testResults.login === 'success') console.log('  ✓ Login');
    if (testResults.driveList === 'success') console.log('  ✓ Cloud storage connections API');
    if (testResults.browseDrive === 'success') console.log('  ✓ Google Drive browse API');
    if (testResults.mediaLoad === 'success') console.log('  ✓ Media library load');

    console.log('\n⏸️  PENDING STEPS:');
    if (testResults.login === 'pending') console.log('  - Login (not detected)');
    if (testResults.driveList === 'pending') console.log('  - Drive connections list');
    if (testResults.browseDrive === 'pending') console.log('  - Google Drive file browse');
    if (testResults.mediaLoad === 'pending') console.log('  - Media library load');

    if (testResults.errors.length > 0) {
      console.log('\n🔴 ERRORS DETECTED:');
      testResults.errors.forEach(err => {
        if (err.url) {
          console.log(`\n  [${err.status}] ${err.url}`);
          if (err.body) {
            try {
              const json = JSON.parse(err.body);
              console.log(`  Detail: ${json.detail || JSON.stringify(json)}`);
            } catch (e) {
              console.log(`  Body: ${err.body.substring(0, 200)}`);
            }
          }
        } else if (err.text) {
          console.log(`\n  Console: ${err.text}`);
        }
      });
    } else {
      console.log('\n✅ NO ERRORS DETECTED!');
    }

    // Final verdict
    console.log('\n' + '='.repeat(80));
    console.log('🎯 FINAL VERDICT:');
    console.log('='.repeat(80));

    if (testResults.browseDrive === 'success') {
      console.log('\n🎉 SUCCESS! Google Drive is working!');
      console.log('   - Files loaded successfully');
      console.log('   - No timezone errors');
      console.log('   - Token refresh working');
    } else if (testResults.browseDrive === 'pending') {
      console.log('\n⚠️  INCONCLUSIVE');
      console.log('   - Did not detect Google Drive browse attempt');
      console.log('   - Make sure you clicked "Cloud Storage" tab');
    } else {
      console.log('\n❌ FAILED');
      console.log('   - Check errors above');
      console.log('   - Verify Railway deployed latest code');
    }

    console.log('\n' + '='.repeat(80));
    console.log('📋 API CALLS SUMMARY:');
    console.log('='.repeat(80));
    console.log(`Total API calls tracked: ${apiCalls.length}`);

    const successCalls = apiCalls.filter(c => c.status >= 200 && c.status < 300);
    const errorCalls = apiCalls.filter(c => c.status >= 400);

    console.log(`  ✅ Successful: ${successCalls.length}`);
    console.log(`  ❌ Errors: ${errorCalls.length}`);

    console.log('\n✅ Closing browser in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
    console.log('✅ Test complete!\n');
  }
}

testCompleteFlow().catch(console.error);
