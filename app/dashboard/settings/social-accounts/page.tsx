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
    const successPlatform = params.get('success'); // Backend sends ?success=platform
    const errorMsg = params.get('error');

    if (successPlatform) {
      setSuccess(`Successfully connected to ${formatPlatformName(successPlatform)}!`);
      window.history.replaceState({}, '', '/dashboard/settings/social-accounts');
      loadConnections();
    } else if (errorMsg) {
      setError(errorMsg);
      window.history.replaceState({}, '', '/dashboard/settings/social-accounts');
    }
  }, []);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/social-auth/status');
      setConnections(response.connections || {});
    } catch (err: any) {
      console.error('Error loading connections:', err);
      // Show a more helpful error message
      if (err.status === 401) {
        setError('Please log in to connect your social accounts');
      } else if (err.status === 404 || err.status === 0) {
        setError('Social authentication service is deploying. Please refresh in a moment.');
      } else {
        setError(err.message || 'Failed to load social account connections');
      }
      // Set empty connections so UI still renders
      setConnections({});
    } finally {
      setLoading(false);
    }
  };

  const connectPlatform = async (platform: string) => {
    try {
      // First, get the OAuth URL from backend (with JWT auth)
      const response = await api.get(`/social-auth/get-auth-url/${platform}`);

      if (response.auth_url) {
        // Then redirect to the OAuth provider
        window.location.href = response.auth_url;
      } else {
        setError('Failed to initiate OAuth flow');
      }
    } catch (err: any) {
      setError(err.message || `Failed to connect to ${formatPlatformName(platform)}`);
    }
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
      icon: 'IG',
      description: 'Share photos and stories with your followers',
      iconBg: 'bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500',
      requirements: 'Requires Instagram Business Account'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: 'in',
      description: 'Professional content for your network',
      iconBg: 'bg-gradient-to-br from-blue-600 to-blue-700',
      requirements: 'Personal or Company Page'
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: 'f',
      description: 'Connect with friends and pages',
      iconBg: 'bg-gradient-to-br from-blue-500 to-blue-600',
      requirements: 'Facebook Page access required'
    },
    {
      id: 'twitter',
      name: 'X (Twitter)',
      icon: '𝕏',
      description: 'Share thoughts and updates in real-time',
      iconBg: 'bg-gradient-to-br from-slate-800 to-black',
      requirements: 'X/Twitter account'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: 'TT',
      description: 'Short-form video content',
      iconBg: 'bg-gradient-to-br from-cyan-400 via-slate-900 to-pink-500',
      requirements: 'TikTok Creator account'
    },
    {
      id: 'youtube',
      name: 'YouTube',
      icon: 'YT',
      description: 'Share videos with the world',
      iconBg: 'bg-gradient-to-br from-red-600 to-red-700',
      requirements: 'YouTube channel'
    },
    {
      id: 'reddit',
      name: 'Reddit',
      icon: 'RD',
      description: 'Engage with communities',
      iconBg: 'bg-gradient-to-br from-orange-600 to-red-600',
      requirements: 'Reddit account with verified email'
    },
    {
      id: 'tumblr',
      name: 'Tumblr',
      icon: 't.',
      description: 'Blogging and social platform',
      iconBg: 'bg-gradient-to-br from-blue-900 to-slate-900',
      requirements: 'Tumblr blog'
    },
    {
      id: 'wordpress',
      name: 'WordPress',
      icon: 'W',
      description: 'Publish blog posts to your site',
      iconBg: 'bg-gradient-to-br from-slate-700 to-slate-900',
      requirements: 'Self-hosted WordPress with REST API'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-4 sm:p-6 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-3 sm:mb-4 md:mb-6 lg:mb-8">
          <h1 className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl font-bold text-white mb-2">Social Accounts</h1>
          <p className="text-gray-400">
            Connect your social media accounts to publish content directly from ORLA³
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-3 sm:px-4 py-3 rounded-lg mb-3 sm:mb-4 md:mb-6">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right text-red-200 hover:text-white"
            >
              </button>
          </div>
        )}

        {success && (
          <div className="bg-green-500/20 border border-green-500 text-green-200 px-3 sm:px-4 py-3 rounded-lg mb-3 sm:mb-4 md:mb-6">
            {success}
            <button
              onClick={() => setSuccess(null)}
              className="float-right text-green-200 hover:text-white"
            >
              </button>
          </div>
        )}

        {/* Stats Card */}
        {!loading && (
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/20 mb-3 sm:mb-4 md:mb-6 lg:mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white mb-1">Connected Accounts</h3>
                <p className="text-gray-400 text-sm">
                  {Object.values(connections).filter(c => c.connected).length} of {platforms.length} platforms connected
                </p>
              </div>
              <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cobalt to-gold">
                {Object.values(connections).filter(c => c.connected).length}
              </div>
            </div>
            <div className="mt-4 h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cobalt to-royal transition-all duration-500"
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
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt"></div>
            <p className="text-gray-400 mt-4">Loading connections...</p>
          </div>
        ) : (
          /* Social Platform Cards */
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            {platforms.map((platform) => {
              const connection = connections[platform.id];
              const isConnected = connection?.connected;

              return (
                <div
                  key={platform.id}
                  className="bg-white/10 backdrop-blur-lg rounded-2xl p-4 sm:p-6 border border-white/20 hover:border-white/40 transition"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-2 sm:gap-3 md:gap-4">
                      <div className={`w-14 h-14 flex items-center justify-center rounded-xl ${platform.iconBg} text-white font-bold text-lg`}>
                        {platform.icon}
                      </div>
                      <div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-1">
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
                        className="px-3 sm:px-4 py-2 border-2 border-red-500/50 hover:border-red-500 text-red-400 hover:text-red-300 rounded-lg font-semibold transition text-sm"
                      >
                        Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => connectPlatform(platform.id)}
                        className="px-3 sm:px-4 py-2 bg-gradient-to-r from-cobalt to-royal hover:from-cobalt-600 hover:to-royal-600 text-white rounded-lg font-semibold transition shadow-lg text-sm"
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
        <div className="mt-4 sm:mt-6 md:mt-8 grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
          {/* How it Works */}
          <div className="bg-cobalt/10 border border-cobalt/30 rounded-xl p-4 sm:p-6">
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
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 sm:p-6">
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

        {/* Platform Support */}
        <div className="mt-4 sm:mt-6 md:mt-8 bg-cobalt/10 border border-cobalt/30 rounded-xl p-4 sm:p-6">
          <div className="flex items-center gap-3 mb-3">
            <h4 className="text-lg font-semibold text-gold">
              Full OAuth Support
            </h4>
          </div>
          <p className="text-gray-300 text-sm">
            All 9 platforms support secure OAuth 2.0 authentication. Click "Connect Account" on any platform to securely link your account.
            Your credentials are encrypted and stored securely. You can disconnect at any time.
          </p>
        </div>
      </div>
    </div>
  );
}
