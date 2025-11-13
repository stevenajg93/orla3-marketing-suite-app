"use client";

import React, { useState, useEffect } from "react";
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
  const [showTrends, setShowTrends] = useState(false);
  const [trends, setTrends] = useState("");
  const [loadingTrends, setLoadingTrends] = useState(false);
  
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
  const [mediaLibraryTab, setMediaLibraryTab] = useState<'generated' | 'drive' | 'pexels-photos' | 'pexels-videos' | 'ai-images' | 'ai-videos'>('generated');
  const [driveAssets, setDriveAssets] = useState<any[]>([]);
  const [driveFolders, setDriveFolders] = useState<any[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [pexelsPhotos, setPexelsPhotos] = useState<any[]>([]);
  const [pexelsVideos, setPexelsVideos] = useState<any[]>([]);
  const [pexelsQuery, setPexelsQuery] = useState('');
  const [mediaLoading, setMediaLoading] = useState(false);
  const [libraryContent, setLibraryContent] = useState<any[]>([]);
  const [blogMetadata, setBlogMetadata] = useState<{ title?: string; content?: string } | null>(null);

  // AI Generation state
  const [aiImagePrompt, setAiImagePrompt] = useState('');
  const [aiVideoPrompt, setAiVideoPrompt] = useState('');
  const [aiAspectRatio, setAiAspectRatio] = useState<'1:1' | '16:9' | '9:16' | '4:3' | '3:4'>('1:1');
  const [aiVideoResolution, setAiVideoResolution] = useState<'720p' | '1080p'>('720p');
  const [generatingAiImage, setGeneratingAiImage] = useState(false);
  const [generatingAiVideo, setGeneratingAiVideo] = useState(false);
  const [aiGeneratedImages, setAiGeneratedImages] = useState<any[]>([]);
  const [aiGeneratedVideos, setAiGeneratedVideos] = useState<any[]>([]);


  const platforms = [
    { id: "instagram" as Platform, name: "Instagram", icon: "", color: "from-gold-intense to-cobalt", discovery: true, autoReply: true },
    { id: "linkedin" as Platform, name: "LinkedIn", icon: "", color: "from-cobalt to-cobalt-700", discovery: true, autoReply: true },
    { id: "facebook" as Platform, name: "Facebook", icon: "", color: "from-cobalt to-cobalt-600", discovery: true, autoReply: true },
    { id: "x" as Platform, name: "X", icon: "", color: "from-slate-800 to-slate-900", discovery: true, autoReply: true },
    { id: "tiktok" as Platform, name: "TikTok", icon: "", color: "from-royal-900 to-cobalt", discovery: false, autoReply: true },
    { id: "youtube" as Platform, name: "YouTube", icon: "", color: "from-red-600 to-red-700", discovery: true, autoReply: true },
    { id: "reddit" as Platform, name: "Reddit", icon: "", color: "from-gold-intense to-red-500", discovery: true, autoReply: false },
    { id: "tumblr" as Platform, name: "Tumblr", icon: "", color: "from-cobalt to-royal", discovery: true, autoReply: true },
    { id: "wordpress" as Platform, name: "WordPress", icon: "", color: "from-gray-700 to-gray-900", discovery: false, autoReply: false },
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

  // Check for pending blog post from Blog Writer on mount
  useEffect(() => {
    const pendingBlog = localStorage.getItem('pendingBlogPost');
    if (pendingBlog) {
      try {
        const blogData = JSON.parse(pendingBlog);

        // Load content into caption
        setCaption(blogData.content);

        // Store metadata for WordPress publishing
        setBlogMetadata({
          title: blogData.metadata.title,
          content: blogData.metadata.full_markdown
        });

        // Clear localStorage
        localStorage.removeItem('pendingBlogPost');

        console.log('Loaded blog from Blog Writer:', blogData.title);
      } catch (e) {
        console.error('Failed to load pending blog post:', e);
      }
    }
  }, []);

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

  const searchPexelsPhotos = async () => {
    if (!pexelsQuery.trim()) return;
    setMediaLoading(true);
    try {
      const data = await api.get(`/media/pexels/photos?query=${encodeURIComponent(pexelsQuery)}&per_page=20`);
      setPexelsPhotos(data.images || []);
    } catch (err) {
      console.error('Failed to search Pexels photos');
    } finally {
      setMediaLoading(false);
    }
  };

  const searchPexelsVideos = async () => {
    if (!pexelsQuery.trim()) return;
    setMediaLoading(true);
    try {
      const data = await api.get(`/media/pexels/videos?query=${encodeURIComponent(pexelsQuery)}&per_page=20`);
      setPexelsVideos(data.videos || []);
    } catch (err) {
      console.error('Failed to search Pexels videos');
    } finally {
      setMediaLoading(false);
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
        console.log('AI Image generated successfully');

        // Save to database so it appears in Generated Content tab
        try {
          await api.post('/library/content', {
            title: `AI Image: ${aiImagePrompt.substring(0, 50)}`,
            content_type: 'image',
            content: aiImagePrompt,
            status: 'draft',
            platform: 'AI Generated',
            tags: ['ai-generated', 'imagen-4-ultra', aiAspectRatio],
            media_url: response.image_data
          });
          console.log('AI Image saved to content library');

          // Reload media library to show new image
          loadMediaLibrary();
        } catch (saveErr) {
          console.error('Failed to save image to library:', saveErr);
          // Don't fail the whole operation if save fails
        }
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
      const response = await api.post('/ai/generate-video-veo', {
        prompt: aiVideoPrompt,
        duration_seconds: 8,
        resolution: aiVideoResolution
      });

      if (response.success && response.job_id) {
        const newVideo = {
          url: response.job_id, // Store job_id as URL temporarily
          prompt: aiVideoPrompt,
          resolution: aiVideoResolution,
          source: 'ai-generated',
          status: response.status || 'generating',
          job_id: response.job_id,
          timestamp: new Date().toISOString()
        };
        setAiGeneratedVideos([newVideo, ...aiGeneratedVideos]);
        console.log('AI Video generation started:', response.job_id);

        // Save to database immediately with "generating" status
        try {
          const saveResponse = await api.post('/library/content', {
            title: `AI Video: ${aiVideoPrompt.substring(0, 50)}`,
            content_type: 'video',
            content: aiVideoPrompt,
            status: 'draft',
            platform: 'AI Generated (Veo 3.1)',
            tags: ['ai-generated', 'veo-3.1', 'generating'],
            media_url: response.job_id // Store job_id temporarily, will update when complete
          });
          console.log('AI Video placeholder saved to content library');

          // Start polling for completion (will update database when done)
          pollVideoStatus(response.job_id, saveResponse.item?.id);

          // Reload media library
          loadMediaLibrary();
        } catch (saveErr) {
          console.error('Failed to save video to library:', saveErr);
          // Still poll even if save fails
          pollVideoStatus(response.job_id);
        }

        alert('Video generation started! This may take 2-5 minutes. It will appear in Generated Content when ready.');
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

  // Poll video status and update database when complete
  const pollVideoStatus = async (jobId: string, contentId?: string) => {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;

    const checkStatus = async () => {
      try {
        const endpoint = jobId.startsWith('projects/')
          ? `/ai/veo-status/${encodeURIComponent(jobId)}`
          : `/ai/video-status/${jobId}`;

        const status = await api.get(endpoint);

        if (status.success && status.status === 'complete' && status.video_url) {
          console.log('Video generation complete:', status.video_url);

          // Update database with final video URL
          if (contentId) {
            await api.patch(`/library/content/${contentId}`, {
              title: `AI Video: ${aiVideoPrompt.substring(0, 50)}`,
              content_type: 'video',
              content: aiVideoPrompt,
              status: 'draft',
              platform: 'AI Generated (Veo 3.1)',
              tags: ['ai-generated', 'veo-3.1', 'complete'],
              media_url: status.video_url
            });
            console.log('Video updated in database');
          }

          // Update UI state
          setAiGeneratedVideos(prev =>
            prev.map(v =>
              v.job_id === jobId
                ? { ...v, url: status.video_url, status: 'complete' }
                : v
            )
          );

          // Reload media library
          loadMediaLibrary();
        } else if (status.success && status.status === 'generating') {
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(checkStatus, 5000); // Check every 5 seconds
          } else {
            console.error('Video generation timeout');
          }
        } else if (status.error) {
          console.error('Video generation failed:', status.error);
        }
      } catch (err) {
        console.error('Error checking video status:', err);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 5000);
        }
      }
    };

    checkStatus();
  };

  const handleMediaSelect = async (item: any) => {
    console.log('Media selected:', item);
    
    // Handle carousel content from library
    if (item.content_type === 'carousel') {
      try {
        const slides = JSON.parse(item.content);
        const images = slides.map((s: any) => s.branded_image || s.image_url).filter(Boolean);
        console.log('Extracted images:', images);
        setSelectedMedia(images);
      } catch (e) {
        console.error('Failed to parse carousel', e);
      }
    } 
    // Handle blog content
    else if (item.content_type === 'blog') {
      console.log('Blog selected - adding to caption');

      // Try to parse metadata first (new format with clean text)
      try {
        const metadata = JSON.parse(item.metadata || '{}');

        // Use full clean content (no character limit) for social posting
        const fullContent = metadata.full_clean || item.content;
        setCaption(fullContent);

        // Store blog metadata for WordPress publishing (needs markdown)
        setBlogMetadata({
          title: metadata.title || item.title,
          content: metadata.full_markdown || item.content
        });
      } catch (e) {
        // Fallback to content if metadata parsing fails (old format)
        // Content field is now clean (no markdown), use it directly
        const cleanContent = item.content.replace(/^#{1,6}\s+/gm, '');  // Strip ## just in case
        setCaption(cleanContent);

        // Store basic metadata for WordPress
        setBlogMetadata({
          title: item.title || "Blog Post",
          content: item.content
        });
      }
      setSelectedMedia([]);
    } 
    // Handle Google Drive files - fetch actual file URL
    else if (item.source === 'drive') {
      console.log('Drive file selected, fetching URL...');
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
          console.log('Drive file selected:', mediaItem);
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
    // Handle Pexels photos and videos
    else if (item.source === 'pexels' && item.url) {
      console.log(`Pexels ${item.type} selected`);
      setSelectedMedia([...selectedMedia, {
        url: item.url,
        type: item.type,
        name: item.name || `Pexels ${item.type}`,
        source: 'pexels'
      }]);
    }
    // Handle AI-generated images and videos
    else if (item.source === 'ai-generated' && item.url) {
      console.log('AI-generated media selected');
      const mediaType = item.prompt?.toLowerCase().includes('video') || item.resolution ? 'video' : 'image';
      setSelectedMedia([...selectedMedia, {
        url: item.url,
        type: mediaType,
        name: `AI ${mediaType}: ${item.prompt?.substring(0, 30) || 'Generated'}`,
        source: 'ai-generated'
      }]);
    }
    // Handle content from Generated Content tab (images/videos in database)
    else if ((item.content_type === 'image' || item.content_type === 'video') && item.media_url) {
      console.log(`${item.content_type} from library selected`);
      setSelectedMedia([...selectedMedia, {
        url: item.media_url,
        type: item.content_type,
        name: item.title || `${item.content_type} from library`,
        source: 'library'
      }]);
    }
    // Fallback for direct URLs
    else if (item.thumbnail || item.url) {
      console.log('Generic media selected');
      const url = item.thumbnail || item.url;
      setSelectedMedia([...selectedMedia, typeof url === 'object' ? url : { url, type: 'image', name: 'Media', source: 'unknown' }]);
    }
    else {
      console.log('Unknown media type:', item);
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

  const fetchTrendingTopics = async () => {
    setLoadingTrends(true);
    try {
      const data = await api.get('/social-caption/trending-topics');
      setTrends(data.trends || '');
      setShowTrends(true);
    } catch (err) {
      console.error('Failed to fetch trends:', err);
      alert('Failed to fetch trending topics. Make sure Perplexity API is configured.');
    } finally {
      setLoadingTrends(false);
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
        // Build request payload
        const payload: any = {
          platform: platform,
          content_type: postType,
          caption: caption,
          image_urls: selectedMedia.map(m => m.url || m.image_url || '')
        };

        // Add blog metadata for WordPress
        if (platform === 'wordpress' && blogMetadata) {
          payload.title = blogMetadata.title;
          payload.content = blogMetadata.content;
          console.log('Publishing to WordPress with title:', blogMetadata.title);
        }

        const result = await api.post(`/publisher/publish`, payload);

        results.push({
          platform: platform,
          success: result.success,
          message: result.success ? `Posted to ${platform}!` : result.error,
          url: result.post_url
        });

      } catch (err) {
        console.error(`Failed to post to ${platform}:`, err);
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
      setPublishMessage(`Successfully posted to ${successCount} platform(s)!`);
    } else if (successCount > 0 && failCount > 0) {
      setPublishMessage(`Posted to ${successCount} platform(s), ${failCount} failed`);
    } else {
      setPublishMessage(`Failed to post to all platforms`);
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
      case "question": return "text-cobalt-300";
      default: return "text-gray-400";
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return "";
      case "negative": return "";
      case "question": return "";
      default: return "";
    }
  };

  const getPlatformIcon = (platform: Platform) => {
    return platforms.find(p => p.id === platform)?.icon || "📱";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      <div className="bg-white/5 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button onClick={() => router.push("/dashboard")} className="text-gold hover:text-cobalt-300 mb-2 flex items-center gap-2 text-sm">
            ← Back to Dashboard
          </button>
          <h1 className="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-400">
            📱 Social Manager
          </h1>
          <p className="text-cobalt-300 mt-1">Create, engage, and schedule all your social content</p>
        </div>
      </div>

      <div className="bg-white/5 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2">
            <button onClick={() => setActiveTab("create")} className={`px-6 py-4 font-semibold transition ${activeTab === "create" ? "text-white border-b-2 border-green-500" : "text-gray-400 hover:text-white"}`}>
              Create
            </button>
            <button onClick={() => setActiveTab("engage")} className={`px-6 py-4 font-semibold transition ${activeTab === "engage" ? "text-white border-b-2 border-cobalt" : "text-gray-400 hover:text-white"}`}>
              Engage
            </button>
            <button onClick={() => setActiveTab("schedule")} className={`px-6 py-4 font-semibold transition ${activeTab === "schedule" ? "text-white border-b-2 border-cobalt" : "text-gray-400 hover:text-white"}`}>
              Schedule
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
                  <button onClick={() => setPostType("text")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "text" ? "bg-gradient-to-r from-green-500 to-emerald-500 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Text Post</button>
                  <button onClick={() => setPostType("video")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "video" ? "bg-gradient-to-r from-red-500 to-red-600 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Video Post</button>
                  <button onClick={() => setPostType("carousel")} className={`flex-1 py-3 rounded-lg font-semibold transition ${postType === "carousel" ? "bg-gradient-to-r from-cobalt to-gold-intense text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Carousel</button>
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
                    className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                  />
                  <button
                    onClick={generateCaption}
                    disabled={generatingCaption || !captionPrompt.trim()}
                    className="px-6 py-2 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {generatingCaption ? "Generating..." : "Generate"}
                  </button>
                  <button
                    onClick={fetchTrendingTopics}
                    disabled={loadingTrends}
                    className="px-6 py-2 bg-gradient-to-r from-gold-intense to-red-500 hover:from-orange-600 hover:to-red-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {loadingTrends ? "Searching..." : "Trends"}
                  </button>
                </div>

                {/* Trending Topics Display */}
                {showTrends && trends && (
                  <div className="mb-4 p-4 bg-gradient-to-br from-orange-900/30 to-red-900/30 border border-gold-intense/30 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span></span> Trending Topics in Videography
                      </h3>
                      <button
                        onClick={() => setShowTrends(false)}
                        className="text-gray-400 hover:text-white transition text-xl"
                      >
                        ×
                      </button>
                    </div>
                    <div className="text-sm text-gray-200 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
                      {trends}
                    </div>
                    <p className="text-xs text-gray-400 mt-3">Use these trending topics to inspire your captions!</p>
                  </div>
                )}
                
                <textarea value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Your AI-generated caption will appear here... Or write your own!" rows={8} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none" />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-sm text-gray-400">{caption.length} characters</span>
                  {selectedPlatforms.includes("x") && caption.length > 280 && (<span className="text-sm text-red-400 font-semibold">Too long for X (280 char limit)</span>)}
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-xl font-bold text-white mb-4">Media</h2>
                <div onClick={() => { 
                  loadMediaLibrary(); 
                  loadDriveFolders();
                  setShowMediaLibrary(true); 
                }} className="border-2 border-dashed border-white/20 rounded-lg p-12 text-center hover:border-cobalt/50 transition cursor-pointer">
                  <div className="text-6xl mb-4"></div>
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
                          <div key={idx} className="relative group bg-black/20 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition">
                            <div className="aspect-video bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center relative">
                              {isVideo ? (
                                <div className="text-center p-4">
                                  <span className="text-4xl mb-2 block"></span>
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
                                          <span class="text-4xl mb-2 block"></span>
                                          <p class="text-xs text-gray-400">Media ${idx + 1}</p>
                                        </div>
                                      `;
                                    }
                                  }}
                                />
                              ) : (
                                <div className="text-center p-4">
                                  <span className="text-4xl mb-2 block"></span>
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
                                  {isVideo ? 'Video' : isImage ? 'Image' : 'File'} {idx + 1}
                                </p>
                                <span className="text-xs text-cobalt-300 ml-2">Drive</span>
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
                  <input type="datetime-local" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt" />
                  <button onClick={publishToSocial} disabled={publishing} className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed">{publishing ? "📤 Publishing..." : "📤 Post Now"}</button>
                  
                  {publishMessage && (
                    <div className={`mt-4 p-4 rounded-lg ${
                      publishMessage.includes("") ? "bg-green-500/20 border border-green-500" : 
                      publishMessage.includes("") ? "bg-gold/20 border border-gold" : 
                      "bg-red-500/20 border border-red-500"
                    }`}>
                      <p className="text-white font-semibold">{publishMessage}</p>
                      {publishResults.length > 0 && (
                        <div className="mt-3 space-y-2">
                          {publishResults.map((result, i) => (
                            <div key={i} className="flex items-center justify-between text-sm">
                              <span className="text-gray-300 capitalize">{result.platform}: {result.message}</span>
                              {result.url && (
                                <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-cobalt-300 hover:text-cobalt-300 underline">View Post</a>
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
                        {selectedPlatforms.includes(platform.id) && (<span className="text-xl"></span>)}
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
              <button onClick={() => setEngageSubTab("inbox")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "inbox" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Inbox ({mockComments.length})
              </button>
              <button onClick={() => setEngageSubTab("discovery")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "discovery" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Discovery
              </button>
              <button onClick={() => setEngageSubTab("settings")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "settings" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Settings
              </button>
            </div>

            {engageSubTab === "inbox" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                  <h2 className="text-2xl font-bold text-white mb-6">Comments Inbox</h2>
                  <div className="space-y-4">
                    {mockComments.map((comment) => (
                      <div key={comment.id} className="bg-white/5 border border-white/10 rounded-lg p-4 hover:border-cobalt/50 transition cursor-pointer" onClick={() => generateAIReplies(comment)}>
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
                  <h2 className="text-xl font-bold text-white mb-4">AI Reply</h2>
                  {!selectedComment ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4"></div>
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
                          <div className="text-4xl mb-2"></div>
                          <p className="text-gold">Generating replies...</p>
                        </div>
                      ) : aiReplies.length > 0 && (
                        <>
                          <div className="space-y-3">
                            {aiReplies.map((reply, idx) => (
                              <div key={idx} className="bg-white/10 rounded-lg p-4 hover:bg-white/20 transition cursor-pointer" onClick={() => setManualReply(reply)}>
                                <div className="flex items-start justify-between mb-2">
                                  <span className="text-xs font-semibold text-gold">Option {idx + 1}</span>
                                  <button className="text-xs text-green-400 hover:text-green-300">Use this →</button>
                                </div>
                                <p className="text-white text-sm">{reply}</p>
                              </div>
                            ))}
                          </div>
                          <div className="border-t border-white/10 pt-4">
                            <label className="block text-white font-semibold mb-2">Manual Reply</label>
                            <textarea value={manualReply} onChange={(e) => setManualReply(e.target.value)} placeholder="Edit AI suggestion or write your own..." rows={4} className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none" />
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
                <h2 className="text-2xl font-bold text-white mb-4">Find Relevant Posts</h2>
                <div className="flex gap-3 mb-6">
                  <input type="text" value={searchKeywords} onChange={(e) => setSearchKeywords(e.target.value)} placeholder="Enter keywords or hashtags" className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt" />
                  <button onClick={searchRelevantPosts} disabled={searchingPosts} className="px-6 py-3 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition disabled:opacity-50">
                    {searchingPosts ? "Searching..." : "Search"}
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
                            <span key={idx} className="text-xs px-2 py-1 bg-cobalt/20 text-cobalt-300 rounded-full">#{tag}</span>
                          ))}
                        </div>
                        <button className="w-full py-2 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition text-sm">
                          Generate Comment
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {engageSubTab === "settings" && (
              <div className="max-w-4xl mx-auto bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                <h2 className="text-2xl font-bold text-white mb-6">Engagement Settings</h2>
                <div className="bg-white/5 rounded-lg p-6 mb-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-2">Auto-Reply</h3>
                      <p className="text-gray-400 text-sm">Let AI automatically respond to comments</p>
                    </div>
                    <button onClick={() => setAutoReplyEnabled(!autoReplyEnabled)} className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${autoReplyEnabled ? "bg-green-500" : "bg-gray-600"}`}>
                      <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${autoReplyEnabled ? "translate-x-7" : "translate-x-1"}`} />
                    </button>
                  </div>
                  {autoReplyEnabled && (
                    <div className="mt-4 p-4 bg-gold/10 border border-gold/30 rounded-lg">
                      <p className="text-gold-400 text-sm font-semibold">Auto-reply is enabled</p>
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
            <div className="text-6xl mb-4"></div>
            <h2 className="text-2xl font-bold text-white mb-2">Schedule View</h2>
            <button onClick={() => router.push("/dashboard/calendar")} className="px-6 py-3 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition">
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
              <div className="px-6 pt-4 flex gap-3 border-b border-white/10 overflow-x-auto">
                <button
                  onClick={() => setMediaLibraryTab('generated')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'generated' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Generated Content
                </button>
                <button
                  onClick={() => setMediaLibraryTab('drive')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'drive' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Google Drive
                </button>
                <button
                  onClick={() => setMediaLibraryTab('pexels-photos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'pexels-photos' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Pexels Photos
                </button>
                <button
                  onClick={() => setMediaLibraryTab('pexels-videos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'pexels-videos' ? 'bg-green-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Pexels Videos
                </button>
                <button
                  onClick={() => setMediaLibraryTab('ai-images')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'ai-images' ? 'bg-gradient-to-r from-gold-600 to-gold-intense text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  🍌 AI Images
                </button>
                <button
                  onClick={() => setMediaLibraryTab('ai-videos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'ai-videos' ? 'bg-gradient-to-r from-red-600 to-red-700 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  AI Videos
                </button>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-auto p-6">
                {/* Generated Content Tab */}
                {mediaLibraryTab === 'generated' && (
                  <div className="grid grid-cols-3 gap-4">
                    {libraryContent.map((item) => (
                      <div key={item.id} onClick={() => handleMediaSelect(item)} className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-cobalt">
                        {/* Show actual media if available */}
                        {item.media_url && item.content_type === 'image' ? (
                          <div className="aspect-square overflow-hidden">
                            <img src={item.media_url} alt={item.title} className="w-full h-full object-cover" />
                          </div>
                        ) : item.media_url && item.content_type === 'video' ? (
                          <div className="aspect-square overflow-hidden bg-black relative group">
                            <video
                              src={item.media_url}
                              className="w-full h-full object-cover"
                              muted
                              loop
                              onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
                              onMouseLeave={(e) => (e.target as HTMLVideoElement).pause()}
                            />
                            <div className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded">VIDEO</div>
                          </div>
                        ) : (
                          <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                            {item.content_type === 'carousel' ? (
                              <span className="text-6xl"></span>
                            ) : item.content_type === 'blog' ? (
                              <span className="text-6xl"></span>
                            ) : (
                              <span className="text-6xl"></span>
                            )}
                          </div>
                        )}
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
                        <div className="text-6xl mb-4"></div>
                        <h3 className="text-xl font-bold text-white mb-2">Connect Google Drive</h3>
                        <p className="text-gray-400 mb-4">No folders found. Connect Drive from Media Library.</p>
                        <button 
                          onClick={() => window.open('/dashboard/media', '_blank')}
                          className="px-6 py-3 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white font-semibold transition"
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
                                className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition"
                              >
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center relative group">
                                  {asset.thumbnail ? (
                                    <img src={asset.thumbnail} alt={asset.name} className="w-full h-full object-cover" />
                                  ) : asset.type === 'folder' ? (
                                    <span className="text-6xl"></span>
                                  ) : asset.type === 'video' ? (
                                    <span className="text-6xl"></span>
                                  ) : asset.type === 'image' ? (
                                    <span className="text-6xl"></span>
                                  ) : (
                                    <span className="text-6xl"></span>
                                  )}
                                  
                                  {/* Hover buttons for files */}
                                  {asset.type !== 'folder' && (
                                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition flex flex-col items-center justify-center gap-2 p-4">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          window.open(`https://drive.google.com/file/d/${asset.id}/view`, '_blank');
                                        }}
                                        className="w-full px-4 py-2 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white text-sm font-semibold transition"
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
                                        className="w-full px-4 py-2 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white text-sm font-semibold transition"
                                      >
                                        Select for Post
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
                
                {/* Pexels Photos Tab */}
                {mediaLibraryTab === 'pexels-photos' && (
                  <div>
                    <div className="mb-6 flex gap-3">
                      <input
                        type="text"
                        value={pexelsQuery}
                        onChange={(e) => setPexelsQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchPexelsPhotos()}
                        placeholder="Search free stock photos..."
                        className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
                      />
                      <button
                        onClick={searchPexelsPhotos}
                        className="px-6 py-3 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition"
                      >
                        Search
                      </button>
                    </div>
                    {mediaLoading ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400">Searching...</p>
                      </div>
                    ) : pexelsPhotos.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4"></div>
                        <h3 className="text-xl font-bold text-white mb-2">Search Pexels Photos</h3>
                        <p className="text-gray-400">Search millions of free, high-quality stock photos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        {pexelsPhotos.map((photo: any) => (
                          <div
                            key={photo.id}
                            onClick={() => handleMediaSelect(photo)}
                            className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-cobalt"
                          >
                            <div className="aspect-square">
                              <img src={photo.thumbnail} alt={photo.name} className="w-full h-full object-cover" />
                            </div>
                            <div className="p-3">
                              <p className="text-xs text-gray-400 truncate">{photo.name}</p>
                              <p className="text-xs text-gray-500 mt-1">By {photo.photographer}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Pexels Videos Tab */}
                {mediaLibraryTab === 'pexels-videos' && (
                  <div>
                    <div className="mb-6 flex gap-3">
                      <input
                        type="text"
                        value={pexelsQuery}
                        onChange={(e) => setPexelsQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchPexelsVideos()}
                        placeholder="Search free stock videos..."
                        className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-green-500"
                      />
                      <button
                        onClick={searchPexelsVideos}
                        className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 rounded-lg text-white font-semibold transition"
                      >
                        Search
                      </button>
                    </div>
                    {mediaLoading ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400">Searching...</p>
                      </div>
                    ) : pexelsVideos.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4"></div>
                        <h3 className="text-xl font-bold text-white mb-2">Search Pexels Videos</h3>
                        <p className="text-gray-400">Search thousands of free, high-quality stock videos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        {pexelsVideos.map((video: any) => (
                          <div
                            key={video.id}
                            onClick={() => handleMediaSelect(video)}
                            className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-green-500"
                          >
                            <div className="aspect-video relative group">
                              <img src={video.thumbnail} alt={video.name} className="w-full h-full object-cover" />
                              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                                <div className="text-white text-4xl"></div>
                              </div>
                              <div className="absolute top-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
                                {Math.floor(video.duration)}s
                              </div>
                            </div>
                            <div className="p-3">
                              <p className="text-xs text-gray-400 truncate">{video.name}</p>
                              <p className="text-xs text-gray-500 mt-1">By {video.user}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* AI Images Tab (Imagen 3 - Nano Banana 🍌) */}
                {mediaLibraryTab === 'ai-images' && (
                  <div>
                    <div className="mb-6 space-y-4">
                      <div className="bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border border-gold/30 rounded-lg p-4">
                        <h4 className="text-lg font-bold text-gold-400 mb-2">🍌 Google Imagen 3 (Nano Banana)</h4>
                        <p className="text-sm text-gray-300 mb-2">Generate high-quality AI images from text prompts. Cost: $0.03 per image.</p>
                      </div>

                      <textarea
                        value={aiImagePrompt}
                        onChange={(e) => setAiImagePrompt(e.target.value)}
                        placeholder="Describe the image you want to generate... (e.g., 'Professional videographer filming a corporate interview in modern office')"
                        rows={3}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-gold resize-none"
                      />

                      <div className="flex gap-4 items-center">
                        <div className="flex-1">
                          <label className="block text-sm text-gray-400 mb-2">Aspect Ratio</label>
                          <select
                            value={aiAspectRatio}
                            onChange={(e) => setAiAspectRatio(e.target.value as any)}
                            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-gold"
                          >
                            <option value="1:1">1:1 Square</option>
                            <option value="16:9">16:9 Landscape</option>
                            <option value="9:16">9:16 Portrait</option>
                            <option value="4:3">4:3 Standard</option>
                            <option value="3:4">3:4 Portrait</option>
                          </select>
                        </div>

                        <button
                          onClick={generateAiImage}
                          disabled={generatingAiImage || !aiImagePrompt.trim()}
                          className="px-8 py-2 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-bold transition mt-6"
                        >
                          {generatingAiImage ? '🍌 Generating...' : '🍌 Generate Image'}
                        </button>
                      </div>
                    </div>

                    {aiGeneratedImages.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">🍌</div>
                        <h3 className="text-xl font-bold text-white mb-2">No AI Images Generated Yet</h3>
                        <p className="text-gray-400">Enter a prompt above and click Generate to create AI images</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        {aiGeneratedImages.map((image: any, idx: number) => (
                          <div
                            key={idx}
                            onClick={() => handleMediaSelect(image)}
                            className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-gold"
                          >
                            <div className="aspect-square">
                              <img src={image.url} alt={image.prompt} className="w-full h-full object-cover" />
                            </div>
                            <div className="p-3">
                              <p className="text-xs text-gray-400 truncate">{image.prompt}</p>
                              <p className="text-xs text-gray-500 mt-1">{image.aspect_ratio}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* AI Videos Tab (Veo 3.1 ) */}
                {mediaLibraryTab === 'ai-videos' && (
                  <div>
                    <div className="mb-6 space-y-4">
                      <div className="bg-gradient-to-r from-red-900/30 to-gold-900/30 border border-red-500/30 rounded-lg p-4">
                        <h4 className="text-lg font-bold text-red-400 mb-2">Google Veo 3.1</h4>
                        <p className="text-sm text-gray-300 mb-2">Generate 8-second AI videos with audio from text prompts. Cost: $0.75/second ($6 per video).</p>
                        <p className="text-xs text-gold-400">Video generation takes 2-5 minutes</p>
                      </div>

                      <textarea
                        value={aiVideoPrompt}
                        onChange={(e) => setAiVideoPrompt(e.target.value)}
                        placeholder="Describe the video you want to generate... (e.g., 'Professional videographer filming behind-the-scenes of a wedding ceremony')"
                        rows={3}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500 resize-none"
                      />

                      <div className="flex gap-4 items-center">
                        <div className="flex-1">
                          <label className="block text-sm text-gray-400 mb-2">Resolution</label>
                          <select
                            value={aiVideoResolution}
                            onChange={(e) => setAiVideoResolution(e.target.value as any)}
                            className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-red-500"
                          >
                            <option value="720p">720p (HD)</option>
                            <option value="1080p">1080p (Full HD) - Higher cost</option>
                          </select>
                        </div>

                        <button
                          onClick={generateAiVideo}
                          disabled={generatingAiVideo || !aiVideoPrompt.trim()}
                          className="px-8 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-bold transition mt-6"
                        >
                          {generatingAiVideo ? 'Generating...' : 'Generate Video'}
                        </button>
                      </div>
                    </div>

                    {aiGeneratedVideos.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4"></div>
                        <h3 className="text-xl font-bold text-white mb-2">No AI Videos Generated Yet</h3>
                        <p className="text-gray-400">Enter a prompt above and click Generate to create AI videos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-3 gap-4">
                        {aiGeneratedVideos.map((video: any, idx: number) => (
                          <div
                            key={idx}
                            onClick={() => video.status === 'complete' && handleMediaSelect(video)}
                            className={`bg-white/5 rounded-lg overflow-hidden ${video.status === 'complete' ? 'cursor-pointer hover:bg-white/10 hover:border-red-500' : 'opacity-50'} transition border border-white/10`}
                          >
                            <div className="aspect-video bg-gradient-to-br from-red-900 to-gold-900 flex items-center justify-center">
                              {video.status === 'generating' ? (
                                <div className="text-center">
                                  <div className="text-4xl mb-2">⏳</div>
                                  <p className="text-sm text-gray-300">Generating...</p>
                                </div>
                              ) : video.url ? (
                                <video src={video.url} className="w-full h-full object-cover" />
                              ) : (
                                <div className="text-4xl"></div>
                              )}
                            </div>
                            <div className="p-3">
                              <p className="text-xs text-gray-400 truncate">{video.prompt}</p>
                              <p className="text-xs text-gray-500 mt-1">{video.resolution} • {video.status}</p>
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
