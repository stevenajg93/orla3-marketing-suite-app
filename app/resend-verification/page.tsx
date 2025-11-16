'use client';

import { useState } from 'react';
import Link from 'next/link';
import { config } from '@/lib/config';

export default function ResendVerificationPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${config.apiUrl}/auth/resend-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setSuccess(true);
      } else {
        setError(data.detail || 'Failed to resend verification email');
      }
    } catch (err: any) {
      setError('Failed to resend verification email. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center p-3 sm:p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
            ORLA³
          </h1>
          <p className="text-sm sm:text-base text-gray-400 mt-2">Marketing Automation Suite</p>
        </div>

        {/* Resend Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-5 sm:p-6 md:p-8 border border-white/20 shadow-2xl">
          {!success ? (
            <>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">Resend Verification Email</h2>
              <p className="text-sm sm:text-base text-gray-400 mb-4 sm:mb-6">
                Enter your email address and we'll send you a new verification link
              </p>

              {error && (
                <div className="mb-4 sm:mb-6 bg-red-900/30 border border-red-500/50 rounded-lg p-3 sm:p-4">
                  <p className="text-red-300 text-xs sm:text-sm">{error}</p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    id="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="w-full px-4 py-3 bg-white/5 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-cobalt focus:ring-2 focus:ring-blue-500/20 transition"
                    placeholder="you@company.com"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 sm:py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white text-sm sm:text-base font-semibold rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sending...' : 'Resend Verification Email'}
                </button>
              </form>

              <div className="mt-4 sm:mt-6 text-center">
                <Link
                  href="/login"
                  className="text-cobalt-300 hover:text-cobalt-300 font-semibold transition text-xs sm:text-sm"
                >
                  Back to Login
                </Link>
              </div>
            </>
          ) : (
            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gold/20 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Email Sent!</h2>
              <p className="text-sm sm:text-base text-gray-400 mb-4 sm:mb-6">
                If the email exists and is unverified, a verification link has been sent. Please check your inbox.
              </p>
              <Link
                href="/login"
                className="inline-block px-5 sm:px-6 py-2.5 sm:py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white text-sm sm:text-base font-semibold rounded-lg transition"
              >
                Go to Login
              </Link>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 sm:mt-8 text-center text-gray-500 text-xs sm:text-sm">
          <p>&copy; 2024 ORLA³ Studio. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
