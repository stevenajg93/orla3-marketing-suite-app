'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function LandingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  const plans = [
    {
      name: 'Starter',
      price: billingCycle === 'monthly' ? 29 : 290,
      credits: 500,
      description: 'Perfect for freelancers and content creators',
      features: [
        '500 credits/month',
        '~100 social captions or 50 blog posts',
        '25 AI-generated ultra images',
        '1 brand voice profile',
        '3 social accounts',
        'Content calendar',
        'Basic competitor tracking (2 competitors)',
        'Credit rollover (up to 250)',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Professional',
      price: billingCycle === 'monthly' ? 79 : 790,
      credits: 2000,
      description: 'Ideal for small businesses and agencies',
      features: [
        '2,000 credits/month',
        '~400 social posts or 200 blog posts',
        '100 AI-generated ultra images',
        '3 brand voice profiles',
        '10 social accounts',
        'Auto-publishing & scheduling',
        'Advanced competitor analysis (5 competitors)',
        'Priority support',
        'Credit rollover (up to 1,000)',
      ],
      cta: 'Start Free Trial',
      popular: true,
    },
    {
      name: 'Business',
      price: billingCycle === 'monthly' ? 199 : 1990,
      credits: 6000,
      description: 'For growing companies and marketing teams',
      features: [
        '6,000 credits/month',
        '~1,200 social posts or 600 blog posts',
        '300 AI-generated ultra images',
        '10 brand voice profiles',
        '25 social accounts',
        'Multi-user collaboration (5 seats)',
        'Unlimited competitor tracking',
        'API access',
        'White-label options',
        'Credit rollover (up to 3,000)',
      ],
      cta: 'Start Free Trial',
      popular: false,
    },
    {
      name: 'Enterprise',
      price: 499,
      credits: 20000,
      description: 'Custom solutions for large organizations',
      features: [
        '20,000+ credits/month',
        'Unlimited AI content generation',
        'Unlimited brand voices',
        'Unlimited social accounts',
        'Unlimited team members',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantees',
        'Full credit rollover',
      ],
      cta: 'Contact Sales',
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                ORLA³
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/login"
                className="text-gray-300 hover:text-white transition px-4 py-2"
              >
                Sign In
              </Link>
              <Link
                href="/signup"
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-2 rounded-lg font-semibold transition"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="inline-block mb-4 px-4 py-2 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-full border border-blue-400/30">
          <span className="text-blue-300 font-semibold">
            🚀 Your Entire Marketing Team, Powered by AI
          </span>
        </div>
        <h1 className="text-6xl md:text-7xl font-black text-white mb-6">
          Save 40+ Hours Per Week
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            Creating Viral Content
          </span>
        </h1>
        <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
          Access <span className="text-white font-bold">8 world-class AI models</span>,{' '}
          <span className="text-white font-bold">millions of stock assets</span>, and{' '}
          <span className="text-white font-bold">automated publishing</span> — all in one
          platform. Get the results of a £100k/year marketing team for less than a gym
          membership.
        </p>
        <div className="flex gap-4 justify-center mb-8">
          <Link
            href="/signup"
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 rounded-lg font-bold text-lg transition shadow-2xl"
          >
            Start Free Trial
          </Link>
          <button className="border-2 border-white/20 hover:border-white/40 text-white px-8 py-4 rounded-lg font-bold text-lg transition backdrop-blur-sm">
            Watch Demo
          </button>
        </div>

        {/* Social Proof */}
        <div className="flex flex-wrap justify-center gap-8 text-gray-400 text-sm">
          <div className="flex items-center gap-2">
            <span className="text-green-400">✓</span> No credit card required
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-400">✓</span> Cancel anytime
          </div>
          <div className="flex items-center gap-2">
            <span className="text-green-400">✓</span> 14-day free trial
          </div>
        </div>
      </section>

      {/* Powered By Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 border-y border-white/10">
        <h3 className="text-center text-gray-400 mb-8 uppercase tracking-wider text-sm font-bold">
          Powered by Industry-Leading AI
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center">
          {[
            { name: 'Claude Sonnet 4', desc: 'Elite content writing', icon: '🧠' },
            { name: 'GPT-4 Turbo', desc: 'Lightning-fast generation', icon: '⚡' },
            { name: 'Google Gemini', desc: 'Multi-modal intelligence', icon: '💎' },
            { name: 'Imagen 4 Ultra', desc: 'Photorealistic images', icon: '🎨' },
            { name: 'Veo 3.1', desc: 'Cinematic video generation', icon: '🎬' },
            { name: 'Unsplash Pro', desc: 'Millions of stock photos', icon: '📸' },
            { name: 'DALL-E 3', desc: 'Creative visuals', icon: '🖼️' },
            { name: 'Competitor AI', desc: 'Market intelligence', icon: '🔍' },
          ].map((tech, idx) => (
            <div key={idx} className="text-center">
              <div className="text-4xl mb-2">{tech.icon}</div>
              <div className="text-white font-bold text-sm">{tech.name}</div>
              <div className="text-gray-500 text-xs">{tech.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ROI Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-white text-center mb-4">
          Replace Your Entire Marketing Department
        </h2>
        <p className="text-xl text-gray-300 text-center mb-12 max-w-3xl mx-auto">
          Save time, money, and sanity. Get professional results without the professional price tag.
        </p>
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {[
            {
              metric: '40+ Hours',
              label: 'Saved Per Week',
              description: 'Stop spending all day creating content. Let AI do the heavy lifting.',
            },
            {
              metric: '£95k/year',
              label: 'Cost Savings',
              description:
                'Get a senior copywriter, designer, and strategist for £29/month.',
            },
            {
              metric: '10x Faster',
              label: 'Content Production',
              description:
                'Create a month of content in an afternoon. Ship faster than your competitors.',
            },
          ].map((stat, idx) => (
            <div
              key={idx}
              className="bg-gradient-to-br from-blue-600/10 to-purple-600/10 backdrop-blur-lg rounded-2xl p-8 border border-blue-400/30 text-center"
            >
              <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
                {stat.metric}
              </div>
              <div className="text-white font-bold text-xl mb-3">{stat.label}</div>
              <p className="text-gray-400">{stat.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-white text-center mb-4">
          Your AI Marketing Team at Your Fingertips
        </h2>
        <p className="text-xl text-gray-300 text-center mb-12 max-w-3xl mx-auto">
          8 industry-leading AI models working together to create content that converts
        </p>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: '✨',
              title: 'Elite AI Content Writers',
              description:
                'Claude Sonnet 4, GPT-4, and Gemini automatically selected for each task. Blog posts, social captions, ad copy — all written by the best AI for the job.',
              time: 'Save 30 hours/week',
            },
            {
              icon: '🎨',
              title: 'Photorealistic Image & Video',
              description:
                'Imagen 4 Ultra for stunning images, Veo 3.1 for cinematic videos, plus millions of Unsplash stock photos. Never run out of visual content.',
              time: 'Save 10 hours/week',
            },
            {
              icon: '📅',
              title: 'Auto-Pilot Social Media',
              description:
                'AI writes, designs, and publishes across all platforms. Schedule months of content in minutes. Never miss a post again.',
              time: 'Save 15 hours/week',
            },
            {
              icon: '🎯',
              title: 'Your Brand Voice, Perfected',
              description:
                'Train AI on your writing style, tone, and brand guidelines. Every piece of content sounds exactly like you wrote it.',
              time: 'Instant consistency',
            },
            {
              icon: '🔍',
              title: 'Spy on Your Competitors',
              description:
                'AI-powered competitor analysis tracks their strategies, content, and trends. Know what works before you spend a penny.',
              time: 'Real-time insights',
            },
            {
              icon: '📊',
              title: 'Searchable Content Vault',
              description:
                'Every asset, every post, every campaign organized and searchable. Find what you need in seconds, not hours.',
              time: 'Instant access',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20 hover:border-blue-400/50 transition group"
            >
              <div className="text-5xl mb-4">{feature.icon}</div>
              <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-gray-300 mb-4">{feature.description}</p>
              <div className="inline-block px-3 py-1 bg-green-500/20 border border-green-500/50 rounded-full">
                <span className="text-green-300 text-sm font-semibold">{feature.time}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20" id="pricing">
        <h2 className="text-4xl font-bold text-white text-center mb-4">
          Simple, Transparent Pricing
        </h2>
        <p className="text-xl text-gray-300 text-center mb-12">
          Pay only for what you use with our flexible credit system
        </p>

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-1 inline-flex border border-white/20">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 rounded-md font-semibold transition ${
                billingCycle === 'monthly'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-6 py-2 rounded-md font-semibold transition ${
                billingCycle === 'annual'
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Annual <span className="text-green-400">(Save 17%)</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`bg-white/10 backdrop-blur-lg rounded-2xl p-8 border ${
                plan.popular
                  ? 'border-blue-400 ring-2 ring-blue-400/50 scale-105'
                  : 'border-white/20'
              } hover:border-blue-400/50 transition relative`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                    Most Popular
                  </span>
                </div>
              )}

              <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm mb-4">{plan.description}</p>

              <div className="mb-6">
                <span className="text-5xl font-black text-white">£{plan.price}</span>
                {plan.name !== 'Enterprise' && (
                  <span className="text-gray-400">
                    /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                  </span>
                )}
              </div>

              <div className="mb-6">
                <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-lg p-3 border border-blue-400/30">
                  <p className="text-blue-300 font-bold text-center">
                    {plan.credits.toLocaleString()} Credits/month
                  </p>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-300">
                    <span className="text-green-400 mt-1">✓</span>
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.cta === 'Contact Sales' ? '/contact' : '/signup'}
                className={`block w-full py-3 rounded-lg font-bold text-center transition ${
                  plan.popular
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Credit Cost Breakdown */}
        <div className="mt-16 bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
          <h3 className="text-2xl font-bold text-white mb-6 text-center">
            How Credits Work
          </h3>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { action: 'Social Caption', credits: 2 },
              { action: 'Full Blog Post', credits: 5 },
              { action: 'AI Image (Standard)', credits: 10 },
              { action: 'AI Image (Ultra)', credits: 20 },
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
                  {item.credits}
                </div>
                <div className="text-gray-300">{item.action}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-12">
          <h2 className="text-4xl font-bold text-white mb-4">
            Stop Wasting Time on Content Creation
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Get 40+ hours back every week. Your competitors are already using AI — don't get left behind.
          </p>
          <Link
            href="/signup"
            className="bg-white text-purple-600 px-8 py-4 rounded-lg font-bold text-lg hover:bg-gray-100 transition inline-block mb-4"
          >
            Start Free Trial — No Credit Card Required
          </Link>
          <p className="text-blue-200 text-sm">
            14-day free trial • Cancel anytime • 8 AI models • Millions of assets
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <h3 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-4">
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
                  <a href="#" className="hover:text-white transition">
                    Privacy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition">
                    Terms
                  </a>
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
