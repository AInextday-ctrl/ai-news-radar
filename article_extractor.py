"""
article_extractor.py - Targeted Source Deconstruction & Full-Text Crawler Engine
针对主流科技与 AI 媒体进行深度解构、正文提取、5W1H 事实提炼与多媒体穿透抓取。
"""

import os
import re
import html
import time
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    import httpx
    HAS_CURL_CFFI = False


class ArticleExtractor:
    """
    针对主流权威媒体定制的高可用深度解构抓取器。
    支持 Wired, Bloomberg, Reuters, NYT, MIT Tech Review, Gizmodo,
    The Verge, TechCrunch, Ars Technica, Fortune, New Yorker, SemiAnalysis,
    CTech, Axios, EU-Startups, Colossus, YC Labs 等媒体。
    """

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    # 常见媒体特定正文容器与选择器规则 (按优先级排列)
    SOURCE_RULES = {
        "wired.com": {
            "containers": [
                r'class="[^"]*body__inner-container[^"]*"[^>]*>(.*?)</div>\s*</div>',
                r'<article[^>]*>(.*?)</article>',
                r'class="[^"]*article-body-component[^"]*"[^>]*>(.*?)</div>',
            ],
            "p_pattern": r'<p[^>]*class="[^"]*paywall[^"]*"[^>]*>(.*?)</p>',
        },
        "theverge.com": {
            "containers": [
                r'class="[^"]*c-entry-content[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*duet--article--article-body-component[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "technologyreview.com": {
            "containers": [
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
                r'id="content--body"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "gizmodo.com": {
            "containers": [
                r'class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "fortune.com": {
            "containers": [
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*gutenberg-content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "arstechnica.com": {
            "containers": [
                r'class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*article-guts[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "techcrunch.com": {
            "containers": [
                r'class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "newyorker.com": {
            "containers": [
                r'class="[^"]*body__inner-container[^"]*"[^>]*>(.*?)</div>\s*</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "calcalistech.com": {
            "containers": [
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*text-wrapper[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*articleText[^"]*"[^>]*>(.*?)</div>',
            ],
        },
        "semianalysis.com": {
            "containers": [
                r'class="[^"]*body\s+markup[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*post-content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "axios.com": {
            "containers": [
                r'data-cy="story-text"[^>]*>(.*?)</div>',
                r'class="[^"]*story-text[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "nytimes.com": {
            "containers": [
                r'name="articleBody"[^>]*>(.*?)</section>',
                r'class="[^"]*StoryBodyCompanionColumn[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "bloomberg.com": {
            "containers": [
                r'class="[^"]*body-copy[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "reuters.com": {
            "containers": [
                r'data-testid="article-body"[^>]*>(.*?)</div>',
                r'class="[^"]*article-body__content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
        "the-decoder.com": {
            "containers": [
                r'class="[^"]*entry-content[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
            ],
        },
    }

    # 常见广告、免责声明、社交引导等噪声过滤关键词
    NOISE_KEYWORDS = [
        "newsletter", "subscribe", "subscription", "terms of use", "privacy policy",
        "cookie policy", "sign up for", "read more:", "photo by", "getty images",
        "all rights reserved", "follow us on", "advertisement", "enable javascript",
        "opens in new tab", "click here", "support independent journalism",
        "this article originally appeared", "share this article", "related stories",
        "disclosure:", "affiliate links", "correction:", "listen to this article"
    ]

    @classmethod
    def fetch_html(cls, url: str, timeout: int = 12) -> Optional[str]:
        """Fetch raw HTML using curl_cffi with Chrome TLS impersonation, fallback to httpx."""
        if not url or not url.startswith("http"):
            return None

        # 1. 优先使用 curl_cffi 模拟 Chrome 浏览器指纹，绕过 Cloudflare 与反爬
        if HAS_CURL_CFFI:
            try:
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "DNT": "1",
                    "Upgrade-Insecure-Requests": "1"
                }
                resp = curl_requests.get(url, impersonate="chrome", headers=headers, timeout=timeout)
                if resp.status_code == 200 and len(resp.text) > 500:
                    return resp.text
            except Exception as e:
                pass

        # 2. 降级使用 httpx
        try:
            import httpx
            with httpx.Client(
                headers={"User-Agent": cls.USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
                follow_redirects=True,
                timeout=timeout
            ) as client:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.text) > 500:
                    return resp.text
        except Exception:
            pass

        return None

    @classmethod
    def extract_article(cls, url: str, html_text: Optional[str] = None) -> Dict[str, Any]:
        """
        深度解构文章，提取段落、小标题、关键引语、数据指标与高清配图。
        """
        result = {
            "url": url,
            "status": "failed",
            "domain": "",
            "title": "",
            "cover_image": None,
            "lead_paragraph": "",
            "paragraphs": [],
            "full_text": "",
            "subheadings": [],
            "key_metrics": [],
            "quotes": [],
            "paras_count": 0,
            "is_substantive": False
        }

        if not url:
            return result

        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        result["domain"] = domain

        # 获取 HTML
        if not html_text:
            html_text = cls.fetch_html(url)
        if not html_text:
            return result

        # 1. 提取高清配图 (og:image / twitter:image)
        m_img = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_img:
            cand_img = html.unescape(m_img.group(1)).strip()
            if not any(bad in cand_img.lower() for bad in ["pml.png", "techmeme.com", "pixel", "spacer", "tracking", "avatar", "icon", "placeholder"]):
                result["cover_image"] = cand_img

        # 2. 提取 meta description 备用导语
        m_desc = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_desc:
            desc_val = html.unescape(m_desc.group(1)).strip()
            if len(desc_val) > 20 and not any(bad in desc_val.lower() for bad in ["javascript", "enable cookies", "cloudflare"]):
                result["lead_paragraph"] = desc_val

        # 3. 寻找正文容器
        clean_html = re.sub(r'<(?:script|style|svg|noscript|header|nav|footer|aside|form|menu)[^>]*>.*?</(?:script|style|svg|noscript|header|nav|footer|aside|form|menu)>', ' ', html_text, flags=re.DOTALL | re.I)
        clean_html = re.sub(r'<div[^>]+(?:class|id)=["\x27][^"\x27]*(?:header|navbar|menu|navigation|sidebar|footer|cookie|banner|share|modal|popup|login|ad-|advertisement)[^"\x27]*["\x27][^>]*>.*?</\s*div\s*>', ' ', clean_html, flags=re.DOTALL | re.I)

        rule = None
        for d_key, r_cfg in cls.SOURCE_RULES.items():
            if d_key in domain:
                rule = r_cfg
                break

        candidate_containers = []
        if rule and "containers" in rule:
            for pat in rule["containers"]:
                for m in re.finditer(pat, clean_html, flags=re.DOTALL | re.IGNORECASE):
                    candidate_containers.append(m.group(1))

        # 通用语义容器兜底
        for pat in [
            r'class="[^"]*(?:article-body|story-body|entry-content|post-content|main-content)[^"]*"[^>]*>(.*?)</div>',
            r'<article[^>]*>(.*?)</article>',
            r'<main[^>]*>(.*?)</main>',
        ]:
            for m in re.finditer(pat, clean_html, flags=re.DOTALL | re.IGNORECASE):
                candidate_containers.append(m.group(1))

        best_container = clean_html
        best_p_count = 0
        for c in candidate_containers:
            p_cnt = len(re.findall(r'<p[^>]*>', c))
            if p_cnt > best_p_count:
                best_p_count = p_cnt
                best_container = c

        # 4. 提取段落与小标题
        p_pattern = r'<p[^>]*>(.*?)</p>'
        if rule and "p_pattern" in rule:
            special_paras = re.findall(rule["p_pattern"], best_container, flags=re.DOTALL | re.IGNORECASE)
            if len(special_paras) >= 3:
                raw_paras = special_paras
            else:
                raw_paras = re.findall(p_pattern, best_container, flags=re.DOTALL | re.IGNORECASE)
        else:
            raw_paras = re.findall(p_pattern, best_container, flags=re.DOTALL | re.IGNORECASE)

        # 提取小标题 (H2, H3)
        raw_headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', best_container, flags=re.DOTALL | re.IGNORECASE)
        subheadings = []
        for h_str in raw_headings:
            clean_h = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', h_str)).split()).strip()
            if 4 <= len(clean_h) <= 100 and not any(b in clean_h.lower() for b in ["comments", "subscribe", "share", "related"]):
                subheadings.append(clean_h)
        result["subheadings"] = subheadings[:8]

        clean_paras = []
        seen = set()
        for p_str in raw_paras:
            clean_p = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', p_str)).split()).strip()
            if len(clean_p) < 40 or len(clean_p) > 4000:
                continue
            
            p_lower = clean_p.lower()
            if any(bad in p_lower for bad in cls.NOISE_KEYWORDS):
                continue
            if not re.search(r'[.!?。！？;；]', clean_p):
                continue
            if clean_p.startswith("(") or clean_p.startswith("（"):
                continue

            # 去重
            p_norm = re.sub(r'\s+', '', p_lower[:50])
            if p_norm in seen:
                continue
            seen.add(p_norm)
            clean_paras.append(clean_p)

        # 5. 提取关键引语 (Direct Quotes)
        quotes = []
        quote_pats = [
            r'["“]([^"”]{20,200})["”]\s*(?:said|says|wrote|added|noted|explained|according to)\s+([A-Z][a-zA-Z\s\.\-]+)',
            r'([A-Z][a-zA-Z\s\.\-]+)\s+(?:said|says|wrote|added|noted|explained):\s*["“]([^"”]{20,200})["”]'
        ]
        full_raw_paras_text = "\n\n".join(clean_paras)
        for qp in quote_pats:
            for qm in re.finditer(qp, full_raw_paras_text):
                quotes.append(f'"{qm.group(1).strip()}" — {qm.group(2).strip()}')
        result["quotes"] = quotes[:5]

        # 6. 提取硬核数据与度量 (Numbers, Dollars, Percentages)
        key_metrics = []
        metric_matches = re.findall(r'(?:\$[\d\.]+\s*(?:billion|million|trillion|B|M|k)?|\b\d+(?:,\d{3})*\s*(?:apps|domains|users|subscribers|models|parameters|tokens|GPUs|chips|percent|%|hours|weeks|months|years)\b)', full_raw_paras_text, re.I)
        for mm in metric_matches:
            mm_clean = mm.strip()
            if mm_clean and mm_clean not in key_metrics:
                key_metrics.append(mm_clean)
        result["key_metrics"] = key_metrics[:8]

        result["paragraphs"] = clean_paras
        result["paras_count"] = len(clean_paras)
        result["full_text"] = "\n\n".join(clean_paras)
        result["is_substantive"] = (len(clean_paras) >= 3) or (len(result["full_text"]) >= 400)
        
        if result["paragraphs"] and not result["lead_paragraph"]:
            result["lead_paragraph"] = result["paragraphs"][0]

        if result["is_substantive"]:
            result["status"] = "success"

        return result


def extract_article_substantive(url: str, html_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Convenience helper to extract article if substantive, else return None."""
    data = ArticleExtractor.extract_article(url, html_text)
    if data.get("is_substantive"):
        return data
    return None
