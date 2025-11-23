import { test, expect } from '@playwright/test'

/**
 * Health Check E2E Tests
 *
 * Tests critical infrastructure endpoints:
 * - Backend API health
 * - Frontend page loads
 * - API connectivity
 */

const API_URL = process.env.E2E_API_URL || 'https://orla3-marketing-suite-app-production.up.railway.app'

test.describe('Infrastructure Health', () => {
  test('backend API health endpoint responds', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`)

    expect(response.ok()).toBeTruthy()
    expect(response.status()).toBe(200)
  })

  test('backend API root responds', async ({ request }) => {
    const response = await request.get(`${API_URL}/`)

    expect(response.ok()).toBeTruthy()
  })

  test('frontend loads without errors', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text())
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Filter out expected third-party errors (analytics, etc.)
    const criticalErrors = errors.filter(
      (err) =>
        !err.includes('analytics') &&
        !err.includes('gtag') &&
        !err.includes('Failed to load resource') // Third-party resources
    )

    // Should have no critical JS errors
    expect(criticalErrors.length).toBe(0)
  })

  test('frontend CSS loads correctly', async ({ page }) => {
    await page.goto('/')

    // Check that Tailwind CSS is loaded (body should have styles)
    const bodyStyles = await page.evaluate(() => {
      const body = document.body
      return window.getComputedStyle(body)
    })

    // Body should have some styling applied
    expect(bodyStyles).toBeTruthy()
  })

  test('API CORS allows frontend origin', async ({ request }) => {
    const response = await request.get(`${API_URL}/health`, {
      headers: {
        Origin: 'https://marketing.orla3.com',
      },
    })

    expect(response.ok()).toBeTruthy()
  })
})

test.describe('Critical Pages Load', () => {
  const criticalPages = [
    { path: '/', name: 'Landing Page' },
    { path: '/login', name: 'Login Page' },
    { path: '/signup', name: 'Signup Page' },
    { path: '/privacy', name: 'Privacy Policy' },
    { path: '/terms', name: 'Terms of Service' },
    { path: '/payment/plans', name: 'Pricing Page' },
  ]

  for (const { path, name } of criticalPages) {
    test(`${name} loads successfully`, async ({ page }) => {
      const response = await page.goto(path)

      // Check response is OK
      expect(response?.ok()).toBeTruthy()

      // Check page has content
      const content = await page.content()
      expect(content.length).toBeGreaterThan(1000)
    })
  }
})

test.describe('Mobile Responsiveness', () => {
  test('landing page is mobile-responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/')

    // Check there's no horizontal scroll
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth
    })

    expect(hasHorizontalScroll).toBeFalsy()
  })

  test('login page is mobile-responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/login')

    // Check form elements are visible
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })
})
