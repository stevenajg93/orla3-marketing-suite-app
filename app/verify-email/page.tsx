'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import config from '@/lib/config';

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams?.get('token');

      if (!token) {
        setStatus('error');
        setMessage('Missing verification token. Please check your email link.');
        return;
      }

      try {
        const response = await fetch(`${config.apiUrl}/auth/verify-email`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (response.ok && data.success) {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to dashboard...');
          setTimeout(() => router.push('/dashboard'), 3000);
        } else {
          setStatus('error');
          setMessage(data.detail || 'Verification failed. The link may be invalid or expired.');
        }
      } catch (error) {
        setStatus('error');
        setMessage('Failed to verify email. Please try again.');
      }
    };

    verifyEmail();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            ORLA³
          </h1>
          <p className="text-gray-400 mt-2">Marketing Automation Suite</p>
        </div>

        {/* Verification Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 shadow-2xl">
          {status === 'loading' && (
            <div className="text-center">
              <div className="inline-block w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
              <h2 className="text-2xl font-bold text-white mb-2">Verifying Email...</h2>
              <p className="text-gray-400">Please wait while we verify your email address</p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Email Verified!</h2>
              <p className="text-gray-400">{message}</p>
              <Link
                href="/dashboard"
                className="inline-block mt-6 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition"
              >
                Go to Dashboard
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Verification Failed</h2>
              <p className="text-gray-400 mb-6">{message}</p>
              <div className="space-y-3">
                <Link
                  href="/login"
                  className="block w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition"
                >
                  Go to Login
                </Link>
                <Link
                  href="/resend-verification"
                  className="block w-full py-3 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg transition border border-white/20"
                >
                  Resend Verification Email
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>&copy; 2024 ORLA³ Studio. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
