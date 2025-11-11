'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

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
  media_url?: string;
};

export default function MediaLibrary() {
  const [activeTab, setActiveTab] = useState<'drive' | 'unsplash' | 'generated' | 'ai-images' | 'ai-videos'>('drive');
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
  const [contentTypeFilter, setContentTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [contentSearchQuery, setContentSearchQuery] = useState('');
  const [dateFilter, setDateFilter] = useState<string>('all');

  // AI Generation state
  const [aiImagePrompt, setAiImagePrompt] = useState('');
  const [aiVideoPrompt, setAiVideoPrompt] = useState('');
  const [aiAspectRatio, setAiAspectRatio] = useState<'1:1' | '16:9' | '9:16' | '4:3' | '3:4'>('1:1');
  const [aiVideoResolution, setAiVideoResolution] = useState<'720p' | '1080p'>('720p');
  const [generatingAiImage, setGeneratingAiImage] = useState(false);
  const [generatingAiVideo, setGeneratingAiVideo] = useState(false);
  const [aiGeneratedImages, setAiGeneratedImages] = useState<any[]>([]);
  const [aiGeneratedVideos, setAiGeneratedVideos] = useState<any[]>([]);

  // Track active polling to prevent duplicates
  const activePollers = useRef<Set<string>>(new Set());

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
      const data = await api.get('/media/status');
      setStatus(data);
    } catch (err) {
      console.error('Failed to load status');
    }
  };

  const loadFolders = async () => {
    try {
      const data = await api.get('/media/folders');
      if (data.folders) {
        setFolders(data.folders);
      }
    } catch (err) {
      console.error('Failed to load folders');
    }
  };

  const loadGeneratedContent = async () => {
    try {
      const data = await api.get('/library/content');
      setGeneratedContent(data.items || []);

      // Resume polling for any videos still generating
      const generatingVideos = (data.items || []).filter(
        (item: GeneratedContent) =>
          item.status === 'generating' &&
          item.content_type === 'video' &&
          item.media_url // media_url contains job_id while generating
      );

      generatingVideos.forEach((video: GeneratedContent) => {
        // Only start polling if not already polling this video
        if (!activePollers.current.has(video.media_url!)) {
          console.log('🔄 Resuming polling for video:', video.id);
          pollVideoStatus(video.media_url!, video.id);
        } else {
          console.log('⏭️ Already polling video:', video.id);
        }
      });
    } catch (err) {
      console.error('Failed to load generated content');
    }
  };

  const deleteGeneratedContent = async (id: string) => {
    try {
      await api.delete(`/library/content/${id}`);
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

      const data = await api.get(`/media/library?${params}`);
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
      const res = await api.get(`/media/unsplash?query=${encodeURIComponent(searchQuery)}&per_page=20`);
      setUnsplashImages(res.images || []);
    } catch (err) {
      console.error("Failed to search Unsplash:", err);
    } finally {
      setLoading(false);
    }
  };

  const generateAiImage = async () => {
    if (!aiImagePrompt.trim()) {
      alert('Please enter a prompt for image generation');
      return;
    }
    setGeneratingAiImage(true);
    try {
      const response = await api.post('/ai/generate-image', {
        prompt: aiImagePrompt,
        aspect_ratio: aiAspectRatio,
        num_images: 1
      });

      if (response.success && response.image_data) {
        const newImage = {
          url: response.image_data,
          prompt: aiImagePrompt,
          aspect_ratio: aiAspectRatio,
          source: 'ai-generated',
          timestamp: new Date().toISOString()
        };
        setAiGeneratedImages([newImage, ...aiGeneratedImages]);

        // Save to content library database
        try {
          await api.post('/library/content', {
            title: `AI Image: ${aiImagePrompt.substring(0, 50)}${aiImagePrompt.length > 50 ? '...' : ''}`,
            content_type: 'image',
            content: aiImagePrompt,
            status: 'draft',
            platform: 'AI Generated',
            tags: ['ai-generated', 'imagen-3'],
            media_url: response.image_data
          });
          console.log('✨ AI Image saved to content library');
        } catch (saveErr) {
          console.error('Failed to save to library:', saveErr);
          // Don't block the UI - image is still in local state
        }

        console.log('✨ AI Image generated successfully');
      } else {
        alert(`Failed to generate image: ${response.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('AI image generation error:', err);
      alert('Failed to generate image. Please try again.');
    } finally {
      setGeneratingAiImage(false);
    }
  };

  const generateAiVideo = async () => {
    if (!aiVideoPrompt.trim()) {
      alert('Please enter a prompt for video generation');
      return;
    }
    setGeneratingAiVideo(true);
    try {
      const response = await api.post('/ai/generate-video', {
        prompt: aiVideoPrompt,
        duration_seconds: 8,
        resolution: aiVideoResolution
      });

      if (response.success && response.job_id) {
        // Save to database immediately with job_id
        const saveResponse = await api.post('/library/content', {
          title: `AI Video: ${aiVideoPrompt.substring(0, 50)}${aiVideoPrompt.length > 50 ? '...' : ''}`,
          content_type: 'video',
          content: aiVideoPrompt,
          status: 'generating',
          platform: 'AI Generated',
          tags: ['ai-generated', 'runway-veo', 'generating'],
          media_url: response.job_id  // Store job_id temporarily
        });

        if (!saveResponse.success || !saveResponse.item?.id) {
          console.error('❌ Failed to save video to database:', saveResponse.error);
          alert(`Video generation started but failed to save to database: ${saveResponse.error || 'Unknown error'}\n\nThe video will generate but you\'ll need to recover it manually.`);
        } else {
          console.log('✨ Video job saved to database:', saveResponse.item.id);
        }

        // Add to local state
        const newVideo = {
          url: null,
          job_id: response.job_id,
          prompt: aiVideoPrompt,
          resolution: aiVideoResolution,
          source: 'ai-generated',
          status: 'generating',
          timestamp: new Date().toISOString()
        };
        setAiGeneratedVideos([newVideo, ...aiGeneratedVideos]);

        // Reload content library to show the generating video
        loadGeneratedContent();

        // Start polling for completion (pass contentId even if undefined - will be handled in polling)
        pollVideoStatus(response.job_id, saveResponse.item?.id);

        alert('Video generation started! This may take 1-3 minutes. You can navigate away - it will save automatically.');
      } else {
        alert(`Failed to generate video: ${response.error || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('AI video generation error:', err);
      alert('Failed to generate video. Please try again.');
    } finally {
      setGeneratingAiVideo(false);
    }
  };

  const pollVideoStatus = async (jobId: string, contentId?: string) => {
    // Mark this video as being polled (prevent duplicate pollers)
    activePollers.current.add(jobId);
    console.log('🎬 Started polling:', jobId);

    const maxAttempts = 60; // 5 minutes max (every 5 seconds)
    let attempts = 0;

    const checkStatus = async () => {
      try {
        const status = await api.get(`/ai/video-status/${jobId}`);

        if (status.success && status.status === 'complete' && status.video_url) {
          console.log('✅ Video generation complete:', status.video_url);

          // Update or create database entry with final video URL
          if (contentId) {
            // Update existing entry
            const contentItem = generatedContent.find(c => c.id === contentId);
            await api.patch(`/library/content/${contentId}`, {
              title: contentItem?.title || 'AI Video',
              content_type: 'video',
              content: contentItem?.content || '',
              status: 'draft',
              platform: 'AI Generated',
              tags: ['ai-generated', 'runway-veo'],
              media_url: status.video_url
            });
            console.log('✅ Video updated in database:', contentId);
          } else {
            // Fallback: Create new entry if initial save failed
            console.warn('⚠️ No contentId - creating new database entry');
            const videoState = aiGeneratedVideos.find(v => v.job_id === jobId);
            await api.post('/library/content', {
              title: `AI Video: ${videoState?.prompt.substring(0, 50) || 'Recovered'}`,
              content_type: 'video',
              content: videoState?.prompt || 'AI generated video',
              status: 'draft',
              platform: 'AI Generated',
              tags: ['ai-generated', 'runway-veo', 'recovered'],
              media_url: status.video_url
            });
            console.log('✅ Video created in database (fallback)');
          }

          // Add to AI Videos tab (component state)
          const videoState = aiGeneratedVideos.find(v => v.job_id === jobId);
          const completedVideo = {
            url: status.video_url,
            job_id: jobId,
            prompt: videoState?.prompt || '',
            resolution: videoState?.resolution || '720p',
            source: 'ai-generated',
            status: 'complete',
            timestamp: new Date().toISOString()
          };
          setAiGeneratedVideos(prev => {
            // Remove the generating placeholder if exists
            const filtered = prev.filter(v => v.job_id !== jobId);
            return [completedVideo, ...filtered];
          });

          // Reload content to show completed video in Generated Content tab
          loadGeneratedContent();

          // Stop polling - remove from active pollers
          activePollers.current.delete(jobId);
          console.log('🛑 Stopped polling (complete):', jobId);
          return;
        } else if (status.success && status.status === 'generating') {
          // Still generating, poll again
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 5000); // Check every 5 seconds
          } else {
            console.error('❌ Video generation timeout');
            activePollers.current.delete(jobId);
            console.log('🛑 Stopped polling (timeout):', jobId);
          }
        } else if (status.error) {
          console.error('❌ Video generation failed:', status.error);
          activePollers.current.delete(jobId);
          console.log('🛑 Stopped polling (error):', jobId);
        }
      } catch (err) {
        console.error('Error checking video status:', err);
        // Retry on error
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 5000);
        } else {
          activePollers.current.delete(jobId);
          console.log('🛑 Stopped polling (max retries):', jobId);
        }
      }
    };

    // Start polling after 10 seconds (give it time to start processing)
    setTimeout(checkStatus, 10000);
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
          <button
            onClick={() => setActiveTab('ai-images')}
            className={`flex-1 py-4 px-6 rounded-lg font-bold transition-all ${
              activeTab === 'ai-images'
                ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            🍌 AI Images
          </button>
          <button
            onClick={() => setActiveTab('ai-videos')}
            className={`flex-1 py-4 px-6 rounded-lg font-bold transition-all ${
              activeTab === 'ai-videos'
                ? 'bg-gradient-to-r from-red-600 to-pink-600 text-white'
                : 'bg-white/5 text-gray-400 hover:bg-white/10'
            }`}
          >
            🎬 AI Videos
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
            ) : activeTab === 'ai-images' ? (
              <>
                <h2 className="text-xl font-bold text-white mb-4">🍌 AI Image Generation</h2>
                <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border border-yellow-500/30 rounded-lg p-3 mb-4">
                  <p className="text-xs text-gray-300">Google Imagen 3 • $0.03/image</p>
                </div>
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Aspect Ratio</label>
                  <select
                    value={aiAspectRatio}
                    onChange={(e) => setAiAspectRatio(e.target.value as any)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="1:1">1:1 Square</option>
                    <option value="16:9">16:9 Landscape</option>
                    <option value="9:16">9:16 Portrait</option>
                    <option value="4:3">4:3 Classic</option>
                    <option value="3:4">3:4 Portrait</option>
                  </select>
                </div>
                <textarea
                  value={aiImagePrompt}
                  onChange={(e) => setAiImagePrompt(e.target.value)}
                  placeholder="Describe the image you want to generate..."
                  rows={4}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 mb-4"
                />
                <button
                  onClick={generateAiImage}
                  disabled={generatingAiImage || !aiImagePrompt.trim()}
                  className="w-full bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-600 hover:to-orange-600 text-white font-bold py-3 px-4 rounded-lg transition-all disabled:opacity-50"
                >
                  {generatingAiImage ? '🍌 Generating...' : '🍌 Generate Image'}
                </button>
              </>
            ) : activeTab === 'ai-videos' ? (
              <>
                <h2 className="text-xl font-bold text-white mb-4">🎬 AI Video Generation</h2>
                <div className="bg-gradient-to-r from-red-900/30 to-pink-900/30 border border-red-500/30 rounded-lg p-3 mb-4">
                  <p className="text-xs text-gray-300">Runway ML Gen-3 • $0.10 per 5s video</p>
                </div>
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Resolution</label>
                  <select
                    value={aiVideoResolution}
                    onChange={(e) => setAiVideoResolution(e.target.value as any)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="720p">720p HD</option>
                    <option value="1080p">1080p Full HD</option>
                  </select>
                </div>
                <textarea
                  value={aiVideoPrompt}
                  onChange={(e) => setAiVideoPrompt(e.target.value)}
                  placeholder="Describe the video you want to generate..."
                  rows={4}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500 mb-4"
                />
                <button
                  onClick={generateAiVideo}
                  disabled={generatingAiVideo || !aiVideoPrompt.trim()}
                  className="w-full bg-gradient-to-r from-red-500 to-pink-500 hover:from-red-600 hover:to-pink-600 text-white font-bold py-3 px-4 rounded-lg transition-all disabled:opacity-50"
                >
                  {generatingAiVideo ? '🎬 Generating...' : '🎬 Generate Video'}
                </button>
                <p className="text-xs text-gray-400 mt-3">⏱️ Video generation takes 2-5 minutes</p>
              </>
            ) : (
              <>
                <h2 className="text-xl font-bold text-white mb-4">Filters</h2>
                <p className="text-gray-400 text-sm mb-4">All your generated blogs, carousels, and captions in one place.</p>
                
                {/* Search */}
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Search</label>
                  <input
                    type="text"
                    value={contentSearchQuery}
                    onChange={(e) => setContentSearchQuery(e.target.value)}
                    placeholder="Search by title..."
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  />
                </div>

                {/* Content Type */}
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Content Type</label>
                  <select
                    value={contentTypeFilter}
                    onChange={(e) => setContentTypeFilter(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="all">All Types</option>
                    <option value="blog">📝 Blogs</option>
                    <option value="carousel">🎨 Carousels</option>
                    <option value="caption">💬 Captions</option>
                    <option value="image">🖼️ Images</option>
                    <option value="video">🎬 Videos</option>
                  </select>
                </div>

                {/* Status */}
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="all">All Status</option>
                    <option value="draft">📝 Draft</option>
                    <option value="published">✅ Published</option>
                    <option value="scheduled">📅 Scheduled</option>
                  </select>
                </div>

                {/* Date Range */}
                <div className="mb-4">
                  <label className="block text-white font-bold mb-2 text-sm">Date Range</label>
                  <select
                    value={dateFilter}
                    onChange={(e) => setDateFilter(e.target.value)}
                    className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
                  >
                    <option value="all">All Time</option>
                    <option value="today">Today</option>
                    <option value="week">This Week</option>
                    <option value="month">This Month</option>
                    <option value="year">This Year</option>
                  </select>
                </div>

                {/* Clear Filters */}
                <button
                  onClick={() => {
                    setContentTypeFilter('all');
                    setStatusFilter('all');
                    setContentSearchQuery('');
                    setDateFilter('all');
                  }}
                  className="w-full bg-white/10 hover:bg-white/20 text-white font-bold py-2 px-4 rounded-lg transition-all text-sm"
                >
                  Clear All Filters
                </button>
              </>
            )}
          </div>

          <div className="lg:col-span-3 bg-white/5 backdrop-blur-lg rounded-2xl p-6 border border-white/10">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">
                {activeTab === 'drive' ? '🔗 Your Drive Assets' : activeTab === 'unsplash' ? '✨ Unsplash Images' : activeTab === 'ai-images' ? '🍌 AI Generated Images' : activeTab === 'ai-videos' ? '🎬 AI Generated Videos' : '💾 Generated Content'}
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

            {activeTab === 'ai-images' ? (
              aiGeneratedImages.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg mb-4">No AI images generated yet.</p>
                  <p className="text-gray-500 text-sm">Use the sidebar to generate your first AI image with Google Imagen 3!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {aiGeneratedImages.map((image: any, idx: number) => (
                    <div
                      key={idx}
                      className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-yellow-400 transition-all"
                    >
                      <img
                        src={image.url}
                        alt={image.prompt}
                        className="w-full h-48 object-cover"
                      />
                      <div className="p-4 bg-slate-800/50">
                        <p className="text-white text-sm mb-2 line-clamp-2">{image.prompt}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs px-2 py-1 rounded font-medium bg-gradient-to-r from-yellow-600 to-orange-600 text-white">
                            🍌 {image.aspect_ratio}
                          </span>
                          <span className="text-gray-400 text-xs">
                            {new Date(image.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="px-4 pb-4 bg-slate-800/50 flex gap-2">
                        <button
                          onClick={() => {
                            const link = document.createElement('a');
                            link.href = image.url;
                            link.download = `ai-image-${Date.now()}.png`;
                            link.click();
                          }}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                        >
                          ⬇️ Download
                        </button>
                        <button
                          onClick={() => setPreviewAsset({ ...image, name: image.prompt, type: 'image', id: idx.toString() })}
                          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                        >
                          👁️ View
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : activeTab === 'ai-videos' ? (
              aiGeneratedVideos.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg mb-4">No AI videos generated yet.</p>
                  <p className="text-gray-500 text-sm">Use the sidebar to generate your first AI video with Runway ML Gen-3!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {aiGeneratedVideos.map((video: any, idx: number) => (
                    <div
                      key={idx}
                      className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-pink-400 transition-all"
                    >
                      {video.status === 'complete' && video.url ? (
                        <video
                          src={video.url}
                          className="w-full h-48 object-cover"
                          controls
                        />
                      ) : (
                        <div className="w-full h-48 bg-gradient-to-br from-red-700 to-pink-700 flex items-center justify-center">
                          <span className="text-white text-sm">
                            {video.status === 'generating' ? '⏳ Generating...' : '🎬 Video'}
                          </span>
                        </div>
                      )}
                      <div className="p-4 bg-slate-800/50">
                        <p className="text-white text-sm mb-2 line-clamp-2">{video.prompt}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-xs px-2 py-1 rounded font-medium bg-gradient-to-r from-red-600 to-pink-600 text-white">
                            🎬 {video.resolution}
                          </span>
                          <span className="text-gray-400 text-xs">
                            {new Date(video.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      {video.status === 'complete' && video.url && (
                        <div className="px-4 pb-4 bg-slate-800/50 flex gap-2">
                          <button
                            onClick={() => {
                              const link = document.createElement('a');
                              link.href = video.url;
                              link.download = `ai-video-${Date.now()}.mp4`;
                              link.click();
                            }}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                          >
                            ⬇️ Download
                          </button>
                          <button
                            onClick={() => window.open(video.url, '_blank')}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold py-2 px-3 rounded transition-all"
                          >
                            👁️ View
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )
            ) : activeTab === 'generated' ? (
              (() => {
                // Apply filters
                let filtered = generatedContent;
                
                // Filter by content type
                if (contentTypeFilter !== 'all') {
                  filtered = filtered.filter(item => item.content_type === contentTypeFilter);
                }
                
                // Filter by status
                if (statusFilter !== 'all') {
                  filtered = filtered.filter(item => item.status === statusFilter);
                }
                
                // Filter by search query
                if (contentSearchQuery.trim()) {
                  filtered = filtered.filter(item => 
                    item.title.toLowerCase().includes(contentSearchQuery.toLowerCase())
                  );
                }
                
                // Filter by date
                if (dateFilter !== 'all') {
                  const now = new Date();
                  filtered = filtered.filter(item => {
                    const itemDate = new Date(item.created_at);
                    switch(dateFilter) {
                      case 'today':
                        return itemDate.toDateString() === now.toDateString();
                      case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                        return itemDate >= weekAgo;
                      case 'month':
                        return itemDate.getMonth() === now.getMonth() && itemDate.getFullYear() === now.getFullYear();
                      case 'year':
                        return itemDate.getFullYear() === now.getFullYear();
                      default:
                        return true;
                    }
                  });
                }
                
                return filtered;
              })().length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-400 text-lg">No generated content yet. Create some blogs or carousels to get started!</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(() => {
                    // Apply same filters
                    let filtered = generatedContent;
                    if (contentTypeFilter !== 'all') filtered = filtered.filter(item => item.content_type === contentTypeFilter);
                    if (statusFilter !== 'all') filtered = filtered.filter(item => item.status === statusFilter);
                    if (contentSearchQuery.trim()) filtered = filtered.filter(item => item.title.toLowerCase().includes(contentSearchQuery.toLowerCase()));
                    if (dateFilter !== 'all') {
                      const now = new Date();
                      filtered = filtered.filter(item => {
                        const itemDate = new Date(item.created_at);
                        switch(dateFilter) {
                          case 'today': return itemDate.toDateString() === now.toDateString();
                          case 'week': return itemDate >= new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                          case 'month': return itemDate.getMonth() === now.getMonth() && itemDate.getFullYear() === now.getFullYear();
                          case 'year': return itemDate.getFullYear() === now.getFullYear();
                          default: return true;
                        }
                      });
                    }
                    return filtered;
                  })().map((item) => (
                    <div
                      key={item.id}
                      className="group bg-white/5 border border-white/10 rounded-xl overflow-hidden hover:border-yellow-400 transition-all cursor-pointer"
                      onClick={() => setPreviewContent(item)}
                    >
                      {/* Show media preview if available, otherwise show icon */}
                      {item.media_url && item.content_type === 'image' ? (
                        <div className="w-full h-40 overflow-hidden">
                          <img
                            src={item.media_url}
                            alt={item.title}
                            className="w-full h-full object-cover"
                          />
                        </div>
                      ) : item.media_url && item.content_type === 'video' ? (
                        <div className="w-full h-40 overflow-hidden bg-black">
                          <video
                            src={item.media_url}
                            className="w-full h-full object-cover"
                            muted
                            loop
                            onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                            onMouseLeave={(e) => (e.target as HTMLVideoElement).pause()}
                          />
                        </div>
                      ) : (
                        <div className="w-full h-40 bg-gradient-to-br from-purple-700 to-purple-900 flex items-center justify-center">
                          <span className="text-6xl">{getFileIcon(item.content_type)}</span>
                        </div>
                      )}

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
                        {/* Show tags if available */}
                        {item.tags && item.tags.length > 0 && (
                          <div className="flex gap-1 mt-2 flex-wrap">
                            {item.tags.slice(0, 3).map((tag: string, idx: number) => (
                              <span key={idx} className="text-xs px-2 py-0.5 rounded bg-white/10 text-gray-300">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
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
              {previewContent.content_type === "image" && previewContent.media_url ? (
                <div className="space-y-4">
                  <img
                    src={previewContent.media_url}
                    alt={previewContent.title}
                    className="w-full rounded-lg"
                  />
                  <div className="text-gray-300 text-sm bg-white/5 rounded-lg p-4">
                    <strong className="text-white">Prompt:</strong> {previewContent.content}
                  </div>
                  {previewContent.tags && previewContent.tags.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {previewContent.tags.map((tag: string, idx: number) => (
                        <span key={idx} className="text-xs px-3 py-1 rounded-full bg-gradient-to-r from-yellow-600 to-orange-600 text-white">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : previewContent.content_type === "video" && previewContent.media_url ? (
                <div className="space-y-4">
                  <video
                    src={previewContent.media_url}
                    controls
                    className="w-full rounded-lg"
                  />
                  <div className="text-gray-300 text-sm bg-white/5 rounded-lg p-4">
                    <strong className="text-white">Prompt:</strong> {previewContent.content}
                  </div>
                  {previewContent.tags && previewContent.tags.length > 0 && (
                    <div className="flex gap-2 flex-wrap">
                      {previewContent.tags.map((tag: string, idx: number) => (
                        <span key={idx} className="text-xs px-3 py-1 rounded-full bg-gradient-to-r from-red-600 to-pink-600 text-white">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ) : previewContent.content_type === "carousel" ? (
                <div className="space-y-4">
                  {(() => {
                    try {
                      const slides = JSON.parse(previewContent.content);
                      return slides.map((slide: any, idx: number) => (
                        <div key={idx} className="bg-white/5 rounded-lg p-4 border border-white/10">
                          <div className="flex gap-4">
                            <img src={slide.branded_image || slide.image_url} alt={slide.alt_hint} className="w-32 h-32 object-cover rounded-lg" />
                            <div className="flex-1">
                              <h4 className="text-white font-bold mb-2">Slide {idx + 1}: {slide.title}</h4>
                              <p className="text-gray-300 text-sm">{slide.body}</p>
                            </div>
                          </div>
                        </div>
                      ));
                    } catch (e) {
                      return <div className="text-red-400">Error parsing carousel data</div>;
                    }
                  })()}
                </div>
              ) : (
                <div className="prose prose-invert max-w-none">
                  <div className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                    {previewContent.content}
                  </div>
                </div>
              )}

              <div className="mt-6 flex gap-4 justify-center pt-6 border-t border-white/10">
                {previewContent.media_url && (
                  <button
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = previewContent.media_url!;
                      link.download = `${previewContent.title.replace(/[^a-z0-9]/gi, '-')}.${previewContent.content_type === 'video' ? 'mp4' : 'png'}`;
                      link.click();
                    }}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg"
                  >
                    ⬇️ Download
                  </button>
                )}
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(previewContent.content);
                    alert('Copied to clipboard!');
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg"
                >
                  📋 Copy {previewContent.content_type === 'image' || previewContent.content_type === 'video' ? 'Prompt' : 'Content'}
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
