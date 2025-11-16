'use client';

import { useState, useEffect } from 'react';
import { createApiClient } from '@/lib/api-client';

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const api = createApiClient();
      // Placeholder - will need backend endpoint
      // const data = await api.get(`/analytics?range=${timeRange}`);

      // Mock data for now
      setStats({
        credits: {
          used: 1247,
          total: 2000,
          percentage: 62
        },
        content: {
          blogs: 24,
          captions: 156,
          images: 45,
          videos: 3
        },
        social: {
          posts: 89,
          engagement: 12453,
          reach: 45678,
          clicks: 2341
        },
        topPlatforms: [
          { name: 'Instagram', posts: 34, engagement: 5234 },
          { name: 'LinkedIn', posts: 28, engagement: 4123 },
          { name: 'Twitter', posts: 27, engagement: 3096 }
        ]
      });
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 sm:mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">Analytics</h1>
              <p className="text-gray-400">Track your marketing performance and credit usage</p>
            </div>

            {/* Time Range Selector */}
            <div className="flex bg-white/10 backdrop-blur-lg rounded-lg p-1 border border-white/20 w-fit">
              <button
                onClick={() => setTimeRange('7d')}
                className={`px-3 sm:px-4 py-2 rounded-md text-sm font-semibold transition ${
                  timeRange === '7d'
                    ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                7 Days
              </button>
              <button
                onClick={() => setTimeRange('30d')}
                className={`px-3 sm:px-4 py-2 rounded-md text-sm font-semibold transition ${
                  timeRange === '30d'
                    ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                30 Days
              </button>
              <button
                onClick={() => setTimeRange('90d')}
                className={`px-3 sm:px-4 py-2 rounded-md text-sm font-semibold transition ${
                  timeRange === '90d'
                    ? 'bg-gradient-to-r from-cobalt to-royal text-white'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                90 Days
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-12 h-12 border-4 border-cobalt border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <>
            {/* Credit Usage */}
            <div className="mb-6 sm:mb-8">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Credit Usage</h2>
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
                  <div>
                    <p className="text-gray-400 text-sm mb-1">Credits Used This Month</p>
                    <p className="text-3xl sm:text-4xl font-black text-white">
                      {stats?.credits.used.toLocaleString()} <span className="text-lg sm:text-xl text-gray-400">/ {stats?.credits.total.toLocaleString()}</span>
                    </p>
                  </div>
                  <div className="mt-4 sm:mt-0 px-4 py-2 bg-cobalt/20 border border-cobalt rounded-lg">
                    <p className="text-cobalt-300 font-bold text-lg sm:text-xl">{stats?.credits.percentage}% Used</p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-white/10 rounded-full h-3 sm:h-4">
                  <div
                    className="bg-gradient-to-r from-cobalt to-royal h-3 sm:h-4 rounded-full transition-all duration-500"
                    style={{ width: `${stats?.credits.percentage}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Content Stats */}
            <div className="mb-6 sm:mb-8">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Content Generated</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.blogs}
                  </p>
                  <p className="text-gray-400 text-sm">Blog Posts</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.captions}
                  </p>
                  <p className="text-gray-400 text-sm">Captions</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.images}
                  </p>
                  <p className="text-gray-400 text-sm">Images</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.videos}
                  </p>
                  <p className="text-gray-400 text-sm">Videos</p>
                </div>
              </div>
            </div>

            {/* Social Media Performance */}
            <div className="mb-6 sm:mb-8">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Social Media Performance</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6 mb-6">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Total Posts</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{stats?.social.posts}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Engagement</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{stats?.social.engagement.toLocaleString()}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Total Reach</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{stats?.social.reach.toLocaleString()}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Click-throughs</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{stats?.social.clicks.toLocaleString()}</p>
                </div>
              </div>

              {/* Top Platforms */}
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 md:p-8 border border-white/20">
                <h3 className="text-base sm:text-lg font-bold text-white mb-4">Top Performing Platforms</h3>
                <div className="space-y-4">
                  {stats?.topPlatforms.map((platform: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-cobalt to-royal rounded-lg flex items-center justify-center text-white font-bold text-sm sm:text-base">
                          {idx + 1}
                        </div>
                        <div>
                          <p className="text-white font-semibold text-sm sm:text-base">{platform.name}</p>
                          <p className="text-gray-400 text-xs sm:text-sm">{platform.posts} posts</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-bold text-sm sm:text-base">{platform.engagement.toLocaleString()}</p>
                        <p className="text-gray-400 text-xs">engagements</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Coming Soon */}
            <div className="bg-cobalt/10 border border-cobalt/30 rounded-2xl p-4 sm:p-6 md:p-8">
              <div className="flex items-start gap-3 sm:gap-4">
                <div className="text-2xl sm:text-3xl md:text-4xl"></div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-cobalt-300 mb-2">More Analytics Coming Soon</h3>
                  <p className="text-gray-300 text-sm sm:text-base">
                    We're building advanced analytics features including content performance insights, audience demographics,
                    best posting times, competitor benchmarking, and ROI tracking. Stay tuned!
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
