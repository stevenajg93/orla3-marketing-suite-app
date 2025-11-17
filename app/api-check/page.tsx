'use client';

import { config } from '@/lib/config';

export default function ApiCheckPage() {
  return (
    <div className="min-h-screen bg-slate-900 p-8">
      <div className="max-w-2xl mx-auto bg-white/10 rounded-xl p-6 border border-white/20">
        <h1 className="text-2xl font-bold text-white mb-4">API Configuration Check</h1>

        <div className="space-y-4">
          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400 text-sm mb-1">API URL</p>
            <p className="text-white font-mono text-lg">{config.apiUrl}</p>
          </div>

          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400 text-sm mb-1">Environment</p>
            <p className="text-white font-mono">{config.isProd ? 'Production' : 'Development'}</p>
          </div>

          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400 text-sm mb-1">Debug Logs Enabled</p>
            <p className="text-white font-mono">{config.enableDebugLogs ? 'Yes' : 'No'}</p>
          </div>

          <div className="bg-black/30 p-4 rounded">
            <p className="text-gray-400 text-sm mb-1">Backend Health Check</p>
            <button
              onClick={async () => {
                try {
                  const response = await fetch(`${config.apiUrl}/health`);
                  const data = await response.json();
                  alert(`Backend Status: ${JSON.stringify(data, null, 2)}`);
                } catch (err: any) {
                  alert(`Error: ${err.message}`);
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded mt-2"
            >
              Test Backend Connection
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
