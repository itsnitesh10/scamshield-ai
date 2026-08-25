import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME = "ScamShield AI"
    ENV = os.getenv("ENV", "development")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "none")
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "")

    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "8"))
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}

    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
