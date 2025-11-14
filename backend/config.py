import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")

    # AI APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")  # Deprecated, keeping for backwards compatibility

    # Application URLs
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Google Drive
    SHARED_DRIVE_ID = os.getenv("SHARED_DRIVE_ID", "0AM2nUL9uMdpsUk9PVA")
    SHARED_DRIVE_NAME = os.getenv("SHARED_DRIVE_NAME", "GECS Labs")
    MARKETING_FOLDER_NAME = os.getenv("MARKETING_FOLDER_NAME", "Marketing")

    # OAuth Credentials - Social Platforms
    INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID")
    INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET")

    LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")

    FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_CLIENT_SECRET")

    TWITTER_CLIENT_ID = os.getenv("TWITTER_CLIENT_ID")
    TWITTER_CLIENT_SECRET = os.getenv("TWITTER_CLIENT_SECRET")

    TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
    TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")

    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")

    TUMBLR_CONSUMER_KEY = os.getenv("TUMBLR_CONSUMER_KEY")
    TUMBLR_CONSUMER_SECRET = os.getenv("TUMBLR_CONSUMER_SECRET")

    WORDPRESS_CLIENT_ID = os.getenv("WORDPRESS_CLIENT_ID")
    WORDPRESS_CLIENT_SECRET = os.getenv("WORDPRESS_CLIENT_SECRET")

    # JWT Authentication
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production-PLEASE")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
    
    @classmethod
    def validate(cls):
        required = {"OPENAI_API_KEY": cls.OPENAI_API_KEY, "ANTHROPIC_API_KEY": cls.ANTHROPIC_API_KEY}
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing: {', '.join(missing)}")
        return True

Config.validate()
