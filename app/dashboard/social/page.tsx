'use client';

import { useState } from 'react';
import Link from 'next/link';

export default function SocialDashboard() {
  const [generating, setGenerating] = useState(false);
  const [socialPosts, setSocialPosts] = useState<any>(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState(['linkedin', 'twitter']);

  const generateSocialPosts = async () => {
    setGenerating(true);
    try {
      const response = await fetch('/api/social', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generate',
          articleTopic: 'ORLA3 Marketing Automation',
          articleContent: 'ORLA3 revolutionizes marketing by automating content creation...',
          platforms: selectedPlatforms
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setSocialPosts(data.posts);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setGenerating(false);
    }
  };

  const platforms = [
    { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
    { id: 'twitter', name: 'Twitter/X', icon: '🐦' },
    { id: 'facebook', name: 'Facebook', icon: '📘' },
    { id: 'instagram', name: 'Instagram', icon: '📸' },
    { id: 'youtube', name: 'YouTube', icon: '📺' },
    { id: 'tiktok', name: 'TikTok', icon: '🎵' },
    { id: 'reddit', name: 'Reddit', icon: '🤖' },
    { id: 'pinterest', name: 'Pinterest', icon: '📌' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              Social Media Command Center
            </h1>
            <p className="text-gray-600">Generate and manage posts across all platforms</p>
          </div>
          <Link 
            href="/dashboard"
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            ← Back to Dashboard
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-4">Select Platforms</h2>
          <div className="grid grid-cols-4 gap-3 mb-6">
            {platforms.map(platform => (
              <label 
                key={platform.id}
                className={`flex items-center p-3 rounded-lg border-2 cursor-pointer transition ${
                  selectedPlatforms.includes(platform.id) 
                    ? 'border-purple-500 bg-purple-50' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedPlatforms.includes(platform.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedPlatforms([...selectedPlatforms, platform.id]);
                    } else {
                      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform.id));
                    }
                  }}
                  className="mr-2"
                />
                <span className="text-xl mr-2">{platform.icon}</span>
                <span className="text-sm font-medium">{platform.name}</span>
              </label>
            ))}
          </div>
          
          <button
            onClick={generateSocialPosts}
            disabled={generating || selectedPlatforms.length === 0}
            className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-3 px-4 rounded-lg"
          >
            {generating ? '⏳ Generating Posts...' : '🚀 Generate Social Posts'}
          </button>
        </div>

        {socialPosts && (
          <div className="space-y-4">
            <div className="bg-green-100 border-l-4 border-green-500 p-4 rounded">
              <p className="text-green-700 font-medium">
                ✅ Generated {Object.keys(socialPosts).length} social posts
              </p>
            </div>
            
            {Object.entries(socialPosts).map(([platform, post]: [string, any]) => (
              <div key={platform} className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-bold capitalize">
                    {platforms.find(p => p.id === platform)?.icon} {platform}
                  </h3>
                  <div className="flex gap-2">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                      Edit
                    </button>
                    <button className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm">
                      Schedule
                    </button>
                  </div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700">
                    {post.content}
                  </pre>
                </div>
                <div className="mt-3 text-xs text-gray-500">
                  Generated: {new Date(post.generated).toLocaleString()}
                </div>
              </div>
            ))}
            
            <div className="bg-blue-50 rounded-xl p-6 mt-6">
              <h3 className="font-bold mb-3">🎯 Next Steps</h3>
              <ul className="space-y-2 text-sm">
                <li>• Schedule posts for optimal times</li>
                <li>• Set up engagement automation</li>
                <li>• Monitor performance</li>
                <li>• A/B test variations</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
