'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

type SocialAccount = {
  id: string;
  platform: string;
  account_name: string;
  account_username?: string;
  account_email?: string;
  profile_image_url?: string;
  is_active: boolean;
  is_default: boolean;
  connected_at: string;
  last_used_at?: string;
};

type Platform = {
  id: string;
  name: string;
  icon: string;
  color: string;
  description: string;
  available: boolean;
};

const PLATFORMS: Platform[] = [
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', color: 'blue', description: 'Professional network & business content', available: true },
  { id: 'instagram', name: 'Instagram', icon: '📸', color: 'pink', description: 'Visual stories & photos', available: false },
  { id: 'facebook', name: 'Facebook', icon: '👥', color: 'blue', description: 'Social network & community', available: false },
  { id: 'twitter', name: 'Twitter/X', icon: '🐦', color: 'sky', description: 'Real-time news & conversations', available: false },
  { id: 'youtube', name: 'YouTube', icon: '▶️', color: 'red', description: 'Video content & channels', available: false },
  { id: 'tiktok', name: 'TikTok', icon: '🎵', color: 'purple', description: 'Short-form video content', available: false },
  { id: 'reddit', name: 'Reddit', icon: '🤖', color: 'orange', description: 'Communities & discussions', available: false },
  { id: 'tumblr', name: 'Tumblr', icon: '📝', color: 'indigo', description: 'Blogging & microblogging', available: false },
  { id: 'wordpress', name: 'WordPress', icon: '✍️', color: 'gray', description: 'Blog posts & articles', available: false },
];

export default function SettingsPage() {
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    loadAccounts();

    // Check for OAuth callback messages
    const params = new URLSearchParams(window.location.search);
    const success = params.get('success');
    const error = params.get('error');

    if (success === 'linkedin_connected') {
      setSuccessMessage('🎉 LinkedIn account connected successfully!');
      // Clear URL params
      window.history.replaceState({}, '', '/dashboard/settings');
    } else if (error) {
      const errorMessages: { [key: string]: string } = {
        'invalid_state': '❌ Invalid OAuth state. Please try again.',
        'token_failed': '❌ Failed to exchange token. Please try again.',
        'profile_failed': '❌ Failed to fetch profile. Please check permissions.',
        'oauth_failed': '❌ OAuth failed. Please try again.'
      };
      setErrorMessage(errorMessages[error] || '❌ An error occurred during authentication.');
      window.history.replaceState({}, '', '/dashboard/settings');
    }
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await api.get('/auth/accounts');
      setAccounts(data.accounts || []);
    } catch (err) {
      console.error('Failed to load accounts:', err);
      setErrorMessage('Failed to load connected accounts');
    } finally {
      setLoading(false);
    }
  };

  const connectPlatform = (platform: string) => {
    // Redirect to OAuth flow
    window.location.href = `${config.apiUrl}/auth/${platform}`;
  };

  const disconnectAccount = async (accountId: string, platformName: string) => {
    if (!confirm(`Are you sure you want to disconnect this ${platformName} account?`)) {
      return;
    }

    try {
      await api.delete(`/auth/accounts/${accountId}`);
      setSuccessMessage(`✅ ${platformName} account disconnected`);
      loadAccounts();
    } catch (err) {
      console.error('Failed to disconnect:', err);
      setErrorMessage('Failed to disconnect account');
    }
  };

  const setDefaultAccount = async (accountId: string, platformName: string) => {
    try {
      await api.post(`/auth/accounts/${accountId}/set-default`);
      setSuccessMessage(`⭐ Set as default ${platformName} account`);
      loadAccounts();
    } catch (err) {
      console.error('Failed to set default:', err);
      setErrorMessage('Failed to set default account');
    }
  };

  const getConnectedAccount = (platformId: string): SocialAccount | undefined => {
    return accounts.find(acc => acc.platform === platformId && acc.is_active);
  };

  const getPlatformColor = (color: string) => {
    const colors: { [key: string]: string } = {
      blue: 'from-blue-600 to-blue-700',
      pink: 'from-pink-600 to-pink-700',
      sky: 'from-sky-600 to-sky-700',
      red: 'from-red-600 to-red-700',
      purple: 'from-purple-600 to-purple-700',
      orange: 'from-orange-600 to-orange-700',
      indigo: 'from-indigo-600 to-indigo-700',
      gray: 'from-gray-600 to-gray-700',
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              ⚙️ Settings
            </h1>
            <p className="text-gray-400 mt-2">Manage your connected social media accounts</p>
          </div>
        </div>

        {/* Success/Error Messages */}
        {successMessage && (
          <div className="mb-6 bg-green-900/30 border border-green-500/50 rounded-lg p-4 flex items-center justify-between">
            <p className="text-green-300">{successMessage}</p>
            <button onClick={() => setSuccessMessage('')} className="text-green-300 hover:text-white">✕</button>
          </div>
        )}

        {errorMessage && (
          <div className="mb-6 bg-red-900/30 border border-red-500/50 rounded-lg p-4 flex items-center justify-between">
            <p className="text-red-300">{errorMessage}</p>
            <button onClick={() => setErrorMessage('')} className="text-red-300 hover:text-white">✕</button>
          </div>
        )}

        {/* Connected Accounts Section */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-8">
          <h2 className="text-2xl font-bold text-white mb-6">🔗 Connected Accounts</h2>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin text-6xl mb-4">⚙️</div>
              <p className="text-gray-400">Loading accounts...</p>
            </div>
          ) : accounts.length === 0 ? (
            <div className="text-center py-12 bg-white/5 rounded-lg border-2 border-dashed border-white/20">
              <div className="text-6xl mb-4">🔌</div>
              <h3 className="text-xl font-bold text-white mb-2">No Accounts Connected</h3>
              <p className="text-gray-400">Connect your first social media account below to start posting!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {accounts.map(account => {
                const platform = PLATFORMS.find(p => p.id === account.platform);
                return (
                  <div
                    key={account.id}
                    className="bg-white/10 rounded-lg p-6 border border-white/20 hover:border-white/40 transition"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="text-4xl">{platform?.icon || '🔗'}</div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-xl font-bold text-white">{account.account_name}</h3>
                            {account.is_default && (
                              <span className="bg-yellow-600 text-white text-xs px-2 py-1 rounded-full font-bold">
                                ⭐ DEFAULT
                              </span>
                            )}
                          </div>
                          <p className="text-gray-400 text-sm">
                            {account.account_username && `@${account.account_username} • `}
                            {account.account_email}
                          </p>
                          <p className="text-gray-500 text-xs mt-1">
                            Connected {new Date(account.connected_at).toLocaleDateString()}
                            {account.last_used_at && ` • Last used ${new Date(account.last_used_at).toLocaleDateString()}`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {!account.is_default && (
                          <button
                            onClick={() => setDefaultAccount(account.id, platform?.name || account.platform)}
                            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg font-semibold transition"
                          >
                            Set Default
                          </button>
                        )}
                        <button
                          onClick={() => disconnectAccount(account.id, platform?.name || account.platform)}
                          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-semibold transition"
                        >
                          Disconnect
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Available Platforms Section */}
        <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10">
          <h2 className="text-2xl font-bold text-white mb-6">➕ Connect More Platforms</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {PLATFORMS.map(platform => {
              const connected = getConnectedAccount(platform.id);
              return (
                <div
                  key={platform.id}
                  className={`bg-white/10 rounded-lg p-6 border ${
                    connected
                      ? 'border-green-500/50 bg-green-900/20'
                      : platform.available
                      ? 'border-white/20 hover:border-white/40'
                      : 'border-white/10 opacity-50'
                  } transition`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-4xl">{platform.icon}</div>
                    {connected && (
                      <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full font-bold">
                        ✓ CONNECTED
                      </span>
                    )}
                    {!platform.available && (
                      <span className="bg-gray-600 text-white text-xs px-2 py-1 rounded-full font-bold">
                        COMING SOON
                      </span>
                    )}
                  </div>

                  <h3 className="text-lg font-bold text-white mb-1">{platform.name}</h3>
                  <p className="text-gray-400 text-sm mb-4">{platform.description}</p>

                  {!connected && platform.available && (
                    <button
                      onClick={() => connectPlatform(platform.id)}
                      className={`w-full py-2 bg-gradient-to-r ${getPlatformColor(platform.color)} hover:opacity-90 text-white rounded-lg font-semibold transition`}
                    >
                      Connect {platform.name}
                    </button>
                  )}

                  {connected && (
                    <p className="text-green-400 text-sm font-semibold text-center">
                      {connected.account_name}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 bg-blue-900/30 border border-blue-500/50 rounded-lg p-6">
          <h3 className="text-lg font-bold text-blue-300 mb-2">ℹ️ About OAuth Connections</h3>
          <ul className="text-gray-300 text-sm space-y-2">
            <li>• Your account credentials are stored securely and encrypted</li>
            <li>• You can disconnect any account at any time</li>
            <li>• Set a default account for each platform to use when posting</li>
            <li>• Tokens automatically refresh to keep your accounts connected</li>
            <li>• Coming soon: Multi-account support for posting to multiple profiles</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
