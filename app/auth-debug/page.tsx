'use client';

import { useState, useEffect } from 'react';
import { config } from '@/lib/config';
import { api } from '@/lib/api-client';

export default function AuthDebugPage() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [apiResponse, setApiResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load tokens from localStorage
    const access = localStorage.getItem('access_token');
    const refresh = localStorage.getItem('refresh_token');
    setAccessToken(access);
    setRefreshToken(refresh);
  }, []);

  const testLibraryEndpoint = async () => {
    try {
      setError(null);
      setApiResponse(null);
      const data = await api.get('/library/content');
      setApiResponse(data);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    }
  };

  const testCloudStorageEndpoint = async () => {
    try {
      setError(null);
      setApiResponse(null);
      const data = await api.get('/cloud-storage/connections');
      setApiResponse(data);
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    }
  };

  const decodeToken = (token: string) => {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) return null;
      const payload = JSON.parse(atob(parts[1]));
      return payload;
    } catch {
      return null;
    }
  };

  const accessPayload = accessToken ? decodeToken(accessToken) : null;

  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="bg-white/10 rounded-xl p-6 border border-white/20">
          <h1 className="text-2xl font-bold text-white mb-4">Authentication Debug Page</h1>

          <div className="space-y-4">
            {/* Access Token */}
            <div className="bg-black/30 p-4 rounded">
              <p className="text-gray-400 text-sm mb-1">Access Token Status</p>
              {accessToken ? (
                <>
                  <p className="text-green-400 font-mono text-sm mb-2">✓ Present</p>
                  <details className="text-xs">
                    <summary className="text-gray-300 cursor-pointer mb-2">Show Token (first 50 chars)</summary>
                    <p className="text-gray-400 font-mono break-all">{accessToken.substring(0, 50)}...</p>
                  </details>
                  {accessPayload && (
                    <div className="mt-2 text-xs text-gray-300">
                      <p>User ID: <span className="text-white font-mono">{accessPayload.sub}</span></p>
                      <p>Email: <span className="text-white">{accessPayload.email}</span></p>
                      <p>Role: <span className="text-white">{accessPayload.role}</span></p>
                      <p>Expires: <span className="text-white">{new Date(accessPayload.exp * 1000).toLocaleString()}</span></p>
                      <p>Expired: <span className={accessPayload.exp * 1000 < Date.now() ? 'text-red-400' : 'text-green-400'}>
                        {accessPayload.exp * 1000 < Date.now() ? 'YES - TOKEN EXPIRED' : 'No'}
                      </span></p>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-red-400 font-mono text-sm">✗ Missing (user not logged in)</p>
              )}
            </div>

            {/* Refresh Token */}
            <div className="bg-black/30 p-4 rounded">
              <p className="text-gray-400 text-sm mb-1">Refresh Token Status</p>
              {refreshToken ? (
                <>
                  <p className="text-green-400 font-mono text-sm">✓ Present</p>
                  <details className="text-xs">
                    <summary className="text-gray-300 cursor-pointer">Show Token (first 50 chars)</summary>
                    <p className="text-gray-400 font-mono break-all">{refreshToken.substring(0, 50)}...</p>
                  </details>
                </>
              ) : (
                <p className="text-red-400 font-mono text-sm">✗ Missing</p>
              )}
            </div>

            {/* API URL */}
            <div className="bg-black/30 p-4 rounded">
              <p className="text-gray-400 text-sm mb-1">Backend API URL</p>
              <p className="text-white font-mono text-sm">{config.apiUrl}</p>
            </div>

            {/* Test Buttons */}
            <div className="bg-black/30 p-4 rounded space-y-3">
              <p className="text-gray-400 text-sm mb-2">Test API Endpoints</p>
              <div className="flex gap-3">
                <button
                  onClick={testLibraryEndpoint}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm"
                >
                  Test /library/content
                </button>
                <button
                  onClick={testCloudStorageEndpoint}
                  className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded text-sm"
                >
                  Test /cloud-storage/connections
                </button>
              </div>
            </div>

            {/* API Response */}
            {apiResponse && (
              <div className="bg-black/30 p-4 rounded">
                <p className="text-green-400 text-sm mb-2">✓ API Response</p>
                <pre className="text-xs text-gray-300 overflow-auto max-h-64">
                  {JSON.stringify(apiResponse, null, 2)}
                </pre>
              </div>
            )}

            {/* Error */}
            {error && (
              <div className="bg-red-900/30 border border-red-500/50 p-4 rounded">
                <p className="text-red-400 text-sm mb-2">✗ Error</p>
                <p className="text-red-300 text-sm">{error}</p>
              </div>
            )}

            {/* Recommendation */}
            <div className="bg-yellow-900/30 border border-yellow-500/50 p-4 rounded">
              <p className="text-yellow-400 text-sm font-bold mb-2">Diagnosis</p>
              {!accessToken ? (
                <p className="text-yellow-300 text-sm">No access token found. Please log in at <a href="/login" className="underline">/login</a></p>
              ) : accessPayload && accessPayload.exp * 1000 < Date.now() ? (
                <p className="text-yellow-300 text-sm">Access token has expired. Try logging out and back in.</p>
              ) : (
                <p className="text-yellow-300 text-sm">Token looks valid. Test the endpoints above to see if API calls work.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
