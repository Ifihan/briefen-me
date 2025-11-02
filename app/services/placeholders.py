"""Compatibility shim for placeholder patterns.

This module used to contain PLACEHOLDER_PATTERNS and content_is_placeholder.
Those were moved to :mod:`app.constants.patterns`. Import from there instead
to avoid duplicating the list.
"""

from app.constants.patterns import PLACEHOLDER_PATTERNS, content_is_placeholder

__all__ = ["PLACEHOLDER_PATTERNS", "content_is_placeholder"]
