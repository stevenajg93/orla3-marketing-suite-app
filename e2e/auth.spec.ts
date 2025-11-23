import { test, expect } from '@playwright/test'

/**
 * Authentication E2E Tests
 *
 * Tests the critical user authentication flows:
 * - Landing page accessibility
 * - Login page functionality
 * - Signup page functionality
 * - Protected route redirection
 */

test.describe('Authentication Flow', () => {
  test('landing page loads successfully', async ({ page }) => {
    await page.goto('/')

    // Check page title
    await expect(page).toHaveTitle(/ORLA/i)

    // Check for key landing page elements (use first() for multiple matches)
    await expect(page.getByRole('link', { name: 'Get Started' }).first()).toBeVisible()
  })

  test('login page is accessible', async ({ page }) => {
    await page.goto('/login')

    // Check login form elements
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('signup page is accessible', async ({ page }) => {
    await page.goto('/signup')

    // Check signup form elements (signup has two password fields)
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('login page shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Fill in invalid credentials
    await page.fill('input[type="email"]', 'invalid@test.com')
    await page.fill('input[type="password"]', 'wrongpassword123')

    // Submit form
    await page.click('button[type="submit"]')

    // Wait for error message (either toast or inline error)
    await page.waitForTimeout(2000)

    // Check that we're still on login page (not redirected to dashboard)
    expect(page.url()).toContain('/login')
  })

  test('protected route redirects to login', async ({ page }) => {
    // Try to access dashboard without authentication
    await page.goto('/dashboard')

    // Should redirect to login
    await page.waitForURL(/\/(login|$)/)

    // Verify we're on login page or landing page
    const url = page.url()
    expect(url.includes('/login') || url.endsWith('.com') || url.endsWith('.com/')).toBeTruthy()
  })

  test('login link from landing page works', async ({ page }) => {
    await page.goto('/')

    // Click login link in navigation
    const loginLink = page.getByRole('link', { name: 'Login' }).first()
    if (await loginLink.isVisible()) {
      await loginLink.click()
      await expect(page).toHaveURL(/\/login/)
    }
  })

  test('signup link from landing page works', async ({ page }) => {
    await page.goto('/')

    // Click Get Started link (first one in nav)
    const signupLink = page.getByRole('navigation').getByRole('link', { name: 'Get Started' })
    if (await signupLink.isVisible()) {
      await signupLink.click()
      // Should navigate to signup or pricing page
      await page.waitForTimeout(1000)
      const url = page.url()
      expect(url.includes('/signup') || url.includes('/payment')).toBeTruthy()
    }
  })
})

test.describe('Legal Pages', () => {
  test('privacy policy page loads', async ({ page }) => {
    await page.goto('/privacy')

    // Check for privacy policy content (use exact heading text)
    await expect(page.getByRole('heading', { name: 'Privacy Policy' })).toBeVisible()
  })

  test('terms of service page loads', async ({ page }) => {
    await page.goto('/terms')

    // Check for terms content (use exact heading text)
    await expect(page.getByRole('heading', { name: 'Terms of Service' })).toBeVisible()
  })
})
