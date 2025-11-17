'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { config } from '@/lib/config';
import { AnimatedPage } from '@/components/AnimatedPage';
import { staggerContainer, staggerItem } from '@/lib/motion';

export default function SelectPlanPage() {
  const router = useRouter();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showPaymentRequired, setShowPaymentRequired] = useState(false);

  // Check if user was redirected from login due to payment requirement
  useEffect(() => {
    const pendingLogin = localStorage.getItem('pending_login_email');
    if (pendingLogin) {
      setShowPaymentRequired(true);
      // Clear the flag
      localStorage.removeItem('pending_login_email');
    }
  }, []);

  const plans = [
    {
      name: 'Starter',
      planId: billingCycle === 'monthly' ? 'starter_monthly' : 'starter_annual',
      price: billingCycle === 'monthly' ? 99 : 990,
      credits: 500,
      description: 'Perfect for freelancers and content creators',
      features: [
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
      popular: false,
    },
    {
      name: 'Professional',
      planId: billingCycle === 'monthly' ? 'professional_monthly' : 'professional_annual',
      price: billingCycle === 'monthly' ? 249 : 2490,
      credits: 2000,
      description: 'Ideal for small businesses and agencies',
      features: [
        '2,000 credits/month',
        '~1,000 social captions or 400 blog posts',
        '100 AI-generated ultra images',
        '10 AI-generated videos (8-sec)',
        '3 brand voice profiles',
        '9 social platform publishing',
        'Auto-publishing & scheduling',
        'Advanced competitor analysis (5 competitors)',
        'Priority support',
        'Credit rollover (up to 1,000)',
      ],
      popular: true,
    },
    {
      name: 'Business',
      planId: billingCycle === 'monthly' ? 'business_monthly' : 'business_annual',
      price: billingCycle === 'monthly' ? 499 : 4990,
      credits: 6000,
      description: 'For growing companies and marketing teams',
      features: [
        '6,000 credits/month',
        '~3,000 social captions or 1,200 blog posts',
        '300 AI-generated ultra images',
        '30 AI-generated videos (8-sec)',
        '10 brand voice profiles',
        '9 social platform publishing',
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
      planId: 'enterprise',
      price: 999,
      credits: 20000,
      description: 'Custom solutions for large organizations',
      features: [
        '20,000 credits/month',
        '~10,000 social captions or 4,000 blog posts',
        '1,000 AI-generated ultra images',
        '100 AI-generated videos (8-sec)',
        'Unlimited brand voices',
        '9 social platform publishing',
        'Unlimited team members',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantees',
        'Full credit rollover (unlimited)',
      ],
      popular: false,
    },
  ];

  const handleSelectPlan = async (planId: string, planName: string) => {
    setLoading(planId);
    setError(null);

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(`${config.apiUrl}/payment/create-checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ plan: planId }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create checkout session');
      }

      // Redirect to Stripe checkout
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('No checkout URL returned');
      }
    } catch (err: any) {
      console.error('Error creating checkout:', err);
      setError(err.message || 'Failed to start checkout process');
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 backdrop-blur-lg bg-white/5">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center">
              <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                ORLA³
              </h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-3 sm:px-4 md:px-6 lg:px-8 py-8 sm:py-12 md:py-16 lg:py-20">
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white mb-3 sm:mb-4">
            Choose Your Plan
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-300 mb-6 sm:mb-8">
            Select a plan to access the Orla³ Marketing Automation Platform
          </p>

          {showPaymentRequired && (
            <div className="max-w-2xl mx-auto mb-6 sm:mb-8 bg-cobalt/20 border border-cobalt/50 rounded-lg p-3 sm:p-4">
              <div className="flex items-start gap-2 sm:gap-3">
                <span className="text-xl sm:text-2xl"></span>
                <div>
                  <p className="text-cobalt-300 font-semibold mb-1 text-sm sm:text-base">Payment Required</p>
                  <p className="text-cobalt-200 text-xs sm:text-sm">
                    To access your account, please select and pay for a subscription plan below.
                    Your account will be activated immediately after payment.
                  </p>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="max-w-2xl mx-auto mb-6 sm:mb-8 bg-red-500/20 border border-red-500/50 rounded-lg p-3 sm:p-4">
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}

          {/* Billing Toggle */}
          <div className="inline-flex bg-white/10 backdrop-blur-lg rounded-lg p-1 border border-white/20">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 sm:px-6 py-2 rounded-md text-sm sm:text-base font-semibold transition ${
                billingCycle === 'monthly'
                  ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-4 sm:px-6 py-2 rounded-md text-sm sm:text-base font-semibold transition ${
                billingCycle === 'annual'
                  ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              Annual <span className="text-gold hidden sm:inline">(Save 17%)</span><span className="text-gold sm:hidden">-17%</span>
            </button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6 lg:gap-8">
          {plans.map((plan) => (
            <div
              key={plan.planId}
              className={`bg-white/10 backdrop-blur-lg rounded-2xl p-5 sm:p-6 md:p-8 border ${
                plan.popular
                  ? 'border-cobalt-400 ring-2 ring-blue-400/50 sm:scale-105'
                  : 'border-white/20'
              } hover:border-cobalt-400/50 transition relative`}
            >
              {plan.popular && (
                <div className="absolute -top-3 sm:-top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-cobalt to-royal text-white px-3 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-bold">
                    Most Popular
                  </span>
                </div>
              )}

              <h3 className="text-xl sm:text-2xl font-bold text-white mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-xs sm:text-sm mb-3 sm:mb-4">{plan.description}</p>

              <div className="mb-4 sm:mb-6">
                <span className="text-3xl sm:text-4xl md:text-5xl font-black text-white">£{plan.price}</span>
                {plan.name !== 'Enterprise' && (
                  <span className="text-sm sm:text-base text-gray-400">
                    /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                  </span>
                )}
              </div>

              <div className="mb-4 sm:mb-6">
                <div className="bg-gradient-to-r from-cobalt/20 to-royal/20 rounded-lg p-2 sm:p-3 border border-cobalt-400/30">
                  <p className="text-cobalt-300 font-bold text-center text-sm sm:text-base">
                    {plan.credits.toLocaleString()} Credits/month
                  </p>
                </div>
              </div>

              <ul className="space-y-2 sm:space-y-3 mb-6 sm:mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-gray-300">
                    <span className="text-gold mt-0.5 sm:mt-1 text-sm"></span>
                    <span className="text-xs sm:text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSelectPlan(plan.planId, plan.name)}
                disabled={loading !== null}
                className={`w-full py-2.5 sm:py-3 rounded-lg text-sm sm:text-base font-bold text-center transition ${
                  plan.popular
                    ? 'bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white'
                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/20'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading === plan.planId ? 'Loading...' : 'Select Plan'}
              </button>
            </div>
          ))}
        </div>

        {/* Credit Cost Breakdown */}
        <div className="mt-10 sm:mt-12 md:mt-16 bg-white/10 backdrop-blur-lg rounded-2xl p-5 sm:p-6 md:p-8 border border-white/20">
          <h3 className="text-xl sm:text-2xl font-bold text-white mb-4 sm:mb-6 text-center">
            How Credits Work
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 sm:gap-6">
            {[
              { action: 'Social Caption', credits: 2, icon: '' },
              { action: 'Full Blog Post', credits: 5, icon: '' },
              { action: 'AI Image (Standard)', credits: 10, icon: '' },
              { action: 'AI Image (Ultra)', credits: 20, icon: '' },
              { action: 'AI Video (8-sec)', credits: 200, icon: '' },
            ].map((item, idx) => (
              <div key={idx} className="text-center">
                <div className="text-2xl sm:text-3xl md:text-4xl mb-1 sm:mb-2">{item.icon}</div>
                <div className="text-2xl sm:text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold mb-1 sm:mb-2">
                  {item.credits}
                </div>
                <div className="text-gray-300 text-xs sm:text-sm">{item.action}</div>
              </div>
            ))}
          </div>
          <p className="text-center text-gray-400 mt-4 sm:mt-6 text-xs sm:text-sm">
            Each plan shows approximate content output. Mix and match however you need - your credits, your choice.
          </p>
        </div>
      </section>
    </div>
  );
}
