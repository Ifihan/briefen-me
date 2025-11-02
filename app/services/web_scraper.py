import re
from typing import Any, Dict
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, HTTPError, Timeout, TooManyRedirects

from app.constants.patterns import PLACEHOLDER_PATTERNS


def scrape_webpage(url: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Scrape webpage content for AI analysis with comprehensive error handling.
    Returns dict with title, description, and main content.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; BriefenMe/1.0; +http://briefen.me)"}
        with requests.Session() as session:
            session.max_redirects = 5
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            path = parsed.path or ""

            if hostname.endswith("twitter.com") or hostname.endswith("x.com"):
                if "/status/" in path or "/statuses/" in path:
                    try:
                        oembed_url = f"https://publish.twitter.com/oembed?url={quote_plus(url)}&omit_script=1"
                        resp = session.get(oembed_url, headers=headers, timeout=timeout)
                        resp.raise_for_status()
                        data = resp.json()

                        html = data.get("html", "")
                        author_name = data.get("author_name", "Twitter")

                        if html:
                            soup_emb = BeautifulSoup(html, "html.parser")
                            tweet_text = soup_emb.get_text(separator=" ", strip=True)
                        else:
                            tweet_text = ""

                        title = f"{author_name} on Twitter"
                        description = tweet_text[:160]
                        content = tweet_text

                        if content:
                            return {
                                "success": True,
                                "title": title,
                                "description": description,
                                "content": content,
                                "url": url,
                            }
                    except Exception:
                        pass

            response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)

            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "This page requires authentication. Please use a publicly accessible URL.",
                    "error_type": "unauthorized",
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Access to this page is forbidden. We cannot access private or restricted content. Please use a public URL.",
                    "error_type": "forbidden",
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Page not found. Please check the URL and try again.",
                    "error_type": "not_found",
                }
            elif response.status_code >= 500:
                return {
                    "success": False,
                    "error": "The website's server is currently unavailable. Please try again later.",
                    "error_type": "server_error",
                }

            response.raise_for_status()

            # Check if content is actually HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return {
                    "success": False,
                    "error": "This URL doesn't point to a webpage. Please provide a link to a web page.",
                    "error_type": "invalid_content",
                }

            soup = BeautifulSoup(response.text, "html.parser")

            title = ""
            if soup.title:
                title = soup.title.string.strip() if soup.title.string else ""
            if not title and soup.find("h1"):
                title = soup.find("h1").get_text().strip()

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"].strip()

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            main_text = soup.get_text(separator=" ", strip=True)[:1000]

            lower_text = re.sub(r"[^a-z0-9\s-]", " ", main_text.lower())
            for pat in PLACEHOLDER_PATTERNS:
                if re.search(pat, lower_text):
                    return {
                        "success": False,
                        "error": (
                            "This page appears to require JavaScript to render its content "
                            "(e.g. 'Enable JavaScript'). We couldn't extract meaningful content."
                        ),
                        "error_type": "content_unavailable",
                    }

            if not title and not description and len(main_text) < 50:
                return {
                    "success": False,
                    "error": "Unable to extract meaningful content from this page. The page might be empty or require JavaScript to load.",
                    "error_type": "no_content",
                }

            return {
                "success": True,
                "title": title,
                "description": description,
                "content": main_text,
                "url": url,
            }

    except Timeout:
        return {
            "success": False,
            "error": f"This page is taking too long to load (>{timeout}s). Please try a different URL or try again later.",
            "error_type": "timeout",
        }
    except ConnectionError:
        return {
            "success": False,
            "error": "Unable to connect to this website. Please check the URL and your internet connection.",
            "error_type": "connection_error",
        }
    except TooManyRedirects:
        return {
            "success": False,
            "error": "This URL has too many redirects. Please try the final destination URL directly.",
            "error_type": "too_many_redirects",
        }
    except HTTPError as e:
        return {
            "success": False,
            "error": f"HTTP error occurred: {str(e)}",
            "error_type": "http_error",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"An unexpected error occurred while processing this page: {str(e)}",
            "error_type": "unknown_error",
        }
