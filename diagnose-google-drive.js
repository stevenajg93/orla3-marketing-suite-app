const { chromium } = require('playwright');

async function diagnoseGoogleDrive() {
  console.log('🔍 GOOGLE DRIVE DIAGNOSTIC TEST\n');
  console.log('=' .repeat(80));

  const browser = await chromium.launch({
    headless: false,
    args: ['--no-sandbox', '--force-device-scale-factor=1']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1
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
  });

  page.on('response', async response => {
    const url = response.url();
    const status = response.status();

    if (url.includes('/cloud-storage') || url.includes('/auth/login')) {
      const log = { url, status, time: new Date().toISOString() };

      try {
        const contentType = response.headers()['content-type'];
        if (contentType && contentType.includes('application/json')) {
          log.body = await response.text();
        }
      } catch (e) {
        log.body = 'Could not read';
      }

      logs.api.push(log);

      const color = status >= 400 ? '\x1b[31m' : '\x1b[32m';
      console.log(`${color}[${status}]` + `\x1b[0m ${url.substring(0, 100)}`);
      if (status >= 400 && log.body) {
        console.log(`  └─ ${log.body.substring(0, 300)}`);
      }
    }
  });

  try {
    console.log('\n📍 Step 1: Loading https://marketing.orla3.com\n');
    await page.goto('https://marketing.orla3.com', { waitUntil: 'networkidle', timeout: 30000 });

    console.log('✅ Page loaded\n');
    console.log('⏳ Please log in and navigate to Media Library > Cloud Storage tab');
    console.log('   The diagnostic will capture all API requests\n');
    console.log('─'.repeat(80) + '\n');

    // Wait 60 seconds for user interaction
    await page.waitForTimeout(60000);

  } catch (error) {
    console.error('\n❌ Error:', error.message);
  } finally {
    console.log('\n\n' + '='.repeat(80));
    console.log('📊 DIAGNOSTIC RESULTS');
    console.log('='.repeat(80));

    const cloudStorageAPIs = logs.api.filter(l => l.url.includes('/cloud-storage'));

    console.log(`\n☁️  Cloud Storage API Calls: ${cloudStorageAPIs.length}`);

    if (cloudStorageAPIs.length > 0) {
      cloudStorageAPIs.forEach(call => {
        console.log(`\n  [${call.status}] ${call.url}`);
        if (call.body) {
          console.log(`  Body: ${call.body.substring(0, 500)}`);
        }
      });

      // Analyze errors
      const errors = cloudStorageAPIs.filter(c => c.status >= 400);
      if (errors.length > 0) {
        console.log('\n\n🔴 ERROR ANALYSIS:');
        errors.forEach(err => {
          console.log(`\n  Status: ${err.status}`);
          console.log(`  URL: ${err.url}`);

          if (err.body) {
            try {
              const json = JSON.parse(err.body);
              console.log(`  Detail: ${json.detail || JSON.stringify(json)}`);

              // Specific diagnosis
              if (err.status === 401) {
                console.log('\n  💡 DIAGNOSIS: 401 Unauthorized');
                if (json.detail && json.detail.includes('Invalid Credentials')) {
                  console.log('     → Google Drive access token is expired');
                  console.log('     → Checking if refresh token logic is working...');
                } else if (json.detail && json.detail.includes('expired')) {
                  console.log('     → Token expired and refresh failed');
                  console.log('     → May need to reconnect Google Drive');
                }
              } else if (err.status === 500) {
                console.log('\n  💡 DIAGNOSIS: 500 Internal Server Error');
                console.log('     → Backend error, check Railway logs');
              } else if (err.status === 404) {
                console.log('\n  💡 DIAGNOSIS: 404 Not Found');
                console.log('     → No Google Drive connection found');
                console.log('     → Need to connect Google Drive');
              }
            } catch (e) {
              console.log(`  Raw body: ${err.body}`);
            }
          }
        });

        console.log('\n\n🔧 RECOMMENDED FIXES:');

        const has401 = errors.some(e => e.status === 401);
        const has404 = errors.some(e => e.status === 404);
        const has500 = errors.some(e => e.status === 500);

        if (has404) {
          console.log('  1. Reconnect Google Drive from Settings');
        } else if (has401) {
          console.log('  1. Check Railway logs for token refresh attempts');
          console.log('  2. Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Railway');
          console.log('  3. If refresh fails: Reconnect Google Drive');
        } else if (has500) {
          console.log('  1. Check Railway logs for detailed error');
          console.log('  2. Verify database connection');
        }
      }
    } else {
      console.log('\n⚠️  No cloud storage API calls detected');
      console.log('   Make sure you clicked on the Cloud Storage tab');
    }

    console.log('\n' + '='.repeat(80));
    console.log('\n✅ Closing in 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
    console.log('✅ Done!\n');
  }
}

diagnoseGoogleDrive().catch(console.error);
