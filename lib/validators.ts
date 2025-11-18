/**
 * Platform-specific validation utilities for social media posts
 * Mirrors backend/utils/validators.py
 */

// Character limits for each platform
export const PLATFORM_CHARACTER_LIMITS: Record<string, number | null> = {
  instagram: 2200,
  linkedin: 3000,
  facebook: 63206,
  twitter: 280,
  x: 280, // Twitter/X alias
  tiktok: 2200, // TikTok caption limit
  youtube: 5000, // YouTube video description limit
  reddit: 40000, // Reddit post body limit
  tumblr: null, // Tumblr has no strict limit
  wordpress: null, // WordPress has no strict limit
};

/**
 * Get character limit for a platform
 */
export function getPlatformCharacterLimit(platform: string): number | null {
  const normalizedPlatform = platform.toLowerCase();
  return PLATFORM_CHARACTER_LIMITS[normalizedPlatform] ?? null;
}

/**
 * Get remaining characters for a platform
 */
export function getRemainingCharacters(content: string, platform: string): number {
  const limit = getPlatformCharacterLimit(platform);
  if (limit === null) {
    return -1; // No limit
  }
  return limit - content.length;
}

/**
 * Check if content exceeds platform character limit
 */
export function isOverCharacterLimit(content: string, platform: string): boolean {
  const limit = getPlatformCharacterLimit(platform);
  if (limit === null) {
    return false; // No limit
  }
  return content.length > limit;
}

/**
 * Validate character limit for content
 */
export function validateCharacterLimit(
  content: string,
  platform: string
): { valid: boolean; error?: string } {
  const normalizedPlatform = platform.toLowerCase();

  if (!(normalizedPlatform in PLATFORM_CHARACTER_LIMITS)) {
    return { valid: true }; // Unknown platform, allow through
  }

  const limit = PLATFORM_CHARACTER_LIMITS[normalizedPlatform];

  if (limit === null) {
    return { valid: true }; // No limit for this platform
  }

  const contentLength = content.length;

  if (contentLength > limit) {
    return {
      valid: false,
      error: `${platform.charAt(0).toUpperCase() + platform.slice(1)} posts are limited to ${limit} characters. Your post is ${contentLength} characters.`,
    };
  }

  return { valid: true };
}

/**
 * Validate media requirements for a platform
 */
export function validateMediaRequirements(
  content: string,
  mediaUrls: string[],
  platform: string
): { valid: boolean; error?: string } {
  const normalizedPlatform = platform.toLowerCase();

  // Instagram requires at least one image
  if (normalizedPlatform === "instagram") {
    if (!mediaUrls || mediaUrls.length === 0) {
      return { valid: false, error: "Instagram posts require at least one image or video" };
    }
  }

  // TikTok requires video
  if (normalizedPlatform === "tiktok") {
    if (!mediaUrls || mediaUrls.length === 0) {
      return { valid: false, error: "TikTok posts require a video" };
    }
  }

  // YouTube requires video
  if (normalizedPlatform === "youtube") {
    if (!mediaUrls || mediaUrls.length === 0) {
      return { valid: false, error: "YouTube posts require a video" };
    }
  }

  // Twitter media limits (up to 4 images OR 1 video)
  if (normalizedPlatform === "twitter" || normalizedPlatform === "x") {
    if (mediaUrls && mediaUrls.length > 4) {
      return { valid: false, error: "Twitter allows maximum 4 images per tweet" };
    }
  }

  return { valid: true };
}

/**
 * Complete validation for post content
 */
export function validateContent(
  content: string,
  mediaUrls: string[],
  platform: string
): { valid: boolean; error?: string } {
  // Validate character limit
  const charValidation = validateCharacterLimit(content, platform);
  if (!charValidation.valid) {
    return charValidation;
  }

  // Validate media requirements
  const mediaValidation = validateMediaRequirements(content, mediaUrls, platform);
  if (!mediaValidation.valid) {
    return mediaValidation;
  }

  return { valid: true };
}

/**
 * Platform compatibility types
 */
export type PostType = "text" | "image" | "video" | "carousel";
export type Platform = "instagram" | "linkedin" | "facebook" | "x" | "tiktok" | "youtube" | "reddit" | "tumblr" | "wordpress";

/**
 * Platform compatibility matrix
 * Defines which platforms support which post types
 */
const PLATFORM_COMPATIBILITY: Record<PostType, Platform[]> = {
  text: [
    "linkedin",
    "facebook",
    "x",
    "reddit",
    "tumblr",
    "wordpress",
  ],
  image: [
    "instagram",
    "linkedin",
    "facebook",
    "x",
    "reddit",
    "tumblr",
    "wordpress",
  ],
  video: [
    "instagram",
    "tiktok",
    "youtube",
    "linkedin",
    "facebook",
    "x",
    "reddit",
    "tumblr",
    "wordpress",
  ],
  carousel: [
    "instagram",
    "linkedin",
    "facebook",
  ],
};

/**
 * Check if a platform supports a post type
 */
export function isPlatformCompatible(platform: Platform, postType: PostType): boolean {
  return PLATFORM_COMPATIBILITY[postType].includes(platform);
}

/**
 * Get all platforms compatible with a post type
 */
export function getCompatiblePlatforms(postType: PostType): Platform[] {
  return PLATFORM_COMPATIBILITY[postType];
}

/**
 * Get platforms NOT compatible with a post type
 */
export function getIncompatiblePlatforms(postType: PostType): Platform[] {
  const allPlatforms: Platform[] = [
    "instagram", "linkedin", "facebook", "x", "tiktok", "youtube", "reddit", "tumblr", "wordpress"
  ];
  return allPlatforms.filter(p => !PLATFORM_COMPATIBILITY[postType].includes(p));
}

/**
 * Get user-friendly reason why platform is incompatible
 */
export function getIncompatibilityReason(platform: Platform, postType: PostType): string | null {
  if (isPlatformCompatible(platform, postType)) {
    return null;
  }

  if (postType === "text") {
    if (platform === "instagram") return "Instagram requires media";
    if (platform === "tiktok") return "TikTok requires video";
    if (platform === "youtube") return "YouTube requires video";
  }

  if (postType === "image") {
    if (platform === "tiktok") return "TikTok requires video";
    if (platform === "youtube") return "YouTube requires video";
  }

  if (postType === "carousel") {
    if (platform === "tiktok") return "TikTok does not support carousels";
    if (platform === "youtube") return "YouTube does not support carousels";
    if (platform === "reddit") return "Reddit does not support carousels";
    if (platform === "tumblr") return "Tumblr does not support carousels";
    if (platform === "wordpress") return "WordPress does not support carousels";
    if (platform === "x") return "X does not support carousel format";
  }

  return `${platform} does not support ${postType} posts`;
}
