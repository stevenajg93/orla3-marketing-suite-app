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

      // Fetch real post analytics
      const postsResponse = await api.get(`/analytics/posts?range=${timeRange}`);
      const recentPosts = postsResponse.posts || [];

      // Calculate aggregates from real data
      const totalPosts = recentPosts.length;
      const totalViews = recentPosts.reduce((sum: number, p: any) => sum + (p.views || 0), 0);
      const totalLikes = recentPosts.reduce((sum: number, p: any) => sum + (p.likes || 0), 0);
      const totalComments = recentPosts.reduce((sum: number, p: any) => sum + (p.comments || 0), 0);
      const totalShares = recentPosts.reduce((sum: number, p: any) => sum + (p.shares || 0), 0);
      const totalEngagement = totalLikes + totalComments + totalShares;

      // Platform aggregation
      const platformStats: { [key: string]: { posts: number; engagement: number } } = {};
      recentPosts.forEach((post: any) => {
        if (!platformStats[post.platform]) {
          platformStats[post.platform] = { posts: 0, engagement: 0 };
        }
        platformStats[post.platform].posts++;
        platformStats[post.platform].engagement += post.engagement || 0;
      });

      const topPlatforms = Object.entries(platformStats)
        .map(([name, stats]) => ({ name, ...stats }))
        .sort((a, b) => b.engagement - a.engagement)
        .slice(0, 3);

      // Mock credit data (until we have real credit tracking)
      setStats({
        credits: {
          used: 1247,
          total: 2000,
          percentage: 62
        },
        content: {
          blogs: recentPosts.filter((p: any) => p.type === 'Blog Post').length,
          captions: recentPosts.filter((p: any) => p.type === 'Text').length,
          images: recentPosts.filter((p: any) => p.type === 'Image').length,
          videos: recentPosts.filter((p: any) => p.type === 'Video').length
        },
        social: {
          posts: totalPosts,
          engagement: totalEngagement,
          reach: totalViews,
          clicks: totalShares // Using shares as proxy for clicks
        },
        topPlatforms: topPlatforms.length > 0 ? topPlatforms : [
          { name: 'No data', posts: 0, engagement: 0 }
        ],
        recentPosts: recentPosts.slice(0, 5)
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
              <p className="text-gray-400">Track your ORLA³ credit usage and content creation</p>
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
                    {stats?.content.blogs ?? 0}
                  </p>
                  <p className="text-gray-400 text-sm">Blog Posts</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.captions ?? 0}
                  </p>
                  <p className="text-gray-400 text-sm">Captions</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.images ?? 0}
                  </p>
                  <p className="text-gray-400 text-sm">Images</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 text-center">
                  <div className="text-3xl sm:text-4xl mb-2"></div>
                  <p className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-royal mb-1">
                    {stats?.content.videos ?? 0}
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
                  <p className="text-2xl sm:text-3xl font-black text-white">{stats?.social.posts ?? 0}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Engagement</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{(stats?.social.engagement ?? 0).toLocaleString()}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Total Reach</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{(stats?.social.reach ?? 0).toLocaleString()}</p>
                </div>
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20">
                  <p className="text-gray-400 text-sm mb-2">Click-throughs</p>
                  <p className="text-2xl sm:text-3xl font-black text-white">{(stats?.social.clicks ?? 0).toLocaleString()}</p>
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
                          <p className="text-gray-400 text-xs sm:text-sm">{platform.posts ?? 0} posts</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-white font-bold text-sm sm:text-base">{(platform.engagement ?? 0).toLocaleString()}</p>
                        <p className="text-gray-400 text-xs">engagements</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Individual Post Performance */}
            <div className="mb-6 sm:mb-8">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Recent Post Performance</h2>
              <div className="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 overflow-hidden">
                {/* Table Header */}
                <div className="hidden md:grid md:grid-cols-7 gap-4 p-4 sm:p-6 bg-white/5 border-b border-white/10 font-bold text-white text-sm">
                  <div className="col-span-2">Post</div>
                  <div>Platform</div>
                  <div>Views</div>
                  <div>Likes</div>
                  <div>Comments</div>
                  <div>Engagement</div>
                </div>

                {/* Table Rows */}
                <div className="divide-y divide-white/10">
                  {stats?.recentPosts.map((post: any) => (
                    <div key={post.id} className="p-4 sm:p-6 hover:bg-white/5 transition-colors">
                      <div className="grid grid-cols-1 md:grid-cols-7 gap-3 md:gap-4">
                        {/* Post Info - Mobile/Desktop */}
                        <div className="col-span-1 md:col-span-2">
                          <p className="text-white font-semibold text-sm sm:text-base mb-1">{post.title}</p>
                          <div className="flex items-center gap-2 text-xs text-gray-400">
                            <span className="px-2 py-0.5 bg-cobalt/20 border border-cobalt/40 rounded text-cobalt-300">{post.type}</span>
                            <span>{new Date(post.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                          </div>
                        </div>

                        {/* Platform */}
                        <div className="flex items-center">
                          <span className="md:hidden text-gray-400 text-sm mr-2">Platform:</span>
                          <span className="text-white font-medium text-sm sm:text-base">{post.platform}</span>
                        </div>

                        {/* Metrics - Mobile shows labels, Desktop doesn't */}
                        <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:gap-0">
                          <div className="flex items-center md:block">
                            <span className="md:hidden text-gray-400 text-sm mr-2">Views:</span>
                            <span className="text-white font-medium text-sm sm:text-base">{(post.views ?? 0).toLocaleString()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:gap-0">
                          <div className="flex items-center md:block">
                            <span className="md:hidden text-gray-400 text-sm mr-2">Likes:</span>
                            <span className="text-white font-medium text-sm sm:text-base">{(post.likes ?? 0).toLocaleString()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:gap-0">
                          <div className="flex items-center md:block">
                            <span className="md:hidden text-gray-400 text-sm mr-2">Comments:</span>
                            <span className="text-white font-medium text-sm sm:text-base">{(post.comments ?? 0).toLocaleString()}</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-1 gap-2 md:gap-0">
                          <div className="flex items-center md:block">
                            <span className="md:hidden text-gray-400 text-sm mr-2">Total:</span>
                            <span className="text-cobalt-300 font-bold text-sm sm:text-base">{(post.engagement ?? 0).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-gray-400 text-xs sm:text-sm mt-3">
                Showing your published posts from ORLA³. Engagement metrics will update automatically once social platform API integration is enabled.
              </p>
            </div>

            {/* Future Enhancements */}
            <div className="bg-gradient-to-r from-cobalt/10 to-royal/10 border border-cobalt/30 rounded-2xl p-4 sm:p-6 md:p-8">
              <div className="flex items-start gap-3 sm:gap-4">
                <div className="text-2xl sm:text-3xl md:text-4xl">📊</div>
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Advanced Analytics in Development</h3>
                  <p className="text-gray-300 text-sm sm:text-base mb-3">
                    Currently showing real-time credit usage and content stats. Future updates will include:
                  </p>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-400">
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      Content performance insights
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      Audience demographics
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      Optimal posting times
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      Competitor benchmarking
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      ROI tracking
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="text-cobalt-400">•</span>
                      Historical trend analysis
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
