import Link from 'next/link';
import { motion } from 'framer-motion';
import { AnimatedPage } from '@/components/AnimatedPage';
import { fadeInUp } from '@/lib/motion';

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center">
              <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                ORLA³
              </h1>
            </Link>
            <div className="flex items-center gap-3 sm:gap-4">
              <Link
                href="/login"
                className="text-gray-300 hover:text-white transition px-3 sm:px-4 py-2 text-sm sm:text-base"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white px-4 sm:px-6 py-2 rounded-lg font-semibold transition text-sm sm:text-base"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 md:py-20">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl sm:rounded-3xl p-6 sm:p-8 md:p-12 border border-white/20">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mb-4 sm:mb-6">Terms of Service</h1>
          <p className="text-gray-400 mb-6 sm:mb-8 text-sm sm:text-base">
            Last updated: November 16, 2025
          </p>

          <div className="space-y-6 sm:space-y-8 text-gray-300">
            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">1. Acceptance of Terms</h2>
              <p className="text-sm sm:text-base">
                By accessing and using ORLA³ Studio (&quot;the Service&quot;), you accept and agree to be bound by the terms and
                provision of this agreement. If you do not agree to abide by the above, please do not use this service.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">2. Description of Service</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                ORLA³ provides an AI-powered marketing automation platform that includes:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>AI content generation (blogs, social captions, images, videos)</li>
                <li>Social media publishing across 9 platforms</li>
                <li>Cloud storage integration (Google Drive, OneDrive, Dropbox)</li>
                <li>Brand voice synthesis and competitor analysis</li>
                <li>Content calendar and scheduling</li>
                <li>Team collaboration tools</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">3. User Accounts</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                To use the Service, you must:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Be at least 18 years of age</li>
                <li>Provide accurate, current, and complete registration information</li>
                <li>Maintain the security of your password and account</li>
                <li>Verify your email address</li>
                <li>Subscribe to a paid plan to access the platform</li>
              </ul>
              <p className="mt-3 sm:mt-4 text-sm sm:text-base">
                You are responsible for all activities that occur under your account.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">4. Subscription Plans and Billing</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                ORLA³ operates on a subscription basis with the following terms:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li><strong>Plans:</strong> Starter, Professional, Business, and Enterprise tiers</li>
                <li><strong>Billing:</strong> Monthly or annual billing cycles</li>
                <li><strong>Credits:</strong> Each plan includes monthly credits for AI content generation</li>
                <li><strong>Payment:</strong> All payments processed securely through Stripe</li>
                <li><strong>Cancellation:</strong> You may cancel your subscription at any time</li>
                <li><strong>Refunds:</strong> No refunds for partial months. Credits reset monthly and do not carry over (except rollover limits per plan)</li>
                <li><strong>Price Changes:</strong> We reserve the right to change prices with 30 days notice</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">5. Credit System</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                ORLA³ uses a credit-based system for AI content generation:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Social Caption: 2 credits</li>
                <li>Blog Post: 5 credits</li>
                <li>AI Image (Standard): 10 credits</li>
                <li>AI Image (Ultra): 20 credits</li>
                <li>AI Video (8-second): 200 credits</li>
              </ul>
              <p className="mt-3 sm:mt-4 text-sm sm:text-base">
                Credits reset on your monthly renewal date. Unused credits may roll over up to plan limits.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">6. Acceptable Use Policy</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                You agree NOT to use the Service to:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Generate illegal, harmful, threatening, abusive, or defamatory content</li>
                <li>Violate any intellectual property rights</li>
                <li>Spam, phish, or engage in fraudulent activity</li>
                <li>Share your account credentials with others</li>
                <li>Attempt to reverse engineer or hack the platform</li>
                <li>Resell or redistribute AI-generated content as a service</li>
                <li>Generate content that violates third-party platform policies</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">7. Content Ownership</h2>
              <p className="text-sm sm:text-base">
                You retain all rights to content you create using ORLA³. We do not claim ownership of your generated content.
                However, you grant us a license to store, process, and display your content to provide the Service. You are
                responsible for ensuring your generated content complies with all applicable laws and third-party rights.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">8. Third-Party Integrations</h2>
              <p className="text-sm sm:text-base">
                ORLA³ integrates with third-party services (social platforms, cloud storage, AI providers). Your use of these
                integrations is subject to their respective terms of service. We are not responsible for third-party service
                availability, changes, or policies.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">9. Service Availability</h2>
              <p className="text-sm sm:text-base">
                We strive for 99.9% uptime but do not guarantee uninterrupted service. We may suspend service for maintenance,
                updates, or emergency repairs. We are not liable for any downtime or service interruptions.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">10. Limitation of Liability</h2>
              <p className="text-sm sm:text-base">
                ORLA³ is provided &quot;as is&quot; without warranties of any kind. We are not liable for any indirect, incidental, special,
                or consequential damages arising from your use of the Service. Our total liability shall not exceed the amount
                you paid in the past 12 months.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">11. Termination</h2>
              <p className="text-sm sm:text-base">
                We reserve the right to suspend or terminate your account if you violate these Terms or engage in fraudulent
                activity. Upon termination, you will lose access to your account and all associated content. You may delete
                your account at any time from Profile Settings.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">12. Changes to Terms</h2>
              <p className="text-sm sm:text-base">
                We may modify these Terms at any time. Material changes will be notified via email. Continued use of the Service
                after changes constitutes acceptance of the new Terms.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">13. Governing Law</h2>
              <p className="text-sm sm:text-base">
                These Terms shall be governed by the laws of the United Kingdom. Any disputes shall be resolved in UK courts.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">14. Contact Information</h2>
              <p className="text-sm sm:text-base">
                For questions about these Terms, please contact us:
              </p>
              <ul className="mt-3 sm:mt-4 space-y-2 text-sm sm:text-base">
                <li>Email: <a href="mailto:legal@orla3.ai" className="text-cobalt-300 hover:text-cobalt-400">legal@orla3.ai</a></li>
                <li>Support: <a href="mailto:support@orla3.ai" className="text-cobalt-300 hover:text-cobalt-400">support@orla3.ai</a></li>
              </ul>
            </section>
          </div>

          <div className="mt-8 sm:mt-12 pt-6 sm:pt-8 border-t border-white/20">
            <Link
              href="/"
              className="inline-block px-4 sm:px-6 py-2 sm:py-3 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white rounded-lg font-semibold transition text-sm sm:text-base"
            >
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          <div className="text-center text-gray-500 text-sm">
            <p>&copy; 2024 ORLA³ Studio. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
