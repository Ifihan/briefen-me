import re
from typing import List

# Centralized placeholder phrases used by JS-only or error pages
PLACEHOLDER_PATTERNS: List[str] = [
    r"enable javascript",
    r"turn on javascript",
    r"javascript is disabled",
    r"please enable javascript",
    r"js-disabled",
    r"enable-javascript",
    r"x-javascript-error",
]


def content_is_placeholder(text: str) -> bool:
    """Return True when the provided text looks like a JS placeholder page."""
    if not text:
        return False
    lower = re.sub(r"[^a-z0-9\s-]", " ", text.lower())
    for pat in PLACEHOLDER_PATTERNS:
        if re.search(pat, lower):
            return True
    return False
