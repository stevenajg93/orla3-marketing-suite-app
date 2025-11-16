'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

function PaymentSuccessContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [countdown, setCountdown] = useState(5);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    // Countdown timer
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    } else {
      // Redirect to dashboard after countdown
      router.push('/dashboard');
    }
  }, [countdown, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center px-3 sm:px-4">
      <div className="max-w-2xl w-full">
        {/* Success Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 border border-white/20 text-center">
          {/* Success Icon */}
          <div className="mb-6 sm:mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full">
              <svg
                className="w-8 h-8 sm:w-10 sm:h-10 md:w-12 md:h-12 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={3}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          </div>

          {/* Success Message */}
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-black text-white mb-3 sm:mb-4">
            Payment Successful!
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 mb-6 sm:mb-8">
            Welcome to Orla³ Marketing Automation Platform
          </p>

          {/* Details */}
          <div className="bg-white/5 rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8 border border-white/10">
            <div className="space-y-2 sm:space-y-3 text-left">
              <div className="flex items-start gap-2 sm:gap-3">
                <span className="text-green-400 text-lg sm:text-xl"></span>
                <div className="flex-1">
                  <p className="text-white text-sm sm:text-base font-semibold">Subscription Activated</p>
                  <p className="text-gray-400 text-xs sm:text-sm">Your account is now fully active</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <span className="text-green-400 text-lg sm:text-xl"></span>
                <div className="flex-1">
                  <p className="text-white text-sm sm:text-base font-semibold">Credits Added</p>
                  <p className="text-gray-400 text-xs sm:text-sm">Your monthly credits are ready to use</p>
                </div>
              </div>
              <div className="flex items-start gap-2 sm:gap-3">
                <span className="text-green-400 text-lg sm:text-xl"></span>
                <div className="flex-1">
                  <p className="text-white text-sm sm:text-base font-semibold">Receipt Sent</p>
                  <p className="text-gray-400 text-xs sm:text-sm">Check your email for the payment receipt</p>
                </div>
              </div>
            </div>
          </div>

          {/* Session ID (for support) */}
          {sessionId && (
            <p className="text-xs text-gray-500 mb-6 sm:mb-8 font-mono break-all">
              Session ID: {sessionId}
            </p>
          )}

          {/* Auto-redirect message */}
          <div className="mb-4 sm:mb-6">
            <p className="text-sm sm:text-base text-gray-300 mb-2">
              Redirecting to dashboard in <span className="text-white font-bold">{countdown}</span> seconds...
            </p>
            <div className="w-full bg-white/10 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-cobalt to-royal h-2 rounded-full transition-all duration-1000"
                style={{ width: `${((5 - countdown) / 5) * 100}%` }}
              />
            </div>
          </div>

          {/* Manual Navigation */}
          <Link
            href="/dashboard"
            className="inline-block w-full sm:w-auto bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-base sm:text-lg transition shadow-2xl"
          >
            Go to Dashboard Now →
          </Link>
        </div>

        {/* Next Steps */}
        <div className="mt-6 sm:mt-8 text-center">
          <p className="text-gray-400 mb-3 sm:mb-4 text-sm sm:text-base">What's next?</p>
          <div className="flex flex-wrap justify-center gap-3 sm:gap-4 text-xs sm:text-sm">
            <Link
              href="/dashboard/brand-voice"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              Set up your brand voice →
            </Link>
            <Link
              href="/dashboard/social"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              Connect social accounts →
            </Link>
            <Link
              href="/dashboard/strategy"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              Generate content strategy →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    }>
      <PaymentSuccessContent />
    </Suspense>
  );
}
