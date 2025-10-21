'use client';

import Link from 'next/link';
import { useState } from 'react';

export default function Dashboard() {
  const tools = [
    {
      id: 'blog',
      title: 'Blog Writer',
      icon: '✍️',
      description: 'Generate SEO-optimized blog posts',
      status: 'READY',
      color: 'from-blue-600 to-purple-600',
      href: '/dashboard/blog'
    },
    {
      id: 'carousel',
      title: 'Carousel Maker',
      icon: '🎠',
      description: 'Create Instagram/LinkedIn carousels',
      status: 'READY',
      color: 'from-pink-600 to-rose-600',
      href: '/dashboard/carousel'
    },
    {
      id: 'caption',
      title: 'Caption Generator',
      icon: '💬',
      description: 'Multi-platform social captions',
      status: 'READY',
      color: 'from-green-600 to-emerald-600',
      href: '/dashboard/caption'
    },
    {
      id: 'video-script',
      title: 'Video Script Writer',
      icon: '🎬',
      description: 'YouTube/TikTok scripts',
      status: 'SOON',
      color: 'from-red-600 to-orange-600',
      href: '/dashboard/video-script'
    },
    {
      id: 'ad-copy',
      title: 'Ad Copy Generator',
      icon: '🎯',
      description: 'Facebook/Google/LinkedIn ads',
      status: 'SOON',
      color: 'from-yellow-600 to-amber-600',
      href: '/dashboard/ad-copy'
    },
    {
      id: 'calendar',
      title: 'Content Calendar',
      icon: '📅',
      description: 'Visual scheduling interface',
      status: 'SOON',
      color: 'from-indigo-600 to-blue-600',
      href: '/dashboard/calendar'
    },
    {
      id: 'analytics',
      title: 'Analytics Dashboard',
      icon: '📊',
      description: 'GA4, GSC, social metrics',
      status: 'SOON',
      color: 'from-purple-600 to-pink-600',
      href: '/dashboard/analytics'
    },
    {
      id: 'text-publisher',
      title: 'Text Publisher',
      icon: '📝',
      description: 'LinkedIn, Twitter, Facebook, Reddit',
      status: 'READY',
      color: 'from-cyan-600 to-blue-600',
      href: '/dashboard/publisher'
    },
    {
      id: 'video-publisher',
      title: 'Video Publisher',
      icon: '🎬',
      description: 'TikTok, Instagram, YouTube Shorts',
      status: 'READY',
      color: 'from-fuchsia-600 to-purple-600',
      href: '/dashboard/video-publisher'
    },
    {
      id: 'media-library',
      title: 'Media Library',
      icon: '📁',
      description: 'Digital asset management',
      status: 'SOON',
      color: 'from-teal-600 to-cyan-600',
      href: '/dashboard/media'
    },
    {
      id: 'competitor',
      title: 'Competitor Monitor',
      icon: '🔍',
      description: 'Track competitor content',
      status: 'SOON',
      color: 'from-orange-600 to-red-600',
      href: '/dashboard/competitor'
    },
    {
      id: 'engagement-bot',
      title: 'Engagement Bot',
      icon: '🤖',
      description: 'Auto-reply + proactive commenting',
      status: 'SOON',
      color: 'from-lime-600 to-green-600',
      href: '/dashboard/engagement'
    }
  ];

  const stats = [
    { label: 'Traffic', value: '0', icon: '📈' },
    { label: 'Engagement', value: '0', icon: '💬' },
    { label: 'Posts Published', value: '0', icon: '📤' },
    { label: 'Bot Comments', value: '0', icon: '🤖' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-12">
          <h1 className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 via-yellow-200 to-yellow-400 mb-4">
            ORLA³ Marketing Suite
          </h1>
          <p className="text-gray-400 text-xl">Autonomous content engine for videography marketplace growth</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          {stats.map((stat, i) => (
            <div key={i} className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
              <div className="text-4xl mb-2">{stat.icon}</div>
              <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-gray-400 text-sm">{stat.label}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6 mb-12">
          {tools.map((tool) => (
            <Link
              key={tool.id}
              href={tool.href}
              className={`group relative bg-gradient-to-br ${tool.color} rounded-2xl p-6 transition-all duration-300 hover:scale-105 hover:shadow-2xl ${
                tool.status === 'SOON' ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <div className="text-5xl mb-4">{tool.icon}</div>
              <h3 className="text-xl font-bold text-white mb-2">{tool.title}</h3>
              <p className="text-white/80 text-sm mb-4">{tool.description}</p>
              <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                tool.status === 'READY' ? 'bg-green-500 text-white' :
                tool.status === 'NEXT' ? 'bg-blue-500 text-white' :
                'bg-gray-500 text-white'
              }`}>
                {tool.status}
              </div>
            </Link>
          ))}
        </div>

        <div className="bg-gradient-to-r from-yellow-600 to-amber-600 rounded-2xl p-8 border border-yellow-400/30">
          <h2 className="text-3xl font-black text-white mb-4">🚀 Getting Started</h2>
          <p className="text-white/90 mb-6">
            ORLA³ Marketing Suite automates your entire content lifecycle. Start with Blog Writer, then use the publishers to distribute across 8+ platforms.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link href="/dashboard/blog" className="bg-white hover:bg-gray-100 text-yellow-700 font-bold py-3 px-6 rounded-lg transition-all">
              Generate Your First Blog
            </Link>
            <Link href="/dashboard/publisher" className="bg-yellow-800 hover:bg-yellow-900 text-white font-bold py-3 px-6 rounded-lg transition-all">
              Publish to Text Platforms
            </Link>
            <Link href="/dashboard/video-publisher" className="bg-purple-800 hover:bg-purple-900 text-white font-bold py-3 px-6 rounded-lg transition-all">
              Publish Videos
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
