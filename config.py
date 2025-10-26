import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///briefen_me.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "100 per hour")

    # URL Shortener Settings
    MAX_SLUG_LENGTH = 50
    SLUG_GENERATION_BATCHES = 3
    SLUG_OPTIONS_PER_BATCH = 5

    AI_THINKING_MODE = os.getenv("AI_THINKING_MODE", "ai_generated")

    # Caching
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")
    CACHE_DEFAULT_TIMEOUT = 300

    # Mailgun Email Configuration
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "mail.briefen.me")
    MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL", "Briefen <noreply@mail.briefen.me>")
