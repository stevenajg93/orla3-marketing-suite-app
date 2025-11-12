'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function BillingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [currentPlan, setCurrentPlan] = useState('Professional');
  const [creditsRemaining, setCreditsRemaining] = useState(1247);
  const [creditsUsed, setCreditsUsed] = useState(753);
  const [totalCredits] = useState(2000);

  const plans = [
    {
      name: 'Starter',
      price: billingCycle === 'monthly' ? 99 : 990,
      credits: 500,
      description: 'Perfect for freelancers and content creators',
      features: [
        '500 credits/month',
        '~100 social captions or 50 blog posts',
        '25 AI-generated ultra images',
        '2 AI-generated videos (8-sec)',
        '1 brand voice profile',
        '3 social accounts',
        'Content calendar',
        'Basic competitor tracking (2 competitors)',
        'Credit rollover (up to 250)',
      ],
      popular: false,
    },
    {
      name: 'Professional',
      price: billingCycle === 'monthly' ? 249 : 2490,
      credits: 2000,
      description: 'Ideal for small businesses and agencies',
      features: [
        '2,000 credits/month',
        '~400 social posts or 200 blog posts',
        '100 AI-generated ultra images',
        '10 AI-generated videos (8-sec)',
        '3 brand voice profiles',
        '10 social accounts',
        'Auto-publishing & scheduling',
        'Advanced competitor analysis (5 competitors)',
        'Priority support',
        'Credit rollover (up to 1,000)',
      ],
      popular: true,
    },
    {
      name: 'Business',
      price: billingCycle === 'monthly' ? 499 : 4990,
      credits: 6000,
      description: 'For growing companies and marketing teams',
      features: [
        '6,000 credits/month',
        '~1,200 social posts or 600 blog posts',
        '300 AI-generated ultra images',
        '30 AI-generated videos (8-sec)',
        '10 brand voice profiles',
        '25 social accounts',
        'Multi-user collaboration (5 seats)',
        'Unlimited competitor tracking',
        'API access',
        'White-label options',
        'Credit rollover (up to 3,000)',
      ],
      popular: false,
    },
    {
      name: 'Enterprise',
      price: 999,
      credits: 20000,
      description: 'Custom solutions for large organizations',
      features: [
        '20,000 credits/month',
        '~4,000 social posts or 2,000 blog posts',
        '1,000 AI-generated ultra images',
        '100 AI-generated videos (8-sec)',
        'Unlimited brand voices',
        'Unlimited social accounts',
        'Unlimited team members',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantees',
        'Full credit rollover',
      ],
      popular: false,
    },
  ];

  const creditPacks = [
    { credits: 500, price: 49, bonus: 0 },
    { credits: 1000, price: 89, bonus: 100 },
    { credits: 2500, price: 199, bonus: 300 },
    { credits: 5000, price: 349, bonus: 750 },
  ];

  const usageHistory = [
    { date: '2025-11-12', action: 'Blog Post Generated', credits: -5, balance: 1247 },
    { date: '2025-11-12', action: 'Social Caption', credits: -2, balance: 1252 },
    { date: '2025-11-11', action: 'AI Video (8s)', credits: -200, balance: 1254 },
    { date: '2025-11-11', action: 'Carousel Generated', credits: -10, balance: 1454 },
    { date: '2025-11-10', action: 'AI Image (Ultra)', credits: -20, balance: 1464 },
    { date: '2025-11-10', action: 'Social Caption', credits: -2, balance: 1484 },
    { date: '2025-11-09', action: 'Blog Post Generated', credits: -5, balance: 1486 },
    { date: '2025-11-09', action: 'Purchased Credits', credits: +500, balance: 1491 },
  ];

  const progressPercentage = (creditsRemaining / totalCredits) * 100;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
            💳 Billing & Credits
          </h1>
          <p className="text-gray-400 mt-2">Manage your subscription and credit balance</p>
        </div>

        {/* Current Plan & Credits Overview */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {/* Current Plan */}
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Current Plan</h2>
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-full text-sm font-bold">
                {currentPlan}
              </span>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-gray-400 text-sm mb-1">Monthly Credits</p>
                <p className="text-3xl font-bold text-white">{totalCredits.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Billing Cycle</p>
                <p className="text-xl font-semibold text-white">Monthly</p>
              </div>
              <div>
                <p className="text-gray-400 text-sm mb-1">Next Billing Date</p>
                <p className="text-xl font-semibold text-white">December 12, 2025</p>
              </div>
              <div className="pt-4">
                <button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-bold transition">
                  Manage Subscription
                </button>
              </div>
            </div>
          </div>

          {/* Credits Overview */}
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
            <h2 className="text-2xl font-bold text-white mb-6">Credits Balance</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-end mb-2">
                  <p className="text-gray-400 text-sm">Remaining</p>
                  <p className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-400">
                    {creditsRemaining.toLocaleString()}
                  </p>
                </div>
                <div className="w-full bg-white/10 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-green-500 to-blue-500 h-full rounded-full transition-all duration-500"
                    style={{ width: `${progressPercentage}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <p className="text-gray-400 text-sm mb-1">Used This Month</p>
                  <p className="text-xl font-semibold text-white">{creditsUsed.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm mb-1">Total Allocated</p>
                  <p className="text-xl font-semibold text-white">{totalCredits.toLocaleString()}</p>
                </div>
              </div>
              <div className="pt-4">
                <a
                  href="#buy-credits"
                  className="block w-full bg-white/10 hover:bg-white/20 border-2 border-purple-400/50 hover:border-purple-400 text-white px-6 py-3 rounded-lg font-bold text-center transition"
                >
                  Buy More Credits
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Credit Packs */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-8" id="buy-credits">
          <h2 className="text-2xl font-bold text-white mb-6">💰 Buy Additional Credits</h2>
          <p className="text-gray-400 mb-6">Need more credits before your next billing cycle? Purchase credit packs instantly.</p>

          <div className="grid md:grid-cols-4 gap-4">
            {creditPacks.map((pack, idx) => (
              <div
                key={idx}
                className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:border-purple-400/50 transition relative"
              >
                {pack.bonus > 0 && (
                  <div className="absolute -top-3 right-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-white text-xs px-3 py-1 rounded-full font-bold">
                    +{pack.bonus} Bonus!
                  </div>
                )}
                <div className="text-center mb-4">
                  <p className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-2">
                    {(pack.credits + pack.bonus).toLocaleString()}
                  </p>
                  <p className="text-gray-400 text-sm">credits</p>
                </div>
                <div className="text-center mb-4">
                  <p className="text-2xl font-bold text-white">£{pack.price}</p>
                  <p className="text-gray-500 text-xs">one-time payment</p>
                </div>
                <button className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-4 py-2 rounded-lg font-semibold transition">
                  Purchase
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Pricing Plans */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">📊 Upgrade Your Plan</h2>
          <p className="text-gray-400 mb-6">Get more credits every month with a higher tier plan.</p>

          {/* Billing Toggle */}
          <div className="flex justify-center mb-8">
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
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, index) => (
              <div
                key={index}
                className={`bg-white/10 backdrop-blur-lg rounded-2xl p-6 border ${
                  plan.name === currentPlan
                    ? 'border-green-400 ring-2 ring-green-400/50'
                    : plan.popular
                    ? 'border-blue-400 ring-2 ring-blue-400/50'
                    : 'border-white/20'
                } hover:border-blue-400/50 transition relative`}
              >
                {plan.name === currentPlan && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-green-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                      Current Plan
                    </span>
                  </div>
                )}
                {plan.popular && plan.name !== currentPlan && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-bold">
                      Most Popular
                    </span>
                  </div>
                )}

                <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                <p className="text-gray-400 text-sm mb-4">{plan.description}</p>

                <div className="mb-6">
                  <span className="text-4xl font-black text-white">£{plan.price}</span>
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

                <ul className="space-y-2 mb-6 text-sm">
                  {plan.features.slice(0, 5).map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-gray-300">
                      <span className="text-green-400 mt-1">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`block w-full py-3 rounded-lg font-bold text-center transition ${
                    plan.name === currentPlan
                      ? 'bg-white/10 text-gray-400 cursor-not-allowed'
                      : plan.popular
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
                      : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                  }`}
                  disabled={plan.name === currentPlan}
                >
                  {plan.name === currentPlan ? 'Current Plan' : plan.name === 'Enterprise' ? 'Contact Sales' : 'Upgrade'}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Usage History */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
          <h2 className="text-2xl font-bold text-white mb-6">📈 Recent Activity</h2>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left text-gray-400 font-semibold pb-3">Date</th>
                  <th className="text-left text-gray-400 font-semibold pb-3">Action</th>
                  <th className="text-right text-gray-400 font-semibold pb-3">Credits</th>
                  <th className="text-right text-gray-400 font-semibold pb-3">Balance</th>
                </tr>
              </thead>
              <tbody>
                {usageHistory.map((item, idx) => (
                  <tr key={idx} className="border-b border-white/10 hover:bg-white/5 transition">
                    <td className="py-3 text-gray-300">{new Date(item.date).toLocaleDateString('en-GB')}</td>
                    <td className="py-3 text-white">{item.action}</td>
                    <td className={`py-3 text-right font-semibold ${item.credits > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {item.credits > 0 ? '+' : ''}{item.credits}
                    </td>
                    <td className="py-3 text-right text-gray-300">{item.balance.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Credit Cost Reference */}
        <div className="mt-8 bg-blue-900/30 border border-blue-500/50 rounded-lg p-6">
          <h3 className="text-lg font-bold text-blue-300 mb-4">ℹ️ Credit Costs</h3>
          <div className="grid md:grid-cols-5 gap-4 text-center">
            {[
              { action: 'Social Caption', credits: 2, icon: '✍️' },
              { action: 'Full Blog Post', credits: 5, icon: '📝' },
              { action: 'AI Image (Standard)', credits: 10, icon: '🖼️' },
              { action: 'AI Image (Ultra)', credits: 20, icon: '🎨' },
              { action: 'AI Video (8-sec)', credits: 200, icon: '🎬' },
            ].map((item, idx) => (
              <div key={idx}>
                <div className="text-3xl mb-2">{item.icon}</div>
                <div className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400 mb-1">
                  {item.credits}
                </div>
                <div className="text-gray-300 text-sm">{item.action}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
