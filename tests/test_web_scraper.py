import json
from unittest.mock import patch

import runpy

# Load module directly to avoid importing the full `app` package which requires Flask
web_scraper = runpy.run_path("app/services/web_scraper.py")


class MockResponse:
    def __init__(self, status_code=200, json_data=None, text="", headers=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self.headers = headers or {"Content-Type": "text/html"}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class MockSession:
    def __init__(self, responses):
        # responses: dict[url] -> MockResponse
        self._responses = responses
        self.max_redirects = 5

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, timeout=None, allow_redirects=True):
        # Return matching response if present, else a generic 404
        for key in self._responses:
            if key in url:
                return self._responses[key]
        return MockResponse(status_code=404)


def test_oembed_tweet_extraction():
    tweet_url = "https://twitter.com/alice/status/12345"
    oembed_json = {
        "html": "<blockquote class=\"twitter-tweet\">Hello world from Alice</blockquote>",
        "author_name": "Alice",
    }

    responses = {"publish.twitter.com/oembed": MockResponse(200, json_data=oembed_json)}

    with patch("requests.Session", return_value=MockSession(responses)):
        result = web_scraper.get("scrape_webpage") and web_scraper["scrape_webpage"](tweet_url)

    assert result["success"] is True
    assert "Alice" in result["title"]
    assert "Hello world from Alice" in result["content"]


def test_tweet_oembed_fallback_private():
    # Simulate oEmbed failing (e.g., private tweet) and main page containing JS placeholder
    tweet_url = "https://twitter.com/bob/status/99999"

    oembed_fail = MockResponse(status_code=404)
    page_text = "Enable JavaScript to view this content"
    page_resp = MockResponse(status_code=200, text=f"<html><body>{page_text}</body></html>")
    page_resp.headers = {"Content-Type": "text/html"}

    responses = {"publish.twitter.com/oembed": oembed_fail, tweet_url: page_resp}

    with patch("requests.Session", return_value=MockSession(responses)):
        result = web_scraper.get("scrape_webpage") and web_scraper["scrape_webpage"](tweet_url)

    assert result["success"] is False
    assert result["error_type"] == "content_unavailable"
