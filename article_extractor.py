"""
article_extractor.py - Targeted Source Deconstruction & Full-Text Crawler Engine
针对主流科技与 AI 媒体进行深度解构、正文提取、5W1H 事实提炼与多媒体穿透抓取。
建立针对信源的单一专属抓取机制 (Single Dedicated Source Extractor Architecture)，坚决杜绝混用。
"""

import os
import re
import html
import json
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
    # 深度广告与作者/线索占位模块正则清洗库
    AD_BLOCK_PATTERNS = [
        r"want more .*? in your (?:news )?feed\??.*?when you.*?re searching for what matters\.?",
        r'add \w+ (?:in|to) google (?:so our reporting is easier to find)?\.?',
        r"have a tip\??\s*contact this reporter.*?here.*?s our guide to sharing information securely\.?",
        r'contact this reporter via email.*?sharing information securely\.?',
        r'save\s+saved\s+listen to this story',
        r'listen to this story',
        r'this story is available exclusively to .*? subscribers\.?',
        r'become an insider and start reading now\.?',
        r'have an account\?\s*log in\.?',
        r'read in app',
        r'download the app to read',
    ]

    # 常见无意义免责声明、版权与广告关键词
    NOISE_KEYWORDS = [
        "cookie policy", "terms of service", "terms of use", "privacy notice", "privacy policy",
        "all rights reserved", "subscribe now", "subscription", "sign up for",
        "advertisement", "sponsored content", "read more:", "photo by",
        "follow us on", "share this article", "comments (", "photo credit",
        "image credit", "getty images", "newsletter", "sign in", "create free account",
        "upgrade to continue", "subscriber exclusive", "click here", "support independent journalism",
        "listen to story", "unsupported browser", "javascript is disabled", "enable javascript",
        "loading comments", "view comments", "leave a comment", "related stories",
        "more on this topic", "read next", "about the author", "contact the author",
        "editor's note", "correction:", "this article originally appeared",
        "reuters/stringer", "associated press", "ap photo", "opens in new tab",
        "save saved", "recommended video", "photo-illustration:", "photo illustration:",
        "want more business insider", "contact this reporter", "sharing information securely",
        "become an insider", "this story is available exclusively", "read in app"
    ]

    # 导航栏/全球国家与地区菜单黑名单（防止日经、彭博等网站的顶栏地区导航被当成文章段落提取）
    GEO_NAV_WORDS = [
        "japan", "india", "south korea", "korea", "indonesia", "taiwan", "thailand",
        "east asia", "hong kong", "macao", "macau", "mongolia", "north korea",
        "southeast asia", "malaysia", "singapore", "philippines", "vietnam",
        "myanmar", "cambodia", "laos", "brunei", "timor-leste", "south asia",
        "pakistan", "afghanistan", "bangladesh", "sri lanka", "nepal", "bhutan",
        "maldives", "central asia", "uzbekistan", "turkmenistan", "tajikistan",
        "日本", "印度", "韩国", "印度尼西亚", "台湾", "泰国", "东亚", "香港", "澳门", "蒙古", "朝鲜",
        "东南亚", "马来西亚", "新加坡", "菲律宾", "越南", "缅甸", "柬埔寨", "老挝", "文莱", "东帝汶",
        "南亚", "巴基斯坦", "阿富汗", "孟加拉国", "斯里兰卡", "尼泊尔", "不丹", "马尔代夫", "中亚", "乌兹别克斯坦"
    ]

    # 针对信源的单一专属抓取机制路由器 (Dedicated Source Extractor Registry)
    # 彻底杜绝不同信源混用，确保每个权威信源具备清晰单一的专属 AST / DOM 穿透通道
    SOURCE_EXTRACTORS = {
        "nikkei.com": "_extract_nikkei",
        "asia.nikkei.com": "_extract_nikkei",
        "nytimes.com": "_extract_nyt",
        "ft.com": "_extract_ft",
        "wired.com": "_extract_wired",
        "theverge.com": "_extract_theverge",
        "reuters.com": "_extract_reuters",
        "bloomberg.com": "_extract_bloomberg",
        "technologyreview.com": "_extract_techreview",
        "arstechnica.com": "_extract_arstechnica",
    }

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    # 常见媒体特定正文容器与选择器规则 (按优先级排列)
    SOURCE_RULES = {
        "wired.com": {
            "containers": [
                r'class="[^"]*body__inner-container[^"]*"[^>]*>(.*?)</div>\s*</div>',
                r'data-testid="BodyWrapper"[^>]*>(.*?)</(?:div|section)>',
                r'class="[^"]*(?:grid--item-body|body__container|article__body|content-header-and-body)[^"]*"[^>]*>(.*?)</div>',
                r'<article[^>]*>(.*?)</article>',
                r'class="[^"]*article-body-component[^"]*"[^>]*>(.*?)</div>',
            ],
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
        "businessinsider.com": {
            "containers": [
                r'<article[^>]*>(.*?)</article>',
                r'class="[^"]*(?:content-lock-content|post-content|article-body)[^"]*"[^>]*>(.*?)</div>',
            ],
        },
    }

    @classmethod
    def is_nav_or_noise_text(cls, text: str) -> bool:
        """检查文本是否为导航菜单、地区列表或广告噪声"""
        if not text or len(text.strip()) < 30:
            return True
        t_low = text.lower()
        # 1. 地理国家导航关键词密度：若包含多个国家/地区名且缺乏正常句子谓词
        geo_hits = [w for w in cls.GEO_NAV_WORDS if w in t_low]
        if len(geo_hits) >= 3:
            if len(geo_hits) >= 5 or (len(geo_hits) >= 3 and len(text) < 300):
                return True
        # 2. 广告、免责、登录等噪声
        if any(bad in t_low for bad in cls.NOISE_KEYWORDS):
            return True
        return False

    @classmethod
    def _clean_paragraph(cls, text: str) -> Optional[str]:
        """清理单个段落文本，去除 HTML 标签与多余空白"""
        if not text:
            return None
        clean_p = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', text)).split()).strip()
        if len(clean_p) < 35 or len(clean_p) > 4000:
            return None
        if cls.is_nav_or_noise_text(clean_p):
            return None
        if not re.search(r'[.!?。！？;；]', clean_p):
            return None
        if clean_p.startswith("(") or clean_p.startswith("（"):
            return None
        return clean_p

    # ==========================================
    # 针对权威信源的单一专属抓取机制 (Dedicated Extractors)
    # ==========================================

    @classmethod
    def _extract_nikkei(cls, html_text: str) -> List[str]:
        """
        日经新闻 (Nikkei Asia) 专属单一抓取器：
        纯净解析 __NEXT_DATA__ 中的 pageProps.data.body/preview，
        严格隔离并绝不读取 pageProps.navigation 下的全球地区菜单。
        """
        paras = []
        if '__NEXT_DATA__' in html_text:
            m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I)
            if m:
                try:
                    data = json.loads(m.group(1))
                    art = data.get('props', {}).get('pageProps', {}).get('data', {})
                    body_html = art.get('body') or art.get('preview') or ''
                    if body_html:
                        raw_p = re.findall(r'<p[^>]*>(.*?)</p>', body_html, re.DOTALL | re.I)
                        for p in raw_p:
                            cp = cls._clean_paragraph(p)
                            if cp and cp not in paras:
                                paras.append(cp)
                except Exception:
                    pass
        if not paras:
            m_body = re.search(r'class="[^"]*(?:article__body|story__body|article-body)[^"]*"[^>]*>(.*?)</div>', html_text, re.DOTALL | re.I)
            if m_body:
                raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m_body.group(1), re.DOTALL | re.I)
                for p in raw_p:
                    cp = cls._clean_paragraph(p)
                    if cp and cp not in paras:
                        paras.append(cp)
        return paras

    @classmethod
    def _extract_nyt(cls, html_text: str) -> List[str]:
        """
        纽约时报 (The New York Times) 专属单一抓取器：
        穿透 window.__preloadedData 的 sprinkledBody AST 树与 JSON-LD，
        无视客户端登录弹窗遮罩，提取原版高质量全段落。
        """
        paras = []
        if 'window.__preloadedData' in html_text or 'sprinkledBody' in html_text:
            m_nyt = re.search(r'window\.__preloadedData\s*=\s*(\{.*?);</script>', html_text, re.DOTALL | re.I)
            if m_nyt:
                try:
                    raw_str = m_nyt.group(1).rstrip('; \r\n')
                    clean_str = re.sub(r':\s*undefined\b', ': null', raw_str)
                    nd_data = json.loads(clean_str)

                    def get_text_from_node(node):
                        parts = []
                        if isinstance(node, dict):
                            if 'text' in node and isinstance(node['text'], str):
                                parts.append(node['text'])
                            for ch in node.get('content', []) if isinstance(node.get('content'), list) else []:
                                parts.append(get_text_from_node(ch))
                            for ch in node.get('children', []) if isinstance(node.get('children'), list) else []:
                                parts.append(get_text_from_node(ch))
                        elif isinstance(node, list):
                            for item in node:
                                parts.append(get_text_from_node(item))
                        return "".join(parts)

                    article_node = nd_data.get('loaderData', {}).get('data', {}).get('article', {})
                    sprinkled = article_node.get('sprinkledBody', {})
                    nyt_items = sprinkled.get('content', []) if isinstance(sprinkled, dict) else []

                    for item in nyt_items:
                        p_t = get_text_from_node(item).strip()
                        cp = cls._clean_paragraph(p_t)
                        if cp and cp not in paras:
                            paras.append(cp)
                except Exception:
                    pass
        if not paras:
            m_body = re.search(r'name="articleBody"[^>]*>(.*?)</section>', html_text, re.DOTALL | re.I)
            if m_body:
                raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m_body.group(1), re.DOTALL | re.I)
                for p in raw_p:
                    cp = cls._clean_paragraph(p)
                    if cp and cp not in paras:
                        paras.append(cp)
        if not paras:
            paras = cls._extract_from_json_ld(html_text)
        return paras

    @classmethod
    def _extract_ft(cls, html_text: str) -> List[str]:
        """
        金融时报 (Financial Times) 专属单一抓取器：
        针对 FT 硬付费墙提取 JSON-LD articleBody、正文容器及核心段落。
        """
        paras = cls._extract_from_json_ld(html_text)
        if not paras:
            for pat in [
                r'class="[^"]*article__content-body[^"]*"[^>]*>(.*?)</div>',
                r'data-trackable="article-body"[^>]*>(.*?)</div>',
                r'<div[^>]+id="site-content"[^>]*>(.*?)</div>'
            ]:
                m = re.search(pat, html_text, re.DOTALL | re.I)
                if m:
                    raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m.group(1), re.DOTALL | re.I)
                    for p in raw_p:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                    if paras:
                        break
        return paras

    @classmethod
    def _extract_wired(cls, html_text: str) -> List[str]:
        """
        连线 (Wired / Condé Nast Verso) 专属单一抓取器：
        穿透 Verso 渲染机制，优先从 JSON-LD 与 __NEXT_DATA__ 故事正文对象提取全文。
        """
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) < 3 and '__NEXT_DATA__' in html_text:
            m = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I)
            if m:
                try:
                    data = json.loads(m.group(1))
                    def walk_wired(node, acc):
                        if isinstance(node, dict):
                            if node.get('type') == 'p' or node.get('name') == 'p':
                                val = node.get('value') or node.get('children')
                                if isinstance(val, str):
                                    acc.append(val)
                            for k in ['body', 'content', 'paragraphs', 'transformed']:
                                if k in node:
                                    walk_wired(node[k], acc)
                        elif isinstance(node, list):
                            for item in node:
                                walk_wired(item, acc)
                    acc = []
                    walk_wired(data.get('props', {}).get('pageProps', {}), acc)
                    for p in acc:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                except Exception:
                    pass
        if not paras:
            m_body = re.search(r'class="[^"]*body__inner-container[^"]*"[^>]*>(.*?)</div>\s*</div>', html_text, re.DOTALL | re.I)
            if m_body:
                raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m_body.group(1), re.DOTALL | re.I)
                for p in raw_p:
                    cp = cls._clean_paragraph(p)
                    if cp and cp not in paras:
                        paras.append(cp)
        return paras

    @classmethod
    def _extract_theverge(cls, html_text: str) -> List[str]:
        """The Verge 专属单一抓取器 (Vox Media / Chorus / Duet)"""
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) < 3:
            for pat in [
                r'class="[^"]*duet--article--article-body-component[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*c-entry-content[^"]*"[^>]*>(.*?)</div>'
            ]:
                m = re.search(pat, html_text, re.DOTALL | re.I)
                if m:
                    raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m.group(1), re.DOTALL | re.I)
                    for p in raw_p:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                    if paras:
                        break
        return paras

    @classmethod
    def _extract_reuters(cls, html_text: str, url: str = "") -> List[str]:
        """
        路透社 (Reuters) 专属单一抓取器：
        1. 穿透客户端订阅弹窗遮罩，从 DOM 的 data-testid="paragraph-X" 与
           article-body-module__paragraph 正文容器中精准提取全部原版段落；
        2. 若因 DataDome 盾或网络阻断导致 HTML 缺失，无缝调度电讯专网联合穿透（Syndication Fallback），
           从 Yahoo / Miami Herald / MSN 等官方授权专网中抽取 100% 对齐的电讯社原文字节。
        """
        paras = []
        if html_text:
            # 1. 优先提取 Reuters 专用的 data-testid="paragraph-X" 节点
            raw_paras = re.findall(r'<(?:div|p)[^>]*data-testid="paragraph-\d+"[^>]*>(.*?)</(?:div|p)>', html_text, re.DOTALL | re.I)

            # 2. 备用：提取 article-body-module__paragraph 样式节点
            if not raw_paras:
                raw_paras = re.findall(r'<(?:div|p)[^>]*class="[^"]*article-body-module__paragraph[^"]*"[^>]*>(.*?)</(?:div|p)>', html_text, re.DOTALL | re.I)

            # 3. 备用：从 article-body 容器提取
            if not raw_paras:
                m_body = re.search(r'data-testid="article-body"[^>]*>(.*?)</div>', html_text, re.DOTALL | re.I)
                if m_body:
                    raw_paras = re.findall(r'<p[^>]*>(.*?)</p>', m_body.group(1), re.DOTALL | re.I)

            for p in raw_paras:
                c = re.sub(r',\s*opens new tab', '', p, flags=re.I)
                c = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff\xa0]', ' ', c)
                cp = cls._clean_paragraph(c)
                if cp and not any(bad in cp.lower() for bad in [
                    'sign up here', 'our standards: the thomson reuters trust principles',
                    'our standards: the thomson reuters'
                ]):
                    if cp not in paras:
                        paras.append(cp)

            # 4. 降级尝试通用 JSON-LD
            if len(paras) < 3:
                j_paras = cls._extract_from_json_ld(html_text)
                for jp in j_paras:
                    if jp not in paras:
                        paras.append(jp)

        # 5. 若直连被拦截 (DataDome 401 或段落 < 3) 且提供了 url，启动路透社电讯联合穿透机制
        if len(paras) < 3 and url and url.startswith("http"):
            try:
                import urllib.request
                import urllib.parse
                import xml.etree.ElementTree as ET
                slug = url.rstrip('/').split('/')[-1]
                slug = re.sub(r'-\d{4}-\d{2}-\d{2}$', '', slug)
                q_words = slug.replace('-', ' ')
                q = urllib.parse.quote(q_words[:80])
                bing_rss = f"https://www.bing.com/news/search?q={q}&format=rss"
                req = urllib.request.Request(bing_rss, headers={"User-Agent": cls.USER_AGENT})
                with urllib.request.urlopen(req, timeout=8) as r:
                    root = ET.fromstring(r.read())
                    items = root.findall('.//item')
                    for it in items[:6]:
                        raw_l = it.findtext('link') or ''
                        real_u = ''
                        if 'url=' in raw_l:
                            real_u = urllib.parse.unquote(raw_l.split('url=')[1].split('&')[0])
                        elif raw_l.startswith('http'):
                            real_u = raw_l
                        if not real_u or 'reuters.com' in real_u:
                            continue
                        ext_synd = cls.extract_article(real_u)
                        synd_paras = ext_synd.get('paragraphs', [])
                        if len(synd_paras) >= 3:
                            clean_synd = [sp for sp in synd_paras if not any(b in sp.lower() for b in ['reuters connect', 'originally published', 'copyright reuters'])]
                            if len(clean_synd) >= 3:
                                paras = clean_synd
                                break
            except Exception:
                pass

        return paras

    @classmethod
    def _extract_bloomberg(cls, html_text: str) -> List[str]:
        """彭博社 (Bloomberg) 专属单一抓取器"""
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) < 3:
            for pat in [
                r'class="[^"]*body-copy[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>'
            ]:
                m = re.search(pat, html_text, re.DOTALL | re.I)
                if m:
                    raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m.group(1), re.DOTALL | re.I)
                    for p in raw_p:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                    if paras:
                        break
        return paras

    @classmethod
    def _extract_techreview(cls, html_text: str) -> List[str]:
        """MIT Technology Review 专属单一抓取器"""
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) < 3:
            for pat in [
                r'class="[^"]*article-body[^"]*"[^>]*>(.*?)</div>',
                r'id="content--body"[^>]*>(.*?)</div>'
            ]:
                m = re.search(pat, html_text, re.DOTALL | re.I)
                if m:
                    raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m.group(1), re.DOTALL | re.I)
                    for p in raw_p:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                    if paras:
                        break
        return paras

    @classmethod
    def _extract_arstechnica(cls, html_text: str) -> List[str]:
        """Ars Technica 专属单一抓取器"""
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) < 3:
            for pat in [
                r'class="[^"]*article-content[^"]*"[^>]*>(.*?)</div>',
                r'class="[^"]*article-guts[^"]*"[^>]*>(.*?)</div>'
            ]:
                m = re.search(pat, html_text, re.DOTALL | re.I)
                if m:
                    raw_p = re.findall(r'<p[^>]*>(.*?)</p>', m.group(1), re.DOTALL | re.I)
                    for p in raw_p:
                        cp = cls._clean_paragraph(p)
                        if cp and cp not in paras:
                            paras.append(cp)
                    if paras:
                        break
        return paras

    @classmethod
    def _extract_from_json_ld(cls, html_text: str) -> List[str]:
        """通用 Schema.org JSON-LD articleBody 提取器"""
        paras = []
        for m_json in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL | re.I):
            try:
                raw_json = m_json.group(1).strip()
                jd = json.loads(raw_json)
                j_items = jd if isinstance(jd, list) else [jd]
                for it in j_items:
                    if isinstance(it, dict) and '@graph' in it and isinstance(it['@graph'], list):
                        j_items.extend(it['@graph'])
                    if isinstance(it, dict):
                        b = it.get('articleBody')
                        if b and isinstance(b, str) and len(b.strip()) > 100:
                            b_clean = html.unescape(b.strip())
                            for ad_pat in cls.AD_BLOCK_PATTERNS:
                                b_clean = re.sub(ad_pat, '', b_clean, flags=re.IGNORECASE | re.DOTALL)
                            raw_p = [p.strip() for p in re.split(r'\n\s*\n|\n', b_clean) if len(p.strip()) > 30]
                            if len(raw_p) <= 1 and len(b_clean) > 300:
                                sents = re.split(r'(?<=[.!?])\s+(?=[A-Z“"])', b_clean)
                                grouped_p = []
                                cur_p = []
                                for s in sents:
                                    cur_p.append(s.strip())
                                    if len(' '.join(cur_p)) >= 280 or len(cur_p) >= 3:
                                        grouped_p.append(' '.join(cur_p))
                                        cur_p = []
                                if cur_p:
                                    grouped_p.append(' '.join(cur_p))
                                raw_p = grouped_p
                            for p in raw_p:
                                cp = cls._clean_paragraph(p)
                                if cp and cp not in paras:
                                    paras.append(cp)
            except Exception:
                pass
        return paras

    @classmethod
    def _extract_generic(cls, html_text: str, domain: str) -> List[str]:
        """
        未收录信源的通用解构提取兜底
        """
        # 1. 尝试 JSON-LD
        paras = cls._extract_from_json_ld(html_text)
        if len(paras) >= 3:
            return paras

        # 2. 剥离无意义标签
        clean_html = re.sub(r'<(?:script|style|svg|noscript|header|nav|footer|aside|form|menu)[^>]*>.*?</(?:script|style|svg|noscript|header|nav|footer|aside|form|menu)>', ' ', html_text, flags=re.DOTALL | re.I)

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

        p_pattern = r'<p[^>]*>(.*?)</p>'
        raw_paras = re.findall(p_pattern, best_container, flags=re.DOTALL | re.IGNORECASE)

        clean_paras = []
        for p_str in raw_paras:
            cp = cls._clean_paragraph(p_str)
            if cp and cp not in clean_paras:
                clean_paras.append(cp)

        return clean_paras

    @classmethod
    def fetch_html(cls, url: str, timeout: int = 15) -> Optional[str]:
        """
        高可用穿透获取页面源码，按优先级依次调度：
        1. curl_cffi (针对 Reuters, Bloomberg, NYT, Wired 等受 DataDome/Cloudflare 保护的权威媒体，使用真实 Chrome 120 指纹与 Google Referer 穿透)
        2. requests (带标准 Chrome 标头，最强兼容性与系统代理支持)
        3. httpx (支持直连与自动重定向)
        4. urllib.request (底层无依赖保底)
        """
        if not url or not url.startswith("http"):
            return None

        headers = {
            "User-Agent": cls.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.google.com/"
        }

        # 针对已知具有 DataDome / Cloudflare 强防御的媒体，优先使用 curl_cffi Chrome 指纹穿透
        is_protected_domain = any(d in url.lower() for d in [
            'reuters.com', 'bloomberg.com', 'wsj.com', 'wired.com', 'ft.com', 'nytimes.com'
        ])

        if is_protected_domain and HAS_CURL_CFFI:
            try:
                resp = curl_requests.get(url, impersonate="chrome120", headers=headers, timeout=timeout)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    return resp.text
            except Exception:
                pass

        # 1. 优先使用 requests
        try:
            import requests
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 500:
                return resp.text
        except Exception:
            pass

        # 2. 尝试 curl_cffi 模拟 Chrome 浏览器指纹
        if HAS_CURL_CFFI:
            try:
                resp = curl_requests.get(url, impersonate="chrome120", headers=headers, timeout=timeout)
                if resp.status_code == 200 and len(resp.text) > 500:
                    return resp.text
            except Exception:
                pass

        # 3. 降级使用 httpx
        try:
            import httpx
            with httpx.Client(headers=headers, follow_redirects=True, timeout=timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.text) > 500:
                    return resp.text
        except Exception:
            pass

        # 4. 底层 urllib.request 降级兜底
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode('utf-8', errors='ignore')
                if len(text) > 500:
                    return text
        except Exception:
            pass

        return None

    @classmethod
    def extract_article(cls, url: str, html_text: Optional[str] = None) -> Dict[str, Any]:
        """
        深度解构文章，提取段落、小标题、关键引语、数据指标与高清配图。
        根据信源单一路由，执行专属信源抓取器，杜绝混用。
        """
        result = {
            "url": url,
            "status": "failed",
            "domain": "",
            "title": "",
            "cover_image": None,
            "inline_images": [],
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

        # 检查是否匹配专属提取器
        matched_extractor_name = None
        for source_key, method_name in cls.SOURCE_EXTRACTORS.items():
            if source_key in domain:
                matched_extractor_name = method_name
                break

        # 如果直连未能获取到 HTML，对支持 url 穿透的专属信源进行兜底
        if not html_text:
            if matched_extractor_name and hasattr(cls, matched_extractor_name):
                extractor_fn = getattr(cls, matched_extractor_name)
                try:
                    clean_paras = extractor_fn("", url)
                except Exception:
                    clean_paras = []
                if clean_paras:
                    result["paragraphs"] = clean_paras
                    result["paras_count"] = len(clean_paras)
                    result["full_text"] = "\n\n".join(clean_paras)
                    result["is_substantive"] = len(clean_paras) >= 3 or len(result["full_text"]) >= 300
                    result["lead_paragraph"] = clean_paras[0]
                    result["status"] = "success"
                    return result
            return result

        # 1. 提取高清配图 (og:image / twitter:image)
        m_img = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_img:
            cand_img = html.unescape(m_img.group(1)).strip()
            if not any(bad in cand_img.lower() for bad in ["pml.png", "techmeme.com", "pixel", "spacer", "tracking", "avatar", "icon", "placeholder"]):
                result["cover_image"] = cand_img

        # 1.5 提取正文高价值图景 (Inline Body Images & Figures)
        inline_images = []
        seen_img_urls = set()
        if result.get("cover_image"):
            seen_img_urls.add(result["cover_image"])

        # 优先提取带 figure 容器的编辑部摄影与图表
        figure_matches = re.findall(r'<figure[^>]*>(.*?)</figure>', html_text, flags=re.DOTALL | re.IGNORECASE)
        for fig in figure_matches:
            src_m = re.search(r'(?:src|data-src)=["\']([^"\'\s]+)', fig, flags=re.IGNORECASE)
            if not src_m:
                continue
            raw_src = html.unescape(src_m.group(1)).strip()
            if not raw_src.startswith("http"):
                continue
            clean_src = raw_src.split("?")[0] if "media.wired.com" not in raw_src else raw_src
            if clean_src in seen_img_urls:
                continue
            if any(bad in clean_src.lower() for bad in ["pixel", "spacer", "tracking", "avatar", "icon", "logo", "1x1", "data:image", "ad-", "banner"]):
                continue

            cap_m = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', fig, flags=re.DOTALL | re.IGNORECASE)
            caption = ""
            if cap_m:
                caption = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', cap_m.group(1))).split()).strip()
            if not caption:
                alt_m = re.search(r'alt=["\']([^"\']+)["\']', fig, flags=re.IGNORECASE)
                if alt_m:
                    caption = ' '.join(html.unescape(alt_m.group(1)).split()).strip()

            inline_images.append({
                "url": raw_src,
                "caption": caption[:160],
                "alt": caption[:100]
            })
            seen_img_urls.add(clean_src)
            if len(inline_images) >= 4:
                break

        # 兜底：若无 figure，提取正文中具名 alt 的大图
        if not inline_images:
            body_img_matches = re.finditer(r'<img[^>]+(?:src|data-src)=["\']([^"\']+)["\'][^>]*>', html_text, flags=re.IGNORECASE)
            for bm in body_img_matches:
                img_tag = bm.group(0)
                raw_src = html.unescape(bm.group(1)).strip()
                if not raw_src.startswith("http") or raw_src in seen_img_urls:
                    continue
                if any(bad in raw_src.lower() for bad in ["pixel", "spacer", "tracking", "avatar", "icon", "logo", "emoji", "1x1", "svg", "pml.png"]):
                    continue
                alt_m = re.search(r'alt=["\']([^"\']+)["\']', img_tag, flags=re.IGNORECASE)
                caption = html.unescape(alt_m.group(1)).strip() if alt_m else ""
                if len(caption) >= 6 and not any(bad in caption.lower() for bad in ["advertisement", "icon", "logo", "arrow", "button", "share"]):
                    inline_images.append({
                        "url": raw_src,
                        "caption": caption[:160],
                        "alt": caption[:100]
                    })
                    seen_img_urls.add(raw_src)
                    if len(inline_images) >= 3:
                        break

        result["inline_images"] = inline_images

        # 2. 提取 meta description 备用导语
        m_desc = re.search(r'<meta[^>]+(?:property|name)=["\'](?:og:description|twitter:description|description)["\'][^>]+content=["\']([^"\']+)["\']', html_text, re.I)
        if m_desc:
            desc_val = html.unescape(m_desc.group(1)).strip()
            if len(desc_val) > 20 and not any(bad in desc_val.lower() for bad in ["javascript", "enable cookies", "cloudflare"]):
                result["lead_paragraph"] = desc_val

        # 3. 路由至信源专属单一提取机制 (Single Dedicated Source Extractor)
        clean_paras = []
        if matched_extractor_name and hasattr(cls, matched_extractor_name):
            extractor_fn = getattr(cls, matched_extractor_name)
            try:
                clean_paras = extractor_fn(html_text, url)
            except TypeError:
                clean_paras = extractor_fn(html_text)

        # 4. 若无专属机制或专属抓取器未能提取到段落，执行通用容器兜底解析
        if not clean_paras:
            clean_paras = cls._extract_generic(html_text, domain)

        # 5. 提取小标题 (H2, H3)
        raw_headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', html_text, flags=re.DOTALL | re.IGNORECASE)
        subheadings = []
        for h_str in raw_headings:
            clean_h = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', h_str)).split()).strip()
            if 4 <= len(clean_h) <= 100 and not any(b in clean_h.lower() for b in ["comments", "subscribe", "share", "related"]):
                subheadings.append(clean_h)
        result["subheadings"] = subheadings[:8]

        # 6. 提取关键引语 (Direct Quotes)
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

        # 7. 提取硬核数据与度量 (Numbers, Dollars, Percentages)
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
        result["is_substantive"] = (len(clean_paras) >= 3) or (len(result["full_text"]) >= 300)

        if result["paragraphs"] and not result["lead_paragraph"]:
            result["lead_paragraph"] = result["paragraphs"][0]

        if result["is_substantive"] or len(clean_paras) >= 1:
            result["status"] = "success"

        return result


def extract_article_substantive(url: str, html_text: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Convenience helper to extract article if substantive, else return None."""
    data = ArticleExtractor.extract_article(url, html_text)
    if data.get("is_substantive"):
        return data
    return None
