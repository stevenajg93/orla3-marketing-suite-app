'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

type MediaAsset = {
  id: string;
  name: string;
  type: string;
  source: string;
  url?: string;
  thumbnail?: string;
  size?: string;
  created_at?: string;
};

type MediaFolder = {
  id: string;
  name: string;
  path: string;
  asset_count: number;
};

export default function MediaLibrary() {
  const [activeTab, setActiveTab] = useState<'drive' | 'unsplash'>('drive');
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [folders, setFolders] = useState<MediaFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [mediaType, setMediaType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [unsplashImages, setUnsplashImages] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);

  useEffect(() => {
    loadStatus();
    loadFolders();
    loadAssets();
  }, []);

  const loadStatus = async () => {
    try {
      const res = await fetch('http://localhost:8000/media/status');
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load status');
    }
  };

  const loadFolders = async () => {
    try {
      const res = await fetch('http://localhost:8000/media/folders');
      const data = await res.json();
      if (data.folders) {
        setFolders(data.folders);
      }
    } catch (err) {
      console.error('Failed to load folders');
    }
  };

  const loadAssets = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedFolder) params.append('folder_id', selectedFolder);
      if (mediaType !== 'all') params.append('media_type', mediaType);

      const res = await fetch(`http://localhost:8000/media/library?${params}`);
      const data = await res.json();
      setAssets(data.assets || []);
    } catch (err) {
      console.error('Failed to load assets');
    } finally {
      setLoading(false);
    }
  };

  const searchUnsplash = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/media/unsplash?query=${encodeURIComponent(searchQuery)}&per_page=20`);
      const data = await res.json();
      setUnsplashImages(data.images || []);
    } catch (err) {
      console.error('Failed to search Unsplash');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssets();
  }, [selectedFolder, mediaType]);

  const currentAssets = activeTab === 'drive' ? assets : unsplashImages;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <Link href="/dashboard" className="text-gray-400 hover:text-white mb-2 inline-block">
              ← Back to Dashboard
            </Link>
            <h1 className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-200">
              📁 Media Library
            </h1>
            <p className="text-gray-400 mt-2">Manage Google Drive assets & generate AI content</p>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className={`rounded-2xl p-6 border ${
            status?.drive?.connected 
              ? 'bg-green-900/40 border-green-400/30' 
              : 'bg-yellow-900/40 border-yellow-400/30'
          }`}>
            <h3 className="text-xl font-bold text-white mb-2">🔗 Google Drive</h3>
            <p className="text-gray-300">{status?.drive?.status}</p>
            {status?.drive?.connected && (
              <p className="text-sm text-gray-400 mt-2">{assets.length} assets found</p>
            )}
          </div>

          <div className={`rounded-2xl p-6 border ${
            status?.unsplash?.connected 
              ? 'bg-green-900/40 border-green-400/30' 
              : 'bg-yellow-900/40 border-yellow-400/30'
          }`}>
            <h3 className="text-xl font-bold text-white mb-2">✨ Unsplash API</h3>
            <p className="text-gray-300">{status?.unsplash?.status}</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('drive')}
            className={`flex-1 py-4 px-6 rounded-lg font-bold transition-all ${
              activeTab === 'drive'
                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            🔗 Google Drive Assets
          </button>
          <button
            onClick={() => setActiveTab('unsplash')}
            className={`flex-1 py-4 px-6 rounded-lg font-bold transition-all ${
              activeTab === 'unsplash'
                ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            ✨ Generate from Unsplash
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
            {activeTab === 'drive' ? (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Filters</h2>

                <div className="mb-6">
                  <label className="block text-white font-bold mb-2 text-sm">Type</label>
                  <select
                    value={mediaType}
                    onChange={(e) => setMediaType(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="all">All Types</option>
                    <option value="video">Videos</option>
                    <option value="image">Images</option>
                    <option value="document">Documents</option>
                  </select>
                </div>

                <h3 className="text-lg font-bold text-white mb-3">Folders</h3>
                <button
                  onClick={() => setSelectedFolder('')}
                  className={`w-full text-left p-3 rounded-lg mb-2 transition-all ${
                    selectedFolder === ''
                      ? 'bg-yellow-600 text-white'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  All Files
                </button>

                {folders.map((folder) => (
                  <button
                    key={folder.id}
                    onClick={() => setSelectedFolder(folder.id)}
                    className={`w-full text-left p-3 rounded-lg mb-2 transition-all ${
                      selectedFolder === folder.id
                        ? 'bg-yellow-600 text-white'
                        : 'bg-white/10 text-gray-300 hover:bg-white/20'
                    }`}
                  >
                    <div className="font-bold text-sm">{folder.name}</div>
                    <div className="text-xs opacity-75">{folder.asset_count} files</div>
                  </button>
                ))}
              </>
            ) : (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Search Unsplash</h2>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchUnsplash()}
                  placeholder="e.g., videography, camera"
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 mb-4"
                />
                <button
                  onClick={searchUnsplash}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-4 rounded-lg transition-all disabled:opacity-50"
                >
                  {loading ? '🔍 Searching...' : '🔍 Search'}
                </button>
              </>
            )}
          </div>

          {/* Assets Grid */}
          <div className="lg:col-span-3 bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
            <h2 className="text-2xl font-bold text-white mb-6">
              {activeTab === 'drive' ? '🔗 Your Assets' : '✨ Unsplash Images'}
            </h2>

            {loading ? (
              <p className="text-gray-400">Loading...</p>
            ) : currentAssets.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">
                  {activeTab === 'drive' 
                    ? 'No assets found. Upload files to your Google Drive.'
                    : 'Search for images above to get started.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentAssets.map((asset) => (
                  <div
                    key={asset.id}
                    className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-yellow-400 transition-all cursor-pointer"
                  >
                    {asset.thumbnail ? (
                      <img 
                        src={asset.thumbnail} 
                        alt={asset.name}
                        className="w-full h-40 object-cover"
                      />
                    ) : (
                      <div className="w-full h-40 bg-gradient-to-br from-purple-900 to-blue-900 flex items-center justify-center">
                        <span className="text-6xl">
                          {asset.type === 'video' ? '🎬' : asset.type === 'image' ? '🖼️' : '📄'}
                        </span>
                      </div>
                    )}
                    
                    <div className="p-4">
                      <h3 className="text-white font-bold text-sm mb-1 truncate">{asset.name}</h3>
                      <div className="flex items-center justify-between">
                        <span className={`text-xs px-2 py-1 rounded ${
                          asset.source === 'drive' ? 'bg-blue-600' : 'bg-purple-600'
                        }`}>
                          {asset.source === 'drive' ? '🔗 Drive' : '✨ Unsplash'}
                        </span>
                        {asset.size && (
                          <span className="text-gray-400 text-xs">
                            {(parseInt(asset.size) / 1024 / 1024).toFixed(2)} MB
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
