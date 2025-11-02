import ipaddress
import re
from typing import Optional, Tuple
from urllib.parse import urlparse
import ipaddress
from app.services.url_cleaner import remove_tracking_parameters


def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and sanitize user-submitted URLs.
    Returns (is_valid, error_message, normalized_url) tuple.
    The normalized_url will be None if validation fails.
    """
    if not url:
        return False, "URL cannot be empty", None

    # Auto-prepend https:// if no scheme is provided
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Check URL format
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format", None

    # Ensure scheme is HTTP or HTTPS
    if parsed.scheme not in ["http", "https"]:
        return False, "Only HTTP and HTTPS URLs are allowed", None

    # Ensure there's a hostname
    if not parsed.netloc:
        return False, "Invalid URL: missing hostname", None

    # Check for private/internal IP addresses (SSRF prevention)
    try:
        # Extract hostname without port
        hostname = parsed.netloc.split(":")[0]

        # Try to parse as IP address
        ip = ipaddress.ip_address(hostname)

        # Block private IP ranges
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False, "Private/internal IP addresses are not allowed", None
    except ValueError:
        # Not an IP address, it's a domain name - that's fine
        pass

    # Block localhost variations
    localhost_patterns = [
        r"^localhost$",
        r"^127\.",
        r"^0\.0\.0\.0$",
        r"^::1$",
        r"^0:0:0:0:0:0:0:1$",
    ]

    hostname = parsed.netloc.split(":")[0].lower()
    for pattern in localhost_patterns:
        if re.match(pattern, hostname):
            return False, "Localhost URLs are not allowed", None

    url = remove_tracking_parameters(url)

    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)", None

    return True, None, url
