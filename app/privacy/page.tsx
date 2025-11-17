import Link from 'next/link';
import { motion } from 'framer-motion';
import { AnimatedPage } from '@/components/AnimatedPage';
import { fadeInUp } from '@/lib/motion';

export default function PrivacyPolicyPage() {
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
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mb-4 sm:mb-6">Privacy Policy</h1>
          <p className="text-gray-400 mb-6 sm:mb-8 text-sm sm:text-base">
            Last updated: November 16, 2025
          </p>

          <div className="space-y-6 sm:space-y-8 text-gray-300">
            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">1. Information We Collect</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                ORLA³ Studio (&quot;we,&quot; &quot;us,&quot; or &quot;our&quot;) collects information that you provide directly to us when you:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Create an account and use our marketing automation platform</li>
                <li>Connect your social media accounts and cloud storage services</li>
                <li>Generate content using our AI-powered tools</li>
                <li>Subscribe to our paid plans and make payments</li>
                <li>Communicate with our support team</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">2. How We Use Your Information</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">We use the information we collect to:</p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Provide, maintain, and improve our marketing automation services</li>
                <li>Process your transactions and manage your subscription</li>
                <li>Generate AI-powered content based on your brand voice and preferences</li>
                <li>Publish content to your connected social media platforms</li>
                <li>Sync with your cloud storage services (Google Drive, OneDrive, Dropbox)</li>
                <li>Send you technical notices, updates, and support messages</li>
                <li>Respond to your comments and questions</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">3. Third-Party Services</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">
                ORLA³ integrates with various third-party services to provide our functionality:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li><strong>AI Models:</strong> OpenAI (GPT-4), Anthropic (Claude), Google (Gemini, Imagen, Veo), Perplexity AI</li>
                <li><strong>Social Platforms:</strong> Instagram, Facebook, LinkedIn, Twitter, TikTok, Pinterest, YouTube, Reddit</li>
                <li><strong>Cloud Storage:</strong> Google Drive, Microsoft OneDrive, Dropbox</li>
                <li><strong>Payment Processing:</strong> Stripe</li>
                <li><strong>Media Assets:</strong> Unsplash, Pexels</li>
              </ul>
              <p className="mt-3 sm:mt-4 text-sm sm:text-base">
                Each third-party service has its own privacy policy. We encourage you to review their policies.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">4. Data Security</h2>
              <p className="text-sm sm:text-base">
                We implement industry-standard security measures to protect your personal information. All data is
                encrypted in transit using SSL/TLS. Access tokens for connected services are securely encrypted and stored.
                However, no method of transmission over the internet is 100% secure.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">5. Data Retention</h2>
              <p className="text-sm sm:text-base">
                We retain your information for as long as your account is active or as needed to provide you services.
                You may delete your account at any time from your Profile Settings. Upon account deletion, we will
                permanently delete all your personal data, content, and connected service tokens within 30 days.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">6. Your Rights</h2>
              <p className="mb-3 sm:mb-4 text-sm sm:text-base">You have the right to:</p>
              <ul className="list-disc list-inside space-y-2 ml-4 text-sm sm:text-base">
                <li>Access, update, or delete your personal information</li>
                <li>Disconnect any connected social media or cloud storage accounts</li>
                <li>Export your generated content</li>
                <li>Cancel your subscription at any time</li>
                <li>Request a copy of your data</li>
              </ul>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">7. Cookies and Tracking</h2>
              <p className="text-sm sm:text-base">
                We use cookies and similar tracking technologies to track activity on our platform and store certain information.
                You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">8. Children&apos;s Privacy</h2>
              <p className="text-sm sm:text-base">
                Our service is not intended for users under the age of 18. We do not knowingly collect personal information
                from children under 18. If you become aware that a child has provided us with personal information, please
                contact us.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">9. Changes to This Policy</h2>
              <p className="text-sm sm:text-base">
                We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new
                Privacy Policy on this page and updating the &quot;Last updated&quot; date.
              </p>
            </section>

            <section>
              <h2 className="text-xl sm:text-2xl font-bold text-white mb-3 sm:mb-4">10. Contact Us</h2>
              <p className="text-sm sm:text-base">
                If you have any questions about this Privacy Policy, please contact us:
              </p>
              <ul className="mt-3 sm:mt-4 space-y-2 text-sm sm:text-base">
                <li>Email: <a href="mailto:privacy@orla3.ai" className="text-cobalt-300 hover:text-cobalt-400">privacy@orla3.ai</a></li>
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
