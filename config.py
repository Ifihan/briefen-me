import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///briefen_me.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_pre_ping": True,
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
        "pool_timeout": 30,
    }

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "100 per hour")

    MAX_SLUG_LENGTH = 50
    SLUG_GENERATION_BATCHES = 3
    SLUG_OPTIONS_PER_BATCH = 5

    AI_THINKING_MODE = os.getenv("AI_THINKING_MODE", "ai_generated")

    TWITTER_FALLBACKS = os.getenv("TWITTER_FALLBACKS", "nitter.net").split(",")

    TEXT_PROXY_URL = os.getenv("TEXT_PROXY_URL", "https://r.jina.ai/http://")

    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")
    CACHE_DEFAULT_TIMEOUT = 300

    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "mail.briefen.me")
    MAILGUN_FROM_EMAIL = os.getenv(
        "MAILGUN_FROM_EMAIL", "Briefen <noreply@mail.briefen.me>"
    )
