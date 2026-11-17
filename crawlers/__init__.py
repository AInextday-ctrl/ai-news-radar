"""
Crawlers Module - Dedicated, Isolated Source Crawlers
=====================================================
Each news source has its own isolated crawler implementation to guarantee:
1. Complete separation of concerns: modifying one source never impacts another.
2. Source-specific DOM selectors, anti-bot handling, and syndication resolution.
3. Lockable contracts: once verified and accepted by user, each module is locked.
"""

from .reuters_crawler import crawl_reuters, is_reuters_url
from .bloomberg_crawler import crawl_bloomberg, is_bloomberg_url, resolve_bloomberg_broadcast_media

__all__ = [
    "crawl_reuters",
    "is_reuters_url",
    "crawl_bloomberg",
    "is_bloomberg_url",
    "resolve_bloomberg_broadcast_media"
]
