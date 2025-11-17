'use client';

import { motion } from 'framer-motion';
import { AnimatedPage } from '@/components/AnimatedPage';
import { fadeInUp } from '@/lib/motion';
import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { config } from '@/lib/config';

function VerifyEmailContent() {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center p-3 sm:p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
            ORLA³
          </h1>
          <p className="text-sm sm:text-base text-gray-400 mt-2">Marketing Automation Suite</p>
        </div>

        {/* Verification Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-5 sm:p-6 md:p-8 border border-white/20 shadow-2xl">
          {status === 'loading' && (
            <div className="text-center">
              <div className="inline-block w-12 h-12 sm:w-16 sm:h-16 border-4 border-cobalt border-t-transparent rounded-full animate-spin mb-3 sm:mb-4"></div>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Verifying Email...</h2>
              <p className="text-sm sm:text-base text-gray-400">Please wait while we verify your email address</p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-gold/20 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Email Verified!</h2>
              <p className="text-sm sm:text-base text-gray-400">{message}</p>
              <Link
                href="/dashboard"
                className="inline-block mt-4 sm:mt-6 px-5 sm:px-6 py-2.5 sm:py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white text-sm sm:text-base font-semibold rounded-lg transition"
              >
                Go to Dashboard
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Verification Failed</h2>
              <p className="text-sm sm:text-base text-gray-400 mb-4 sm:mb-6">{message}</p>
              <div className="space-y-2 sm:space-y-3">
                <Link
                  href="/login"
                  className="block w-full py-2.5 sm:py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white text-sm sm:text-base font-semibold rounded-lg transition"
                >
                  Go to Login
                </Link>
                <Link
                  href="/resend-verification"
                  className="block w-full py-2.5 sm:py-3 bg-white/10 hover:bg-white/20 text-white text-sm sm:text-base font-semibold rounded-lg transition border border-white/20"
                >
                  Resend Verification Email
                </Link>
              </div>
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

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center p-3 sm:p-4">
        <div className="inline-block w-12 h-12 sm:w-16 sm:h-16 border-4 border-cobalt border-t-transparent rounded-full animate-spin"></div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
}
