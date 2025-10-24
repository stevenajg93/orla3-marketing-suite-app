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
  webViewLink?: string;
};

type MediaFolder = {
  id: string;
  name: string;
  path: string;
  asset_count: number;
};

type GeneratedContent = {
  id: string;
  title: string;
  content_type: string;
  content: string;
  created_at: string;
  status: string;
  tags?: string[];
};

export default function MediaLibrary() {
  const [activeTab, setActiveTab] = useState<'drive' | 'unsplash' | 'generated'>('drive');
  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [folders, setFolders] = useState<MediaFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [selectedFolderName, setSelectedFolderName] = useState<string>('All Files');
  const [breadcrumbs, setBreadcrumbs] = useState<{id: string, name: string}[]>([]);
  const [mediaType, setMediaType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [unsplashImages, setUnsplashImages] = useState<MediaAsset[]>([]);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [previewContent, setPreviewContent] = useState<GeneratedContent | null>(null);

  useEffect(() => {
    loadStatus();
    loadFolders();
    loadGeneratedContent();
  }, []);

  useEffect(() => {
    if (activeTab === 'drive' && selectedFolder) {
      loadAssets();
    }
  }, [selectedFolder, mediaType, activeTab]);

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

  const loadGeneratedContent = async () => {
    try {
      const res = await fetch('http://localhost:8000/library/content');
      const data = await res.json();
      setGeneratedContent(data.items || []);
    } catch (err) {
      console.error('Failed to load generated content');
    }
  };

  const deleteGeneratedContent = async (id: string) => {
    try {
      await fetch(`http://localhost:8000/library/content/${id}`, { method: 'DELETE' });
      loadGeneratedContent();
      setPreviewContent(null);
    } catch (err) {
      console.error('Failed to delete content');
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
      setAssets([]);
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

  const handleFolderClick = (folderId: string, folderName: string) => {
    setSelectedFolder(folderId);
    setSelectedFolderName(folderName);
    setBreadcrumbs([...breadcrumbs, { id: folderId, name: folderName }]);
  };

  const handleAssetClick = (asset: MediaAsset) => {
    if (asset.type === 'folder') {
      handleFolderClick(asset.id, asset.name);
    } else {
      setPreviewAsset(asset);
    }
  };

  const handleDownload = (asset: MediaAsset) => {
    const downloadUrl = `https://drive.google.com/uc?export=download&id=${asset.id}`;
    window.open(downloadUrl, '_blank');
  };

  const handleBreadcrumbClick = (index: number) => {
    const newBreadcrumbs = breadcrumbs.slice(0, index + 1);
    setBreadcrumbs(newBreadcrumbs);
    const folder = newBreadcrumbs[newBreadcrumbs.length - 1];
    setSelectedFolder(folder.id);
    setSelectedFolderName(folder.name);
  };

  const handleAllFilesClick = () => {
    setSelectedFolder('');
    setSelectedFolderName('All Files');
    setBreadcrumbs([]);
  };

  const getFileIcon = (type: string) => {
    switch(type) {
      case 'folder': return '📁';
      case 'video': return '🎬';
      case 'image': return '🖼️';
      case 'document': return '📄';
      case 'blog': return '📝';
      case 'carousel': return '🎨';
      case 'caption': return '💬';
      default: return '📄';
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'published': return 'bg-green-600';
      case 'scheduled': return 'bg-blue-600';
      case 'draft': return 'bg-yellow-600';
      default: return 'bg-gray-600';
    }
  };

  const currentAssets = activeTab === 'drive' ? assets : activeTab === 'unsplash' ? unsplashImages : [];

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
            <p className="text-gray-400 mt-2">Manage Google Drive assets & generated AI content</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className={`rounded-2xl p-6 border ${
            status?.drive?.connected 
              ? 'bg-green-900/40 border-green-400/30' 
              : 'bg-yellow-900/40 border-yellow-400/30'
          }`}>
            <h3 className="text-xl font-bold text-white mb-2">🔗 Google Drive</h3>
            <p className="text-gray-300">{status?.drive?.status}</p>
            {status?.drive?.connected && (
              <p className="text-sm text-gray-400 mt-2">{folders.length} folders found</p>
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

          <div className="rounded-2xl p-6 border bg-purple-900/40 border-purple-400/30">
            <h3 className="text-xl font-bold text-white mb-2">💾 Generated Content</h3>
            <p className="text-gray-300">{generatedContent.length} items saved</p>
          </div>
        </div>

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
          <button
            onClick={() => setActiveTab('generated')}
            className={`flex-1 py-4 px-6 rounded-lg font-bold transition-all ${
              activeTab === 'generated'
                ? 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-black'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            💾 Generated Content
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
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
                  onClick={handleAllFilesClick}
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
                    onClick={() => handleFolderClick(folder.id, folder.name)}
                    className={`w-full text-left p-3 rounded-lg mb-2 transition-all ${
                      selectedFolder === folder.id
                        ? 'bg-yellow-600 text-white'
                        : 'bg-white/10 text-gray-300 hover:bg-white/20'
                    }`}
                  >
                    <div className="font-bold text-sm truncate">{folder.name}</div>
                  </button>
                ))}
              </>
            ) : activeTab === 'unsplash' ? (
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
            ) : (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Filters</h2>
                <p className="text-gray-400 text-sm">All your generated blogs, carousels, and captions in one place.</p>
              </>
            )}
          </div>

          <div className="lg:col-span-3 bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                {activeTab === 'drive' ? '🔗 Your Drive Assets' : activeTab === 'unsplash' ? '✨ Unsplash Images' : '💾 Generated Content'}
              </h2>
              {activeTab === 'drive' && breadcrumbs.length > 0 && (
                <div className="flex items-center gap-2 text-sm text-gray-400 flex-wrap">
                  <span className="cursor-pointer hover:text-yellow-400" onClick={handleAllFilesClick}>Marketing</span>
                  {breadcrumbs.map((crumb, index) => (
                    <span key={`breadcrumb-${index}-${crumb.id}`} className="flex items-center gap-2">
                      <span>/</span>
                      <span 
                        className="cursor-pointer hover:text-yellow-400"
                        onClick={() => handleBreadcrumbClick(index)}
                      >
                        {crumb.name}
                      </span>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {activeTab === 'generated' ? (
              generatedContent.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg">No generated content yet. Create some blogs or carousels to get started!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {generatedContent.map((item) => (
                    <div
                      key={item.id}
                      className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-yellow-400 transition-all cursor-pointer"
                      onClick={() => setPreviewContent(item)}
                    >
                      <div className="w-full h-40 bg-gradient-to-br from-purple-700 to-purple-900 flex items-center justify-center">
                        <span className="text-6xl">{getFileIcon(item.content_type)}</span>
                      </div>
                      
                      <div className="p-4 bg-slate-800/50">
                        <h3 className="text-white font-bold text-sm mb-2 truncate">{item.title}</h3>
                        <div className="flex items-center justify-between">
                          <span className={`text-xs px-2 py-1 rounded font-medium ${getStatusColor(item.status)}`}>
                            {item.status}
                          </span>
                          <span className="text-gray-400 text-xs">
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
                <p className="text-gray-400 mt-4">Loading...</p>
              </div>
            ) : currentAssets.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">
                  {activeTab === 'drive' 
                    ? 'Select a folder to view files.'
                    : 'Search for images above to get started.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentAssets.map((asset) => (
                  <div
                    key={asset.id}
                    className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-yellow-400 transition-all"
                  >
                    <div 
                      onClick={() => handleAssetClick(asset)}
                      className="cursor-pointer"
                    >
                      {asset.thumbnail && asset.type !== 'folder' ? (
                        <img 
                          src={asset.thumbnail} 
                          alt={asset.name}
                          className="w-full h-40 object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                            (e.target as HTMLImageElement).nextElementSibling?.classList.remove('hidden');
                          }}
                        />
                      ) : null}
                      <div className={`w-full h-40 bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center ${asset.thumbnail && asset.type !== 'folder' ? 'hidden' : ''}`}>
                        <span className="text-6xl">
                          {getFileIcon(asset.type)}
                        </span>
                      </div>
                      
                      <div className="p-4 bg-slate-800/50">
                        <h3 className="text-white font-bold text-sm mb-2 truncate">{asset.name}</h3>
                        <div className="flex items-center justify-between">
                          <span className={`text-xs px-2 py-1 rounded font-medium ${
                            asset.type === 'folder' ? 'bg-yellow-600 text-white' : asset.source === 'drive' ? 'bg-blue-600 text-white' : 'bg-purple-600 text-white'
                          }`}>
                            {asset.type === 'folder' ? '📁 Folder' : asset.source === 'drive' ? '🔗 Drive' : '✨ Unsplash'}
                          </span>
                          {asset.size && parseInt(asset.size) > 0 && (
                            <span className="text-gray-300 text-xs">
                              {(parseInt(asset.size) / 1024 / 1024).toFixed(2)} MB
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {asset.type !== 'folder' && (
                      <div className="px-4 pb-4 bg-slate-800/50 flex gap-2">
                        <button
                          onClick={() => handleDownload(asset)}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                        >
                          ⬇️ Download
                        </button>
                        <button
                          onClick={() => window.open(`https://drive.google.com/file/d/${asset.id}/view`, '_blank')}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                        >
                          👁️ View
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {previewAsset && (
        <div 
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8"
          onClick={() => setPreviewAsset(null)}
        >
          <div className="max-w-6xl w-full max-h-full overflow-auto bg-slate-900 rounded-2xl border border-white/20" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-white">{previewAsset.name}</h3>
              <button
                onClick={() => setPreviewAsset(null)}
                className="text-white hover:text-red-400 text-3xl"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              {previewAsset.type === 'image' ? (
                <img 
                  src={previewAsset.url || `https://drive.google.com/uc?export=view&id=${previewAsset.id}`}
                  alt={previewAsset.name}
                  className="w-full h-auto rounded-lg"
                />
              ) : previewAsset.type === 'video' ? (
                <video 
                  controls 
                  className="w-full h-auto rounded-lg"
                  src={`https://drive.google.com/uc?export=view&id=${previewAsset.id}`}
                >
                  Your browser doesn't support video playback.
                </video>
              ) : (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg mb-4">Preview not available for this file type</p>
                  <button
                    onClick={() => window.open(`https://drive.google.com/file/d/${previewAsset.id}/view`, '_blank')}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
                  >
                    Open in Google Drive
                  </button>
                </div>
              )}
              <div className="mt-6 flex gap-4 justify-center">
                <button
                  onClick={() => handleDownload(previewAsset)}
                  className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg"
                >
                  ⬇️ Download
                </button>
                <button
                  onClick={() => window.open(`https://drive.google.com/file/d/${previewAsset.id}/view`, '_blank')}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
                >
                  👁️ Open in Drive
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {previewContent && (
        <div 
          className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8"
          onClick={() => setPreviewContent(null)}
        >
          <div className="max-w-4xl w-full max-h-full overflow-auto bg-slate-900 rounded-2xl border border-white/20" onClick={(e) => e.stopPropagation()}>
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-white">{previewContent.title}</h3>
                <span className={`text-xs px-2 py-1 rounded font-medium ${getStatusColor(previewContent.status)} mt-2 inline-block`}>
                  {previewContent.status}
                </span>
              </div>
              <button
                onClick={() => setPreviewContent(null)}
                className="text-white hover:text-red-400 text-3xl"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <div className="prose prose-invert max-w-none">
                <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                  {previewContent.content}
                </div>
              </div>
              <div className="mt-6 flex gap-4 justify-center pt-6 border-t border-white/10">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(previewContent.content);
                    alert('Copied to clipboard!');
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
                >
                  📋 Copy Content
                </button>
                <button
                  onClick={() => deleteGeneratedContent(previewContent.id)}
                  className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-lg"
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
