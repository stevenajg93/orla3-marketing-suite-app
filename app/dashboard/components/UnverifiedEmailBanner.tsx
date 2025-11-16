'use client';

import { useState } from 'react';
import { config } from '@/lib/config';

interface UnverifiedEmailBannerProps {
  userEmail: string;
}

export default function UnverifiedEmailBanner({ userEmail }: UnverifiedEmailBannerProps) {
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  const handleResendEmail = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${config.apiUrl}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: userEmail }),
      });

      if (response.ok) {
        setSent(true);
      }
    } catch (error) {
      console.error('Failed to resend verification email:', error);
    } finally {
      setLoading(false);
    }
  };

  if (dismissed) return null;

  return (
    <div className="bg-gradient-to-r from-gold-600/40 via-gold-intense/40 to-gold-600/40 backdrop-blur-lg border border-gold/30 rounded-lg p-4 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="flex-shrink-0">
            <svg
              className="w-6 h-6 text-gold-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h3 className="text-white font-semibold mb-1">Email Not Verified</h3>
            <p className="text-gray-300 text-sm mb-3">
              Please verify your email address to unlock all features. Check your inbox for a verification link.
            </p>
            {!sent ? (
              <button
                onClick={handleResendEmail}
                disabled={loading}
                className="px-4 py-2 bg-gold-600 hover:bg-gold-700 text-white text-sm font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Resend Verification Email'}
              </button>
            ) : (
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-gold-600/30 border border-gold/50 rounded-lg">
                <svg className="w-4 h-4 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gold text-sm font-medium">Verification email sent!</span>
              </div>
            )}
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 text-gray-400 hover:text-white transition"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
