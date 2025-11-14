"""
Platform-specific validation utilities for social media posts
"""

# Character limits for each platform
PLATFORM_CHARACTER_LIMITS = {
    "instagram": 2200,
    "linkedin": 3000,
    "facebook": 63206,
    "twitter": 280,
    "x": 280,  # Twitter/X alias
    "tiktok": 2200,  # TikTok caption limit
    "youtube": 5000,  # YouTube video description limit
    "reddit": 40000,  # Reddit post body limit
    "tumblr": None,  # Tumblr has no strict limit
    "wordpress": None,  # WordPress has no strict limit
}


class ContentValidator:
    """Validates social media content before publishing"""

    @staticmethod
    def validate_character_limit(content: str, platform: str) -> tuple[bool, str]:
        """
        Validate content length for platform

        Args:
            content: The text content to validate
            platform: Platform name (lowercase)

        Returns:
            tuple: (is_valid, error_message)
        """
        platform = platform.lower()

        if platform not in PLATFORM_CHARACTER_LIMITS:
            return True, ""  # Unknown platform, allow through

        limit = PLATFORM_CHARACTER_LIMITS[platform]

        if limit is None:
            return True, ""  # No limit for this platform

        content_length = len(content)

        if content_length > limit:
            return False, f"{platform.title()} posts are limited to {limit} characters. Your post is {content_length} characters."

        return True, ""

    @staticmethod
    def validate_media_requirements(content: str, media_urls: list, platform: str) -> tuple[bool, str]:
        """
        Validate media requirements for platform

        Args:
            content: The text content
            media_urls: List of media URLs
            platform: Platform name (lowercase)

        Returns:
            tuple: (is_valid, error_message)
        """
        platform = platform.lower()

        # Instagram requires at least one image
        if platform == "instagram":
            if not media_urls or len(media_urls) == 0:
                return False, "Instagram posts require at least one image or video"

        # TikTok requires video
        if platform == "tiktok":
            if not media_urls or len(media_urls) == 0:
                return False, "TikTok posts require a video"

        # YouTube requires video
        if platform == "youtube":
            if not media_urls or len(media_urls) == 0:
                return False, "YouTube posts require a video"

        # Reddit requires subreddit (checked elsewhere)

        # Twitter media limits (up to 4 images OR 1 video)
        if platform in ["twitter", "x"]:
            if media_urls and len(media_urls) > 4:
                return False, "Twitter allows maximum 4 images per tweet"

        return True, ""

    @staticmethod
    def validate_content(content: str, media_urls: list, platform: str) -> tuple[bool, str]:
        """
        Complete validation for post content

        Args:
            content: The text content
            media_urls: List of media URLs
            platform: Platform name (lowercase)

        Returns:
            tuple: (is_valid, error_message)
        """
        # Validate character limit
        is_valid, error = ContentValidator.validate_character_limit(content, platform)
        if not is_valid:
            return False, error

        # Validate media requirements
        is_valid, error = ContentValidator.validate_media_requirements(content, media_urls, platform)
        if not is_valid:
            return False, error

        return True, ""


def get_platform_character_limit(platform: str) -> int:
    """Get character limit for platform"""
    platform = platform.lower()
    return PLATFORM_CHARACTER_LIMITS.get(platform, None)


def get_remaining_characters(content: str, platform: str) -> int:
    """Get remaining characters for platform"""
    limit = get_platform_character_limit(platform)
    if limit is None:
        return -1  # No limit
    return limit - len(content)
