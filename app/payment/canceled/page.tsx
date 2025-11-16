'use client';

import Link from 'next/link';

export default function PaymentCanceledPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 flex items-center justify-center px-3 sm:px-4">
      <div className="max-w-2xl w-full">
        {/* Canceled Card */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 border border-white/20 text-center">
          {/* Canceled Icon */}
          <div className="mb-6 sm:mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 md:w-24 md:h-24 bg-gradient-to-br from-gold-intense to-gold-600 rounded-full">
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
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
          </div>

          {/* Canceled Message */}
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-black text-white mb-3 sm:mb-4">
            Payment Canceled
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 mb-6 sm:mb-8">
            Your payment was not processed
          </p>

          {/* Info Box */}
          <div className="bg-white/5 rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8 border border-white/10 text-left">
            <p className="text-sm sm:text-base text-gray-300 mb-3 sm:mb-4">
              No charges have been made to your account. You can return to the plan selection
              page to choose a different plan or try again.
            </p>
            <p className="text-gray-400 text-xs sm:text-sm">
              If you experienced any issues during checkout, please contact our support team
              and we'll be happy to help.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 sm:space-y-4">
            <Link
              href="/payment/plans"
              className="block w-full bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-base sm:text-lg transition shadow-2xl"
            >
              Try Again
            </Link>
            <Link
              href="/"
              className="block w-full bg-white/10 hover:bg-white/20 text-white border border-white/20 px-6 sm:px-8 py-3 sm:py-4 rounded-lg font-bold text-base sm:text-lg transition"
            >
              Return to Home
            </Link>
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-6 sm:mt-8 text-center">
          <p className="text-gray-400 mb-3 sm:mb-4 text-sm sm:text-base">Need help?</p>
          <div className="flex flex-wrap justify-center gap-3 sm:gap-4 text-xs sm:text-sm">
            <a
              href="mailto:support@orla3.com"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              Contact Support
            </a>
            <Link
              href="/#pricing"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              View Pricing Details
            </Link>
            <Link
              href="/login"
              className="text-cobalt-300 hover:text-cobalt-300 transition"
            >
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
