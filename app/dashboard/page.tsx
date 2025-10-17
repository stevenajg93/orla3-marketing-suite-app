'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function Dashboard() {
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState('');

  const generateContent = async () => {
    setGenerating(true);
    setStatus('Generating content...');
    
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStatus(`✅ Generated ${data.count} articles successfully!`);
      } else {
        setStatus('❌ Error generating content');
      }
    } catch (error) {
      setStatus('❌ Error connecting to API');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              ORLA3 Command Center
            </h1>
            <p className="text-gray-600">Your complete marketing automation headquarters</p>
          </div>
          <div className="flex gap-3">
            <Link 
              href="/dashboard/articles"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-6 rounded-lg"
            >
              📚 Articles
            </Link>
            <Link 
              href="/dashboard/social"
              className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-6 rounded-lg"
            >
              🚀 Social Media
            </Link>
          </div>
        </div>
        
        {status && (
          <div className="bg-white rounded-lg shadow p-4 mb-6 border-l-4 border-blue-500">
            {status}
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-3xl mb-2">📊</div>
            <div className="text-2xl font-bold">1,234</div>
            <div className="text-gray-500">Views Today</div>
            <div className="text-green-500 text-sm">↑ 23%</div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-3xl mb-2">✨</div>
            <div className="text-2xl font-bold">3</div>
            <div className="text-gray-500">Articles Generated</div>
            <div className="text-green-500 text-sm">Ready to publish</div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-3xl mb-2">🚀</div>
            <div className="text-2xl font-bold">12</div>
            <div className="text-gray-500">Social Posts</div>
            <div className="text-green-500 text-sm">Across 8 platforms</div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="text-3xl mb-2">💰</div>
            <div className="text-2xl font-bold">$2,450</div>
            <div className="text-gray-500">Revenue Impact</div>
            <div className="text-green-500 text-sm">This week</div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">🎯 Content Generation</h2>
            <div className="space-y-3">
              <button 
                onClick={generateContent}
                disabled={generating}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg"
              >
                {generating ? '⏳ Generating...' : '📝 Generate Articles'}
              </button>
              <Link 
                href="/dashboard/articles"
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 px-4 rounded-lg block text-center"
              >
                📄 View All Articles
              </Link>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">🚀 Social Media</h2>
            <div className="space-y-3">
              <Link 
                href="/dashboard/social"
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-3 px-4 rounded-lg block text-center"
              >
                💬 Generate Social Posts
              </Link>
              <button className="w-full bg-pink-600 hover:bg-pink-700 text-white font-medium py-3 px-4 rounded-lg">
                📅 Schedule Posts
              </button>
              <button className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg">
                💬 Engage Audience
              </button>
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-xl font-bold mb-4">📈 Analytics & Optimization</h2>
            <div className="space-y-3">
              <button className="w-full bg-orange-600 hover:bg-orange-700 text-white font-medium py-3 px-4 rounded-lg">
                📊 View Analytics
              </button>
              <button className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg">
                🎯 Run A/B Tests
              </button>
              <button className="w-full bg-teal-600 hover:bg-teal-700 text-white font-medium py-3 px-4 rounded-lg">
                🔄 Refresh Content
              </button>
            </div>
          </div>
        </div>
        
        <div className="mt-8 bg-gradient-to-r from-purple-600 to-blue-600 rounded-xl p-6 text-white">
          <h2 className="text-2xl font-bold mb-2">🤖 Full Automation Active</h2>
          <p className="mb-4">Your ORLA3 system is monitoring, generating, and optimizing 24/7</p>
          <div className="flex gap-4">
            <button className="bg-white text-purple-600 font-medium py-2 px-4 rounded-lg hover:bg-gray-100">
              View Automation Log
            </button>
            <button className="bg-white/20 text-white font-medium py-2 px-4 rounded-lg hover:bg-white/30">
              Configure Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
