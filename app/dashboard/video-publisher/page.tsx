'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const VIDEO_PLATFORMS = [
  { id: 'tiktok', name: 'TikTok', icon: '🎵', color: 'from-black to-gray-800' },
  { id: 'youtube', name: 'YouTube Shorts', icon: '▶️', color: 'from-red-600 to-red-700' },
  { id: 'instagram', name: 'Instagram Reels', icon: '📸', color: 'from-pink-500 to-purple-600' }
];

export default function VideoPublisher() {
  const [driveStatus, setDriveStatus] = useState<any>(null);
  const [videos, setVideos] = useState<any[]>([]);
  const [folders, setFolders] = useState<any[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [caption, setCaption] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    checkDriveStatus();
  }, []);

  const checkDriveStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/drive/status');
      const data = await res.json();
      setDriveStatus(data);
      
      if (data.connected) {
        loadVideos();
        loadFolders();
      }
    } catch (err) {
      console.error('Failed to check Drive status');
    }
  };

  const loadVideos = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/drive/videos');
      const data = await res.json();
      setVideos(data.files || []);
    } catch (err) {
      setError('Failed to load videos from Drive');
    } finally {
      setLoading(false);
    }
  };

  const loadFolders = async () => {
    try {
      const res = await fetch('http://localhost:8000/drive/folders');
      const data = await res.json();
      setFolders(data.folders || []);
    } catch (err) {
      console.error('Failed to load folders');
    }
  };

  const generateCaption = async () => {
    if (!selectedVideo) {
      setError('Please select a video first');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      // AI generates caption based on video filename and context
      const response = await fetch('http://localhost:8000/social/caption', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: selectedVideo.name,
          platform: 'instagram',
          tone: 'professional',
          length: 'short'
        })
      });

      const data = await response.json();
      setCaption(data.caption || 'Caption generated');
    } catch (err) {
      setError('Failed to generate caption');
    } finally {
      setGenerating(false);
    }
  };

  const togglePlatform = (platformId: string) => {
    if (selectedPlatforms.includes(platformId)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platformId));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platformId]);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-200">
              🎬 Video Publisher
            </h1>
            <p className="text-gray-400 mt-2">Publish real videographer content to TikTok, YouTube, Instagram</p>
          </div>
        </div>

        {/* Drive Connection Status */}
        <div className={`rounded-2xl p-6 border mb-6 ${
          driveStatus?.connected 
            ? 'bg-green-900/40 border-green-400/30' 
            : 'bg-yellow-900/40 border-yellow-400/30'
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white mb-2">
                {driveStatus?.connected ? '✅ Google Drive Connected' : '⚠️ Google Drive Not Connected'}
              </h3>
              <p className="text-gray-300">{driveStatus?.message}</p>
            </div>
            {!driveStatus?.connected && (
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg">
                Connect Drive
              </button>
            )}
          </div>
        </div>

        {driveStatus?.connected ? (
          <>
            {/* Video Selection */}
            <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-white">Select Video from Drive</h2>
                <button
                  onClick={loadVideos}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg text-sm"
                >
                  🔄 Refresh
                </button>
              </div>

              {loading ? (
                <p className="text-gray-400">Loading videos...</p>
              ) : videos.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {videos.map((video) => (
                    <div
                      key={video.id}
                      onClick={() => setSelectedVideo(video)}
                      className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                        selectedVideo?.id === video.id
                          ? 'bg-purple-600 border-purple-400'
                          : 'bg-white/5 border-white/10 hover:border-white/30'
                      }`}
                    >
                      <div className="text-4xl mb-2">🎥</div>
                      <h3 className="text-white font-bold truncate">{video.name}</h3>
                      <p className="text-gray-400 text-sm mt-1">
                        {video.size ? `${Math.round(parseInt(video.size) / 1024 / 1024)}MB` : 'Unknown size'}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400 mb-4">No videos found in Drive</p>
                  <p className="text-gray-500 text-sm">Upload videos to your connected Google Drive folder</p>
                </div>
              )}
            </div>

            {/* Caption Generation */}
            {selectedVideo && (
              <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
                <h2 className="text-2xl font-bold text-white mb-6">Generate Caption</h2>
                
                <div className="mb-6">
                  <p className="text-gray-400 mb-2">Selected Video:</p>
                  <p className="text-white font-bold">{selectedVideo.name}</p>
                </div>

                <button
                  onClick={generateCaption}
                  disabled={generating}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold py-4 px-8 rounded-lg mb-6 disabled:opacity-50"
                >
                  {generating ? '✨ Generating Caption...' : '⚡ Generate AI Caption'}
                </button>

                {caption && (
                  <div>
                    <label className="block text-white font-bold mb-2">Generated Caption</label>
                    <textarea
                      value={caption}
                      onChange={(e) => setCaption(e.target.value)}
                      rows={6}
                      className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Platform Selection */}
            {caption && (
              <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-8 border border-white/10 mb-6">
                <h2 className="text-2xl font-bold text-white mb-6">Select Platforms</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  {VIDEO_PLATFORMS.map(platform => (
                    <button
                      key={platform.id}
                      onClick={() => togglePlatform(platform.id)}
                      className={`p-6 rounded-xl border-2 transition-all ${
                        selectedPlatforms.includes(platform.id)
                          ? `bg-gradient-to-br ${platform.color} border-white/40`
                          : 'bg-white/5 border-white/10 hover:border-white/30'
                      }`}
                    >
                      <div className="text-4xl mb-2">{platform.icon}</div>
                      <div className="text-white font-bold">{platform.name}</div>
                    </button>
                  ))}
                </div>

                <button
                  disabled={selectedPlatforms.length === 0}
                  className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-black font-bold py-4 px-8 rounded-lg disabled:opacity-50"
                >
                  🚀 Publish to {selectedPlatforms.length} Platform{selectedPlatforms.length !== 1 ? 's' : ''}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4">🔌</div>
            <h3 className="text-2xl font-bold text-white mb-4">Connect Google Drive</h3>
            <p className="text-gray-400 mb-6">
              Connect your Google Drive to access video content uploaded by your videographer team
            </p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-lg">
              Connect Google Drive
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-500/20 border border-red-500 rounded-lg p-4 text-red-200">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
