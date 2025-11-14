'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

interface CloudConnection {
  provider: 'google_drive' | 'onedrive' | 'dropbox';
  connected: boolean;
  provider_email?: string;
  connected_at?: string;
}

export default function CloudStorageSettings() {
  const [connections, setConnections] = useState<CloudConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Check for OAuth callback success/error in URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const cloudConnect = params.get('cloud_connect');
    const provider = params.get('provider');

    if (cloudConnect === 'success' && provider) {
      setSuccess(`Successfully connected to ${provider.replace('_', ' ')}!`);
      // Remove query params from URL
      window.history.replaceState({}, '', '/dashboard/settings/cloud-storage');
      loadConnections();
    } else if (cloudConnect === 'error') {
      const message = params.get('message') || 'Failed to connect';
      setError(message);
      window.history.replaceState({}, '', '/dashboard/settings/cloud-storage');
    }
  }, []);

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get('/cloud-storage/connections');

      if (response.success) {
        setConnections(response.connections || []);
      } else {
        setError('Failed to load cloud storage connections');
      }
    } catch (err: any) {
      console.error('Error loading connections:', err);

      // Show specific error message
      const errorMessage = err?.message || 'Failed to load cloud storage connections';

      // If not authenticated, show helpful message
      if (err?.status === 401 || errorMessage.includes('authorization')) {
        setError('Please log in to view cloud storage connections');

        // Redirect to login after a delay
        setTimeout(() => {
          window.location.href = '/auth/login';
        }, 2000);
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const connectProvider = async (provider: string) => {
    try {
      // Get token from localStorage
      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('You must be logged in to connect cloud storage');
        return;
      }

      // Make authenticated request to get OAuth URL
      // The backend will create state token and redirect to OAuth provider
      const url = `${config.apiUrl}/cloud-storage/connect/${provider}`;

      // Redirect to backend OAuth endpoint with token in URL
      // Backend will validate token and initiate OAuth flow
      window.location.href = `${url}?token=${encodeURIComponent(token)}`;
    } catch (err) {
      setError(`Failed to initiate ${provider} connection`);
      console.error(err);
    }
  };

  const disconnectProvider = async (provider: string) => {
    if (!confirm(`Disconnect from ${provider.replace('_', ' ')}?`)) {
      return;
    }

    try {
      await api.delete(`/cloud-storage/disconnect/${provider}`);
      setSuccess(`Disconnected from ${provider.replace('_', ' ')}`);
      loadConnections();
    } catch (err) {
      setError(`Failed to disconnect from ${provider}`);
    }
  };

  const getConnection = (provider: string): CloudConnection | undefined => {
    return connections.find(c => c.provider === provider);
  };

  const providers = [
    {
      id: 'google_drive',
      name: 'Google Drive',
      icon: '',
      description: 'Access your files from Google Drive',
      color: 'from-cobalt to-cobalt'
    },
    {
      id: 'onedrive',
      name: 'Microsoft OneDrive',
      icon: '',
      description: 'Access your files from OneDrive',
      color: 'from-cobalt to-royal'
    },
    {
      id: 'dropbox',
      name: 'Dropbox',
      icon: '',
      description: 'Access your files from Dropbox',
      color: 'from-cobalt to-royal'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Cloud Storage</h1>
          <p className="text-gray-400">
            Connect your cloud storage accounts to import brand assets and files
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
              </button>
          </div>
        )}

        {/* Loading State */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt"></div>
            <p className="text-gray-400 mt-4">Loading connections...</p>
          </div>
        ) : (
          /* Cloud Storage Cards */
          <div className="grid gap-6">
            {providers.map((provider) => {
              const connection = getConnection(provider.id);
              const isConnected = connection?.connected;

              return (
                <div
                  key={provider.id}
                  className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 hover:border-white/40 transition"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className={`text-5xl p-4 rounded-xl bg-gradient-to-br ${provider.color}`}>
                        {provider.icon}
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-white mb-1">
                          {provider.name}
                        </h3>
                        <p className="text-gray-400 mb-2">
                          {provider.description}
                        </p>
                        {isConnected && connection?.provider_email && (
                          <div className="flex items-center gap-2 text-green-400 text-sm">
                            <span className="inline-block w-2 h-2 bg-green-400 rounded-full"></span>
                            Connected as {connection.provider_email}
                          </div>
                        )}
                        {isConnected && connection?.connected_at && (
                          <p className="text-gray-500 text-sm mt-1">
                            Connected {new Date(connection.connected_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Action Button */}
                    <div>
                      {isConnected ? (
                        <button
                          onClick={() => disconnectProvider(provider.id)}
                          className="px-6 py-2 border-2 border-red-500/50 hover:border-red-500 text-red-400 hover:text-red-300 rounded-lg font-semibold transition"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={() => connectProvider(provider.id)}
                          className={`px-6 py-2 bg-gradient-to-r ${provider.color} hover:opacity-90 text-white rounded-lg font-semibold transition shadow-lg`}
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 bg-cobalt/10 border border-cobalt/30 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-cobalt-300 mb-2">
            Privacy & Security
          </h4>
          <ul className="text-gray-300 space-y-2 text-sm">
            <li>• Your credentials are encrypted and stored securely</li>
            <li>• We only access files you explicitly choose to import</li>
            <li>• You can disconnect at any time</li>
            <li>• Your tokens are never shared with third parties</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
