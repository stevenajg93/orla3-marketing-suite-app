from dotenv import load_dotenv
import os

def load_environment():
    # Walk upward until we find .env.local
    base_path = os.path.abspath(os.path.dirname(__file__))
    while base_path != '/':
        env_path = os.path.join(base_path, ".env.local")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            return
        base_path = os.path.dirname(base_path)
    print("⚠️  .env.local not found; environment variables not loaded")
