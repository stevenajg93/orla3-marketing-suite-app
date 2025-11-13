'use client';

import Link from 'next/link';
import { useAuth } from '@/lib/context/AuthContext';
import UnverifiedEmailBanner from './components/UnverifiedEmailBanner';

const contentCreation = [
  { name: 'Blog Writer', icon: '', href: '/dashboard/blog', description: 'AI-powered long-form content', color: 'from-cobalt to-cobalt-600' },
  { name: 'Carousel Maker', icon: '', href: '/dashboard/carousel', description: 'Engaging social carousels', color: 'from-cobalt to-cobalt-600' },
  { name: 'Media Library', icon: '', href: '/dashboard/media', description: 'Browse & manage assets', color: 'from-gold to-gold-600' },
];

const socialManagement = [
  { name: 'Social Manager', icon: '', href: '/dashboard/social', description: 'Unified social posting & scheduling', color: 'from-gradient-to-r from-green-500 to-emerald-500' },
];

const planningAnalysis = [
  { name: 'Content Calendar', icon: '', href: '/dashboard/calendar', description: 'Plan & schedule content', color: 'from-royal to-royal-600' },
  { name: 'Analytics', icon: '', href: '/dashboard/analytics', description: 'Track performance', color: 'from-teal-500 to-teal-600', disabled: true },
  { name: 'Brand Voice', icon: '', href: '/dashboard/brand-voice', description: 'Consistent messaging', color: 'from-cobalt to-cobalt-600', disabled: false },
  { name: 'Competitor Analysis', icon: '', href: '/dashboard/competitor', description: 'Market insights', color: 'from-gold-intense to-gold-600', disabled: false },
  { name: 'Strategy Planner', icon: '', href: '/dashboard/strategy', description: 'Content strategy', color: 'from-cobalt to-cobalt-600', disabled: false },
  { name: 'Find a Videographer', icon: '', href: 'https://orla3.com/browse', description: 'Hire professional creators', color: 'from-cobalt to-gold-intense', external: true },
];

const ToolCard = ({ tool }: { tool: any }) => {
  const LinkWrapper = tool.external ? 'a' : Link;
  const linkProps = tool.external
    ? { href: tool.href, target: '_blank', rel: 'noopener noreferrer' }
    : { href: tool.disabled ? '#' : tool.href };

  return (
    <LinkWrapper
      {...linkProps}
      className={`group relative overflow-hidden rounded-2xl border border-white/10 transition-all ${
        tool.disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'hover:scale-105 hover:border-white/30 cursor-pointer'
      }`}
    >
      <div className={`absolute inset-0 bg-gradient-to-br ${tool.color} opacity-10 group-hover:opacity-20 transition-opacity`}></div>
      <div className="relative p-6 bg-white/5 backdrop-blur-lg">
        <div className="flex items-start justify-between">
          <div className="text-5xl mb-4">{tool.icon}</div>
          {tool.isNew && (
            <span className="px-2 py-1 bg-green-500/20 border border-green-500 rounded-full text-green-300 text-xs font-bold animate-pulse">
              NEW
            </span>
          )}
          {tool.external && (
            <span className="text-gray-400 text-xs">↗</span>
          )}
        </div>
        <h3 className="text-2xl font-bold text-white mb-2">{tool.name}</h3>
        <p className="text-gray-400">{tool.description}</p>
        {tool.disabled && (
          <span className="inline-block mt-3 px-3 py-1 bg-gold-600/30 text-gold-400 text-xs font-bold rounded-full">
            Coming Soon
          </span>
        )}
      </div>
    </LinkWrapper>
  );
};

export default function Dashboard() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Unverified Email Banner */}
        {user && !user.email_verified && (
          <UnverifiedEmailBanner userEmail={user.email} />
        )}

        <div className="mb-12">
          <h1 className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold-400 to-gold-200 mb-4">
            Orla³ Marketing Suite
          </h1>
          <p className="text-xl text-gray-300">AI-powered marketing automation at your fingertips</p>
        </div>

        {/* TIER 1: Content Creation */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl"></span>
            Content Creation
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {contentCreation.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>

        {/* TIER 2: Social Management */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl"></span>
            Social Management
          </h2>
          <div className="grid grid-cols-1 gap-6">
            {socialManagement.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>

        {/* TIER 3: Planning & Intelligence */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl"></span>
            Planning & Intelligence
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {planningAnalysis.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>
      </div>
    </div>
  );
}
