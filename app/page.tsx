'use client';

import Link from 'next/link';
import { useState, useRef } from 'react';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const { scrollYProgress } = useScroll();
  const heroY = useTransform(scrollYProgress, [0, 0.5], ['0%', '20%']);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.2], [1, 0.3]);

  const plans = [
    {
      name: 'Starter',
      price: billingCycle === 'monthly' ? 99 : 990,
      credits: 500,
      users: 1,
      description: 'Perfect for solo creators and freelancers',
      features: [
        '1 user included',
        'Google/OneDrive/Dropbox shared drive required',
        '500 credits/month',
        '~250 social captions or 100 blog posts',
        '25 AI-generated ultra images',
        '2 AI-generated videos (8-sec)',
        '1 brand voice profile',
        '9 social platform publishing',
        'Content calendar',
        'Basic competitor tracking',
        'Credit rollover (up to 250)',
      ],
      cta: 'Get Started',
      popular: false,
    },
    {
      name: 'Professional',
      price: billingCycle === 'monthly' ? 249 : 2490,
      credits: 2000,
      users: 3,
      additionalUserPrice: 50,
      description: 'Ideal for small teams and boutique agencies',
      features: [
        '3 users included',
        'Additional users: $50/user/month',
        '5GB ORLA³ storage OR shared drive',
        '2,000 credits/month',
        '~1,000 social captions or 400 blog posts',
        '100 AI-generated ultra images',
        '10 AI-generated videos (8-sec)',
        '3 brand voice profiles',
        'Google/OneDrive/Dropbox team integration',
        '9 social platform publishing',
        'Auto-publishing & scheduling',
        'Advanced competitor analysis (5 competitors)',
        'Priority support',
        'Credit rollover (up to 1,000)',
      ],
      cta: 'Get Started',
      popular: true,
    },
    {
      name: 'Business',
      price: billingCycle === 'monthly' ? 499 : 4990,
      credits: 6000,
      users: 10,
      additionalUserPrice: 35,
      description: 'For growing marketing teams and agencies',
      features: [
        '10 users included',
        'Additional users: $35/user/month',
        '25GB ORLA³ storage OR shared drive',
        '6,000 credits/month',
        '~3,000 social captions or 1,200 blog posts',
        '300 AI-generated ultra images',
        '30 AI-generated videos (8-sec)',
        '10 brand voice profiles',
        'Google/OneDrive/Dropbox team integration',
        '9 social platform publishing',
        'Team collaboration & roles',
        'Unlimited competitor tracking',
        'API access',
        'White-label options',
        'Credit rollover (up to 3,000)',
      ],
      cta: 'Get Started',
      popular: false,
    },
    {
      name: 'Enterprise',
      price: 999,
      credits: 20000,
      users: 25,
      description: 'Custom solutions for large organizations',
      features: [
        '25+ users included',
        'Unlimited team members available',
        'Custom pricing for additional users',
        '100GB ORLA³ storage OR unlimited shared drive',
        '20,000 credits/month',
        '~10,000 social captions or 4,000 blog posts',
        '1,000 AI-generated ultra images',
        '100 AI-generated videos (8-sec)',
        'Unlimited brand voices',
        'Google/OneDrive/Dropbox team integration',
        '9 social platform publishing',
        'Advanced team permissions',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantees',
        'Full credit rollover (unlimited)',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-black">
      {/* Navigation */}
      <nav className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                ORLA³
              </h1>
            </div>
            <div className="flex items-center gap-2 sm:gap-3 md:gap-4">
              <Link
                href="/login"
                className="text-gray-300 hover:text-white transition px-3 sm:px-4 py-2"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white px-6 py-2 rounded-lg font-semibold transition"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24 text-center relative overflow-hidden">
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="relative z-10"
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="inline-block mb-4 px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt/20 to-royal/20 rounded-full border border-cobalt-400/30"
          >
            <span className="text-cobalt-300 font-semibold">
              Marketing Superpowers, Powered by AI
            </span>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.9, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
            className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-black text-white mb-3 sm:mb-4 md:mb-6"
          >
            Automate Your Marketing
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
              Keep Creating Brilliance
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="text-base sm:text-lg md:text-xl text-gray-300 mb-3 sm:mb-4 md:mb-6 lg:mb-8 max-w-3xl mx-auto"
          >
            Let AI handle the routine marketing - daily posts, captions, blog updates - so you can
            focus on what matters: <span className="text-white font-bold">your craft</span>. Access{' '}
            <span className="text-white font-bold">8 specialized AI models</span> and{' '}
            <span className="text-white font-bold">millions of stock assets</span> to keep your
            business visible while you do what you do best.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="flex gap-2 sm:gap-3 md:gap-4 justify-center mb-3 sm:mb-4 md:mb-6 lg:mb-8"
          >
            <Link
              href="/signup"
              className="bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white px-4 py-3 sm:px-6 sm:py-4 md:px-8 rounded-lg font-bold text-lg transition-all duration-300 ease-out shadow-2xl hover:scale-[1.02] hover:shadow-cobalt/50"
            >
              Get Started
            </Link>
            <button className="border-2 border-white/20 hover:border-white/40 text-white px-4 py-3 sm:px-6 sm:py-4 md:px-8 rounded-lg font-bold text-lg transition-all duration-300 ease-out backdrop-blur-sm hover:scale-[1.02]">
              Watch Demo
            </button>
          </motion.div>

          {/* Social Proof */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.6, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-wrap justify-center gap-2 sm:gap-3 md:gap-4 lg:gap-6 xl:gap-8 text-gray-400 text-sm"
          >
            <div className="flex items-center gap-2">
              <span className="text-gold"></span> Cancel anytime
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gold"></span> Instant access
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gold"></span> All features included
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Powered By Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 border-y border-white/10">
        <h3 className="text-center text-gray-400 mb-8 uppercase tracking-wider text-sm font-bold">
          Powered By Industry-Leading AI
        </h3>
        <div className="flex flex-wrap justify-center items-center gap-2 sm:gap-3 md:gap-4 lg:gap-6 text-gray-300">
          {[
            'Claude Sonnet 4',
            'GPT-4o',
            'GPT-4o Mini',
            'Gemini 2.0 Flash',
            'Perplexity AI',
            'Google Imagen 4 Ultra',
            'Google Veo 3.1',
            'Unsplash API',
            'Pexels API'
          ].map((tech, idx) => (
            <span key={idx} className="text-sm font-medium">
              {tech}
            </span>
          ))}
        </div>
      </section>

      {/* ROI Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-4 sm:mb-6 md:mb-8 lg:mb-12"
        >
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
            Strategy-First Marketing That Actually Works
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto">
            Not just content generation. A complete marketing system that starts with you, analyzes your market,
            builds strategy, and executes across all channels automatically.
          </p>
        </motion.div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 mb-16">
          {[
            {
              metric: 'AI Auto-Select',
              label: 'Best Model, Best Price',
              description: 'Our system automatically chooses the optimal AI model for each task from 8 options, maximizing your credits and results at the best live market price.',
            },
            {
              metric: 'Chain Reaction',
              label: 'Strategy-First System',
              description:
                'Starts with your brand identity and strengths, analyzes competitor strategies, identifies your unique angle, then generates all content from this strategic foundation.',
            },
            {
              metric: 'Full Automation',
              label: 'Knowledge → Results',
              description:
                'Feed your knowledge once. Get personalized strategy. Apply automated actions. Schedule everywhere from one place. Sit back and watch the results compound.',
            },
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.6, delay: idx * 0.1, ease: [0.22, 1, 0.36, 1] }}
              whileHover={{ y: -4, transition: { duration: 0.3, ease: 'easeOut' } }}
              className="bg-gradient-to-br from-cobalt/10 to-royal/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-cobalt-400/30 hover:border-cobalt-400/50 text-center hover:shadow-2xl hover:shadow-cobalt/20 transition-all duration-300"
            >
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: idx * 0.1 + 0.2, ease: [0.22, 1, 0.36, 1] }}
                className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold mb-2"
              >
                {stat.metric}
              </motion.div>
              <div className="text-white font-bold text-base sm:text-lg md:text-xl mb-3">{stat.label}</div>
              <p className="text-gray-400">{stat.description}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-4 sm:mb-6 md:mb-8 lg:mb-12"
        >
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
            Professional Marketing Tools at Your Fingertips
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto">
            8 specialized AI models working together to create content that converts
          </p>
        </motion.div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
          {[
            {
              icon: '',
              title: 'Elite AI Content Writers',
              description:
                'Claude Sonnet 4, GPT-4, and Gemini automatically selected for each task. Blog posts, social captions, ad copy all written by the best AI for the job.',
              time: 'Save 30 hours/week',
            },
            {
              icon: '',
              title: 'Photorealistic Image & Video',
              description:
                'Imagen 4 Ultra for stunning images, Veo 3.1 for cinematic videos, plus millions of Unsplash stock photos. Never run out of visual content.',
              time: 'Save 10 hours/week',
            },
            {
              icon: '',
              title: 'Auto-Pilot Social Media',
              description:
                'AI writes, designs, and publishes across all platforms. Schedule months of content in minutes. Never miss a post again.',
              time: 'Save 15 hours/week',
            },
            {
              icon: '',
              title: 'Your Brand Voice, Perfected',
              description:
                'Train AI on your writing style, tone, and brand guidelines. Every piece of content sounds exactly like you wrote it.',
              time: 'Instant consistency',
            },
            {
              icon: '',
              title: 'Spy on Your Competitors',
              description:
                'AI-powered competitor analysis tracks their strategies, content, and trends. Know what works before you spend a penny.',
              time: 'Real-time insights',
            },
            {
              icon: '',
              title: 'Searchable Content Vault',
              description:
                'Every asset, every post, every campaign organized and searchable. Find what you need in seconds, not hours.',
              time: 'Instant access',
            },
          ].map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.6, delay: index * 0.08, ease: [0.22, 1, 0.36, 1] }}
              whileHover={{ y: -4, transition: { duration: 0.3, ease: 'easeOut' } }}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20 hover:border-cobalt-400/50 hover:shadow-2xl hover:shadow-cobalt/10 transition-all duration-300 group"
            >
              <div className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl mb-4">{feature.icon}</div>
              <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-300 mb-4">{feature.description}</p>
              <div className="inline-block px-3 py-1 bg-gold/20 border border-gold/50 rounded-full">
                <span className="text-gold text-sm font-semibold">{feature.time}</span>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Social Engagement Suite - NEW SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24 relative overflow-hidden">
        {/* Animated background gradient */}
        <motion.div
          animate={{
            background: [
              'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 80% 50%, rgba(139, 92, 246, 0.1) 0%, transparent 50%)',
              'radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.1) 0%, transparent 50%)',
            ],
          }}
          transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 pointer-events-none"
        />

        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="text-center mb-4 sm:mb-6 md:mb-8 lg:mb-12"
          >
            <div className="inline-block mb-4 px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt/20 to-royal/20 rounded-full border border-cobalt-400/30">
              <span className="text-cobalt-300 font-semibold">Social Engagement Suite</span>
            </div>
            <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
              Don't Just Post. <span className="text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">Engage & Grow</span>
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto">
              AI-powered engagement tools that find conversations, reply authentically, and build relationships while you focus on creating
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8 mb-12">
            {[
              {
                title: 'AI Comment Replies',
                description: 'Automatically generate brand-aligned responses to comments across all platforms. Never leave your audience hanging again.',
                features: ['Brand voice consistency', 'Sentiment analysis', 'Priority sorting', 'Multi-platform support'],
                gradient: 'from-blue-500/20 to-cobalt/20',
                borderGradient: 'from-blue-400/30 to-cobalt-400/30',
              },
              {
                title: 'Social Discovery',
                description: 'Search non-follower posts by keywords and trends. Find and engage with relevant conversations before your competitors do.',
                features: ['Keyword tracking', 'Trend monitoring', 'Real-time discovery', 'Engagement suggestions'],
                gradient: 'from-royal/20 to-royal/20',
                borderGradient: 'from-royal-400/30 to-royal/30',
              },
              {
                title: 'Trends Search',
                description: 'Real-time trending topics discovery to inform your content strategy and engagement timing. Stay ahead of the curve.',
                features: ['Live trend analysis', 'Industry insights', 'Timing optimization', 'Content opportunities'],
                gradient: 'from-gold/20 to-gold-intense/20',
                borderGradient: 'from-gold/30 to-gold-intense/30',
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ duration: 0.6, delay: index * 0.1, ease: [0.22, 1, 0.36, 1] }}
                whileHover={{ y: -4, transition: { duration: 0.3, ease: 'easeOut' } }}
                className={`bg-gradient-to-br ${feature.gradient} backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-gradient-to-r ${feature.borderGradient} hover:shadow-2xl hover:shadow-cobalt/20 transition-all duration-300`}
              >
                <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-gray-300 mb-3 sm:mb-4 md:mb-6">{feature.description}</p>
                <ul className="space-y-2">
                  {feature.features.map((item, idx) => (
                    <motion.li
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.4, delay: index * 0.1 + 0.3 + idx * 0.05, ease: [0.22, 1, 0.36, 1] }}
                      className="flex items-center gap-2 text-sm text-gray-400"
                    >
                      <span className="text-gold">✓</span>
                      <span>{item}</span>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="text-center"
          >
            <div className="inline-block bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20">
              <p className="text-gray-300 mb-4">
                <span className="text-white font-bold">Engagement Suite</span> transforms passive posting into active community building
              </p>
              <div className="flex flex-wrap justify-center gap-2 sm:gap-3 md:gap-4 lg:gap-6 text-sm">
                <div className="text-center">
                  <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">3x</div>
                  <div className="text-gray-400">More Engagement</div>
                </div>
                <div className="text-center">
                  <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-royal to-royal mb-1">5x</div>
                  <div className="text-gray-400">Faster Growth</div>
                </div>
                <div className="text-center">
                  <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense mb-1">10x</div>
                  <div className="text-gray-400">Time Saved</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Premium Content CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24">
        <div className="bg-gradient-to-br from-royal/20 to-cobalt/20 backdrop-blur-lg rounded-3xl p-6 sm:p-8 md:p-12 border border-cobalt-400/30">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8 items-center">
            <div>
              <div className="inline-block mb-4 px-3 sm:px-4 py-2 bg-cobalt/30 rounded-full border border-cobalt-400/50">
                <span className="text-cobalt-300 font-semibold">Premium Content</span>
              </div>
              <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
                Need Professional Videography?
              </h2>
              <p className="text-base sm:text-lg md:text-xl text-gray-300 mb-3 sm:mb-4 md:mb-6">
                AI handles your daily marketing. When you need cinematic videos, event coverage,
                or premium videography work, connect with verified UK videographers near you.
              </p>
              <ul className="space-y-3 mb-3 sm:mb-4 md:mb-6 lg:mb-8 text-gray-300">
                <li className="flex items-start gap-2">
                  <span className="text-gold mt-1"></span>
                  <span>Browse portfolios of verified UK videographers</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gold mt-1"></span>
                  <span>Find local videography talent by location, style, and budget</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-gold mt-1"></span>
                  <span>Commission custom video content for your biggest campaigns</span>
                </li>
              </ul>
              <a
                href="https://orla3.com/browse"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-700 hover:to-gold-700 text-white px-4 py-3 sm:px-6 sm:py-4 md:px-8 rounded-lg font-bold text-lg transition shadow-2xl"
              >
                Find Videographers Near Me →
              </a>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { icon: '', label: 'Videographers', count: '500+' },
                { icon: '', label: 'Wedding Films', count: '200+' },
                { icon: '', label: 'Corporate Video', count: '150+' },
                { icon: '', label: 'Event Coverage', count: '250+' },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="bg-white/10 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/20 text-center"
                >
                  <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl mb-2">{item.icon}</div>
                  <div className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-1">{item.count}</div>
                  <div className="text-gray-400 text-sm">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SEO & AI Search Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24 bg-gradient-to-b from-transparent via-cobalt/5 to-transparent">
        <div className="text-center mb-4 sm:mb-6 md:mb-8 lg:mb-12">
          <div className="inline-block mb-4 px-3 sm:px-4 py-2 bg-gradient-to-r from-gold/20 to-cobalt/20 rounded-full border border-gold/30">
            <span className="text-gold font-semibold">
              Built for Discovery
            </span>
          </div>
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
            Optimized for SEO & AI Search
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 max-w-3xl mx-auto">
            Our blog posts aren't just well-written—they're engineered to rank on Google
            and appear in AI search results like ChatGPT, Perplexity, and Claude.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:gap-8 mb-12">
          {/* Traditional SEO */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20 hover:border-gold/50 transition">
            <div className="flex items-start gap-2 sm:gap-3 md:gap-4 mb-3 sm:mb-4 md:mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-gold to-gold-600 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-2">Traditional Search Engines</h3>
                <p className="text-gold font-semibold mb-4">Rank Higher on Google</p>
              </div>
            </div>
            <ul className="space-y-3 text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-gold mt-1">✓</span>
                <span><strong className="text-white">SEO-optimized headlines</strong> with target keywords naturally integrated</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-gold mt-1">✓</span>
                <span><strong className="text-white">Structured content</strong> with proper H1-H6 hierarchy for crawlers</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-gold mt-1">✓</span>
                <span><strong className="text-white">Meta descriptions</strong> crafted to improve click-through rates</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-gold mt-1">✓</span>
                <span><strong className="text-white">Internal linking</strong> suggestions to boost domain authority</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-gold mt-1">✓</span>
                <span><strong className="text-white">Long-form content</strong> (1500-3000 words) that ranks better</span>
              </li>
            </ul>
          </div>

          {/* AI Search */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20 hover:border-cobalt/50 transition">
            <div className="flex items-start gap-2 sm:gap-3 md:gap-4 mb-3 sm:mb-4 md:mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-cobalt to-royal rounded-xl flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-2">AI Search Engines</h3>
                <p className="text-cobalt-300 font-semibold mb-4">Cited by ChatGPT, Perplexity & Claude</p>
              </div>
            </div>
            <ul className="space-y-3 text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-cobalt-300 mt-1">✓</span>
                <span><strong className="text-white">Authoritative tone</strong> that AI models recognize as credible sources</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cobalt-300 mt-1">✓</span>
                <span><strong className="text-white">Factual, well-researched</strong> content AI assistants trust to cite</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cobalt-300 mt-1">✓</span>
                <span><strong className="text-white">Clear answers</strong> to common questions in your niche</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cobalt-300 mt-1">✓</span>
                <span><strong className="text-white">Up-to-date information</strong> that stays relevant for AI training</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-cobalt-300 mt-1">✓</span>
                <span><strong className="text-white">Your domain gets mentioned</strong> when users ask AI about your topics</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-gold/10 to-gold-intense/10 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-gold/20 text-center">
            <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense mb-2">
              2-3x
            </div>
            <p className="text-white font-semibold mb-1">Better Rankings</p>
            <p className="text-gray-400 text-sm">SEO-optimized posts rank higher faster</p>
          </div>
          <div className="bg-gradient-to-br from-cobalt/10 to-royal/10 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-cobalt/20 text-center">
            <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-2">
              100%
            </div>
            <p className="text-white font-semibold mb-1">AI-Ready Content</p>
            <p className="text-gray-400 text-sm">Formatted for AI search engines to cite</p>
          </div>
          <div className="bg-gradient-to-br from-gold/10 to-gold-intense/10 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-gold/20 text-center">
            <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense mb-2">
              24/7
            </div>
            <p className="text-white font-semibold mb-1">Discovery</p>
            <p className="text-gray-400 text-sm">Your content works while you sleep</p>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24" id="pricing">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center mb-4 sm:mb-6 md:mb-8 lg:mb-12"
        >
          <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4">
            Simple, Transparent Pricing
          </h2>
          <p className="text-base sm:text-lg md:text-xl text-gray-300">
            Pay only for what you use with our flexible credit system
          </p>
        </motion.div>

        {/* Billing Toggle */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="flex justify-center mb-4 sm:mb-6 md:mb-8 lg:mb-12"
        >
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-1 inline-flex border border-white/20">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 rounded-md font-semibold transition ${
                billingCycle === 'monthly'
                  ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-6 py-2 rounded-md font-semibold transition ${
                billingCycle === 'annual'
                  ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Annual <span className="text-gold">(Save 17%)</span>
            </button>
          </div>
        </motion.div>

        {/* Pricing Cards */}
        <motion.div
          initial="initial"
          animate="animate"
          variants={{
            initial: {},
            animate: {
              transition: {
                staggerChildren: 0.08,
                delayChildren: 0.2,
              },
            },
          }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8"
        >
          {plans.map((plan, index) => (
            <motion.div
              key={index}
              variants={{
                initial: {
                  opacity: 0,
                  y: 20,
                },
                animate: {
                  opacity: 1,
                  y: 0,
                  transition: {
                    duration: 0.5,
                    ease: [0.22, 1, 0.36, 1],
                  },
                },
              }}
              whileHover={{ y: -8, transition: { duration: 0.2, ease: 'easeOut' } }}
              className={`bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border ${
                plan.popular
                  ? 'border-cobalt-400 ring-2 ring-blue-400/50 scale-105'
                  : 'border-white/20'
              } hover:border-cobalt-400/50 hover:shadow-2xl hover:shadow-cobalt/20 transition-all duration-300 relative`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-cobalt to-royal text-white px-3 sm:px-4 py-1 rounded-full text-sm font-bold">
                    Most Popular
                  </span>
                </div>
              )}

              <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm mb-4">{plan.description}</p>

              <div className="mb-3 sm:mb-4 md:mb-6">
                <span className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-black text-white">£{plan.price}</span>
                {plan.name !== 'Enterprise' && (
                  <span className="text-gray-400">
                    /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                  </span>
                )}
              </div>

              <div className="mb-3 sm:mb-4 md:mb-6">
                <div className="bg-gradient-to-r from-cobalt/20 to-royal/20 rounded-lg p-3 border border-cobalt-400/30">
                  <p className="text-cobalt-300 font-bold text-center">
                    {plan.credits.toLocaleString()} Credits/month
                  </p>
                </div>
              </div>

              <ul className="space-y-3 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-300">
                    <span className="text-gold mt-1"></span>
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.cta === 'Contact Sales' ? '/contact' : '/signup'}
                className={`block w-full py-3 rounded-lg font-bold text-center transition ${
                  plan.popular
                    ? 'bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </motion.div>

        {/* Credit Cost Breakdown */}
        <div className="mt-16 bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20">
          <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6 text-center">
            How Credits Work
          </h3>
          <div className="grid md:grid-cols-5 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            {[
              { action: 'Social Caption', credits: 2, icon: '' },
              { action: 'Full Blog Post', credits: 5, icon: '' },
              { action: 'AI Image (Standard)', credits: 10, icon: '' },
              { action: 'AI Image (Ultra)', credits: 20, icon: '' },
              { action: 'AI Video (8-sec)', credits: 200, icon: '' },
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl mb-2">{item.icon}</div>
                <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold mb-2">
                  {item.credits}
                </div>
                <div className="text-gray-300 text-sm">{item.action}</div>
              </div>
            ))}
          </div>
          <p className="text-center text-gray-400 mt-6 text-sm">
            Each plan shows approximate content output. Mix and match however you need - your credits, your choice.
          </p>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 lg:py-24 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="bg-gradient-to-r from-cobalt to-royal rounded-3xl p-6 sm:p-8 md:p-12 shadow-2xl"
        >
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
            className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-bold text-white mb-4"
          >
            Supercharge Your Marketing Today
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="text-base sm:text-lg md:text-xl text-cobalt-100 mb-3 sm:mb-4 md:mb-6 lg:mb-8"
          >
            CMO-level strategy, professional content, and enterprise-grade execution,
            powered by 8 specialized AI models at a fraction of traditional costs.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            <Link
              href="/signup"
              className="bg-white text-cobalt px-4 py-3 sm:px-6 sm:py-4 md:px-8 rounded-lg font-bold text-lg hover:bg-gray-100 hover:scale-[1.02] transition-all duration-300 ease-out inline-block mb-4 shadow-lg"
            >
              Get Started Now
            </Link>
          </motion.div>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.45, ease: [0.22, 1, 0.36, 1] }}
            className="text-cobalt-200 text-sm"
          >
            Cancel anytime • Professional marketing capabilities • Instant access
          </motion.p>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-4 md:px-8 py-12">
          <div className="grid md:grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3 md:gap-4 lg:gap-6 xl:gap-8 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
            <div>
              <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold mb-4">
                ORLA³
              </h3>
              <p className="text-gray-400">
                AI-powered marketing automation for modern businesses
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <a href="#" className="hover:text-white transition">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="hover:text-white transition">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    API
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <a href="#" className="hover:text-white transition">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    Blog
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    Contact
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400">
                <li>
                  <Link href="/privacy" className="hover:text-white transition">
                    Privacy
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="hover:text-white transition">
                    Terms
                  </Link>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 text-center text-gray-500">
            <p>&copy; 2024 ORLA³ Studio. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
