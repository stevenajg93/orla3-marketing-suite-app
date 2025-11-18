"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from 'framer-motion';
import { api } from '@/lib/api-client';
import { config } from '@/lib/config';
import { AnimatedPage } from '@/components/AnimatedPage';
import { fadeInUp } from '@/lib/motion';
import {
  getPlatformCharacterLimit,
  isOverCharacterLimit,
  isPlatformCompatible,
  getIncompatibilityReason,
} from '@/lib/validators';

type PostType = "text" | "image" | "video" | "carousel";
type Platform = "instagram" | "linkedin" | "facebook" | "x" | "tiktok" | "youtube" | "reddit" | "tumblr" | "wordpress";
type Tab = "create" | "engage" | "schedule";
type EngageSubTab = "inbox" | "discovery" | "settings";
type Mode = "quick" | "studio";
type StudioPlatform = Platform;
type InstagramPostType = "feed" | "carousel" | "reel" | "story";

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

  // Mode state (Quick Post vs Studio)
  const [mode, setMode] = useState<Mode>("quick");
  const [studioPlatform, setStudioPlatform] = useState<StudioPlatform>("instagram");
  const [instagramPostType, setInstagramPostType] = useState<InstagramPostType>("feed");

  // Quick Post state
  const [postType, setPostType] = useState<PostType>("text");
  const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);
  const [caption, setCaption] = useState("");

  // Instagram Studio state
  const [reelCoverUrl, setReelCoverUrl] = useState("");
  const [shareToFeed, setShareToFeed] = useState(true);

  // YouTube Studio state
  const [youtubeTitle, setYoutubeTitle] = useState("");
  const [youtubePrivacy, setYoutubePrivacy] = useState<"public" | "private" | "unlisted">("private");
  const [youtubeCategory, setYoutubeCategory] = useState("22");
  const [isShort, setIsShort] = useState(false);
  const [youtubeThumbnail, setYoutubeThumbnail] = useState("");

  // Facebook Studio state
  const [facebookPostType, setFacebookPostType] = useState<"text" | "link" | "photo" | "video" | "album">("text");
  const [facebookLinkUrl, setFacebookLinkUrl] = useState("");

  // TikTok Studio state
  const [tiktokPrivacy, setTiktokPrivacy] = useState<"PUBLIC_TO_EVERYONE" | "SELF_ONLY" | "MUTUAL_FOLLOW_FRIENDS">("SELF_ONLY");
  const [disableDuet, setDisableDuet] = useState(false);
  const [disableComment, setDisableComment] = useState(false);
  const [disableStitch, setDisableStitch] = useState(false);

  // LinkedIn Studio state
  const [linkedinPostType, setLinkedinPostType] = useState<"text" | "image" | "video" | "article">("text");
  const [articleTitle, setArticleTitle] = useState("");
  const [articleUrl, setArticleUrl] = useState("");

  // X Studio state
  const [xPostType, setXPostType] = useState<"text" | "image" | "video">("text");

  // Reddit Studio state
  const [redditPostType, setRedditPostType] = useState<"text" | "link" | "image" | "video">("text");
  const [redditSubreddit, setRedditSubreddit] = useState("");
  const [redditTitle, setRedditTitle] = useState("");
  const [redditLinkUrl, setRedditLinkUrl] = useState("");

  // Tumblr Studio state
  const [tumblrPostType, setTumblrPostType] = useState<"text" | "photo">("text");

  // WordPress Studio state
  const [wordpressTitle, setWordpressTitle] = useState("");
  const [wordpressStatus, setWordpressStatus] = useState<"publish" | "draft">("draft");

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
  const [mediaLibraryTab, setMediaLibraryTab] = useState<'generated' | 'cloud' | 'pexels-photos' | 'pexels-videos' | 'ai-images' | 'ai-videos'>('generated');
  const [cloudStorageProvider, setCloudStorageProvider] = useState<'google_drive' | 'dropbox' | 'onedrive' | null>(null);
  const [connectedProviders, setConnectedProviders] = useState<string[]>([]);
  const [driveAssets, setDriveAssets] = useState<any[]>([]);
  const [driveFolders, setDriveFolders] = useState<any[]>([]);
  const [driveFolderId, setDriveFolderId] = useState<string>('');
  const [dropboxFiles, setDropboxFiles] = useState<any[]>([]);
  const [dropboxFolders, setDropboxFolders] = useState<any[]>([]);
  const [dropboxPath, setDropboxPath] = useState<string>('');
  const [onedriveFiles, setOnedriveFiles] = useState<any[]>([]);
  const [onedriveFolders, setOnedriveFolders] = useState<any[]>([]);
  const [onedrivePath, setOnedrivePath] = useState<string>('');
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
    { id: "instagram" as Platform, name: "Instagram", color: "from-gold-intense to-cobalt", discovery: true, autoReply: true },
    { id: "linkedin" as Platform, name: "LinkedIn", color: "from-cobalt to-cobalt-700", discovery: true, autoReply: true },
    { id: "facebook" as Platform, name: "Facebook", color: "from-cobalt to-cobalt-600", discovery: true, autoReply: true },
    { id: "x" as Platform, name: "X", color: "from-slate-800 to-slate-900", discovery: true, autoReply: true },
    { id: "tiktok" as Platform, name: "TikTok", color: "from-royal-900 to-cobalt", discovery: false, autoReply: true },
    { id: "youtube" as Platform, name: "YouTube", color: "from-cobalt to-royal", discovery: true, autoReply: true },
    { id: "reddit" as Platform, name: "Reddit", color: "from-gold-intense to-gold", discovery: true, autoReply: false },
    { id: "tumblr" as Platform, name: "Tumblr", color: "from-cobalt to-royal", discovery: true, autoReply: true },
    { id: "wordpress" as Platform, name: "WordPress", color: "from-slate-700 to-slate-900", discovery: false, autoReply: false },
  ];

  // Real comments from API (no more mocks!)
  const [comments, setComments] = useState<Comment[]>([]);
  const [loadingComments, setLoadingComments] = useState(false);

  // Auto-deselect incompatible platforms when post type changes
  useEffect(() => {
    setSelectedPlatforms(prevSelected =>
      prevSelected.filter(platform => isPlatformCompatible(platform, postType))
    );
  }, [postType]);

  const togglePlatform = (platform: Platform) => {
    // Check if platform is compatible with current post type
    if (!isPlatformCompatible(platform, postType)) {
      return; // Don't allow selection of incompatible platforms
    }

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

  // Load media library content and connected providers when modal opens
  useEffect(() => {
    if (showMediaLibrary) {
      loadMediaLibrary();
      loadConnectedProviders();
    }
  }, [showMediaLibrary]);

  const loadMediaLibrary = async () => {
    setMediaLoading(true);
    try {
      console.log('📚 Loading generated content...');
      const data = await api.get('/library/content');
      console.log('✓ Generated content loaded:', data.items?.length || 0, 'items');
      setLibraryContent(data.items || []);
    } catch (err: any) {
      console.error('❌ Failed to load media library:', err);
      alert(`Failed to load generated content: ${err.message || 'Unknown error'}`);
    } finally {
      setMediaLoading(false);
    }
  };

  const loadConnectedProviders = async () => {
    try {
      console.log('☁️ Loading connected providers...');
      const data = await api.get('/cloud-storage/connections');
      console.log('☁️ Provider response:', data);
      if (data.success && data.connections) {
        const providers = data.connections.map((conn: any) => conn.provider);
        console.log('☁️ Found providers:', providers);
        setConnectedProviders(providers);

        // Set initial cloud storage provider to first connected one
        if (providers.length > 0) {
          const firstProvider = providers[0];
          setCloudStorageProvider(firstProvider);

          // Load files for the first provider
          if (firstProvider === 'google_drive') {
            loadDriveFiles('');
          } else if (firstProvider === 'dropbox') {
            loadDropboxFiles('');
          } else if (firstProvider === 'onedrive') {
            loadOnedriveFiles('');
          }
        }
      }
    } catch (err) {
      console.error('Failed to load connected providers:', err);
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

  const loadDriveFiles = async (folder_id: string = '') => {
    setMediaLoading(true);
    try {
      const params = new URLSearchParams();
      if (folder_id) params.append('folder_id', folder_id);
      const data = await api.get(`/cloud-storage/browse/google_drive?${params}`);
      setDriveAssets(data.files || []);
      setDriveFolders(data.folders || []);
    } catch (err: any) {
      console.error('Failed to load Google Drive files:', err);
      if (err?.status === 404) {
        alert('Google Drive not connected. Please connect Google Drive in Settings > Cloud Storage.');
      }
    } finally {
      setMediaLoading(false);
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

  const loadDropboxFiles = async (path: string = '') => {
    setMediaLoading(true);
    try {
      const params = new URLSearchParams();
      if (path) params.append('path', path);
      const data = await api.get(`/cloud-storage/browse/dropbox?${params}`);
      setDropboxFiles(data.files || []);
      setDropboxFolders(data.folders || []);
    } catch (err: any) {
      console.error('Failed to load Dropbox files:', err);
      if (err?.status === 404) {
        alert('Dropbox not connected. Please connect Dropbox in Settings > Cloud Storage.');
      }
    } finally {
      setMediaLoading(false);
    }
  };

  const loadOnedriveFiles = async (path: string = '') => {
    setMediaLoading(true);
    try {
      const params = new URLSearchParams();
      if (path) params.append('path', path);
      const data = await api.get(`/cloud-storage/browse/onedrive?${params}`);
      setOnedriveFiles(data.files || []);
      setOnedriveFolders(data.folders || []);
    } catch (err: any) {
      console.error('Failed to load OneDrive files:', err);
      if (err?.status === 404) {
        alert('OneDrive not connected. Please connect OneDrive in Settings > Cloud Storage.');
      }
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
    // Handle Dropbox files - fetch temporary download link
    else if (item.source === 'dropbox') {
      console.log('Dropbox file selected, fetching download link...');
      try {
        const data = await api.get(`/cloud-storage/file/dropbox/${encodeURIComponent(item.id)}`);

        if (data.success && data.link) {
          const mediaItem = {
            url: data.link,
            type: item.type || 'file',
            name: item.name || 'Dropbox File',
            source: 'dropbox'
          };
          console.log('Dropbox file selected:', mediaItem);
          setSelectedMedia([...selectedMedia, mediaItem]);
        } else {
          console.error('Failed to get Dropbox file link');
          alert('Could not load Dropbox file.');
        }
      } catch (err) {
        console.error('Error fetching Dropbox file:', err);
        alert('Failed to load Dropbox file');
      }
    }
    // Handle OneDrive files - use download URL from API
    else if (item.source === 'onedrive') {
      console.log('OneDrive file selected');
      // OneDrive API returns download_url directly
      if (item.url || item.download_url) {
        const mediaItem = {
          url: item.url || item.download_url,
          type: item.type || 'file',
          name: item.name || 'OneDrive File',
          source: 'onedrive'
        };
        console.log('OneDrive file selected:', mediaItem);
        setSelectedMedia([...selectedMedia, mediaItem]);
      } else {
        // Fetch download URL if not provided
        try {
          const data = await api.get(`/cloud-storage/file/onedrive/${item.id}`);

          if (data.success && data.download_url) {
            const mediaItem = {
              url: data.download_url,
              type: item.type || 'file',
              name: data.name || item.name || 'OneDrive File',
              source: 'onedrive'
            };
            console.log('OneDrive file selected:', mediaItem);
            setSelectedMedia([...selectedMedia, mediaItem]);
          } else {
            console.error('Failed to get OneDrive file URL');
            alert('Could not load OneDrive file.');
          }
        } catch (err) {
          console.error('Error fetching OneDrive file:', err);
          alert('Failed to load OneDrive file');
        }
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

    // Validate based on mode
    if (mode === "quick") {
      if (selectedPlatforms.length === 0) {
        alert('Please select at least one platform');
        return;
      }
    } else if (mode === "studio") {
      // Studio mode validation
      if (studioPlatform === "instagram") {
        if (instagramPostType === "reel") {
          if (selectedMedia.length === 0 || !selectedMedia[0]?.content_type?.includes('video')) {
            alert('Please upload a video for your Reel');
            return;
          }
        }
        if (instagramPostType === "story" && selectedMedia.length === 0) {
          alert('Please upload media for your Story');
          return;
        }
        if (instagramPostType === "feed" && selectedMedia.length === 0) {
          alert('Please select at least one image for Feed post');
          return;
        }
        if (instagramPostType === "carousel" && selectedMedia.length < 2) {
          alert('Carousel requires at least 2 images');
          return;
        }
      }

      if (studioPlatform === "youtube") {
        if (selectedMedia.length === 0 || !selectedMedia[0]?.content_type?.includes('video')) {
          alert('YouTube requires a video');
          return;
        }
        if (!youtubeTitle.trim()) {
          alert('Please add a video title');
          return;
        }
      }

      if (studioPlatform === "facebook") {
        if (facebookPostType === "link" && !facebookLinkUrl.trim()) {
          alert('Please add a URL for your link post');
          return;
        }
        if (facebookPostType === "photo" && selectedMedia.length === 0) {
          alert('Please select at least one photo');
          return;
        }
        if (facebookPostType === "video" && (selectedMedia.length === 0 || !selectedMedia[0]?.content_type?.includes('video'))) {
          alert('Please select a video');
          return;
        }
        if (facebookPostType === "album" && selectedMedia.length < 2) {
          alert('Album requires at least 2 photos');
          return;
        }
      }

      if (studioPlatform === "tiktok") {
        if (selectedMedia.length === 0 || !selectedMedia[0]?.content_type?.includes('video')) {
          alert('TikTok requires a video');
          return;
        }
      }

      if (studioPlatform === "linkedin") {
        if (linkedinPostType === "image" && selectedMedia.length === 0) {
          alert('Please select an image');
          return;
        }
        if (linkedinPostType === "video" && (selectedMedia.length === 0 || !selectedMedia[0]?.content_type?.includes('video'))) {
          alert('Please select a video');
          return;
        }
        if (linkedinPostType === "article" && !articleTitle.trim()) {
          alert('Article posts require a title');
          return;
        }
      }

      if (studioPlatform === "x") {
        if (xPostType === "image" && selectedMedia.length === 0) {
          alert('Please select at least one image');
          return;
        }
        if (xPostType === "image" && selectedMedia.length > 4) {
          alert('X supports maximum 4 images per post');
          return;
        }
        if (xPostType === "video" && selectedMedia.length === 0) {
          alert('Please select a video');
          return;
        }
      }

      if (studioPlatform === "reddit") {
        if (!redditSubreddit.trim()) {
          alert('Please enter a subreddit name');
          return;
        }
        if (!redditTitle.trim()) {
          alert('Please add a post title');
          return;
        }
        if (redditTitle.length > 300) {
          alert('Reddit titles must be under 300 characters');
          return;
        }
        if (redditPostType === "link" && !redditLinkUrl.trim()) {
          alert('Please add a URL for your link post');
          return;
        }
        if (redditPostType === "image" && selectedMedia.length === 0) {
          alert('Please select an image');
          return;
        }
        if (redditPostType === "video" && selectedMedia.length === 0) {
          alert('Please select a video');
          return;
        }
      }

      if (studioPlatform === "tumblr") {
        if (tumblrPostType === "photo" && selectedMedia.length === 0) {
          alert('Please select a photo');
          return;
        }
      }

      if (studioPlatform === "wordpress") {
        if (!wordpressTitle.trim()) {
          alert('Please add a blog post title');
          return;
        }
      }
    }

    setPublishing(true);
    setPublishResults([]);
    setPublishMessage('');

    const results = [];

    // Determine platforms to publish to
    const platformsToPublish = mode === "quick" ? selectedPlatforms : [studioPlatform];

    for (const platform of platformsToPublish) {
      try {
        let payload: any = {
          platform: platform,
          caption: caption,
        };

        // Studio mode - platform-specific payloads
        if (mode === "studio" && platform === "instagram") {
          if (instagramPostType === "reel") {
            payload.content_type = "reel";
            payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
            payload.cover_url = reelCoverUrl || null;
            payload.share_to_feed = shareToFeed;
          } else if (instagramPostType === "story") {
            payload.content_type = "story";
            const isVideo = selectedMedia[0]?.content_type?.includes('video');
            if (isVideo) {
              payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
            } else {
              payload.image_urls = [selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''];
            }
          } else if (instagramPostType === "carousel") {
            payload.content_type = "carousel";
            payload.image_urls = selectedMedia.map(m => m.url || m.image_url || '');
          } else {
            // Feed post
            payload.content_type = "image";
            payload.image_urls = selectedMedia.map(m => m.url || m.image_url || '');
          }
        } else if (mode === "studio" && platform === "youtube") {
          payload.content_type = "video";
          payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          payload.title = youtubeTitle;
          payload.privacy = youtubePrivacy;
          payload.category_id = youtubeCategory;
          payload.is_short = isShort;
          payload.thumbnail_url = youtubeThumbnail || null;
        } else if (mode === "studio" && platform === "facebook") {
          payload.content_type = facebookPostType;

          if (facebookPostType === "text") {
            // Text-only post
            // No additional fields needed
          } else if (facebookPostType === "link") {
            // Link post
            payload.link_url = facebookLinkUrl;
          } else if (facebookPostType === "photo") {
            // Single photo
            payload.image_urls = [selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''];
          } else if (facebookPostType === "video") {
            // Video post
            payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          } else if (facebookPostType === "album") {
            // Photo album
            payload.image_urls = selectedMedia.map(m => m.url || m.image_url || '');
          }
        } else if (mode === "studio" && platform === "tiktok") {
          payload.content_type = "video";
          payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          payload.tiktok_privacy = tiktokPrivacy;
          payload.disable_duet = disableDuet;
          payload.disable_comment = disableComment;
          payload.disable_stitch = disableStitch;
        } else if (mode === "studio" && platform === "linkedin") {
          payload.content_type = linkedinPostType;
          if (linkedinPostType === "text") {
            // Text-only post
          } else if (linkedinPostType === "image") {
            // Image post
            payload.image_urls = [selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''];
          } else if (linkedinPostType === "video") {
            // Video post
            payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          } else if (linkedinPostType === "article") {
            // Article post
            payload.article_title = articleTitle;
            payload.article_url = articleUrl;
          }
        } else if (mode === "studio" && (platform === "x" || platform === "twitter")) {
          payload.content_type = xPostType;
          if (xPostType === "image") {
            // Image post (up to 4 images)
            payload.image_urls = selectedMedia.map(m => m.url || m.image_url || '');
          } else if (xPostType === "video") {
            // Video post
            payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          }
          // Text-only posts don't need additional fields
        } else if (mode === "studio" && platform === "reddit") {
          payload.subreddit = redditSubreddit;
          payload.title = redditTitle;
          payload.content_type = redditPostType;

          if (redditPostType === "text") {
            // Text post - caption goes in the text field
          } else if (redditPostType === "link") {
            payload.link_url = redditLinkUrl;
          } else if (redditPostType === "image") {
            payload.image_urls = [selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''];
          } else if (redditPostType === "video") {
            payload.video_url = selectedMedia[0]?.url || selectedMedia[0]?.media_url || '';
          }
        } else if (mode === "studio" && platform === "tumblr") {
          payload.content_type = tumblrPostType;
          if (tumblrPostType === "photo") {
            payload.image_urls = [selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''];
          }
          // Text-only posts don't need additional fields
        } else if (mode === "studio" && platform === "wordpress") {
          payload.title = wordpressTitle;
          payload.content = caption; // Caption becomes blog post content
          payload.status = wordpressStatus;
        } else {
          // Quick Post mode - use postType
          payload.content_type = postType;
          payload.image_urls = selectedMedia.map(m => m.url || m.image_url || '');

          // Add blog metadata for WordPress
          if (platform === 'wordpress' && blogMetadata) {
            payload.title = blogMetadata.title;
            payload.content = blogMetadata.content;
            console.log('Publishing to WordPress with title:', blogMetadata.title);
          }
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
  // Load real comments from all connected platforms
  const loadComments = async () => {
    setLoadingComments(true);
    try {
      const response = await apiClient.get('/social/comments/all?limit=50');
      if (response.data) {
        // Transform API response to match Comment interface
        const transformedComments = response.data.map((c: any) => ({
          id: c.id,
          platform: c.platform as Platform,
          postTitle: c.post_id,  // Use post_id as title for now
          author: c.author,
          content: c.text,
          timestamp: formatTimestamp(c.timestamp),
          sentiment: c.sentiment || 'neutral'
        }));
        setComments(transformedComments);
      }
    } catch (error) {
      console.error('Failed to load comments:', error);
      // Don't show error to user, just keep comments empty
    } finally {
      setLoadingComments(false);
    }
  };

  // Format ISO timestamp to relative time
  const formatTimestamp = (isoTimestamp: string): string => {
    try {
      const date = new Date(isoTimestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 60) return `${diffMins} minutes ago`;
      if (diffHours < 24) return `${diffHours} hours ago`;
      return `${diffDays} days ago`;
    } catch {
      return 'recently';
    }
  };

  // Generate AI replies using backend /comments/reply endpoint
  const generateAIReplies = async (comment: Comment) => {
    setSelectedComment(comment);
    setGeneratingReplies(true);
    setAiReplies([]);

    try {
      const response = await apiClient.post('/comments/reply', {
        comment_text: comment.content,
        platform: comment.platform,
        author: comment.author
      });

      if (response.data && response.data.replies) {
        setAiReplies(response.data.replies);
      } else if (response.data && response.data.reply) {
        // Single reply format
        setAiReplies([response.data.reply]);
      }
    } catch (error) {
      console.error('Failed to generate AI replies:', error);
      setAiReplies(['Failed to generate replies. Please try again.']);
    } finally {
      setGeneratingReplies(false);
    }
  };

  const searchRelevantPosts = async () => {
    if (!discoveryQuery.trim()) {
      return;
    }

    setSearchingPosts(true);
    setDiscoveryPosts([]);

    try {
      // Search across Twitter and Reddit
      const response = await apiClient.post('/social/discover/all', {
        query: discoveryQuery,
        platforms: ['twitter', 'reddit'],
        limit: 20
      });

      if (response.data) {
        // Transform API response to match DiscoveryPost interface
        const transformedPosts = response.data.map((p: any) => ({
          id: p.id,
          platform: p.platform as Platform,
          author: p.author,
          content: p.content,
          hashtags: p.hashtags || [],
          engagement: p.engagement || 0,
          timestamp: formatTimestamp(p.timestamp)
        }));
        setDiscoveryPosts(transformedPosts);
      }
    } catch (error) {
      console.error('Failed to search posts:', error);
      // Show user-friendly message
      setDiscoveryPosts([]);
    } finally {
      setSearchingPosts(false);
    }
  };

  // Load comments when Engage tab is selected
  useEffect(() => {
    if (activeTab === 'engage' && engageSubTab === 'inbox' && comments.length === 0) {
      loadComments();
    }
  }, [activeTab, engageSubTab]);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "positive": return "text-gold";
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
    return platforms.find(p => p.id === platform)?.icon || "";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-royal-800 to-slate-900">
      <div className="bg-white/5 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <button onClick={() => router.push("/dashboard")} className="text-gold hover:text-cobalt-300 mb-2 flex items-center gap-2 text-sm">
            ← Back to Dashboard
          </button>
          <h1 className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-gold to-gold-intense">
            Social Manager
          </h1>
          <p className="text-cobalt-300 mt-1">Create, engage, and schedule all your social content</p>
        </div>
      </div>

      <div className="bg-white/5 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-2">
            <button onClick={() => setActiveTab("create")} className={`px-6 py-3 sm:py-4 font-semibold transition ${activeTab === "create" ? "text-white border-b-2 border-gold" : "text-gray-400 hover:text-white"}`}>
              Create
            </button>
            <button onClick={() => setActiveTab("engage")} className={`px-6 py-3 sm:py-4 font-semibold transition ${activeTab === "engage" ? "text-white border-b-2 border-cobalt" : "text-gray-400 hover:text-white"}`}>
              Engage
            </button>
            <button onClick={() => setActiveTab("schedule")} className={`px-6 py-3 sm:py-4 font-semibold transition ${activeTab === "schedule" ? "text-white border-b-2 border-cobalt" : "text-gray-400 hover:text-white"}`}>
              Schedule
            </button>
          </div>
        </div>
      </div>

      {/* Mode Switcher - Quick Post vs Studio */}
      {activeTab === "create" && (
        <div className="bg-white/5 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex gap-2 sm:gap-3">
              <button
                onClick={() => setMode("quick")}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition text-sm sm:text-base ${
                  mode === "quick"
                    ? "bg-gradient-to-r from-gold to-gold-intense text-white"
                    : "bg-white/10 text-gray-400 hover:bg-white/20"
                }`}
              >
                Quick Post
              </button>
              <button
                onClick={() => setMode("studio")}
                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg font-semibold transition text-sm sm:text-base ${
                  mode === "studio"
                    ? "bg-gradient-to-r from-cobalt to-royal text-white"
                    : "bg-white/10 text-gray-400 hover:bg-white/20"
                }`}
              >
                Platform Studio
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Platform Tabs for Studio Mode */}
      {activeTab === "create" && mode === "studio" && (
        <div className="bg-white/5 border-b border-white/10">
          <div className="max-w-7xl mx-auto px-3 sm:px-6">
            <div className="flex gap-1 sm:gap-2 overflow-x-auto scrollbar-hide">
              {[
                { id: "instagram" as Platform, name: "Instagram", color: "from-gold-intense to-cobalt" },
                { id: "youtube" as Platform, name: "YouTube", color: "from-cobalt to-royal" },
                { id: "tiktok" as Platform, name: "TikTok", color: "from-royal-900 to-cobalt" },
                { id: "linkedin" as Platform, name: "LinkedIn", color: "from-cobalt to-cobalt-700" },
                { id: "facebook" as Platform, name: "Facebook", color: "from-cobalt to-cobalt-600" },
                { id: "x" as Platform, name: "X", color: "from-slate-800 to-slate-900" },
                { id: "reddit" as Platform, name: "Reddit", color: "from-gold-intense to-gold" },
                { id: "tumblr" as Platform, name: "Tumblr", color: "from-cobalt to-royal" },
                { id: "wordpress" as Platform, name: "WordPress", color: "from-slate-700 to-slate-900" },
              ].map((platform) => (
                <button
                  key={platform.id}
                  onClick={() => setStudioPlatform(platform.id)}
                  className={`px-3 sm:px-4 py-2 sm:py-3 font-semibold whitespace-nowrap transition text-xs sm:text-sm ${
                    studioPlatform === platform.id
                      ? `text-white border-b-2 border-gold bg-gradient-to-r ${platform.color} bg-clip-text text-transparent`
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {platform.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-4 sm:py-6 md:py-8">
        {activeTab === "create" && mode === "quick" && (
          <div className="grid grid-cols-1 lg:grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
            <div className="lg:col-span-2 space-y-2 sm:space-y-3 md:space-y-4 lg:space-y-6">
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Post Type</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <button onClick={() => setPostType("text")} className={`py-3 rounded-lg font-semibold transition ${postType === "text" ? "bg-gradient-to-r from-gold to-gold-intense text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Text Post</button>
                  <button onClick={() => setPostType("image")} className={`py-3 rounded-lg font-semibold transition ${postType === "image" ? "bg-gradient-to-r from-cobalt-600 to-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Image Post</button>
                  <button onClick={() => setPostType("video")} className={`py-3 rounded-lg font-semibold transition ${postType === "video" ? "bg-gradient-to-r from-red-500 to-red-600 text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Video Post</button>
                  <button onClick={() => setPostType("carousel")} className={`py-3 rounded-lg font-semibold transition ${postType === "carousel" ? "bg-gradient-to-r from-cobalt to-gold-intense text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>Carousel</button>
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Caption</h2>
                
                {/* AI Caption Generator */}
                <div className="mb-3 flex gap-2">
                  <input
                    type="text"
                    value={captionPrompt}
                    onChange={(e) => setCaptionPrompt(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && generateCaption()}
                    placeholder="Describe what you want the caption about... (e.g. 'Promote videography for weddings')"
                    className="flex-1 px-3 sm:px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
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
                    className="px-6 py-2 bg-gradient-to-r from-gold-intense to-red-500 hover:from-gold-intense hover:to-red-600 rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                  >
                    {loadingTrends ? "Searching..." : "Trends"}
                  </button>
                </div>

                {/* Trending Topics Display */}
                {showTrends && trends && (
                  <div className="mb-4 p-3 sm:p-4 bg-gradient-to-br from-gold-intense/30 to-red-900/30 border border-gold-intense/30 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <span></span> Trending Topics in Videography
                      </h3>
                      <button
                        onClick={() => setShowTrends(false)}
                        className="text-gray-400 hover:text-white transition text-base sm:text-lg md:text-xl"
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
                
                <textarea value={caption} onChange={(e) => setCaption(e.target.value)} placeholder="Your AI-generated caption will appear here... Or write your own!" rows={8} className="w-full px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none" />

                {/* Platform-specific character counters */}
                <div className="mt-3 space-y-2">
                  {selectedPlatforms.length === 0 && (
                    <span className="text-sm text-gray-400">{caption.length} characters</span>
                  )}
                  {selectedPlatforms.map((platform) => {
                    const limit = getPlatformCharacterLimit(platform);
                    const isOver = isOverCharacterLimit(caption, platform);

                    if (limit === null) {
                      return (
                        <div key={platform} className="flex items-center justify-between text-sm">
                          <span className="text-gray-400 capitalize">{platform === 'x' ? 'X (Twitter)' : platform}</span>
                          <span className="text-gray-400">{caption.length} characters (no limit)</span>
                        </div>
                      );
                    }

                    return (
                      <div key={platform} className="flex items-center justify-between text-sm">
                        <span className="text-gray-400 capitalize">{platform === 'x' ? 'X (Twitter)' : platform}</span>
                        <span className={isOver ? "text-red-400 font-semibold" : "text-gray-400"}>
                          {caption.length} / {limit} {isOver && '- Over limit'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Media</h2>
                <div onClick={() => { 
                  loadMediaLibrary(); 
                  loadDriveFolders();
                  setShowMediaLibrary(true); 
                }} className="border-2 border-dashed border-white/20 rounded-lg p-6 sm:p-8 md:p-12 text-center hover:border-cobalt/50 transition cursor-pointer">
                  <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
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
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                                <div className="text-center p-3 sm:p-4">
                                  <span className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl mb-2 block"></span>
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
                                        <div class="text-center p-3 sm:p-4">
                                          <span class="text-2xl sm:text-xl sm:text-base sm:text-lg md:text-xl lg:text-2xl md:text-3xl md:text-4xl mb-2 block"></span>
                                          <p class="text-xs text-gray-400">Media ${idx + 1}</p>
                                        </div>
                                      `;
                                    }
                                  }}
                                />
                              ) : (
                                <div className="text-center p-3 sm:p-4">
                                  <span className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl mb-2 block"></span>
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

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Schedule</h2>
                <div className="flex gap-2 sm:gap-3 md:gap-4">
                  <input type="datetime-local" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} className="flex-1 px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt" />
                  <button onClick={publishToSocial} disabled={publishing} className="px-6 py-3 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense rounded-lg text-white font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed">{publishing ? "Publishing..." : "Post Now"}</button>
                  
                  {publishMessage && (
                    <div className={`mt-4 p-3 sm:p-4 rounded-lg ${
                      publishMessage.includes("") ? "bg-gold/20 border border-gold" : 
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

            <div className="space-y-2 sm:space-y-3 md:space-y-4 lg:space-y-6">
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Platforms</h2>
                <div className="space-y-3">
                  {platforms.map((platform) => {
                    const isCompatible = isPlatformCompatible(platform.id, postType);
                    const incompatibilityReason = getIncompatibilityReason(platform.id, postType);
                    const isSelected = selectedPlatforms.includes(platform.id);

                    return (
                      <div key={platform.id} className="relative group">
                        <button
                          onClick={() => togglePlatform(platform.id)}
                          disabled={!isCompatible}
                          className={`w-full p-3 sm:p-4 rounded-lg border-2 transition ${
                            !isCompatible
                              ? "border-white/10 bg-white/5 text-gray-600 opacity-50 cursor-not-allowed"
                              : isSelected
                              ? `border-transparent bg-gradient-to-r ${platform.color} text-white`
                              : "border-white/20 bg-white/5 text-gray-400 hover:border-white/40"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <span className="font-semibold text-sm sm:text-base">{platform.name}</span>
                            </div>
                            {isSelected && (
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                        </button>

                        {!isCompatible && incompatibilityReason && (
                          <div className="hidden group-hover:block absolute z-10 left-0 right-0 top-full mt-2 p-2 sm:p-3 bg-slate-900 border border-white/20 rounded-lg shadow-xl">
                            <p className="text-xs sm:text-sm text-gray-300">{incompatibilityReason}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Preview</h2>

                {selectedPlatforms.length === 0 ? (
                  <div className="bg-white rounded-lg p-3 sm:p-4 aspect-square flex items-center justify-center">
                    <p className="text-gray-400 text-center">Select platforms to see preview</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {selectedPlatforms.map((platform) => (
                      <div key={platform} className="bg-white rounded-lg overflow-hidden">
                        {/* Platform-specific preview cards */}
                        {platform === 'instagram' && (
                          <div className="p-4">
                            {/* Instagram header */}
                            <div className="flex items-center gap-3 mb-3">
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-intense to-cobalt"></div>
                            </div>

                            {/* Media preview */}
                            {selectedMedia.length > 0 && (
                              <div className="mb-3 -mx-4">
                                <img
                                  src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                  alt="Post preview"
                                  className="w-full aspect-square object-cover"
                                />
                                {selectedMedia.length > 1 && (
                                  <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                                    1/{selectedMedia.length}
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Instagram caption */}
                            {caption && (
                              <div className="text-sm text-gray-900 whitespace-pre-wrap">
                                {caption.length > 125 ? caption.substring(0, 125) + '... more' : caption}
                              </div>
                            )}
                          </div>
                        )}

                        {platform === 'linkedin' && (
                          <div className="p-4">
                            {/* LinkedIn header */}
                            <div className="flex items-center gap-3 mb-3">
                              <div className="w-12 h-12 rounded-full bg-cobalt"></div>
                            </div>

                            {/* LinkedIn caption */}
                            {caption && (
                              <div className="text-sm text-gray-900 mb-3 whitespace-pre-wrap">
                                {caption}
                              </div>
                            )}

                            {/* Media preview */}
                            {selectedMedia.length > 0 && (
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Post preview"
                                className="w-full rounded aspect-video object-cover"
                              />
                            )}
                          </div>
                        )}

                        {platform === 'x' && (
                          <div className="p-4">
                            {/* X/Twitter header */}
                            <div className="flex gap-3">
                              <div className="w-12 h-12 rounded-full bg-slate-800"></div>
                              <div className="flex-1">
                                {/* Tweet text */}
                                {caption && (
                                  <div className="text-sm text-gray-900 mb-3 whitespace-pre-wrap">
                                    {caption}
                                  </div>
                                )}

                                {/* Media preview */}
                                {selectedMedia.length > 0 && (
                                  <div className="grid grid-cols-2 gap-1 rounded-2xl overflow-hidden border border-gray-200">
                                    {selectedMedia.slice(0, 4).map((media, idx) => (
                                      <img
                                        key={idx}
                                        src={media.url || media.thumbnail_url}
                                        alt={`Preview ${idx + 1}`}
                                        className="w-full aspect-square object-cover"
                                      />
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}

                        {platform === 'facebook' && (
                          <div className="p-4">
                            {/* Facebook header */}
                            <div className="flex items-center gap-3 mb-3">
                              <div className="w-10 h-10 rounded-full bg-cobalt-600"></div>
                            </div>

                            {/* Facebook caption */}
                            {caption && (
                              <div className="text-sm text-gray-900 mb-3 whitespace-pre-wrap">
                                {caption}
                              </div>
                            )}

                            {/* Media preview */}
                            {selectedMedia.length > 0 && (
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Post preview"
                                className="w-full -mx-4 mb-2"
                              />
                            )}
                          </div>
                        )}

                        {/* Generic preview for other platforms */}
                        {!['instagram', 'linkedin', 'x', 'facebook'].includes(platform) && (
                          <div className="p-4">
                            <div className="flex items-center gap-3 mb-3">
                              <div className="w-10 h-10 rounded-full bg-gray-300"></div>
                              <div>
                                <p className="font-semibold text-gray-900 text-sm capitalize">{platform}</p>
                                <p className="text-xs text-gray-500">Preview</p>
                              </div>
                            </div>

                            <div className="text-sm text-gray-900 mb-3 whitespace-pre-wrap">
                              {caption}
                            </div>

                            {selectedMedia.length > 0 && (
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Post preview"
                                className="w-full rounded"
                              />
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* STUDIO MODE CONTENT */}
        {activeTab === "create" && mode === "studio" && (
          <div>
            {/* Instagram Studio */}
            {studioPlatform === "instagram" && (
              <div className="space-y-4 sm:space-y-6">
                {/* Instagram Post Type Selector */}
                <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                  <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">Instagram Post Type</h2>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <button
                      onClick={() => setInstagramPostType("feed")}
                      className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                        instagramPostType === "feed"
                          ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                          : "bg-white/10 text-gray-400 hover:bg-white/20"
                      }`}
                    >
                      Feed Post
                    </button>
                    <button
                      onClick={() => setInstagramPostType("carousel")}
                      className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                        instagramPostType === "carousel"
                          ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                          : "bg-white/10 text-gray-400 hover:bg-white/20"
                      }`}
                    >
                      Carousel
                    </button>
                    <button
                      onClick={() => setInstagramPostType("reel")}
                      className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                        instagramPostType === "reel"
                          ? "bg-gradient-to-r from-cobalt-600 to-cobalt text-white"
                          : "bg-white/10 text-gray-400 hover:bg-white/20"
                      }`}
                    >
                      Reel
                    </button>
                    <button
                      onClick={() => setInstagramPostType("story")}
                      className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                        instagramPostType === "story"
                          ? "bg-gradient-to-r from-royal to-cobalt text-white"
                          : "bg-white/10 text-gray-400 hover:bg-white/20"
                      }`}
                    >
                      Story
                    </button>
                  </div>
                </div>

                {/* Instagram Feed Post Composer */}
                {instagramPostType === "feed" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {/* Compose Column */}
                    <div className="space-y-4 sm:space-y-6">
                      {/* Media Upload */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Media</h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Selected"
                                className="w-full aspect-square object-cover rounded-lg"
                              />
                              <p className="text-sm text-gray-400">Click to change media</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Click to select media</p>
                            </div>
                          )}
                        </div>

                        {/* Aspect Ratio Selector */}
                        <div className="mt-4">
                          <label className="block text-sm font-medium text-gray-300 mb-2">Aspect Ratio</label>
                          <div className="grid grid-cols-3 gap-2">
                            <button className="py-2 px-3 text-xs bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                              Square 1:1
                            </button>
                            <button className="py-2 px-3 text-xs bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                              Portrait 4:5
                            </button>
                            <button className="py-2 px-3 text-xs bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                              Landscape 16:9
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Caption */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Caption</h3>
                        <textarea
                          value={caption}
                          onChange={(e) => setCaption(e.target.value)}
                          placeholder="Write your Instagram caption..."
                          rows={6}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                        />
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-sm text-gray-400">{caption.length} / 2,200</span>
                          {caption.length > 2200 && (
                            <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                          )}
                        </div>
                      </div>

                      {/* Instagram-specific Options */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Options</h3>
                        <div className="space-y-3">
                          <button className="w-full py-2 px-4 text-left text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                            Add Location
                          </button>
                          <button className="w-full py-2 px-4 text-left text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                            Add Alt Text
                          </button>
                          <button className="w-full py-2 px-4 text-left text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                            Tag Products
                          </button>
                        </div>
                      </div>

                      {/* Publish Button */}
                      <button
                        onClick={publishToSocial}
                        disabled={publishing || !caption.trim() || selectedMedia.length === 0}
                        className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {publishing ? "Publishing..." : "Post to Instagram"}
                      </button>
                    </div>

                    {/* Preview Column */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>
                      <div className="bg-white rounded-lg overflow-hidden max-w-sm mx-auto">
                        <div className="p-4">
                          {/* Instagram header */}
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-intense to-cobalt"></div>
                          </div>

                          {/* Media preview */}
                          {selectedMedia.length > 0 ? (
                            <div className="mb-3 -mx-4">
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Post preview"
                                className="w-full aspect-square object-cover"
                              />
                            </div>
                          ) : (
                            <div className="mb-3 -mx-4 bg-gray-200 aspect-square flex items-center justify-center">
                              <p className="text-gray-400 text-sm">No media selected</p>
                            </div>
                          )}

                          {/* Instagram caption */}
                          {caption && (
                            <div className="text-sm text-gray-900 whitespace-pre-wrap">
                              {caption.length > 125 ? caption.substring(0, 125) + "... more" : caption}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Instagram Carousel Composer */}
                {instagramPostType === "carousel" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {/* Compose Column */}
                    <div className="space-y-4 sm:space-y-6">
                      {/* Multi-Media Upload */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Media (2-10 images)</h3>

                        {/* Selected Media Grid */}
                        {selectedMedia.length > 0 && (
                          <div className="grid grid-cols-3 gap-2 mb-4">
                            {selectedMedia.map((media, index) => (
                              <div key={index} className="relative group">
                                <img
                                  src={media.url || media.thumbnail_url}
                                  alt={`Slide ${index + 1}`}
                                  className="w-full aspect-square object-cover rounded-lg"
                                />
                                <div className="absolute top-1 left-1 bg-black/70 text-white text-xs px-2 py-1 rounded">
                                  {index + 1}
                                </div>
                                <button
                                  onClick={() => setSelectedMedia(selectedMedia.filter((_, i) => i !== index))}
                                  className="absolute top-1 right-1 bg-red-600 text-white text-xs w-6 h-6 rounded-full opacity-0 group-hover:opacity-100 transition"
                                >
                                  ×
                                </button>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Add More Button */}
                        {selectedMedia.length < 10 && (
                          <div
                            onClick={() => setShowMediaLibrary(true)}
                            className="border-2 border-dashed border-white/20 rounded-lg p-6 text-center cursor-pointer hover:border-cobalt transition"
                          >
                            <div className="text-3xl text-gray-400">+</div>
                            <p className="text-sm text-gray-400 mt-2">
                              {selectedMedia.length === 0 ? 'Select 2-10 images' : `Add more (${selectedMedia.length}/10)`}
                            </p>
                          </div>
                        )}

                        {selectedMedia.length === 1 && (
                          <p className="text-sm text-red-400 mt-2">Carousel requires at least 2 images</p>
                        )}
                      </div>

                      {/* Caption */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Caption</h3>
                        <textarea
                          value={caption}
                          onChange={(e) => setCaption(e.target.value)}
                          placeholder="Write your Instagram carousel caption..."
                          rows={6}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                        />
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-sm text-gray-400">{caption.length} / 2,200</span>
                          {caption.length > 2200 && (
                            <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                          )}
                        </div>
                      </div>

                      {/* Instagram-specific Options */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Options</h3>
                        <div className="space-y-3">
                          <button className="w-full py-2 px-4 text-left text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                            Add Location
                          </button>
                          <button className="w-full py-2 px-4 text-left text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                            Add Alt Text for each image
                          </button>
                        </div>
                      </div>

                      {/* Publish Button */}
                      <button
                        onClick={publishToSocial}
                        disabled={publishing || !caption.trim() || selectedMedia.length < 2 || selectedMedia.length > 10}
                        className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {publishing ? "Publishing..." : "Post Carousel to Instagram"}
                      </button>
                    </div>

                    {/* Preview Column */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>
                      <div className="bg-white rounded-lg overflow-hidden max-w-sm mx-auto">
                        <div className="p-4">
                          {/* Instagram header */}
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-intense to-cobalt"></div>
                          </div>

                          {/* Carousel Media Preview */}
                          {selectedMedia.length > 0 ? (
                            <div className="mb-3 -mx-4 relative">
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Carousel preview"
                                className="w-full aspect-square object-cover"
                              />
                              {selectedMedia.length > 1 && (
                                <div className="absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-1 rounded">
                                  1/{selectedMedia.length}
                                </div>
                              )}
                              {/* Carousel dots */}
                              <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-1">
                                {selectedMedia.map((_, index) => (
                                  <div
                                    key={index}
                                    className={`w-1.5 h-1.5 rounded-full ${index === 0 ? 'bg-cobalt' : 'bg-white/50'}`}
                                  />
                                ))}
                              </div>
                            </div>
                          ) : (
                            <div className="mb-3 -mx-4 bg-gray-200 aspect-square flex items-center justify-center">
                              <p className="text-gray-400 text-sm">Select 2-10 images</p>
                            </div>
                          )}

                          {/* Instagram caption */}
                          {caption && (
                            <div className="text-sm text-gray-900 whitespace-pre-wrap">
                              {caption.length > 125 ? caption.substring(0, 125) + "... more" : caption}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Instagram Reels Composer */}
                {instagramPostType === "reel" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {/* Compose Column */}
                    <div className="space-y-4 sm:space-y-6">
                      {/* Video Upload */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Video</h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                            <div className="space-y-3">
                              <video
                                src={selectedMedia[0].url}
                                className="w-full aspect-[9/16] object-cover rounded-lg mx-auto max-h-96"
                                controls
                              />
                              <p className="text-sm text-gray-400">Click to change video</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select vertical video (9:16)</p>
                              <p className="text-xs text-gray-500">15-90 seconds recommended</p>
                            </div>
                          )}
                        </div>

                        {/* Video Requirements */}
                        <div className="mt-4 p-3 bg-cobalt/10 border border-cobalt/20 rounded-lg">
                          <p className="text-xs text-gray-300">
                            <span className="font-semibold">Requirements:</span> Vertical (9:16), 15-90 seconds
                          </p>
                        </div>
                      </div>

                      {/* Cover Image Selector */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Cover Image</h3>
                        <p className="text-sm text-gray-400 mb-3">Select a frame from your video as the cover</p>
                        <button className="w-full py-3 px-4 text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition">
                          Choose from Video
                        </button>
                      </div>

                      {/* Caption */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Caption</h3>
                        <textarea
                          value={caption}
                          onChange={(e) => setCaption(e.target.value)}
                          placeholder="Write your Reel caption..."
                          rows={5}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                        />
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-sm text-gray-400">{caption.length} / 2,200</span>
                          {caption.length > 2200 && (
                            <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                          )}
                        </div>
                      </div>

                      {/* Reels Options */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Options</h3>
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={shareToFeed}
                            onChange={(e) => setShareToFeed(e.target.checked)}
                            className="w-4 h-4 text-cobalt bg-white/10 border-white/20 rounded focus:ring-cobalt"
                          />
                          <span className="text-sm text-gray-300">Share to Feed</span>
                        </label>
                      </div>

                      {/* Publish Button */}
                      <button
                        onClick={publishToSocial}
                        disabled={publishing || !caption.trim() || selectedMedia.length === 0 || !selectedMedia[0].content_type?.includes('video')}
                        className="w-full py-4 bg-gradient-to-r from-cobalt-600 to-cobalt text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {publishing ? "Publishing..." : "Post Reel to Instagram"}
                      </button>
                    </div>

                    {/* Preview Column */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>
                      <div className="bg-black rounded-lg overflow-hidden max-w-xs mx-auto aspect-[9/16]">
                        {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                          <div className="relative h-full">
                            <video
                              src={selectedMedia[0].url}
                              className="w-full h-full object-cover"
                              muted
                              loop
                            />
                            {/* Reels UI Overlay */}
                            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                              <div className="flex items-center gap-2 mb-2">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-intense to-cobalt"></div>
                              </div>
                              {caption && (
                                <p className="text-white text-sm line-clamp-2">
                                  {caption}
                                </p>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="h-full flex items-center justify-center bg-gray-900">
                            <p className="text-gray-400 text-sm px-4 text-center">Select a vertical video</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Instagram Stories Composer */}
                {instagramPostType === "story" && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                    {/* Compose Column */}
                    <div className="space-y-4 sm:space-y-6">
                      {/* Media Upload */}
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Story Media</h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              {selectedMedia[0].content_type?.includes('video') ? (
                                <video
                                  src={selectedMedia[0].url}
                                  className="w-full aspect-[9/16] object-cover rounded-lg mx-auto max-h-96"
                                  controls
                                />
                              ) : (
                                <img
                                  src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                  alt="Story"
                                  className="w-full aspect-[9/16] object-cover rounded-lg mx-auto max-h-96"
                                />
                              )}
                              <p className="text-sm text-gray-400">Click to change media</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select vertical media (9:16)</p>
                              <p className="text-xs text-gray-500">Image or video</p>
                            </div>
                          )}
                        </div>

                        {/* Story Requirements */}
                        <div className="mt-4 p-3 bg-royal/10 border border-royal/20 rounded-lg">
                          <p className="text-xs text-gray-300">
                            <span className="font-semibold">Note:</span> Stories expire after 24 hours
                          </p>
                        </div>
                      </div>

                      {/* Publish Button */}
                      <button
                        onClick={publishToSocial}
                        disabled={publishing || selectedMedia.length === 0}
                        className="w-full py-4 bg-gradient-to-r from-royal to-cobalt text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {publishing ? "Publishing..." : "Post Story to Instagram"}
                      </button>

                      {/* 24h Expiry Notice */}
                      <div className="bg-royal/10 border border-royal/20 rounded-lg p-4">
                        <p className="text-sm text-gray-300 text-center">
                          Stories will be visible for 24 hours
                        </p>
                      </div>
                    </div>

                    {/* Preview Column */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>
                      <div className="bg-black rounded-lg overflow-hidden max-w-xs mx-auto aspect-[9/16]">
                        {selectedMedia.length > 0 ? (
                          <div className="relative h-full">
                            {selectedMedia[0].content_type?.includes('video') ? (
                              <video
                                src={selectedMedia[0].url}
                                className="w-full h-full object-cover"
                                muted
                                loop
                              />
                            ) : (
                              <img
                                src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                alt="Story preview"
                                className="w-full h-full object-cover"
                              />
                            )}

                            {/* Story UI Overlay */}
                            <div className="absolute top-0 left-0 right-0 p-4">
                              <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-intense to-cobalt border-2 border-white"></div>
                                <span className="text-white/70 text-xs">now</span>
                              </div>
                            </div>

                            {/* Text Overlay */}
                            {caption && (
                              <div className="absolute inset-0 flex items-center justify-center p-8">
                                <p className="text-white text-2xl font-bold text-center drop-shadow-lg">
                                  {caption}
                                </p>
                              </div>
                            )}

                            {/* 24h Timer */}
                            <div className="absolute top-4 left-4 right-4 h-1 bg-white/30 rounded-full">
                              <div className="h-full w-1/3 bg-white rounded-full"></div>
                            </div>
                          </div>
                        ) : (
                          <div className="h-full flex items-center justify-center bg-gray-900">
                            <p className="text-gray-400 text-sm px-4 text-center">Select vertical media for your story</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* YouTube Studio */}
            {studioPlatform === "youtube" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Video Upload */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Video</h3>
                      <div
                        onClick={() => setShowMediaLibrary(true)}
                        className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                      >
                        {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                          <div className="space-y-3">
                            <video
                              src={selectedMedia[0].url}
                              className="w-full aspect-video object-cover rounded-lg mx-auto"
                              controls
                            />
                            <p className="text-sm text-gray-400">Click to change video</p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="text-4xl text-gray-400">+</div>
                            <p className="text-sm text-gray-400">Select video from library</p>
                            <p className="text-xs text-gray-500">MP4, MOV, AVI supported</p>
                          </div>
                        )}
                      </div>

                      {/* Video Type Toggle */}
                      <div className="mt-4 p-3 bg-cobalt/10 border border-cobalt/20 rounded-lg">
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={isShort}
                            onChange={(e) => setIsShort(e.target.checked)}
                            className="w-4 h-4 text-cobalt bg-white/10 border-white/20 rounded focus:ring-cobalt"
                          />
                          <span className="text-sm text-gray-300">YouTube Short (vertical video, under 60s)</span>
                        </label>
                      </div>
                    </div>

                    {/* Title */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Title</h3>
                      <input
                        type="text"
                        value={youtubeTitle}
                        onChange={(e) => setYoutubeTitle(e.target.value)}
                        placeholder="Enter video title..."
                        maxLength={100}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{youtubeTitle.length} / 100</span>
                        {youtubeTitle.length > 100 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                    </div>

                    {/* Description */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Description</h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder="Tell viewers about your video..."
                        rows={6}
                        maxLength={5000}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{caption.length} / 5,000</span>
                        {caption.length > 5000 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                    </div>

                    {/* Thumbnail Upload */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Custom Thumbnail (Optional)</h3>
                      <button
                        onClick={() => setShowMediaLibrary(true)}
                        className="w-full py-3 px-4 text-sm bg-white/10 hover:bg-white/20 text-gray-300 rounded-lg transition"
                      >
                        {youtubeThumbnail ? "Change Thumbnail" : "Upload Thumbnail"}
                      </button>
                      <p className="text-xs text-gray-400 mt-2">1280x720px recommended (16:9 ratio)</p>
                    </div>

                    {/* Privacy & Category */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Settings</h3>

                      {/* Privacy */}
                      <div className="mb-4">
                        <label className="block text-sm text-gray-300 mb-2">Privacy</label>
                        <select
                          value={youtubePrivacy}
                          onChange={(e) => setYoutubePrivacy(e.target.value as "public" | "private" | "unlisted")}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                        >
                          <option value="private">Private</option>
                          <option value="unlisted">Unlisted</option>
                          <option value="public">Public</option>
                        </select>
                      </div>

                      {/* Category */}
                      <div>
                        <label className="block text-sm text-gray-300 mb-2">Category</label>
                        <select
                          value={youtubeCategory}
                          onChange={(e) => setYoutubeCategory(e.target.value)}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                        >
                          <option value="22">People & Blogs</option>
                          <option value="1">Film & Animation</option>
                          <option value="2">Autos & Vehicles</option>
                          <option value="10">Music</option>
                          <option value="15">Pets & Animals</option>
                          <option value="17">Sports</option>
                          <option value="19">Travel & Events</option>
                          <option value="20">Gaming</option>
                          <option value="23">Comedy</option>
                          <option value="24">Entertainment</option>
                          <option value="25">News & Politics</option>
                          <option value="26">Howto & Style</option>
                          <option value="27">Education</option>
                          <option value="28">Science & Technology</option>
                        </select>
                      </div>
                    </div>

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || !youtubeTitle.trim() || selectedMedia.length === 0 || !selectedMedia[0].content_type?.includes('video')}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Uploading..." : `Upload ${isShort ? "Short" : "Video"} to YouTube`}
                    </button>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* Video Preview */}
                    <div className="bg-black rounded-lg overflow-hidden mb-4">
                      {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                        <video
                          src={selectedMedia[0].url}
                          className={`w-full object-cover ${isShort ? 'aspect-[9/16] max-h-[600px]' : 'aspect-video'}`}
                          controls
                        />
                      ) : (
                        <div className={`w-full ${isShort ? 'aspect-[9/16] max-h-[600px]' : 'aspect-video'} bg-gray-900 flex items-center justify-center`}>
                          <p className="text-gray-400 text-sm px-4 text-center">Upload a video to see preview</p>
                        </div>
                      )}
                    </div>

                    {/* Video Details Preview */}
                    <div className="space-y-3">
                      <h4 className="font-bold text-white text-base">
                        {youtubeTitle || "Video Title"}
                      </h4>
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <span>{youtubePrivacy === "public" ? "Public" : youtubePrivacy === "unlisted" ? "Unlisted" : "Private"}</span>
                        <span>•</span>
                        <span>{isShort ? "Short" : "Video"}</span>
                      </div>
                      {caption && (
                        <p className="text-sm text-gray-300 line-clamp-3">{caption}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Facebook Studio */}
            {studioPlatform === "facebook" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Post Type Selector */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Post Type</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {[
                          { id: "text" as const, label: "Text" },
                          { id: "link" as const, label: "Link" },
                          { id: "photo" as const, label: "Photo" },
                          { id: "video" as const, label: "Video" },
                          { id: "album" as const, label: "Album" },
                        ].map((type) => (
                          <button
                            key={type.id}
                            onClick={() => setFacebookPostType(type.id)}
                            className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                              facebookPostType === type.id
                                ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                                : "bg-white/10 text-gray-400 hover:bg-white/20"
                            }`}
                          >
                            {type.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Caption/Message */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                        {facebookPostType === "link" ? "Message" : "Caption"}
                      </h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder="What's on your mind?"
                        rows={6}
                        maxLength={63206}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{caption.length.toLocaleString()} / 63,206</span>
                        {caption.length > 63206 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                    </div>

                    {/* Link URL (for link posts) */}
                    {facebookPostType === "link" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Link URL</h3>
                        <input
                          type="url"
                          value={facebookLinkUrl}
                          onChange={(e) => setFacebookLinkUrl(e.target.value)}
                          placeholder="https://example.com"
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt"
                        />
                        <p className="text-xs text-gray-400 mt-2">Facebook will automatically generate a preview</p>
                      </div>
                    )}

                    {/* Media Upload (for photo/video/album) */}
                    {(facebookPostType === "photo" || facebookPostType === "video" || facebookPostType === "album") && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                          {facebookPostType === "photo" && "Photo"}
                          {facebookPostType === "video" && "Video"}
                          {facebookPostType === "album" && "Photos"}
                        </h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              {facebookPostType === "video" && selectedMedia[0].content_type?.includes('video') ? (
                                <video
                                  src={selectedMedia[0].url}
                                  className="w-full aspect-video object-cover rounded-lg mx-auto"
                                  controls
                                />
                              ) : facebookPostType === "album" ? (
                                <div className="grid grid-cols-3 gap-2">
                                  {selectedMedia.slice(0, 6).map((media, idx) => (
                                    <img
                                      key={idx}
                                      src={media.url || media.thumbnail_url}
                                      alt={`Photo ${idx + 1}`}
                                      className="w-full aspect-square object-cover rounded-lg"
                                    />
                                  ))}
                                  {selectedMedia.length > 6 && (
                                    <div className="w-full aspect-square bg-white/10 rounded-lg flex items-center justify-center text-white font-bold">
                                      +{selectedMedia.length - 6}
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <img
                                  src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                                  alt="Preview"
                                  className="w-full aspect-video object-cover rounded-lg mx-auto"
                                />
                              )}
                              <p className="text-sm text-gray-400">
                                {facebookPostType === "album"
                                  ? `${selectedMedia.length} photo${selectedMedia.length > 1 ? 's' : ''} selected`
                                  : "Click to change"}
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">
                                {facebookPostType === "album" ? "Select photos from library (2-50)" : "Select from library"}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || !caption.trim()}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Publishing..." : "Post to Facebook"}
                    </button>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* Facebook Post Preview */}
                    <div className="bg-white rounded-lg overflow-hidden">
                      {/* Post Header */}
                      <div className="p-4 border-b border-gray-200">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cobalt to-royal"></div>
                        </div>
                      </div>

                      {/* Post Content */}
                      <div className="p-4">
                        {caption && (
                          <p className="text-gray-900 text-sm mb-3 whitespace-pre-wrap">{caption}</p>
                        )}
                      </div>

                      {/* Media Preview */}
                      {facebookPostType === "link" && facebookLinkUrl && (
                        <div className="border-t border-gray-200">
                          <div className="aspect-video bg-gray-100 flex items-center justify-center">
                            <span className="text-gray-400 text-sm">Link Preview</span>
                          </div>
                          <div className="p-3 bg-gray-50 border-t border-gray-200">
                            <p className="text-xs text-gray-500 uppercase">
                              {new URL(facebookLinkUrl).hostname}
                            </p>
                            <p className="text-sm font-semibold text-gray-900 truncate">{facebookLinkUrl}</p>
                          </div>
                        </div>
                      )}

                      {facebookPostType === "photo" && selectedMedia.length > 0 && (
                        <img
                          src={selectedMedia[0].url || selectedMedia[0].thumbnail_url}
                          alt="Preview"
                          className="w-full aspect-square object-cover"
                        />
                      )}

                      {facebookPostType === "video" && selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') && (
                        <video
                          src={selectedMedia[0].url}
                          className="w-full aspect-video object-cover"
                          controls
                        />
                      )}

                      {facebookPostType === "album" && selectedMedia.length > 0 && (
                        <div className="grid grid-cols-2 gap-0.5">
                          {selectedMedia.slice(0, 4).map((media, idx) => (
                            <img
                              key={idx}
                              src={media.url || media.thumbnail_url}
                              alt={`Photo ${idx + 1}`}
                              className="w-full aspect-square object-cover"
                            />
                          ))}
                        </div>
                      )}

                      {/* Post Actions */}
                      <div className="border-t border-gray-200 p-3 flex justify-around text-gray-600 text-sm font-semibold">
                        <button className="hover:bg-gray-100 px-4 py-2 rounded">Like</button>
                        <button className="hover:bg-gray-100 px-4 py-2 rounded">Comment</button>
                        <button className="hover:bg-gray-100 px-4 py-2 rounded">Share</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TikTok Studio */}
            {studioPlatform === "tiktok" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:space-y-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Video Upload */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Video</h3>
                      <div
                        onClick={() => setShowMediaLibrary(true)}
                        className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                      >
                        {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                          <div className="space-y-3">
                            <video
                              src={selectedMedia[0].url}
                              className="w-full max-w-xs mx-auto aspect-[9/16] object-cover rounded-lg"
                              controls
                            />
                            <p className="text-sm text-gray-400">Click to change video</p>
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="text-4xl text-gray-400">+</div>
                            <p className="text-sm text-gray-400">Select vertical video from library</p>
                            <p className="text-xs text-gray-500">9:16 aspect ratio recommended</p>
                            <p className="text-xs text-gray-500">Max 60 seconds</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Caption */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Caption</h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder="Describe your video..."
                        rows={6}
                        maxLength={2200}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{caption.length} / 2,200</span>
                        {caption.length > 2200 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-2">Add hashtags to increase discoverability</p>
                    </div>

                    {/* Privacy Settings */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Privacy</h3>
                      <select
                        value={tiktokPrivacy}
                        onChange={(e) => setTiktokPrivacy(e.target.value as typeof tiktokPrivacy)}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-cobalt"
                      >
                        <option value="SELF_ONLY">Private (Only You)</option>
                        <option value="MUTUAL_FOLLOW_FRIENDS">Friends</option>
                        <option value="PUBLIC_TO_EVERYONE">Public (Everyone)</option>
                      </select>
                    </div>

                    {/* Permissions */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Permissions</h3>
                      <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={disableDuet}
                            onChange={(e) => setDisableDuet(e.target.checked)}
                            className="w-4 h-4 text-cobalt bg-white/10 border-white/20 rounded focus:ring-cobalt"
                          />
                          <div>
                            <span className="text-sm text-gray-300 block">Disable Duet</span>
                            <span className="text-xs text-gray-500">Others can't create duets with your video</span>
                          </div>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={disableStitch}
                            onChange={(e) => setDisableStitch(e.target.checked)}
                            className="w-4 h-4 text-cobalt bg-white/10 border-white/20 rounded focus:ring-cobalt"
                          />
                          <div>
                            <span className="text-sm text-gray-300 block">Disable Stitch</span>
                            <span className="text-xs text-gray-500">Others can't stitch your video</span>
                          </div>
                        </label>
                        <label className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={disableComment}
                            onChange={(e) => setDisableComment(e.target.checked)}
                            className="w-4 h-4 text-cobalt bg-white/10 border-white/20 rounded focus:ring-cobalt"
                          />
                          <div>
                            <span className="text-sm text-gray-300 block">Disable Comments</span>
                            <span className="text-xs text-gray-500">Turn off comments for this video</span>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || selectedMedia.length === 0 || !selectedMedia[0].content_type?.includes('video')}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Uploading..." : "Post to TikTok"}
                    </button>

                    {/* Processing Notice */}
                    <div className="bg-cobalt/10 border border-cobalt/20 rounded-lg p-4">
                      <p className="text-sm text-gray-300 text-center">
                        TikTok videos may take a few minutes to process after upload
                      </p>
                    </div>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* TikTok-style Preview */}
                    <div className="bg-black rounded-lg overflow-hidden max-w-xs mx-auto">
                      {selectedMedia.length > 0 && selectedMedia[0].content_type?.includes('video') ? (
                        <div className="relative aspect-[9/16]">
                          <video
                            src={selectedMedia[0].url}
                            className="w-full h-full object-cover"
                            muted
                            loop
                          />

                          {/* TikTok UI Overlay */}
                          <div className="absolute inset-0 pointer-events-none">
                            {/* Caption Overlay */}
                            {caption && (
                              <div className="absolute bottom-20 left-4 right-16 text-white">
                                <p className="text-sm">{caption.slice(0, 100)}{caption.length > 100 ? '...' : ''}</p>
                              </div>
                            )}

                            {/* Right Side Actions */}
                            <div className="absolute bottom-20 right-2 space-y-6">
                              <div className="text-center">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cobalt to-royal border-2 border-white mb-1"></div>
                              </div>
                              <div className="text-center">
                                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center mb-1">
                                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                  </svg>
                                </div>
                              </div>
                              <div className="text-center">
                                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center mb-1">
                                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                  </svg>
                                </div>
                                {disableComment && <p className="text-white text-xs">Off</p>}
                              </div>
                              <div className="text-center">
                                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center mb-1">
                                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                                  </svg>
                                </div>
                              </div>
                            </div>

                            {/* Privacy Indicator */}
                            <div className="absolute top-4 right-4">
                              <div className="bg-black/50 px-3 py-1 rounded-full">
                                <span className="text-white text-xs">
                                  {tiktokPrivacy === "PUBLIC_TO_EVERYONE" ? "Public" :
                                   tiktokPrivacy === "MUTUAL_FOLLOW_FRIENDS" ? "Friends" :
                                   "Private"}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="aspect-[9/16] bg-gray-900 flex items-center justify-center">
                          <p className="text-gray-400 text-sm px-4 text-center">Upload a vertical video to see preview</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* LinkedIn Studio */}
            {studioPlatform === "linkedin" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Post Type Selector */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Post Type</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {[
                          { id: "text" as const, label: "Text" },
                          { id: "image" as const, label: "Image" },
                          { id: "video" as const, label: "Video" },
                          { id: "article" as const, label: "Article" },
                        ].map((type) => (
                          <button
                            key={type.id}
                            onClick={() => setLinkedinPostType(type.id)}
                            className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                              linkedinPostType === type.id
                                ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                                : "bg-white/10 text-gray-400 hover:bg-white/20"
                            }`}
                          >
                            {type.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Caption/Post Content */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                        {linkedinPostType === "article" ? "Article Content" : "Post"}
                      </h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder={linkedinPostType === "article" ? "Write your article content..." : "What do you want to talk about?"}
                        rows={8}
                        maxLength={3000}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{caption.length.toLocaleString()} / 3,000</span>
                        {caption.length > 3000 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                    </div>

                    {/* Article Title (for article posts) */}
                    {linkedinPostType === "article" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Article Title</h3>
                        <input
                          type="text"
                          value={articleTitle}
                          onChange={(e) => setArticleTitle(e.target.value)}
                          placeholder="Enter article headline"
                          maxLength={200}
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt"
                        />
                        <p className="text-xs text-gray-400 mt-2">{articleTitle.length} / 200 characters</p>
                      </div>
                    )}

                    {/* Article URL (optional for article posts) */}
                    {linkedinPostType === "article" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Article URL (Optional)</h3>
                        <input
                          type="url"
                          value={articleUrl}
                          onChange={(e) => setArticleUrl(e.target.value)}
                          placeholder="https://example.com/article"
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt"
                        />
                        <p className="text-xs text-gray-400 mt-2">Link to external article (if sharing from blog)</p>
                      </div>
                    )}

                    {/* Media Upload (for image/video posts) */}
                    {(linkedinPostType === "image" || linkedinPostType === "video") && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                          {linkedinPostType === "image" ? "Image" : "Video"}
                        </h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              {linkedinPostType === "image" ? (
                                <img
                                  src={selectedMedia[0].url}
                                  alt="Selected"
                                  className="w-full max-w-sm mx-auto rounded-lg"
                                />
                              ) : (
                                <video
                                  src={selectedMedia[0].url}
                                  className="w-full max-w-sm mx-auto rounded-lg"
                                  controls
                                />
                              )}
                              <p className="text-sm text-gray-400">Click to change {linkedinPostType}</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select {linkedinPostType} from library</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || (linkedinPostType === "article" && !articleTitle.trim())}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Publishing..." : "Post to LinkedIn"}
                    </button>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* LinkedIn-style Preview */}
                    <div className="bg-white rounded-lg overflow-hidden">
                      {/* Profile Header */}
                      <div className="p-4 border-b border-gray-200">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cobalt to-royal"></div>
                        </div>
                      </div>

                      {/* Post Content */}
                      <div className="p-4">
                        {linkedinPostType === "article" && articleTitle && (
                          <h3 className="font-bold text-gray-900 text-lg mb-2">{articleTitle}</h3>
                        )}
                        {caption && (
                          <p className="text-sm text-gray-900 whitespace-pre-wrap mb-3">
                            {caption.slice(0, 200)}{caption.length > 200 ? '...' : ''}
                          </p>
                        )}
                        {caption.length > 200 && (
                          <button className="text-sm text-cobalt font-semibold">...see more</button>
                        )}

                        {/* Media Preview */}
                        {linkedinPostType === "image" && selectedMedia.length > 0 && (
                          <img
                            src={selectedMedia[0].url}
                            alt="Post"
                            className="w-full mt-3 rounded"
                          />
                        )}
                        {linkedinPostType === "video" && selectedMedia.length > 0 && (
                          <video
                            src={selectedMedia[0].url}
                            className="w-full mt-3 rounded"
                            controls
                          />
                        )}
                        {linkedinPostType === "article" && articleUrl && (
                          <div className="mt-3 border border-gray-200 rounded overflow-hidden">
                            <div className="bg-gray-100 h-32 flex items-center justify-center">
                              <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                              </svg>
                            </div>
                            <div className="p-3 bg-gray-50">
                              <p className="text-xs text-gray-600">{articleUrl.replace(/^https?:\/\//, '').split('/')[0]}</p>
                              <p className="text-sm font-semibold text-gray-900 mt-1">{articleTitle || "Article Title"}</p>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Engagement Bar */}
                      <div className="border-t border-gray-200 px-4 py-2">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <button className="flex items-center gap-2 hover:text-cobalt transition">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                            </svg>
                            <span>Like</span>
                          </button>
                          <button className="flex items-center gap-2 hover:text-cobalt transition">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                            </svg>
                            <span>Comment</span>
                          </button>
                          <button className="flex items-center gap-2 hover:text-cobalt transition">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Repost</span>
                          </button>
                          <button className="flex items-center gap-2 hover:text-cobalt transition">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                            </svg>
                            <span>Send</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* X (Twitter) Studio */}
            {studioPlatform === "x" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Post Type Selector */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Post Type</h3>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { id: "text" as const, label: "Text" },
                          { id: "image" as const, label: "Images" },
                          { id: "video" as const, label: "Video" },
                        ].map((type) => (
                          <button
                            key={type.id}
                            onClick={() => setXPostType(type.id)}
                            className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                              xPostType === type.id
                                ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                                : "bg-white/10 text-gray-400 hover:bg-white/20"
                            }`}
                          >
                            {type.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Post Text */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Post</h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder="What is happening?!"
                        rows={6}
                        maxLength={280}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-white resize-none"
                      />
                      <div className="flex items-center justify-between mt-3">
                        <span className="text-sm text-gray-400">{caption.length} / 280</span>
                        {caption.length > 280 && (
                          <span className="text-sm text-red-400 font-semibold">- Over limit</span>
                        )}
                      </div>
                    </div>

                    {/* Media Upload (for image posts) */}
                    {xPostType === "image" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                          Images (Up to 4)
                        </h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              <div className={`grid ${selectedMedia.length === 1 ? 'grid-cols-1' : 'grid-cols-2'} gap-2`}>
                                {selectedMedia.slice(0, 4).map((media, idx) => (
                                  <img
                                    key={idx}
                                    src={media.url}
                                    alt={`Selected ${idx + 1}`}
                                    className="w-full aspect-square object-cover rounded-lg"
                                  />
                                ))}
                              </div>
                              <p className="text-sm text-gray-400">
                                {selectedMedia.length} image{selectedMedia.length !== 1 ? 's' : ''} selected - Click to change
                              </p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select images from library</p>
                              <p className="text-xs text-gray-500">Maximum 4 images</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Video Upload (for video posts) */}
                    {xPostType === "video" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                          Video
                        </h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              <video
                                src={selectedMedia[0].url}
                                className="w-full max-w-sm mx-auto rounded-lg"
                                controls
                              />
                              <p className="text-sm text-gray-400">Click to change video</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select video from library</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || (xPostType === "image" && selectedMedia.length === 0) || (xPostType === "video" && selectedMedia.length === 0)}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Posting..." : "Post to X"}
                    </button>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* X-style Preview */}
                    <div className="bg-black rounded-lg overflow-hidden">
                      <div className="p-4">
                        {/* Profile Header */}
                        <div className="flex gap-3 mb-3">
                          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-white to-gray-400"></div>
                          <div className="flex-1">
                            {/* Post Text */}
                            {caption && (
                              <p className="text-white text-sm mb-3 whitespace-pre-wrap">{caption}</p>
                            )}

                            {/* Media Preview */}
                            {xPostType === "image" && selectedMedia.length > 0 && (
                              <div className={`grid gap-1 rounded-2xl overflow-hidden mb-3 ${
                                selectedMedia.length === 1 ? 'grid-cols-1' :
                                selectedMedia.length === 2 ? 'grid-cols-2' :
                                selectedMedia.length === 3 ? 'grid-cols-2' :
                                'grid-cols-2'
                              }`}>
                                {selectedMedia.slice(0, 4).map((media, idx) => (
                                  <img
                                    key={idx}
                                    src={media.url}
                                    alt={`Post ${idx + 1}`}
                                    className={`w-full ${
                                      selectedMedia.length === 3 && idx === 0 ? 'col-span-2' : ''
                                    } ${
                                      selectedMedia.length === 1 ? 'max-h-96' : 'aspect-square'
                                    } object-cover`}
                                  />
                                ))}
                              </div>
                            )}

                            {xPostType === "video" && selectedMedia.length > 0 && (
                              <video
                                src={selectedMedia[0].url}
                                className="w-full rounded-2xl mb-3"
                                controls
                              />
                            )}

                            {/* Engagement Bar */}
                            <div className="flex items-center justify-between text-gray-500 pt-3 border-t border-gray-800">
                              <button className="w-8 h-8 rounded-full hover:bg-blue-400/10 flex items-center justify-center transition">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                              </button>
                              <button className="w-8 h-8 rounded-full hover:bg-green-400/10 flex items-center justify-center transition">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                              </button>
                              <button className="w-8 h-8 rounded-full hover:bg-red-400/10 flex items-center justify-center transition">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                                </svg>
                              </button>
                              <button className="w-8 h-8 rounded-full hover:bg-blue-400/10 flex items-center justify-center transition">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                              </button>
                              <button className="w-8 h-8 rounded-full hover:bg-blue-400/10 flex items-center justify-center transition">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                                </svg>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Reddit Studio */}
            {studioPlatform === "reddit" && (
              <div className="space-y-4 sm:space-y-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                  {/* Compose Column */}
                  <div className="space-y-4 sm:space-y-6">
                    {/* Post Type Selector */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Post Type</h3>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {[
                          { id: "text" as const, label: "Text" },
                          { id: "link" as const, label: "Link" },
                          { id: "image" as const, label: "Image" },
                          { id: "video" as const, label: "Video" },
                        ].map((type) => (
                          <button
                            key={type.id}
                            onClick={() => setRedditPostType(type.id)}
                            className={`py-3 px-4 rounded-lg font-semibold transition text-sm ${
                              redditPostType === type.id
                                ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                                : "bg-white/10 text-gray-400 hover:bg-white/20"
                            }`}
                          >
                            {type.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Subreddit */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Subreddit</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-400">r/</span>
                        <input
                          type="text"
                          value={redditSubreddit}
                          onChange={(e) => setRedditSubreddit(e.target.value)}
                          placeholder="videography"
                          className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:border-cobalt focus:outline-none"
                        />
                      </div>
                    </div>

                    {/* Post Title */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">Title</h3>
                      <input
                        type="text"
                        value={redditTitle}
                        onChange={(e) => setRedditTitle(e.target.value)}
                        maxLength={300}
                        placeholder="Post title (max 300 characters)"
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:border-cobalt focus:outline-none"
                      />
                      <div className="flex justify-between mt-2">
                        <span className="text-sm text-gray-400">{redditTitle.length} / 300</span>
                        {redditTitle.length > 300 && (
                          <span className="text-sm text-gold-intense">Title too long</span>
                        )}
                      </div>
                    </div>

                    {/* Post Content / Link URL */}
                    {redditPostType === "link" && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">Link URL</h3>
                        <input
                          type="url"
                          value={redditLinkUrl}
                          onChange={(e) => setRedditLinkUrl(e.target.value)}
                          placeholder="https://example.com"
                          className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:border-cobalt focus:outline-none"
                        />
                      </div>
                    )}

                    {/* Caption / Post Body */}
                    <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                      <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                        {redditPostType === "text" ? "Post Text" : "Caption"}
                      </h3>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder={redditPostType === "text" ? "Your post content..." : "Optional caption..."}
                        className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-500 focus:border-cobalt focus:outline-none min-h-[120px]"
                      />
                    </div>

                    {/* Media Selection */}
                    {(redditPostType === "image" || redditPostType === "video") && (
                      <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                        <h3 className="text-base sm:text-lg font-bold text-white mb-4">
                          {redditPostType === "image" ? "Image" : "Video"}
                        </h3>
                        <div
                          onClick={() => setShowMediaLibrary(true)}
                          className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center cursor-pointer hover:border-cobalt transition"
                        >
                          {selectedMedia.length > 0 ? (
                            <div className="space-y-3">
                              {redditPostType === "image" && selectedMedia[0]?.content_type?.includes('image') && (
                                <img
                                  src={selectedMedia[0].url}
                                  alt="Selected"
                                  className="w-full max-h-48 object-cover rounded-lg mx-auto"
                                />
                              )}
                              {redditPostType === "video" && selectedMedia[0]?.content_type?.includes('video') && (
                                <video
                                  src={selectedMedia[0].url}
                                  className="w-full max-h-48 object-cover rounded-lg mx-auto"
                                  controls
                                />
                              )}
                              <p className="text-sm text-gray-400">Click to change</p>
                            </div>
                          ) : (
                            <div className="space-y-3">
                              <div className="text-4xl text-gray-400">+</div>
                              <p className="text-sm text-gray-400">Select from library</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing || !redditSubreddit.trim() || !redditTitle.trim()}
                      className="w-full py-4 bg-gradient-to-r from-gold to-gold-intense text-white font-bold rounded-lg hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {publishing ? "Posting..." : "Post to Reddit"}
                    </button>
                  </div>

                  {/* Preview Column */}
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                    <h3 className="text-base sm:text-lg font-bold text-white mb-4">Preview</h3>

                    {/* Reddit-style Preview */}
                    <div className="bg-white rounded-lg overflow-hidden">
                      <div className="p-4">
                        {/* Upvote Section */}
                        <div className="flex gap-3">
                          <div className="flex flex-col items-center gap-1">
                            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                            <span className="text-sm font-bold text-gray-600">Vote</span>
                            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>

                          <div className="flex-1">
                            {/* Subreddit Header */}
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs font-bold text-gray-900">r/{redditSubreddit || "subreddit"}</span>
                              <span className="text-xs text-gray-500">• Posted by u/ORLA³</span>
                            </div>

                            {/* Post Title */}
                            <h4 className="text-lg font-bold text-gray-900 mb-2">
                              {redditTitle || "Your post title appears here"}
                            </h4>

                            {/* Post Content */}
                            {redditPostType === "text" && caption && (
                              <p className="text-sm text-gray-700 mb-3 whitespace-pre-wrap">{caption}</p>
                            )}

                            {/* Link Preview */}
                            {redditPostType === "link" && redditLinkUrl && (
                              <div className="border border-gray-300 rounded-lg p-3 mb-3">
                                <div className="w-full h-32 bg-gray-200 rounded mb-2"></div>
                                <p className="text-xs text-gray-600 truncate">{redditLinkUrl}</p>
                              </div>
                            )}

                            {/* Image Preview */}
                            {redditPostType === "image" && selectedMedia.length > 0 && selectedMedia[0]?.content_type?.includes('image') && (
                              <img
                                src={selectedMedia[0].url}
                                alt="Post"
                                className="w-full rounded-lg mb-3"
                              />
                            )}

                            {/* Video Preview */}
                            {redditPostType === "video" && selectedMedia.length > 0 && selectedMedia[0]?.content_type?.includes('video') && (
                              <video
                                src={selectedMedia[0].url}
                                className="w-full rounded-lg mb-3"
                                controls
                              />
                            )}

                            {/* Action Bar */}
                            <div className="flex items-center gap-4 text-gray-500 text-sm">
                              <button className="flex items-center gap-1 hover:bg-gray-100 px-2 py-1 rounded">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                </svg>
                                <span>Comments</span>
                              </button>
                              <button className="flex items-center gap-1 hover:bg-gray-100 px-2 py-1 rounded">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                                </svg>
                                <span>Share</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tumblr Studio */}
            {studioPlatform === "tumblr" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Panel - Composer */}
                <div className="space-y-6">
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-6">Create Tumblr Post</h3>

                    {/* Post Type Selector */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-3">Post Type</label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => setTumblrPostType("text")}
                          className={`px-4 py-3 rounded-lg font-semibold transition ${
                            tumblrPostType === "text"
                              ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                              : "bg-white/10 text-gray-400 hover:bg-white/20"
                          }`}
                        >
                          Text
                        </button>
                        <button
                          onClick={() => setTumblrPostType("photo")}
                          className={`px-4 py-3 rounded-lg font-semibold transition ${
                            tumblrPostType === "photo"
                              ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                              : "bg-white/10 text-gray-400 hover:bg-white/20"
                          }`}
                        >
                          Photo
                        </button>
                      </div>
                    </div>

                    {/* Caption */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-2">
                        Caption {tumblrPostType === "text" ? "(Post Content)" : "(Photo Caption)"}
                      </label>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder={tumblrPostType === "text" ? "Write your Tumblr post..." : "Add a caption to your photo..."}
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold resize-none"
                        rows={8}
                      />
                    </div>

                    {/* Media Selection for Photo Posts */}
                    {tumblrPostType === "photo" && (
                      <div className="mb-6">
                        <label className="block text-sm font-semibold text-white mb-2">Photo</label>
                        {selectedMedia.length > 0 ? (
                          <div className="relative">
                            <img
                              src={selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''}
                              alt="Selected"
                              className="w-full h-48 object-cover rounded-lg border border-white/10"
                            />
                            <button
                              onClick={() => setSelectedMedia([])}
                              className="absolute top-2 right-2 bg-black/70 text-white px-3 py-1 rounded-lg text-sm hover:bg-black/90"
                            >
                              Remove
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setActiveTab("media")}
                            className="w-full px-4 py-8 bg-white/5 border-2 border-dashed border-white/20 rounded-lg text-gray-400 hover:bg-white/10 hover:border-gold transition"
                          >
                            Select photo from Media Library
                          </button>
                        )}
                      </div>
                    )}

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing}
                      className="w-full bg-gradient-to-r from-gold to-gold-intense text-white font-bold py-3 px-6 rounded-lg hover:opacity-90 transition disabled:opacity-50"
                    >
                      {publishing ? "Publishing..." : "Publish to Tumblr"}
                    </button>
                  </div>
                </div>

                {/* Right Panel - Preview */}
                <div className="space-y-6">
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-6">Preview</h3>

                    {/* Tumblr-style Post Preview */}
                    <div className="bg-white rounded-lg overflow-hidden shadow-lg">
                      {/* Blog Header */}
                      <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-4 py-3 border-b border-gray-200">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-gold to-gold-intense rounded-lg flex items-center justify-center text-white font-bold text-lg">
                            O
                          </div>
                          <div>
                            <div className="font-bold text-gray-900">orla3-blog</div>
                            <div className="text-xs text-gray-500">Just now</div>
                          </div>
                        </div>
                      </div>

                      {/* Post Content */}
                      <div className="p-4 bg-white">
                        {tumblrPostType === "photo" && selectedMedia.length > 0 && (
                          <img
                            src={selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''}
                            alt="Post"
                            className="w-full rounded-lg mb-3"
                          />
                        )}

                        <div className="text-gray-900 whitespace-pre-wrap">
                          {caption || (
                            <span className="text-gray-400 italic">
                              {tumblrPostType === "text" ? "Your post content will appear here..." : "Your caption will appear here..."}
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Post Actions */}
                      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <button className="flex items-center gap-2 hover:text-gray-900 transition">
                            <span>Notes</span>
                          </button>
                          <button className="flex items-center gap-2 hover:text-gray-900 transition">
                            <span>Reblog</span>
                          </button>
                          <button className="flex items-center gap-2 hover:text-gray-900 transition">
                            <span>Like</span>
                          </button>
                        </div>
                      </div>

                      {/* Tags Section */}
                      <div className="px-4 py-3 bg-white border-t border-gray-200">
                        <div className="flex flex-wrap gap-2">
                          <span className="text-xs text-gray-500">#orla3</span>
                          <span className="text-xs text-gray-500">#marketing</span>
                          <span className="text-xs text-gray-500">#automation</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* WordPress Studio */}
            {studioPlatform === "wordpress" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Panel - Composer */}
                <div className="space-y-6">
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-6">Create WordPress Post</h3>

                    {/* Post Title */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-2">Post Title</label>
                      <input
                        type="text"
                        value={wordpressTitle}
                        onChange={(e) => setWordpressTitle(e.target.value)}
                        placeholder="Enter your blog post title..."
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold"
                      />
                    </div>

                    {/* Post Content */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-2">Post Content</label>
                      <textarea
                        value={caption}
                        onChange={(e) => setCaption(e.target.value)}
                        placeholder="Write your blog post content..."
                        className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold resize-none"
                        rows={12}
                      />
                    </div>

                    {/* Featured Image */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-2">Featured Image (Optional)</label>
                      {selectedMedia.length > 0 ? (
                        <div className="relative">
                          <img
                            src={selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''}
                            alt="Featured"
                            className="w-full h-48 object-cover rounded-lg border border-white/10"
                          />
                          <button
                            onClick={() => setSelectedMedia([])}
                            className="absolute top-2 right-2 bg-black/70 text-white px-3 py-1 rounded-lg text-sm hover:bg-black/90"
                          >
                            Remove
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setActiveTab("media")}
                          className="w-full px-4 py-8 bg-white/5 border-2 border-dashed border-white/20 rounded-lg text-gray-400 hover:bg-white/10 hover:border-gold transition"
                        >
                          Select featured image from Media Library
                        </button>
                      )}
                    </div>

                    {/* Publish Status */}
                    <div className="mb-6">
                      <label className="block text-sm font-semibold text-white mb-3">Publish Status</label>
                      <div className="grid grid-cols-2 gap-3">
                        <button
                          onClick={() => setWordpressStatus("draft")}
                          className={`px-4 py-3 rounded-lg font-semibold transition ${
                            wordpressStatus === "draft"
                              ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                              : "bg-white/10 text-gray-400 hover:bg-white/20"
                          }`}
                        >
                          Save as Draft
                        </button>
                        <button
                          onClick={() => setWordpressStatus("publish")}
                          className={`px-4 py-3 rounded-lg font-semibold transition ${
                            wordpressStatus === "publish"
                              ? "bg-gradient-to-r from-gold-intense to-cobalt text-white"
                              : "bg-white/10 text-gray-400 hover:bg-white/20"
                          }`}
                        >
                          Publish Live
                        </button>
                      </div>
                    </div>

                    {/* Publish Button */}
                    <button
                      onClick={publishToSocial}
                      disabled={publishing}
                      className="w-full bg-gradient-to-r from-gold to-gold-intense text-white font-bold py-3 px-6 rounded-lg hover:opacity-90 transition disabled:opacity-50"
                    >
                      {publishing ? "Publishing..." : `${wordpressStatus === "publish" ? "Publish" : "Save Draft"} to WordPress`}
                    </button>
                  </div>
                </div>

                {/* Right Panel - Preview */}
                <div className="space-y-6">
                  <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
                    <h3 className="text-xl font-bold text-white mb-6">Preview</h3>

                    {/* WordPress-style Blog Post Preview */}
                    <div className="bg-white rounded-lg overflow-hidden shadow-lg">
                      {/* Featured Image */}
                      {selectedMedia.length > 0 && (
                        <img
                          src={selectedMedia[0]?.url || selectedMedia[0]?.image_url || ''}
                          alt="Featured"
                          className="w-full h-64 object-cover"
                        />
                      )}

                      {/* Post Content */}
                      <div className="p-6">
                        {/* Post Title */}
                        <h1 className="text-3xl font-bold text-gray-900 mb-4">
                          {wordpressTitle || (
                            <span className="text-gray-400 italic text-2xl">Your post title will appear here...</span>
                          )}
                        </h1>

                        {/* Post Meta */}
                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-6 pb-4 border-b border-gray-200">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-gradient-to-br from-gold to-gold-intense rounded-full flex items-center justify-center text-white font-bold text-xs">
                              O
                            </div>
                            <span className="font-semibold">ORLA³</span>
                          </div>
                          <span>•</span>
                          <span>Just now</span>
                          <span>•</span>
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            wordpressStatus === "publish"
                              ? "bg-green-100 text-green-700"
                              : "bg-yellow-100 text-yellow-700"
                          }`}>
                            {wordpressStatus === "publish" ? "Published" : "Draft"}
                          </span>
                        </div>

                        {/* Post Body */}
                        <div className="prose prose-lg max-w-none text-gray-700 whitespace-pre-wrap">
                          {caption || (
                            <span className="text-gray-400 italic">
                              Your blog post content will appear here...
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Post Footer */}
                      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4 text-sm text-gray-600">
                            <button className="hover:text-gray-900 transition">Share</button>
                            <button className="hover:text-gray-900 transition">Comment</button>
                            <button className="hover:text-gray-900 transition">Like</button>
                          </div>
                          <div className="text-sm text-gray-500">
                            Categories: Marketing, Automation
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Placeholder for other platforms */}
            {studioPlatform !== "instagram" && studioPlatform !== "youtube" && studioPlatform !== "facebook" && studioPlatform !== "tiktok" && studioPlatform !== "linkedin" && studioPlatform !== "x" && studioPlatform !== "reddit" && studioPlatform !== "tumblr" && studioPlatform !== "wordpress" && (
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-8 border border-white/10 text-center">
                <h3 className="text-xl font-bold text-white mb-2 capitalize">{studioPlatform} Studio</h3>
                <p className="text-gray-400">Platform composer coming soon</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "engage" && (
          <>
            <div className="flex gap-3 mb-3 sm:mb-4 md:mb-6">
              <button onClick={() => setEngageSubTab("inbox")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "inbox" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Inbox ({comments.length})
              </button>
              <button onClick={() => setEngageSubTab("discovery")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "discovery" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Discovery
              </button>
              <button onClick={() => setEngageSubTab("settings")} className={`px-6 py-3 rounded-lg font-semibold transition ${engageSubTab === "settings" ? "bg-cobalt text-white" : "bg-white/10 text-gray-400 hover:bg-white/20"}`}>
                Settings
              </button>
            </div>

            {engageSubTab === "inbox" && (
              <div className="grid grid-cols-1 lg:grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4 lg:gap-6">
                <div className="lg:col-span-2 bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                  <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6">Comments Inbox</h2>
                  <div className="space-y-2 sm:space-y-3 md:space-y-4">
                    {loadingComments ? (
                      <div className="text-center py-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
                        <p className="text-gray-400">Loading comments from connected platforms...</p>
                      </div>
                    ) : comments.length === 0 ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400 mb-4">No comments yet from your connected platforms.</p>
                        <button
                          onClick={loadComments}
                          className="text-cobalt hover:text-royal transition-colors"
                        >
                          Refresh
                        </button>
                      </div>
                    ) : comments.map((comment) => (
                      <div key={comment.id} className="bg-white/5 border border-white/10 rounded-lg p-3 sm:p-4 hover:border-cobalt/50 transition cursor-pointer" onClick={() => generateAIReplies(comment)}>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="text-base sm:text-lg md:text-xl lg:text-2xl">{getPlatformIcon(comment.platform)}</span>
                            <div>
                              <p className="text-white font-semibold">{comment.author}</p>
                              <p className="text-sm text-gray-400">{comment.postTitle}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`text-base sm:text-lg md:text-xl ${getSentimentColor(comment.sentiment)}`}>{getSentimentIcon(comment.sentiment)}</span>
                            <span className="text-xs text-gray-500">{comment.timestamp}</span>
                          </div>
                        </div>
                        <p className="text-white/90">{comment.content}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                  <h2 className="text-base sm:text-lg md:text-xl font-bold text-white mb-4">AI Reply</h2>
                  {!selectedComment ? (
                    <div className="text-center py-12">
                      <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                      <p className="text-gray-400">Select a comment to generate AI replies</p>
                    </div>
                  ) : (
                    <div className="space-y-2 sm:space-y-3 md:space-y-4">
                      <div className="bg-white/10 rounded-lg p-3 sm:p-4">
                        <p className="text-sm text-gray-400 mb-2">Replying to:</p>
                        <p className="text-white">{selectedComment.content}</p>
                      </div>
                      {generatingReplies ? (
                        <div className="text-center py-4 sm:py-6 md:py-8">
                          <div className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl mb-2"></div>
                          <p className="text-gold">Generating replies...</p>
                        </div>
                      ) : aiReplies.length > 0 && (
                        <>
                          <div className="space-y-3">
                            {aiReplies.map((reply, idx) => (
                              <div key={idx} className="bg-white/10 rounded-lg p-3 sm:p-4 hover:bg-white/20 transition cursor-pointer" onClick={() => setManualReply(reply)}>
                                <div className="flex items-start justify-between mb-2">
                                  <span className="text-xs font-semibold text-gold">Option {idx + 1}</span>
                                  <button className="text-xs text-gold hover:text-gold">Use this →</button>
                                </div>
                                <p className="text-white text-sm">{reply}</p>
                              </div>
                            ))}
                          </div>
                          <div className="border-t border-white/10 pt-4">
                            <label className="block text-white font-semibold mb-2">Manual Reply</label>
                            <textarea value={manualReply} onChange={(e) => setManualReply(e.target.value)} placeholder="Edit AI suggestion or write your own..." rows={4} className="w-full px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt resize-none" />
                            <button className="w-full mt-3 py-3 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense rounded-lg text-white font-semibold transition">Send Reply</button>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {engageSubTab === "discovery" && (
              <div className="bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-4">Find Relevant Posts</h2>
                <div className="flex gap-3 mb-3 sm:mb-4 md:mb-6">
                  <input type="text" value={searchKeywords} onChange={(e) => setSearchKeywords(e.target.value)} placeholder="Enter keywords or hashtags" className="flex-1 px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:border-cobalt" />
                  <button onClick={searchRelevantPosts} disabled={searchingPosts} className="px-6 py-3 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition disabled:opacity-50">
                    {searchingPosts ? "Searching..." : "Search"}
                  </button>
                </div>
                {discoveryPosts.length > 0 && (
                  <div className="space-y-2 sm:space-y-3 md:space-y-4">
                    {discoveryPosts.map((post) => (
                      <div key={post.id} className="bg-white/5 border border-white/10 rounded-lg p-3 sm:p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="text-base sm:text-lg md:text-xl lg:text-2xl">{getPlatformIcon(post.platform)}</span>
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
                        <button className="w-full py-2 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense rounded-lg text-white font-semibold transition text-sm">
                          Generate Comment
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {engageSubTab === "settings" && (
              <div className="max-w-4xl mx-auto bg-white/5 backdrop-blur-lg rounded-xl p-4 sm:p-6 border border-white/10">
                <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-3 sm:mb-4 md:mb-6">Engagement Settings</h2>
                <div className="bg-white/5 rounded-lg p-4 sm:p-6 mb-3 sm:mb-4 md:mb-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">Auto-Reply</h3>
                      <p className="text-gray-400 text-sm">Let AI automatically respond to comments</p>
                    </div>
                    <button onClick={() => setAutoReplyEnabled(!autoReplyEnabled)} className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${autoReplyEnabled ? "bg-gold" : "bg-gray-600"}`}>
                      <span className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${autoReplyEnabled ? "translate-x-7" : "translate-x-1"}`} />
                    </button>
                  </div>
                  {autoReplyEnabled && (
                    <div className="mt-4 p-3 sm:p-4 bg-gold/10 border border-gold/30 rounded-lg">
                      <p className="text-gold-400 text-sm font-semibold">Auto-reply is enabled</p>
                    </div>
                  )}
                </div>
                <button className="w-full py-3 sm:py-4 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense rounded-lg text-white font-bold transition">
                  Save Settings
                </button>
              </div>
            )}
          </>
        )}

        {activeTab === "schedule" && (
          <div className="bg-white/5 backdrop-blur-lg rounded-xl p-6 sm:p-8 md:p-12 border border-white/10 text-center">
            <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
            <h2 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white mb-2">Schedule View</h2>
            <button onClick={() => router.push("/dashboard/calendar")} className="px-6 py-3 bg-gradient-to-r from-cobalt to-gold-intense hover:from-cobalt-600 hover:to-gold-600 rounded-lg text-white font-semibold transition">
              Open Content Calendar
            </button>
          </div>
        )}
      </div>

        {/* Media Library Modal */}
        {showMediaLibrary && (
          <div className="fixed inset-0 bg-black/90 flex items-center justify-center z-50 p-4 sm:p-6 md:p-8" onClick={() => setShowMediaLibrary(false)}>
            <div className="max-w-6xl w-full max-h-[80vh] bg-slate-900 rounded-2xl border border-white/20 flex flex-col" onClick={(e) => e.stopPropagation()}>
              {/* Modal Header */}
              <div className="p-4 sm:p-6 border-b border-white/10 flex items-center justify-between">
                <h3 className="text-base sm:text-lg md:text-xl lg:text-2xl font-bold text-white">Browse Media Library</h3>
                <button onClick={() => setShowMediaLibrary(false)} className="text-white hover:text-red-400 text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl">×</button>
              </div>
              
              {/* Tabs - Sticky to prevent content overlap */}
              <div className="sticky top-0 z-20 bg-slate-900 px-6 pt-4 flex gap-3 border-b border-white/10 overflow-x-auto flex-shrink-0">
                <button
                  onClick={() => setMediaLibraryTab('generated')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'generated' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Generated Content
                </button>
                <button
                  onClick={() => {
                    setMediaLibraryTab('cloud');
                    if (connectedProviders.length > 0 && !cloudStorageProvider) {
                      setCloudStorageProvider(connectedProviders[0] as any);
                    }
                  }}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'cloud' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Cloud Storage
                </button>
                <button
                  onClick={() => setMediaLibraryTab('pexels-photos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'pexels-photos' ? 'bg-cobalt text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Pexels Photos
                </button>
                <button
                  onClick={() => setMediaLibraryTab('pexels-videos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'pexels-videos' ? 'bg-gold-600 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  Pexels Videos
                </button>
                <button
                  onClick={() => setMediaLibraryTab('ai-images')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'ai-images' ? 'bg-gradient-to-r from-gold-600 to-gold-intense text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  AI Images
                </button>
                <button
                  onClick={() => setMediaLibraryTab('ai-videos')}
                  className={`px-6 py-3 rounded-t-lg font-semibold transition whitespace-nowrap ${mediaLibraryTab === 'ai-videos' ? 'bg-gradient-to-r from-red-600 to-red-700 text-white' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
                >
                  AI Videos
                </button>
              </div>

              {/* Content Area */}
              <div className="flex-1 overflow-auto p-4 sm:p-6">
                {/* Generated Content Tab */}
                {mediaLibraryTab === 'generated' && (
                  <>
                    {mediaLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
                          <p className="text-gray-400">Loading generated content...</p>
                        </div>
                      </div>
                    ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
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
                              <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                            ) : item.content_type === 'blog' ? (
                              <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                            ) : (
                              <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
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
                  </>
                )}

                {/* Cloud Storage Tab */}
                {mediaLibraryTab === 'cloud' && (
                  <div>
                    {mediaLoading ? (
                      <div className="flex items-center justify-center py-12">
                        <div className="text-center">
                          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cobalt mx-auto mb-4"></div>
                          <p className="text-gray-400">Loading cloud storage...</p>
                        </div>
                      </div>
                    ) : connectedProviders.length === 0 ? (
                      <div className="text-center py-12">
                        <svg className="w-20 h-20 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                        </svg>
                        <h3 className="text-xl font-bold text-white mb-2">No Cloud Storage Connected</h3>
                        <p className="text-gray-400 mb-4">Connect Google Drive, Dropbox, or OneDrive</p>
                        <button
                          onClick={() => window.open('/dashboard/settings/cloud-storage', '_blank')}
                          className="px-6 py-3 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white font-semibold transition"
                        >
                          Connect Cloud Storage
                        </button>
                      </div>
                    ) : (
                      <div>
                        <div className="mb-6 flex gap-3 flex-wrap">
                          {connectedProviders.includes('google_drive') && (
                            <button
                              onClick={() => { setCloudStorageProvider('google_drive'); loadDriveFiles(''); }}
                              className={`px-4 py-2 rounded-lg font-semibold transition ${cloudStorageProvider === 'google_drive' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}`}
                            >
                              Google Drive
                            </button>
                          )}
                          {connectedProviders.includes('dropbox') && (
                            <button
                              onClick={() => { setCloudStorageProvider('dropbox'); loadDropboxFiles(''); }}
                              className={`px-4 py-2 rounded-lg font-semibold transition ${cloudStorageProvider === 'dropbox' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}`}
                            >
                              Dropbox
                            </button>
                          )}
                          {connectedProviders.includes('onedrive') && (
                            <button
                              onClick={() => { setCloudStorageProvider('onedrive'); loadOnedriveFiles(''); }}
                              className={`px-4 py-2 rounded-lg font-semibold transition ${cloudStorageProvider === 'onedrive' ? 'bg-cobalt text-white' : 'bg-white/10 text-gray-400 hover:bg-white/20'}`}
                            >
                              OneDrive
                            </button>
                          )}
                        </div>

                        {cloudStorageProvider === 'google_drive' && driveAssets && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {driveAssets.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer">
                                {file.thumbnail ? (
                                  <img src={file.thumbnail} alt={file.name} className="w-full aspect-square object-cover" />
                                ) : (
                                  <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                    <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                    </svg>
                                  </div>
                                )}
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {cloudStorageProvider === 'dropbox' && dropboxFiles && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {dropboxFiles.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-royal transition cursor-pointer">
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                  </svg>
                                </div>
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {cloudStorageProvider === 'onedrive' && onedriveFiles && (
                          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                            {onedriveFiles.map((file: any) => (
                              <div key={file.id} onClick={() => handleMediaSelect(file)} className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer">
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                  </svg>
                                </div>
                                <div className="p-3">
                                  <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Google Drive Tab */}
                {mediaLibraryTab === 'drive' && (
                  <div>
                    {driveFolders.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">Connect Google Drive</h3>
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
                            className="w-full px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white"
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
                          <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
                            {driveAssets.map((asset: any) => (
                              <div 
                                key={asset.id}
                                className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition"
                              >
                                <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center relative group">
                                  {asset.thumbnail ? (
                                    <img src={asset.thumbnail} alt={asset.name} className="w-full h-full object-cover" />
                                  ) : asset.type === 'folder' ? (
                                    <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                                  ) : asset.type === 'video' ? (
                                    <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                                  ) : asset.type === 'image' ? (
                                    <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                                  ) : (
                                    <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                                  )}
                                  
                                  {/* Hover buttons for files */}
                                  {asset.type !== 'folder' && (
                                    <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition flex flex-col items-center justify-center gap-2 p-3 sm:p-4">
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          window.open(`https://drive.google.com/file/d/${asset.id}/view`, '_blank');
                                        }}
                                        className="w-full px-3 sm:px-4 py-2 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white text-sm font-semibold transition"
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
                                        className="w-full px-3 sm:px-4 py-2 bg-cobalt hover:bg-cobalt-700 rounded-lg text-white text-sm font-semibold transition"
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

                {/* Dropbox Tab */}
                {mediaLibraryTab === 'dropbox' && (
                  <div>
                    {mediaLoading ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400">Loading Dropbox files...</p>
                      </div>
                    ) : dropboxFiles.length === 0 && dropboxFolders.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">Dropbox Connected</h3>
                        <p className="text-gray-400">No files found in this folder.</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
                        {/* Folders */}
                        {dropboxFolders.map((folder: any) => (
                          <div
                            key={folder.id}
                            onClick={() => {
                              setDropboxPath(folder.path);
                              loadDropboxFiles(folder.path);
                            }}
                            className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-royal transition cursor-pointer"
                          >
                            <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                              <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                            </div>
                            <div className="p-3">
                              <h4 className="text-white font-bold text-sm truncate">{folder.name}</h4>
                              <p className="text-xs text-gray-400 capitalize">Folder</p>
                            </div>
                          </div>
                        ))}
                        {/* Files */}
                        {dropboxFiles.map((file: any) => (
                          <div
                            key={file.id}
                            className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-royal transition group"
                          >
                            <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center relative">
                              {file.type === 'image' ? (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              ) : file.type === 'video' ? (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              ) : (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              )}
                              <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition flex flex-col items-center justify-center gap-2 p-3 sm:p-4">
                                <button
                                  onClick={() => handleMediaSelect({ ...file, source: 'dropbox' })}
                                  className="w-full px-3 sm:px-4 py-2 bg-royal hover:bg-royal-700 rounded-lg text-white text-sm font-semibold transition"
                                >
                                  Select for Post
                                </button>
                              </div>
                            </div>
                            <div className="p-3">
                              <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                              <p className="text-xs text-gray-400 capitalize">{file.type}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* OneDrive Tab */}
                {mediaLibraryTab === 'onedrive' && (
                  <div>
                    {mediaLoading ? (
                      <div className="text-center py-12">
                        <p className="text-gray-400">Loading OneDrive files...</p>
                      </div>
                    ) : onedriveFiles.length === 0 && onedriveFolders.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">OneDrive Connected</h3>
                        <p className="text-gray-400">No files found in this folder.</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
                        {/* Folders */}
                        {onedriveFolders.map((folder: any) => (
                          <div
                            key={folder.id}
                            onClick={() => {
                              setOnedrivePath(`items/${folder.id}`);
                              loadOnedriveFiles(`items/${folder.id}`);
                            }}
                            className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition cursor-pointer"
                          >
                            <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center">
                              <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                            </div>
                            <div className="p-3">
                              <h4 className="text-white font-bold text-sm truncate">{folder.name}</h4>
                              <p className="text-xs text-gray-400 capitalize">Folder • {folder.item_count || 0} items</p>
                            </div>
                          </div>
                        ))}
                        {/* Files */}
                        {onedriveFiles.map((file: any) => (
                          <div
                            key={file.id}
                            className="bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-cobalt transition group"
                          >
                            <div className="aspect-square bg-gradient-to-br from-royal-900 to-slate-900 flex items-center justify-center relative">
                              {file.type === 'image' ? (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              ) : file.type === 'video' ? (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              ) : (
                                <span className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl"></span>
                              )}
                              <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 transition flex flex-col items-center justify-center gap-2 p-3 sm:p-4">
                                <button
                                  onClick={() => handleMediaSelect({ ...file, source: 'onedrive', url: file.download_url })}
                                  className="w-full px-3 sm:px-4 py-2 bg-royal-600 hover:bg-cobalt rounded-lg text-white text-sm font-semibold transition"
                                >
                                  Select for Post
                                </button>
                              </div>
                            </div>
                            <div className="p-3">
                              <h4 className="text-white font-bold text-sm truncate">{file.name}</h4>
                              <p className="text-xs text-gray-400 capitalize">{file.type}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Pexels Photos Tab */}
                {mediaLibraryTab === 'pexels-photos' && (
                  <div>
                    <div className="mb-3 sm:mb-4 md:mb-6 flex gap-3">
                      <input
                        type="text"
                        value={pexelsQuery}
                        onChange={(e) => setPexelsQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchPexelsPhotos()}
                        placeholder="Search free stock photos..."
                        className="flex-1 px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-cobalt"
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
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">Search Pexels Photos</h3>
                        <p className="text-gray-400">Search millions of free, high-quality stock photos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
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
                    <div className="mb-3 sm:mb-4 md:mb-6 flex gap-3">
                      <input
                        type="text"
                        value={pexelsQuery}
                        onChange={(e) => setPexelsQuery(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && searchPexelsVideos()}
                        placeholder="Search free stock videos..."
                        className="flex-1 px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-gold"
                      />
                      <button
                        onClick={searchPexelsVideos}
                        className="px-6 py-3 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense rounded-lg text-white font-semibold transition"
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
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">Search Pexels Videos</h3>
                        <p className="text-gray-400">Search thousands of free, high-quality stock videos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
                        {pexelsVideos.map((video: any) => (
                          <div
                            key={video.id}
                            onClick={() => handleMediaSelect(video)}
                            className="bg-white/5 rounded-lg overflow-hidden cursor-pointer hover:bg-white/10 transition border border-white/10 hover:border-gold"
                          >
                            <div className="aspect-video relative group">
                              <img src={video.thumbnail} alt={video.name} className="w-full h-full object-cover" />
                              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                                <div className="text-white text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl"></div>
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

                {/* AI Images Tab (Imagen 3 - Nano Banana ) */}
                {mediaLibraryTab === 'ai-images' && (
                  <div>
                    <div className="mb-3 sm:mb-4 md:mb-6 space-y-2 sm:space-y-3 md:space-y-4">
                      <div className="bg-gradient-to-r from-gold-600/30 to-gold-intense/30 border border-gold/30 rounded-lg p-3 sm:p-4">
                        <h4 className="text-lg font-bold text-gold-400 mb-2">Google Imagen 3 (Nano Banana)</h4>
                        <p className="text-sm text-gray-300 mb-2">Generate high-quality AI images from text prompts. Cost: $0.03 per image.</p>
                      </div>

                      <textarea
                        value={aiImagePrompt}
                        onChange={(e) => setAiImagePrompt(e.target.value)}
                        placeholder="Describe the image you want to generate... (e.g., 'Professional videographer filming a corporate interview in modern office')"
                        rows={3}
                        className="w-full px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-gold resize-none"
                      />

                      <div className="flex gap-2 sm:gap-3 md:gap-4 items-center">
                        <div className="flex-1">
                          <label className="block text-sm text-gray-400 mb-2">Aspect Ratio</label>
                          <select
                            value={aiAspectRatio}
                            onChange={(e) => setAiAspectRatio(e.target.value as any)}
                            className="w-full px-3 sm:px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-gold"
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
                          className="px-4 sm:px-6 md:px-8 py-2 bg-gradient-to-r from-gold to-gold-intense hover:from-gold-600 hover:to-gold-intense disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-bold transition mt-6"
                        >
                          {generatingAiImage ? 'Generating...' : 'Generate Image'}
                        </button>
                      </div>
                    </div>

                    {aiGeneratedImages.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">No AI Images Generated Yet</h3>
                        <p className="text-gray-400">Enter a prompt above and click Generate to create AI images</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
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
                    <div className="mb-3 sm:mb-4 md:mb-6 space-y-2 sm:space-y-3 md:space-y-4">
                      <div className="bg-gradient-to-r from-red-900/30 to-gold-900/30 border border-red-500/30 rounded-lg p-3 sm:p-4">
                        <h4 className="text-lg font-bold text-red-400 mb-2">Google Veo 3.1</h4>
                        <p className="text-sm text-gray-300 mb-2">Generate 8-second AI videos with audio from text prompts. Cost: $0.75/second ($6 per video).</p>
                        <p className="text-xs text-gold-400">Video generation takes 2-5 minutes</p>
                      </div>

                      <textarea
                        value={aiVideoPrompt}
                        onChange={(e) => setAiVideoPrompt(e.target.value)}
                        placeholder="Describe the video you want to generate... (e.g., 'Professional videographer filming behind-the-scenes of a wedding ceremony')"
                        rows={3}
                        className="w-full px-3 sm:px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500 resize-none"
                      />

                      <div className="flex gap-2 sm:gap-3 md:gap-4 items-center">
                        <div className="flex-1">
                          <label className="block text-sm text-gray-400 mb-2">Resolution</label>
                          <select
                            value={aiVideoResolution}
                            onChange={(e) => setAiVideoResolution(e.target.value as any)}
                            className="w-full px-3 sm:px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:border-red-500"
                          >
                            <option value="720p">720p (HD)</option>
                            <option value="1080p">1080p (Full HD) - Higher cost</option>
                          </select>
                        </div>

                        <button
                          onClick={generateAiVideo}
                          disabled={generatingAiVideo || !aiVideoPrompt.trim()}
                          className="px-4 sm:px-6 md:px-8 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white font-bold transition mt-6"
                        >
                          {generatingAiVideo ? 'Generating...' : 'Generate Video'}
                        </button>
                      </div>
                    </div>

                    {aiGeneratedVideos.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-3xl sm:text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl md:text-5xl lg:text-6xl mb-4"></div>
                        <h3 className="text-base sm:text-lg md:text-xl font-bold text-white mb-2">No AI Videos Generated Yet</h3>
                        <p className="text-gray-400">Enter a prompt above and click Generate to create AI videos</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 sm:grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3 md:gap-4">
                        {aiGeneratedVideos.map((video: any, idx: number) => (
                          <div
                            key={idx}
                            onClick={() => video.status === 'complete' && handleMediaSelect(video)}
                            className={`bg-white/5 rounded-lg overflow-hidden ${video.status === 'complete' ? 'cursor-pointer hover:bg-white/10 hover:border-red-500' : 'opacity-50'} transition border border-white/10`}
                          >
                            <div className="aspect-video bg-gradient-to-br from-red-900 to-gold-900 flex items-center justify-center">
                              {video.status === 'generating' ? (
                                <div className="text-center">
                                  <div className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl mb-2">⏳</div>
                                  <p className="text-sm text-gray-300">Generating...</p>
                                </div>
                              ) : video.url ? (
                                <video src={video.url} className="w-full h-full object-cover" />
                              ) : (
                                <div className="text-2xl sm:text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl md:text-4xl"></div>
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
