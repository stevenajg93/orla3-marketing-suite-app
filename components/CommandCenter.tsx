"use client";

import React from "react";
import { useRouter } from "next/navigation";

const subsystems = [
  { id: "articles", name: "Draft Generator", icon: "📝", color: "from-royal to-cobalt", endpoint: "/content/draft" },
  { id: "primer", name: "AI Primer", icon: "🎯", color: "from-cobalt to-cobalt-500", endpoint: "/content/prime" },
  { id: "carousel", name: "Carousel Maker", icon: "🎠", color: "from-gold to-gold-intense", endpoint: "/social/carousel" },
  { id: "brand", name: "Brand Voice", icon: "🎨", color: "from-gold-intense to-red-500", endpoint: "/brand/rewrite" },
  { id: "analytics", name: "Analytics", icon: "📊", color: "from-cobalt to-royal", endpoint: "/analytics/refresh" },
  { id: "ads", name: "Paid Ads", icon: "💰", color: "from-gold to-gold-intense", endpoint: "/ads/generate" },
  { id: "crm", name: "CRM Assistant", icon: "👥", color: "from-gold-intense to-gold", endpoint: "/crm/associate" },
  { id: "publisher", name: "Multi-Platform", icon: "🌐", color: "from-cobalt to-cobalt-500", endpoint: "/publish/adapt" },
  { id: "comments", name: "Comments", icon: "💬", color: "from-gold-intense to-gold", endpoint: "/comments/reply" },
  { id: "competitor", name: "Competitor", icon: "🔍", color: "from-red-500 to-gold-intense", endpoint: "/competitor/analyze" },
  { id: "media", name: "Media Manager", icon: "🎬", color: "from-royal to-cobalt", endpoint: "/media/search" },
  { id: "collab", name: "Team Collab", icon: "🤝", color: "from-cobalt to-cobalt-500", endpoint: "/collab/workflow" },
];

export default function CommandCenter() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-black">
      <div className="border-b border-white/10 backdrop-blur-xl bg-black/20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-3xl">🚀</div>
            <div>
              <h1 className="text-2xl font-bold text-white">ORLA3 Command Center</h1>
              <p className="text-sm text-royal-300">12 AI-Powered Subsystems Active</p>
            </div>
          </div>
          <button className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition">
            Settings
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="text-4xl font-bold text-white mb-1">847</div>
            <div className="text-sm text-royal-300">Total Articles</div>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="text-4xl font-bold text-white mb-1">12</div>
            <div className="text-sm text-royal-300">Active Subsystems</div>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="text-4xl font-bold text-white mb-1">94%</div>
            <div className="text-sm text-royal-300">Success Rate</div>
          </div>
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
            <div className="text-4xl font-bold text-white mb-1">2.4k</div>
            <div className="text-sm text-royal-300">API Calls Today</div>
          </div>
        </div>

        <h2 className="text-2xl font-bold text-white mb-6">AI Subsystems</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {subsystems.map((system) => (
            <button
              key={system.id}
              onClick={() => router.push(`/dashboard/${system.id}`)}
              className="group relative bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10 hover:border-white/30 transition-all hover:scale-105 hover:shadow-2xl"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${system.color} opacity-0 group-hover:opacity-10 rounded-xl transition`} />
              <div className="text-5xl mb-3">{system.icon}</div>
              <h3 className="text-lg font-semibold text-white mb-1">{system.name}</h3>
              <p className="text-sm text-royal-300">{system.endpoint}</p>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
