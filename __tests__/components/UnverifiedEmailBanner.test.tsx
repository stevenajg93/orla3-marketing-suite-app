import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import UnverifiedEmailBanner from '@/app/dashboard/components/UnverifiedEmailBanner'

// Mock the config module
jest.mock('@/lib/config', () => ({
  config: {
    apiUrl: 'http://localhost:8000',
  },
}))

// Mock fetch globally
const mockFetch = jest.fn()
global.fetch = mockFetch

describe('UnverifiedEmailBanner', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  it('renders the banner with warning message', () => {
    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    expect(screen.getByText('Email Not Verified')).toBeInTheDocument()
    expect(
      screen.getByText(/Please verify your email address to unlock all features/)
    ).toBeInTheDocument()
    expect(screen.getByText('Resend Verification Email')).toBeInTheDocument()
  })

  it('hides the banner when dismiss button is clicked', () => {
    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    // Find and click the dismiss button (X icon)
    const dismissButton = screen.getByRole('button', { name: '' })
    fireEvent.click(dismissButton)

    expect(screen.queryByText('Email Not Verified')).not.toBeInTheDocument()
  })

  it('shows loading state when resend button is clicked', async () => {
    mockFetch.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true }), 100))
    )

    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    const resendButton = screen.getByText('Resend Verification Email')
    fireEvent.click(resendButton)

    expect(screen.getByText('Sending...')).toBeInTheDocument()
  })

  it('shows success message after resending verification email', async () => {
    mockFetch.mockResolvedValue({ ok: true })

    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    const resendButton = screen.getByText('Resend Verification Email')
    fireEvent.click(resendButton)

    await waitFor(() => {
      expect(screen.getByText('Verification email sent!')).toBeInTheDocument()
    })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/auth/resend-verification',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com' }),
      })
    )
  })

  it('handles API error gracefully', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    const resendButton = screen.getByText('Resend Verification Email')
    fireEvent.click(resendButton)

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        'Failed to resend verification email:',
        expect.any(Error)
      )
    })

    consoleSpy.mockRestore()
  })

  it('does not show success message if response is not ok', async () => {
    mockFetch.mockResolvedValue({ ok: false })

    render(<UnverifiedEmailBanner userEmail="test@example.com" />)

    const resendButton = screen.getByText('Resend Verification Email')
    fireEvent.click(resendButton)

    await waitFor(() => {
      expect(screen.queryByText('Verification email sent!')).not.toBeInTheDocument()
    })

    // Button should be enabled again
    expect(screen.getByText('Resend Verification Email')).toBeInTheDocument()
  })
})
