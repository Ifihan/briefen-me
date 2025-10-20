import re
from urllib.parse import urlparse
import ipaddress


def validate_url(url):
    """
    Validate and sanitize user-submitted URLs.
    Returns (is_valid, error_message) tuple.
    """
    if not url:
        return False, "URL cannot be empty"

    # Check URL format
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Ensure scheme is HTTP or HTTPS
    if parsed.scheme not in ['http', 'https']:
        return False, "Only HTTP and HTTPS URLs are allowed"

    # Ensure there's a hostname
    if not parsed.netloc:
        return False, "Invalid URL: missing hostname"

    # Check for private/internal IP addresses (SSRF prevention)
    try:
        # Extract hostname without port
        hostname = parsed.netloc.split(':')[0]

        # Try to parse as IP address
        ip = ipaddress.ip_address(hostname)

        # Block private IP ranges
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False, "Private/internal IP addresses are not allowed"
    except ValueError:
        # Not an IP address, it's a domain name - that's fine
        pass

    # Block localhost variations
    localhost_patterns = [
        r'^localhost$',
        r'^127\.',
        r'^0\.0\.0\.0$',
        r'^::1$',
        r'^0:0:0:0:0:0:0:1$'
    ]

    hostname = parsed.netloc.split(':')[0].lower()
    for pattern in localhost_patterns:
        if re.match(pattern, hostname):
            return False, "Localhost URLs are not allowed"

    # URL length check
    if len(url) > 2048:
        return False, "URL is too long (max 2048 characters)"

    return True, None