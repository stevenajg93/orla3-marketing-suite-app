import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    SHARED_DRIVE_ID = os.getenv("SHARED_DRIVE_ID", "0AM2nUL9uMdpsUk9PVA")
    SHARED_DRIVE_NAME = os.getenv("SHARED_DRIVE_NAME", "GECS Labs")
    MARKETING_FOLDER_NAME = os.getenv("MARKETING_FOLDER_NAME", "Marketing")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    
    @classmethod
    def validate(cls):
        required = {"OPENAI_API_KEY": cls.OPENAI_API_KEY, "ANTHROPIC_API_KEY": cls.ANTHROPIC_API_KEY}
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing: {', '.join(missing)}")
        return True

Config.validate()
