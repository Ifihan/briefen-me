import requests
from bs4 import BeautifulSoup
from requests.exceptions import Timeout, ConnectionError, HTTPError, TooManyRedirects
from urllib.parse import urlparse, urlunparse
from typing import Optional, Dict
from flask import current_app


_PLACEHOLDER_PATTERNS = [
    "enable javascript",
    "js-disabled",
    "x-javascript-error",
    "javascript is required",
]


def scrape_webpage(url: str, timeout: int = 15) -> Dict:
    """
    Scrape webpage content for AI analysis with comprehensive error handling.
    Returns dict with title, description, and main content.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; BriefenMe/1.0; +http://briefen.me)"
        }
        with requests.Session() as session:
            session.max_redirects = 5
            response = session.get(
                url, headers=headers, timeout=timeout, allow_redirects=True
            )

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

            def _looks_like_js_blocked(text: Optional[str]) -> bool:
                if not text:
                    return False
                lower = text.lower()
                return any(b in lower for b in _PLACEHOLDER_PATTERNS)

            parsed = urlparse(url)
            host = parsed.netloc.lower() if parsed.netloc else ""
            fallback_used: Optional[str] = None

            # Properly check if the host is twitter.com or x.com (including subdomains)
            is_twitter = host == "twitter.com" or host.endswith(".twitter.com")
            is_x = host == "x.com" or host.endswith(".x.com")

            if _looks_like_js_blocked(response.text) and (is_twitter or is_x):
                try:
                    fallbacks = current_app.config.get("TWITTER_FALLBACKS", ["nitter.net"])
                    if isinstance(fallbacks, str):
                        fallbacks = [h.strip() for h in fallbacks.split(",") if h.strip()]

                    tried = []
                    for fb in fallbacks:
                        # Attempt to replace the host with the fallback host
                        fb_netloc = host.replace("twitter.com", fb).replace("x.com", fb)
                        fb_parsed = parsed._replace(scheme="https", netloc=fb_netloc)
                        fb_url = urlunparse(fb_parsed)
                        tried.append(fb_url)
                        fb_resp = session.get(fb_url, headers=headers, timeout=timeout)
                        if fb_resp.status_code == 200 and "text/html" in fb_resp.headers.get("Content-Type", "") and not _looks_like_js_blocked(fb_resp.text):
                            response = fb_resp
                            url = fb_url
                            fallback_used = fb
                            break

                    if (not response or _looks_like_js_blocked(response.text)):
                        text_proxy = current_app.config.get("TEXT_PROXY_URL")
                        if text_proxy:
                            tp = text_proxy.strip()
                            if not tp.endswith("http://") and not tp.endswith("https://"):
                                tp = tp.rstrip("/") + "/http://"

                            proxy_url = tp + parsed.netloc + parsed.path
                            if parsed.query:
                                proxy_url += f"?{parsed.query}"

                            proxy_resp = session.get(proxy_url, headers=headers, timeout=timeout)
                            if proxy_resp.status_code == 200 and len(proxy_resp.text or "") > 50:
                                response = proxy_resp
                                url = proxy_url
                                fallback_used = "text-proxy"
                except Exception:
                    # If fallbacks fail, continue and allow later checks to handle the no-content case
                    pass

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
                "fallback_used": fallback_used,
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
