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
from .fortune_crawler import crawl_fortune, is_fortune_url
from .wsj_crawler import crawl_wsj, is_wsj_url
from .verge_crawler import crawl_verge, is_verge_url
from .nyt_crawler import crawl_nyt, is_nyt_url
from .wapo_crawler import crawl_wapo, is_wapo_url
from .washsun_crawler import crawl_washsun, is_washsun_url
from .ft_crawler import crawl_ft, is_ft_url
from .wired_crawler import crawl_wired, is_wired_url
from .mittr_crawler import crawl_mittr, is_mittr_url
from .techcrunch_crawler import crawl_techcrunch, is_techcrunch_url
from .arstechnica_crawler import crawl_arstechnica, is_arstechnica_url
from .cnbc_crawler import crawl_cnbc, is_cnbc_url
from .decoder_crawler import crawl_decoder, is_decoder_url
from .openai_crawler import crawl_openai, is_openai_url
from .siliconangle_crawler import crawl_siliconangle, is_siliconangle_url
from .semafor_crawler import crawl_semafor, is_semafor_url
from .coindesk_crawler import crawl_coindesk, is_coindesk_url
from .cbsnews_crawler import crawl_cbsnews, is_cbsnews_url
from .ifixit_crawler import crawl_ifixit, is_ifixit_url
from .nineto5mac_crawler import crawl_nineto5mac, is_nineto5mac_url
from .tomshardware_crawler import crawl_tomshardware, is_tomshardware_url
from .bbc_crawler import crawl_bbc, is_bbc_url
from .content_filters import is_low_value_roundup_or_promo, detect_low_value_roundup_or_promo

__all__ = [
    "crawl_reuters",
    "is_reuters_url",
    "crawl_bloomberg",
    "is_bloomberg_url",
    "resolve_bloomberg_broadcast_media",
    "crawl_fortune",
    "is_fortune_url",
    "crawl_wsj",
    "is_wsj_url",
    "crawl_verge",
    "is_verge_url",
    "crawl_nyt",
    "is_nyt_url",
    "crawl_wapo",
    "is_wapo_url",
    "crawl_washsun",
    "is_washsun_url",
    "crawl_ft",
    "is_ft_url",
    "crawl_wired",
    "is_wired_url",
    "crawl_mittr",
    "is_mittr_url",
    "crawl_techcrunch",
    "is_techcrunch_url",
    "crawl_arstechnica",
    "is_arstechnica_url",
    "crawl_cnbc",
    "is_cnbc_url",
    "crawl_decoder",
    "is_decoder_url",
    "crawl_openai",
    "is_openai_url",
    "crawl_siliconangle",
    "is_siliconangle_url",
    "crawl_semafor",
    "is_semafor_url",
    "crawl_coindesk",
    "is_coindesk_url",
    "crawl_cbsnews",
    "is_cbsnews_url",
    "crawl_ifixit",
    "is_ifixit_url",
    "crawl_nineto5mac",
    "is_nineto5mac_url",
    "crawl_tomshardware",
    "is_tomshardware_url",
    "crawl_bbc",
    "is_bbc_url",
    "is_low_value_roundup_or_promo",
    "detect_low_value_roundup_or_promo"
]
