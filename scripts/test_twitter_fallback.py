#!/usr/bin/env python3
"""
Manual test helper for Twitter/X fallback behavior.
Run this from the repo root. It creates a minimal Flask app context so `scrape_webpage` can read config.

Usage:
    python scripts/test_twitter_fallback.py https://x.com/user/status/1234567890
"""
import sys
import json
from flask import Flask

from app.services.web_scraper import scrape_webpage


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_twitter_fallback.py <url>")
        sys.exit(2)

    url = sys.argv[1]

    app = Flask(__name__)
    # Load default config from the project's config module
    app.config.from_object("config.Config")

    with app.app_context():
        print(f"Testing scrape for: {url}\n")
        result = scrape_webpage(url)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
