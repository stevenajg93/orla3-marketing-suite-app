'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

interface SocialConnection {
  platform: string;
  connected: boolean;
  service_id?: string;
  account_name?: string;
  connected_at?: string;
}

export default function SocialAccountsSettings() {
  const [connections, setConnections] = useState<Record<string, SocialConnection>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check for OAuth callback success/error in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const socialConnect = params.get('social_connect');
    const platform = params.get('platform');
    const errorMsg = params.get('error');

    if (socialConnect === 'success' && platform) {
      setSuccess(`Successfully connected to ${formatPlatformName(platform)}!`);
      window.history.replaceState({}, '', '/dashboard/settings/social-accounts');
      loadConnections();
    } else if (socialConnect === 'error' || errorMsg) {
      const message = errorMsg || params.get('message') || 'Failed to connect';
      setError(message);
      window.history.replaceState({}, '', '/dashboard/settings/social-accounts');
    }
  }, []);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await api.get('/publisher/status');
      setConnections(response.platforms || {});
    } catch (err: any) {
      console.error('Error loading connections:', err);
      setError(err.message || 'Failed to load social account connections');
    } finally {
      setLoading(false);
    }
  };

  const connectPlatform = (platform: string) => {
    // Redirect to backend OAuth endpoint
    window.location.href = `${config.apiUrl}/social-auth/connect/${platform}`;
  };

  const disconnectPlatform = async (platform: string) => {
    if (!confirm(`Disconnect from ${formatPlatformName(platform)}?`)) {
      return;
    }

    try {
      await api.post(`/social-auth/disconnect/${platform}`);
      setSuccess(`Disconnected from ${formatPlatformName(platform)}`);
      loadConnections();
    } catch (err: any) {
      setError(err.message || `Failed to disconnect from ${platform}`);
    }
  };

  const formatPlatformName = (platform: string): string => {
    const names: Record<string, string> = {
      'instagram': 'Instagram',
      'linkedin': 'LinkedIn',
      'twitter': 'Twitter/X',
      'facebook': 'Facebook',
      'tiktok': 'TikTok',
      'youtube': 'YouTube',
      'reddit': 'Reddit',
      'tumblr': 'Tumblr',
      'wordpress': 'WordPress'
    };
    return names[platform] || platform;
  };

  const platforms = [
    {
      id: 'instagram',
      name: 'Instagram',
      icon: '',
      description: 'Share photos and stories with your followers',
      color: 'from-pink-500 to-purple-500',
      requirements: 'Requires Instagram Business Account'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: '',
      description: 'Professional content for your network',
      color: 'from-blue-600 to-blue-700',
      requirements: 'Personal or Company Page'
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: '',
      description: 'Connect with friends and pages',
      color: 'from-blue-500 to-blue-600',
      requirements: 'Facebook Page access required'
    },
    {
      id: 'twitter',
      name: 'X (Twitter)',
      icon: '𝕏',
      description: 'Share thoughts and updates in real-time',
      color: 'from-slate-800 to-slate-900',
      requirements: 'X/Twitter account'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: '',
      description: 'Short-form video content',
      color: 'from-black to-pink-500',
      requirements: 'TikTok Creator account'
    },
    {
      id: 'youtube',
      name: 'YouTube',
      icon: '',
      description: 'Share videos with the world',
      color: 'from-red-600 to-red-700',
      requirements: 'YouTube channel'
    },
    {
      id: 'reddit',
      name: 'Reddit',
      icon: '',
      description: 'Engage with communities',
      color: 'from-orange-500 to-red-500',
      requirements: 'Reddit account with verified email'
    },
    {
      id: 'tumblr',
      name: 'Tumblr',
      icon: '',
      description: 'Blogging and social platform',
      color: 'from-indigo-500 to-blue-600',
      requirements: 'Tumblr blog'
    },
    {
      id: 'wordpress',
      name: 'WordPress',
      icon: '',
      description: 'Publish blog posts to your site',
      color: 'from-gray-700 to-gray-900',
      requirements: 'Self-hosted WordPress with REST API'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Social Accounts</h1>
          <p className="text-gray-400">
            Connect your social media accounts to publish content directly from ORLA³
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right text-red-200 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {success && (
          <div className="bg-green-500/20 border border-green-500 text-green-200 px-4 py-3 rounded-lg mb-6">
            {success}
            <button
              onClick={() => setSuccess(null)}
              className="float-right text-green-200 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Stats Card */}
        {!loading && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">Connected Accounts</h3>
                <p className="text-gray-400 text-sm">
                  {Object.values(connections).filter(c => c.connected).length} of {platforms.length} platforms connected
                </p>
              </div>
              <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                {Object.values(connections).filter(c => c.connected).length}
              </div>
            </div>
            <div className="mt-4 h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                style={{
                  width: `${(Object.values(connections).filter(c => c.connected).length / platforms.length) * 100}%`
                }}
              />
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="text-gray-400 mt-4">Loading connections...</p>
          </div>
        ) : (
          /* Social Platform Cards */
          <div className="grid md:grid-cols-2 gap-6">
            {platforms.map((platform) => {
              const connection = connections[platform.id];
              const isConnected = connection?.connected;

              return (
                <div
                  key={platform.id}
                  className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:border-white/40 transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4">
                      <div className={`text-4xl p-3 rounded-xl bg-gradient-to-br ${platform.color}`}>
                        {platform.icon}
                      </div>
                      <div>
                        <h3 className="text-xl font-bold text-white mb-1">
                          {platform.name}
                        </h3>
                        <p className="text-gray-400 text-sm mb-2">
                          {platform.description}
                        </p>
                        {isConnected && connection?.service_id && (
                          <div className="flex items-center gap-2 text-green-400 text-sm">
                            <span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                            Connected
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Requirements */}
                  <div className="text-xs text-gray-500 mb-4 pl-16">
                    {platform.requirements}
                  </div>

                  {/* Action Button */}
                  <div className="pl-16">
                    {isConnected ? (
                      <button
                        onClick={() => disconnectPlatform(platform.id)}
                        className="px-4 py-2 border-2 border-red-500/50 hover:border-red-500 text-red-400 hover:text-red-300 rounded-lg font-semibold transition text-sm"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => connectPlatform(platform.id)}
                        className={`px-4 py-2 bg-gradient-to-r ${platform.color} hover:opacity-90 text-white rounded-lg font-semibold transition shadow-lg text-sm`}
                      >
                        Connect Account
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Info Boxes */}
        <div className="mt-8 grid md:grid-cols-2 gap-6">
          {/* How it Works */}
          <div className="bg-cobalt/10 border border-blue-500/30 rounded-xl p-6">
            <h4 className="text-lg font-semibold text-cobalt-300 mb-3">
              How It Works
            </h4>
            <ul className="text-gray-300 space-y-2 text-sm">
              <li>• Click "Connect Account" for any platform</li>
              <li>• Authorize ORLA³ to post on your behalf</li>
              <li>• Start publishing from the Social Manager</li>
              <li>• Schedule posts or publish instantly</li>
            </ul>
          </div>

          {/* Privacy & Security */}
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6">
            <h4 className="text-lg font-semibold text-green-400 mb-3">
              Privacy & Security
            </h4>
            <ul className="text-gray-300 space-y-2 text-sm">
              <li>• Your credentials are encrypted and secure</li>
              <li>• We only post what you explicitly approve</li>
              <li>• Disconnect anytime in one click</li>
              <li>• Your tokens are never shared</li>
            </ul>
          </div>
        </div>

        {/* Coming Soon Badge */}
        <div className="mt-8 bg-cobalt/10 border border-cobalt/30 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl"></span>
            <h4 className="text-lg font-semibold text-gold">
              Coming Soon
            </h4>
          </div>
          <p className="text-gray-300 text-sm">
            OAuth flows for each platform are currently in development. Connect your accounts via API keys in the meantime,
            or contact support for early access to beta OAuth integrations.
          </p>
        </div>
      </div>
    </div>
  );
}
