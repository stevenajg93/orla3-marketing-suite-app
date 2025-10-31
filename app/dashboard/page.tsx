'use client';

import Link from 'next/link';

const contentCreation = [
  { name: 'Blog Writer', icon: '✍️', href: '/dashboard/blog', description: 'AI-powered long-form content', color: 'from-blue-500 to-blue-600' },
  { name: 'Carousel Maker', icon: '🎨', href: '/dashboard/carousel', description: 'Engaging social carousels', color: 'from-purple-500 to-purple-600' },
  { name: 'Media Library', icon: '📁', href: '/dashboard/media', description: 'Browse & manage assets', color: 'from-yellow-500 to-yellow-600' },
];

const socialManagement = [
  { name: 'Social Manager', icon: '📱', href: '/dashboard/social', description: 'Unified social posting & scheduling', color: 'from-gradient-to-r from-green-500 to-emerald-500', isNew: true },
];

const planningAnalysis = [
  { name: 'Content Calendar', icon: '📅', href: '/dashboard/calendar', description: 'Plan & schedule content', color: 'from-indigo-500 to-indigo-600' },
  { name: 'Analytics', icon: '📊', href: '/dashboard/analytics', description: 'Track performance', color: 'from-teal-500 to-teal-600', disabled: true },
  { name: 'Brand Voice', icon: '🎯', href: '/dashboard/brand-voice', description: 'Consistent messaging', color: 'from-cyan-500 to-cyan-600', disabled: false },
  { name: 'Competitor Analysis', icon: '🔍', href: '/dashboard/competitor', description: 'Market insights', color: 'from-rose-500 to-rose-600', disabled: false },
{ name: 'Strategy Planner', icon: '🎪', href: '/dashboard/strategy', description: 'Content strategy', color: 'from-violet-500 to-violet-600', disabled: false },
];

const ToolCard = ({ tool }: { tool: any }) => (
  <Link
    href={tool.disabled ? '#' : tool.href}
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
      </div>
      <h3 className="text-2xl font-bold text-white mb-2">{tool.name}</h3>
      <p className="text-gray-400">{tool.description}</p>
      {tool.disabled && (
        <span className="inline-block mt-3 px-3 py-1 bg-yellow-600/30 text-yellow-400 text-xs font-bold rounded-full">
          Coming Soon
        </span>
      )}
    </div>
  </Link>
);

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-12">
          <h1 className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-200 mb-4">
            🎪 Orla³ Marketing Suite
          </h1>
          <p className="text-xl text-gray-300">AI-powered marketing automation at your fingertips</p>
        </div>

        {/* TIER 1: Content Creation */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl">✨</span>
            Content Creation
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {contentCreation.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>

        {/* TIER 2: Social Management */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl">📱</span>
            Social Management
          </h2>
          <div className="grid grid-cols-1 gap-6">
            {socialManagement.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>

        {/* TIER 3: Planning & Intelligence */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <span className="text-3xl">📊</span>
            Planning & Intelligence
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {planningAnalysis.map((tool) => <ToolCard key={tool.name} tool={tool} />)}
          </div>
        </div>

        {/* Progress Tracker */}
        <div className="mt-12 bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 p-8">
          <h2 className="text-3xl font-bold text-white mb-4">✅ Progress Tracker</h2>
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="flex-1 bg-white/10 rounded-full h-4 overflow-hidden">
                <div className="bg-gradient-to-r from-green-500 to-green-600 h-full" style={{ width: '44%' }}></div>
              </div>
              <span className="text-white font-bold">4/9 Tools Complete</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="bg-green-900/40 border border-green-400/30 rounded-xl p-4">
                <div className="text-3xl mb-2">✅</div>
                <div className="text-green-400 font-bold">4 Complete</div>
              </div>
              <div className="bg-yellow-900/40 border border-yellow-400/30 rounded-xl p-4">
                <div className="text-3xl mb-2">🚧</div>
                <div className="text-yellow-400 font-bold">1 In Progress</div>
              </div>
              <div className="bg-blue-900/40 border border-blue-400/30 rounded-xl p-4">
                <div className="text-3xl mb-2">📋</div>
                <div className="text-blue-400 font-bold">4 Planned</div>
              </div>
              <div className="bg-purple-900/40 border border-purple-400/30 rounded-xl p-4">
                <div className="text-3xl mb-2">🎯</div>
                <div className="text-purple-400 font-bold">44% Done</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
