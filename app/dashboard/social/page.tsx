"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';

type PostType = "text" | "video" | "carousel";
type Platform = "instagram" | "linkedin" | "facebook" | "x" | "tiktok" | "youtube" | "reddit" | "tumblr";
type Tab = "create" | "engage" | "schedule";
type EngageSubTab = "inbox" | "discovery" | "settings";

type Comment = {
  id: string;
  platform: Platform;
  postTitle: string;
  author: string;
  content: string;
  timestamp: string;
  sentiment: "positive" | "negative" | "neutral" | "question";
};

type DiscoveryPost = {
  id: string;
  platform: Platform;
  author: string;
  content: string;
  hashtags: string[];
  engagement: number;
  timestamp: string;
};

export default function SocialManagerPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("create");
  const [engageSubTab, setEngageSubTab] = useState<EngageSubTab>("inbox");
  const [postType, setPostType] = useState<PostType>("text");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>(["instagram"]);
  const [caption, setCaption] = useState("");
  
  // Publishing state
  const [publishing, setPublishing] = useState(false);
  const [publishResults, setPublishResults] = useState<any[]>([]);
  const [publishMessage, setPublishMessage] = useState("");
  const [captionPrompt, setCaptionPrompt] = useState("");
  const [generatingCaption, setGeneratingCaption] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  
  // Engagement state
  const [selectedComment, setSelectedComment] = useState<Comment | null>(null);
  const [aiReplies, setAiReplies] = useState<string[]>([]);
  const [generatingReplies, setGeneratingReplies] = useState(false);
  const [manualReply, setManualReply] = useState("");
  const [autoReplyEnabled, setAutoReplyEnabled] = useState(false);
  
  // Discovery state
  const [searchKeywords, setSearchKeywords] = useState("");
  const [discoveryPosts, setDiscoveryPosts] = useState<DiscoveryPost[]>([]);
  const [searchingPosts, setSearchingPosts] = useState(false);

  // Media library state
  const [showMediaLibrary, setShowMediaLibrary] = useState(false);
  const [selectedMedia, setSelectedMedia] = useState<any[]>([]);
  const [mediaLibraryTab, setMediaLibraryTab] = useState<'generated' | 'drive' | 'unsplash'>('generated');
  const [driveAssets, setDriveAssets] = useState<any[]>([]);
  const [driveFolders, setDriveFolders] = useState<any[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [unsplashImages, setUnsplashImages] = useState<any[]>([]);
  const [unsplashQuery, setUnsplashQuery] = useState('');
  const [mediaLoading, setMediaLoading] = useState(false);
  const [libraryContent, setLibraryContent] = useState<any[]>([]);


  const platforms = [
    { id: "instagram" as Platform, name: "Instagram", icon: "📷", color: "from-pink-500 to-purple-500", discovery: true, autoReply: true },
    { id: "linkedin" as Platform, name: "LinkedIn", icon: "💼", color: "from-blue-600 to-blue-700", discovery: true, autoReply: true },
    { id: "facebook" as Platform, name: "Facebook", icon: "👍", color: "from-blue-500 to-blue-600", discovery: true, autoReply: true },
    { id: "x" as Platform, name: "X", icon: "❌", color: "from-slate-800 to-slate-900", discovery: true, autoReply: true },
    { id: "tiktok" as Platform, name: "TikTok", icon: "🎵", color: "from-black to-pink-500", discovery: false, autoReply: true },
    { id: "youtube" as Platform, name: "YouTube", icon: "▶️", color: "from-red-600 to-red-700", discovery: true, autoReply: true },
    { id: "reddit" as Platform, name: "Reddit", icon: "🤖", color: "from-orange-500 to-red-500", discovery: true, autoReply: false },
    { id: "tumblr" as Platform, name: "Tumblr", icon: "🔷", color: "from-indigo-500 to-blue-600", discovery: true, autoReply: true },
    { id: "wordpress" as Platform, name: "WordPress", icon: "📝", color: "from-gray-700 to-gray-900", discovery: false, autoReply: false },
  ];

  const mockComments: Comment[] = [
    { id: "1", platform: "instagram", postTitle: "UK Videographer Guide", author: "@sarah_designs", content: "This is so helpful! Do you have recommendations for London specifically?", timestamp: "2 hours ago", sentiment: "question" },
    { id: "2", platform: "linkedin", postTitle: "Corporate Video Tips", author: "John Marketing", content: "Great insights! We just hired a videographer and wish we'd seen this first.", timestamp: "5 hours ago", sentiment: "positive" },
    { id: "3", platform: "x", postTitle: "Video Production Costs", author: "@tech_startup", content: "These prices seem way too high for small businesses", timestamp: "1 day ago", sentiment: "negative" },
    { id: "4", platform: "tiktok", postTitle: "Behind the Scenes", author: "CreativeStudio22", content: "Love this content! Following for more", timestamp: "3 hours ago", sentiment: "positive" },
  ];

  const mockDiscoveryPosts: DiscoveryPost[] = [
    { id: "1", platform: "instagram", author: "@startup_tales", content: "Looking for a corporate videographer in Manchester. Any recommendations?", hashtags: ["videography", "manchester", "business"], engagement: 24, timestamp: "3 hours ago" },
    { id: "2", platform: "x", author: "@ukbusiness", content: "Just wrapped our first brand video. The difference between cheap and quality videography is night and day!", hashtags: ["branding", "videoproduction"], engagement: 156, timestamp: "5 hours ago" },
    { id: "3", platform: "linkedin", author: "Marketing Director", content: "We're hiring a videographer for our product launch. What should we look for in their portfolio?", hashtags: ["hiring", "videography", "productlaunch"], engagement: 89, timestamp: "1 day ago" },
  ];

  const togglePlatform = (platform: Platform) => {
    if (selectedPlatforms.includes(platform)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform]);
    }
  };


  const loadMediaLibrary = async () => {
    try {
      const data = await api.get('/library/content');
      setLibraryContent(data.items || []);
    } catch (err) {
      console.error('Failed to load media library');
    }
  };

  const loadDriveFolders = async () => {
    try {
      const data = await api.get('/media/folders');
      setDriveFolders(data.folders || []);
    } catch (err) {
      console.error('Failed to load Drive folders');
    }
  };

  const loadDriveAssets = async (folderId?: string) => {
    setMediaLoading(true);
    try {
      const params = new URLSearchParams();
      if (folderId) params.append('folder_id', folderId);
      const data = await api.get(`/media/library?${params}`);
      setDriveAssets(data.assets || []);
    } catch (err) {
      console.error('Failed to load Drive assets');
    } finally {
      setMediaLoading(false);
    }
  };

  const searchUnsplash = async () => {
    if (!unsplashQuery.trim()) return;
    setMediaLoading(true);
    try {
      const res = await api.get(`/media/unsplash?query=${encodeURIComponent(unsplashQuery)}&per_page=20`);
      const data = await res.json();
      setUnsplashImages(data.images || []);
    } catch (err) {
      console.error('Failed to search Unsplash');
    } finally {
      setMediaLoading(false);
    }
  };

  const handleMediaSelect = async (item: any) => {
    console.log('🎯 Media selected:', item);
    
    // Handle carousel content from library
    if (item.content_type === 'carousel') {
      try {
        const slides = JSON.parse(item.content);
        const images = slides.map((s: any) => s.branded_image || s.image_url).filter(Boolean);
        console.log('📸 Extracted images:', images);
        setSelectedMedia(images);
      } catch (e) {
        console.error('Failed to parse carousel', e);
      }
    } 
    // Handle blog content
    else if (item.content_type === 'blog') {
      console.log('📝 Blog selected - adding to caption');
      const excerpt = item.content;
      setCaption(excerpt);
      setSelectedMedia([]);
    } 
    // Handle Google Drive files - fetch actual file URL
    else if (item.source === 'drive') {
      console.log('📁 Drive file selected, fetching URL...');
      try {
        const data = await api.get(`/social/drive-file/${item.id}`);
        
        if (data.success) {
          // Store file with metadata for proper display
          const mediaItem = {
            url: data.thumbnail_link || data.web_content_link || data.web_view_link,
            type: data.mime_type || '',
            name: data.name || 'Unknown File',
            source: 'drive',
            folder: item.folderName || 'Drive'
          };
          console.log('✅ Drive file selected:', mediaItem);
          setSelectedMedia([...selectedMedia, mediaItem]);
        } else {
          console.error('Failed to get Drive file URL');
          alert('Could not load Drive file. It may be a shortcut or restricted file.');
        }
      } catch (err) {
        console.error('Error fetching Drive file:', err);
        alert('Failed to load Drive file');
      }
    }
    // Handle Unsplash images
    else if (item.source === 'unsplash' && item.url) {
      console.log('✨ Unsplash image selected');
      setSelectedMedia([...selectedMedia, { url: item.url, type: 'image', name: item.name || 'Unsplash Image', source: 'unsplash' }]);
    }
    // Fallback for direct URLs
    else if (item.thumbnail || item.url) {
      console.log('📷 Generic media selected');
      const url = item.thumbnail || item.url;
      setSelectedMedia([...selectedMedia, typeof url === 'string' ? url : url]);
    } 
    else {
      console.log('📄 Unknown media type');
    }
    
    setShowMediaLibrary(false);
  };


  const generateCaption = async () => {
    if (!captionPrompt.trim()) {
      alert('Please enter a prompt describing what you want the caption to be about');
      return;
    }
    
    setGeneratingCaption(true);
    try {
      const context = {
        prompt: captionPrompt,
        platforms: selectedPlatforms,
        postType: postType,
        hasMedia: selectedMedia.length > 0,
        mediaCount: selectedMedia.length
      };
      
      const data = await api.post(`/social-caption/generate-caption`, context);
      setCaption(data.caption || 'Generated caption');
      setCaptionPrompt(''); // Clear prompt after generation
    } catch (err) {
      console.error('Failed to generate caption:', err);
      alert('Failed to generate caption');
    } finally {
      setGeneratingCaption(false);
    }
  };


  const publishToSocial = async () => {
    if (!caption.trim()) {
      alert('Please write or generate a caption first');
      return;
    }
    
    if (selectedPlatforms.length === 0) {
      alert('Please select at least one platform');
      return;
    }
    
    setPublishing(true);
    setPublishResults([]);
    setPublishMessage('');
    
    const results = [];
    
    for (const platform of selectedPlatforms) {
      try {
        const response = await api.post(`/publisher/publish`, {
            platform: platform,
            content_type: postType,
            caption: caption,
            image_urls: selectedMedia.map(m => m.url || m.image_url || '')
        });
        
        const result = await response.json();
        results.push({
          platform: platform,
          success: result.success,
          message: result.success ? `Posted to ${platform}!` : result.error,
          url: result.post_url
        });
        
      } catch (err) {
        results.push({
          platform: platform,
          success: false,
          message: `Failed to post to ${platform}`
        });
      }
    }
    
    setPublishResults(results);
    
    const successCount = results.filter(r => r.success).length;
    const failCount = results.filter(r => !r.success).length;
    
    if (successCount > 0 && failCount === 0) {
      setPublishMessage(`✅ Successfully posted to ${successCount} platform(s)!`);
    } else if (successCount > 0 && failCount > 0) {
      setPublishMessage(`⚠️ Posted to ${successCount} platform(s), ${failCount} failed`);
    } else {
      setPublishMessage(`❌ Failed to post to all platforms`);
    }
    
    setTimeout(() => {
      setPublishMessage('');
      setPublishResults([]);
    }, 10000);
    
    setPublishing(false);
  };
  const generateAIReplies = async (comment: Comment) => {
    setSelectedComment(comment);
    setGeneratingReplies(true);
    setAiReplies([]);
    
    setTimeout(() => {
      setAiReplies([
        "Thanks for asking! We have a great list of London-based videographers. DM us and we'll send you some recommendations!",
        "Great question! London has some amazing talent. Check out our directory at orla3.com/london for vetted professionals in your area!",
        "Absolutely! We work with several excellent videographers in London. What's your budget and project type? Happy to point you in the right direction!"
      ]);
      setGeneratingReplies(false);
    }, 2000);
  };

  const searchRelevantPosts = async () => {
    setSearchingPosts(true);
    setDiscoveryPosts([]);
    
    setTimeout(() => {
      setDiscoveryPosts(mockDiscoveryPosts);
      setSearchingPosts(false);
    }, 2000);
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return "text-green-400";
      case "negative": return "text-red-400";
      case "question": return "text-blue-400";
      default: return "text-gray-400";
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return "😊";
      case "negative": return "😕";
      case "question": return "❓";
      default: return "💬";
    }
  };

  const getPlatformIcon = (platform: Platform) => {
    return platforms.find(p => p.id === platform)?.icon || "📱";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="bg-white/5 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button onClick={() => router.push("/dashboard")} className="text-purple-400 hover:text-purple-300 mb-2 flex items-center gap-2 text-sm">
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
            📱 Social Manager
          </h1>
          <p className="text-purple-300 mt-1">Create, engage, and schedule all your social content</p>
        </div>
      </div>

      <div className="bg-white/5 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2">
            <button onClick={() => setActiveTab("create")} className={`px-6 py-4 font-semibold transition ${activeTab === "create" ? "text-white border-b-2 border-green-500" : "text-gray-400 hover:text-white"}`}>
              📝 Create
            </button>
            <button onClick={() => setActiveTab("engage")} className={`px-6 py-4 font-semibold transition ${activeTab === "engage" ? "text-white border-b-2 border-purple-500" : "text-gray-400 hover:text-white"}`}>
              💬 Engage
            </button>
            <button onClick={() => setActiveTab("schedule")} className={`px-6 py-4 font-semibold transition ${activeTab === "schedule" ? "text-white border-b-2 border-blue-500" : "text-gray-400 hover:text-white"}`}>
              📅 Schedule
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === "create" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Post Type</h2>
                <div className="flex gap-3">
                  <button onClick={() => setPostType("text")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "text" ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>📝 Text Post</button>
                  <button onClick={() => setPostType("video")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "video" ? "bg-gradient-to-r from-red-500 to-pink-500 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>🎬 Video Post</button>
                  <button onClick={() => setPostType("carousel")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "carousel" ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>🎨 Carousel</button>
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Caption</h2>
                
                {/* AI Caption Generator */}
                <div className="mb-3 flex gap-2">
                  <input
                    type="text"
                    value={captionPrompt}
                    onChange={(e) => setCaptionPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && generateCaption()}
                    placeholder="Describe what you want the caption about... (e.g. 'Promote videography for weddings')"
                    className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
                  />
                  <button 
                    onClick={generateCaption} 
                    disabled={generatingCaption || !captionPrompt.trim()}
                    className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {generatingCaption ? "✨ Generating..." : "✨ Generate"}
                  </button>
                </div>
                
                <textarea value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Your AI-generated caption will appear here... Or write your own!" rows={8} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500 resize-none" />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-sm text-gray-400">{caption.length} characters</span>
                  {selectedPlatforms.includes("x") && caption.length > 280 && (<span className="text-sm text-red-400 font-semibold">⚠️ Too long for X (280 char limit)</span>)}
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Media</h2>
                <div onClick={() => { 
                  loadMediaLibrary(); 
                  loadDriveFolders();
                  setShowMediaLibrary(true); 
                }} className="border-2 border-dashed border-white/20 rounded-lg p-12 text-center hover:border-purple-500/50 transition cursor-pointer">
                  <div className="text-6xl mb-4">📁</div>
                  <p className="text-gray-400 mb-2">Click to browse Media Library</p>
                  <p className="text-sm text-gray-500">or drag and drop files here</p>
                </div>
                
                {/* Selected Media Preview */}
                {selectedMedia.length > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-3">
                      <p className="text-sm font-semibold text-white">Selected Media ({selectedMedia.length})</p>
                      <button 
                        onClick={() => setSelectedMedia([])}
                        className="text-xs text-red-400 hover:text-red-300 transition font-medium"
                      >
                        Clear All
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {selectedMedia.map((media, idx) => {
                        // Handle both object format (new) and string format (old/carousel)
                        console.log('📺 Preview media item:', media, 'Type:', typeof media);
                        const mediaUrl = typeof media === 'object' ? media.url : media;
                        const mediaType = typeof media === 'object' ? media.type : '';
                        const mediaName = typeof media === 'object' ? media.name : `Media ${idx + 1}`;
                        const mediaSource = typeof media === 'object' ? media.source : 'unknown';
                        
                        const isVideo = mediaType.includes('video') || 
                          mediaUrl.includes('video') || 
                          mediaUrl.endsWith('.mp4') || 
                          mediaUrl.endsWith('.mov') || 
                          mediaUrl.endsWith('.avi') ||
                          mediaUrl.endsWith('.webm');
                        
                        const isImage = mediaType.includes('image') ||
                          mediaUrl.includes('image') ||
                          mediaUrl.endsWith('.jpg') ||
                          mediaUrl.endsWith('.jpeg') ||
                          mediaUrl.endsWith('.png') ||
                          mediaUrl.endsWith('.gif') ||
                          mediaUrl.endsWith('.webp');
                        
                        return (
                          <div key={idx} className="relative group bg-black/20 rounded-lg overflow-hidden border border-white/10 hover:border-purple-500 transition">
                            <div className="aspect-video bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center relative">
                              {isVideo ? (
                                <div className="text-center p-4">
                                  <span className="text-4xl mb-2 block">🎥</span>
                                  <p className="text-xs text-gray-400">Video File</p>
                                </div>
                              ) : isImage ? (
                                <img 
                                  src={mediaUrl} 
                                  alt={`Selected ${idx + 1}`} 
                                  className="w-full h-full object-cover"
                                  onError={(e) => {
                                    const target = e.currentTarget;
                                    target.style.display = 'none';
                                    const parent = target.parentElement;
                                    if (parent) {
                                      parent.innerHTML = `
                                        <div class="text-center p-4">
                                          <span class="text-4xl mb-2 block">📄</span>
                                          <p class="text-xs text-gray-400">Media ${idx + 1}</p>
                                        </div>
                                      `;
                                    }
                                  }}
                                />
                              ) : (
                                <div className="text-center p-4">
                                  <span className="text-4xl mb-2 block">📄</span>
                                  <p className="text-xs text-gray-400">Document</p>
                                </div>
                              )}
                            </div>
                            <button 
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMedia(selectedMedia.filter((_, i) => i !== idx));
                              }}
                              className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-8 h-8 flex items-center justify-center opacity-0 group-hover:opacity-100 transition shadow-lg font-bold"
                            >
                              ×
                            </button>
                            <div className="p-2 bg-black/40">
                              <div className="flex items-center justify-between">
                                <p className="text-xs text-white font-medium truncate flex-1">
                                  {isVideo ? '🎬 Video' : isImage ? '🖼️ Image' : '📄 File'} {idx + 1}
                                </p>
                                <span className="text-xs text-blue-400 ml-2">📁 Drive</span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Schedule</h2>
                <div className="flex gap-4">
                  <input type="datetime-local" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-purple-500" />
                  <button onClick={publishToSocial} disabled={publishing} className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed">{publishing ? "📤 Publishing..." : "📤 Post Now"}</button>
                  
                  {publishMessage && (
                    <div className={`mt-4 p-4 rounded-lg ${
                      publishMessage.includes("✅") ? "bg-green-500/20 border border-green-500" : 
                      publishMessage.includes("⚠️") ? "bg-yellow-500/20 border border-yellow-500" : 
                      "bg-red-500/20 border border-red-500"
                    }`}>
                      <p className="text-white font-semibold">{publishMessage}</p>
                      {publishResults.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {publishResults.map((result, i) => (
                            <div key={i} className="flex items-center justify-between text-sm">
                              <span className="text-gray-300 capitalize">{result.platform}: {result.message}</span>
                              {result.url && (
                                <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:text-blue-300 underline">View Post</a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Platforms</h2>
                <div className="space-y-3">
                  {platforms.map((platform) => (
                    <button key={platform.id} onClick={() => togglePlatform(platform.id)} className={`w-full p-4 rounded-lg border-2 transition ${selectedPlatforms.includes(platform.id) ? `border-transparent bg-gradient-to-r ${platform.color} text-white` : "border-white/20 bg-white/5 text-gray-400 hover:border-white/40"}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{platform.icon}</span>
                          <span className="font-semibold">{platform.name}</span>
                        </div>
                        {selectedPlatforms.includes(platform.id) && (<span className="text-xl">✓</span>)}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Preview</h2>
                <div className="bg-white rounded-lg p-4 aspect-square flex items-center justify-center">
                  <p className="text-gray-400 text-center">Select platforms to see preview</p>
                </div>
              </div>
            </div>
          </div>
        )}
        {activeTab === "engage" && (
          <>
            <div className="flex gap-3 mb-6">
              <button onClick={() => setEngageSubTab("inbox")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "inbox" ? "bg-purple-600 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                💬 Inbox ({mockComments.length})
              </button>
              <button onClick={() => setEngageSubTab("discovery")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "discovery" ? "bg-purple-600 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                🔍 Discovery
              </button>
              <button onClick={() => setEngageSubTab("settings")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "settings" ? "bg-purple-600 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                ⚙️ Settings
              </button>
            </div>

            {engageSubTab === "inbox" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                  <h2 className="text-2xl font-bold text-white mb-6">💬 Comments Inbox</h2>
                  <div className="space-y-4">
                    {mockComments.map((comment) => (
                      <div key={comment.id} className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-purple-500/50 transition cursor-pointer" onClick={() => generateAIReplies(comment)}>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{getPlatformIcon(comment.platform)}</span>
                            <div>
                              <p className="text-white font-semibold">{comment.author}</p>
                              <p className="text-sm text-gray-400">{comment.postTitle}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-xl ${getSentimentColor(comment.sentiment)}`}>{getSentimentIcon(comment.sentiment)}</span>
                            <span className="text-xs text-gray-500">{comment.timestamp}</span>
                          </div>
                        </div>
                        <p className="text-white/90">{comment.content}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                  <h2 className="text-xl font-bold text-white mb-4">✨ AI Reply</h2>
                  {!selectedComment ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">💬</div>
                      <p className="text-gray-400">Select a comment to generate AI replies</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="bg-white/10 rounded-lg p-4">
                        <p className="text-sm text-gray-400 mb-2">Replying to:</p>
                        <p className="text-white">{selectedComment.content}</p>
                      </div>
                      {generatingReplies ? (
                        <div className="text-center py-8">
                          <div className="text-4xl mb-2">✨</div>
                          <p className="text-purple-400">Generating replies...</p>
                        </div>
                      ) : aiReplies.length > 0 && (
                        <>
                          <div className="space-y-3">
                            {aiReplies.map((reply, idx) => (
                              <div key={idx} className="bg-white/10 rounded-lg p-4 hover:bg-white/20 transition cursor-pointer" onClick={() => setManualReply(reply)}>
                                <div className="flex items-start justify-between mb-2">
                                  <span className="text-xs font-semibold text-purple-400">Option {idx + 1}</span>
                                  <button className="text-xs text-green-400 hover:text-green-300">Use this →</button>
                                </div>
                                <p className="text-white text-sm">{reply}</p>
                              </div>
                            ))}
                          </div>
                          <div className="border-t border-white/10 pt-4">
                            <label className="block text-white font-semibold mb-2">Manual Reply</label>
                            <textarea value={manualReply} onChange={(e) => setManualReply(e.target.value)} placeholder="Edit AI suggestion or write your own..." rows={4} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500 resize-none" />
                            <button className="w-full mt-3 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition">Send Reply</button>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {engageSubTab === "discovery" && (
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-2xl font-bold text-white mb-4">🔍 Find Relevant Posts</h2>
                <div className="flex gap-3 mb-6">
                  <input type="text" value={searchKeywords} onChange={(e) => setSearchKeywords(e.target.value)} placeholder="Enter keywords or hashtags" className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-purple-500" />
                  <button onClick={searchRelevantPosts} disabled={searchingPosts} className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition disabled:opacity-50">
                    {searchingPosts ? "🔍 Searching..." : "🔍 Search"}
                  </button>
                </div>
                {discoveryPosts.length > 0 && (
                  <div className="space-y-4">
                    {discoveryPosts.map((post) => (
                      <div key={post.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">{getPlatformIcon(post.platform)}</span>
                            <p className="text-white font-semibold">{post.author}</p>
                          </div>
                          <p className="text-sm text-gray-400">{post.engagement} engagements</p>
                        </div>
                        <p className="text-white/90 mb-3">{post.content}</p>
                        <div className="flex gap-2 mb-3">
                          {post.hashtags.map((tag, idx) => (
                            <span key={idx} className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded-full">#{tag}</span>
                          ))}
                        </div>
                        <button className="w-full py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition text-sm">
                          ✨ Generate Comment
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {engageSubTab === "settings" && (
              <div className="max-w-4xl mx-auto bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-2xl font-bold text-white mb-6">⚙️ Engagement Settings</h2>
                <div className="bg-white/5 rounded-lg p-6 mb-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-2">🤖 Auto-Reply</h3>
                      <p className="text-gray-400 text-sm">Let AI automatically respond to comments</p>
                    </div>
                    <button onClick={() => setAutoReplyEnabled(!autoReplyEnabled)} className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${autoReplyEnabled ? "bg-green-500" : "bg-gray-600"}`}>
                      <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${autoReplyEnabled ? "translate-x-7" : "translate-x-1"}`} />
                    </button>
                  </div>
                  {autoReplyEnabled && (
                    <div className="mt-4 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                      <p className="text-yellow-400 text-sm font-semibold">⚠️ Auto-reply is enabled</p>
                    </div>
                  )}
                </div>
                <button className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-bold transition">
                  💾 Save Settings
                </button>
              </div>
            )}
          </>
        )}

        {activeTab === "schedule" && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-12 border border-white/10 text-center">
            <div className="text-6xl mb-4">📅</div>
            <h2 className="text-2xl font-bold text-white mb-2">Schedule View</h2>
            <button onClick={() => router.push("/dashboard/calendar")} className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition">
              Open Content Calendar
            </button>
          </div>
        )}
      </div>

        {/* Media Library Modal */}
        {showMediaLibrary && (
          <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-8" onClick={() => setShowMediaLibrary(false)}>
            <div className="max-w-6xl w-full max-h-[80vh] bg-slate-900 rounded-2xl border border-white/20 flex flex-col" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="p-6 border-b border-white/10 flex items-center justify-between">
                <h3 className="text-2xl font-bold text-white">Browse Media Library</h3>
                <button onClick={() => setShowMediaLibrary(false)} className="text-white hover:text-red-400 text-3xl">×</button>
              </div>
              
              {/* Tabs */}
              <div className="px-6 pt-4 flex gap-3 border-b border-white/10">
                <button 
                  onClick={() => setMediaLibraryTab('generated')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition ${mediaLibraryTab === 'generated' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  🎨 Generated Content
                </button>
                <button 
                  onClick={() => setMediaLibraryTab('drive')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition ${mediaLibraryTab === 'drive' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  📁 Google Drive
                </button>
                <button 
                  onClick={() => setMediaLibraryTab('unsplash')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition ${mediaLibraryTab === 'unsplash' ? 'bg-purple-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  ✨ Unsplash
                </button>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-auto p-6">
                {/* Generated Content Tab */}
                {mediaLibraryTab === 'generated' && (
                  <div className="grid grid-cols-3 gap-4">
                    {libraryContent.map((item) => (
                      <div key={item.id} onClick={() => handleMediaSelect(item)} className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-purple-500">
                        <div className="aspect-square bg-gradient-to-br from-purple-900 to-slate-900 flex items-center justify-center">
                          {item.content_type === 'carousel' ? (
                            <span className="text-6xl">🎨</span>
                          ) : item.content_type === 'blog' ? (
                            <span className="text-6xl">📝</span>
                          ) : (
                            <span className="text-6xl">📄</span>
                          )}
                        </div>
                        <div className="p-3">
                      <h4 className="text-white font-bold text-sm truncate">{item.title}</h4>
                      <p className="text-xs text-gray-400 capitalize">{item.content_type}</p>
                    </div>
                  </div>
                ))}
                {libraryContent.length === 0 && (
                  <div className="col-span-3 text-center py-12">
                    <p className="text-gray-400">No content in library yet</p>
                  </div>
                )}
                  </div>
                )}
                
                {/* Google Drive Tab */}
                {mediaLibraryTab === 'drive' && (
                  <div>
                    {driveFolders.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">📁</div>
                        <h3 className="text-xl font-bold text-white mb-2">Connect Google Drive</h3>
                        <p className="text-gray-400 mb-4">No folders found. Connect Drive from Media Library.</p>
                        <button 
                          onClick={() => window.open('/dashboard/media', '_blank')}
                          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-semibold transition"
                        >
                          Open Media Library
                        </button>
                      </div>
                    ) : (
                      <div>
                        <div className="mb-4">
                          <select 
                            value={selectedFolder}
                            onChange={(e) => { setSelectedFolder(e.target.value); loadDriveAssets(e.target.value); }}
                            className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white"
                          >
                            <option value="">All Files</option>
                            {driveFolders.map((folder: any) => (
                              <option key={folder.id} value={folder.id}>{folder.name}</option>
                            ))}
                          </select>
                        </div>
                        {mediaLoading ? (
                          <div className="text-center py-12">
                            <p className="text-gray-400">Loading...</p>
                          </div>
                        ) : driveAssets.length === 0 ? (
                          <div className="text-center py-12">
                            <p className="text-gray-400">No assets found in this folder</p>
                          </div>
                        ) : (
                          <div className="grid grid-cols-3 gap-4">
                            {driveAssets.map((asset: any) => (
                              <div 
                                key={asset.id}
                                className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-blue-500 transition"
                              >
                                <div className="aspect-square bg-gradient-to-br from-blue-900 to-slate-900 flex items-center justify-center relative group">
                                  {asset.thumbnail ? (
                                    <img src={asset.thumbnail} alt={asset.name} className="w-full h-full object-cover" />
                                  ) : asset.type === 'folder' ? (
                                    <span className="text-6xl">📁</span>
                                  ) : asset.type === 'video' ? (
                                    <span className="text-6xl">🎬</span>
                                  ) : asset.type === 'image' ? (
                                    <span className="text-6xl">🖼️</span>
                                  ) : (
                                    <span className="text-6xl">📄</span>
                                  )}
                                  
                                  {/* Hover buttons for files */}
                                  {asset.type !== 'folder' && (
                                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition flex flex-col items-center justify-center gap-2 p-4">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          window.open(`https://drive.google.com/file/d/${asset.id}/view`, '_blank');
                                        }}
                                        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm font-semibold transition"
                                      >
                                        👁️ Preview in Drive
                                      </button>
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          // Add current folder name to asset
                                          const folderName = driveFolders.find(f => f.id === selectedFolder)?.name || 'Drive';
                                          handleMediaSelect({ ...asset, folderName });
                                        }}
                                        className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm font-semibold transition"
                                      >
                                        ✓ Select for Post
                                      </button>
                                    </div>
                                  )}
                                  
                                  {/* Click overlay for folders */}
                                  {asset.type === 'folder' && (
                                    <div 
                                      onClick={() => {
                                        setSelectedFolder(asset.id);
                                        loadDriveAssets(asset.id);
                                      }}
                                      className="absolute inset-0 cursor-pointer"
                                    />
                                  )}
                                </div>
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{asset.name}</h4>
                                  <p className="text-xs text-gray-400 capitalize">{asset.type}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                {/* Unsplash Tab */}
                {mediaLibraryTab === 'unsplash' && (
                  <div>
                    <div className="mb-6 flex gap-3">
                      <input
                        type="text"
                        value={unsplashQuery}
                        onChange={(e) => setUnsplashQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchUnsplash()}
                        placeholder="Search free stock photos..."
                        className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
                      />
                      <button
                        onClick={searchUnsplash}
                        className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 rounded-lg text-white font-semibold transition"
                      >
                        Search
                      </button>
                    </div>
                    {mediaLoading ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400">Searching...</p>
                      </div>
                    ) : unsplashImages.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">✨</div>
                        <h3 className="text-xl font-bold text-white mb-2">Search Unsplash</h3>
                        <p className="text-gray-400">Search millions of free stock photos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        {unsplashImages.map((image: any) => (
                          <div 
                            key={image.id}
                            onClick={() => handleMediaSelect(image)}
                            className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-pink-500"
                          >
                            <div className="aspect-square">
                              <img src={image.thumbnail} alt={image.name} className="w-full h-full object-cover" />
                            </div>
                            <div className="p-3">
                              <p className="text-xs text-gray-400 truncate">{image.name}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

    </div>
  );
}
