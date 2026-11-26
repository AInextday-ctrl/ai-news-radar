#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Codebase Fast Index & Auto-Sync Engine v2.0 (AI 代码与规则极速索引同步系统)
------------------------------------------------------------------------
专为 AI 辅助开发与自动化流水线设计的极速索引引擎：
1. 毫秒级符号与模块倒排索引 (Python AST 含别名 + 核心前端 JS 符号提取)
2. 全量信源与爬虫路由注册表 (覆盖 31 个隔离爬虫 + YouTube/X/arXiv，自动校验零漂移)
3. 项目作用域规则与技能预算监测 (AGENTS.md 24 KB 截断红线 + .agents/skills/* 索引)
4. 底层数据存储仓元数据索引与分级键值直查 (免全盘慢扫，按需回退归档仓)
5. 代码与规则修改全自动增量同步 (Auto-Sync Hook & Integrity Guard 联动)
"""

from __future__ import annotations

import ast
import glob
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 stdout/stderr on Windows consoles
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_JSON_PATH = os.path.join(ROOT_DIR, "tools", "codebase_index.json")
INDEX_MD_PATH = os.path.join(ROOT_DIR, "tools", "CODEBASE_INDEX.md")

# Antigravity per-file rule cap (24,000 bytes)
RULE_MAX_BYTES = 24000
RULE_WARN_BYTES = 20000

# Active frontend JS files (non-minified source of truth)
CORE_JS_FILES: List[str] = [
    "public/js/app.js",
    "public/js/monetization.js",
    "public/js/page_language.js",
    "public/js/page_theme.js",
    "public/js/chinese_converter.js",
    "public/m/js/mobile.js",
]

# Active production scripts under scripts/ (excluding one-off ad-hoc inspection scripts)
CORE_PIPELINE_SCRIPTS: List[str] = [
    "scripts/update_arena_leaderboard.py",
    "scripts/localize_tool_images.py",
    "scripts/export_archive_volumes.py",
    "scripts/push_indexnow.py",
    "scripts/rebuild_public_data.py",
    "scripts/purify_language_data.py",
    "scripts/sync_curated_tools.py",
    "scripts/enrich_github_tools.py",
    "scripts/enrich_tool_media.py",
    "scripts/update_prompt_templates.py",
]

# Architectural Tiers
TIER_MAPPING: Dict[str, Dict[str, Any]] = {
    "crawlers": {
        "title": "信源抓取与解析层 (Dedicated Source Crawlers)",
        "pattern": r"^crawlers/.*\.py$",
        "desc": "31 个隔离权威信源爬虫、通用内容过滤器（content_filters.py）与统一路由导出（__init__.py）。",
    },
    "core": {
        "title": "流水线核心调度层 (Core Pipeline & Orchestration)",
        "files": [
            "main.py",
            "processor.py",
            "fetcher.py",
            "article_extractor.py",
            "apify_crawler.py",
            "config.py",
            "knowledge_base.py",
            "translate_fast.py",
        ],
        "desc": "系统中央调度、信源分发、推文增量抓取、正文提取与去重清洗管道。",
    },
    "curation": {
        "title": "研判精选与头条矩阵 (Curator & Intelligence Highlights)",
        "files": [
            "curator_engine.py",
            "topic_cluster.py",
            "language_sentinel.py",
            "tweet_classifier.py",
            "tool_fusion.py",
        ],
        "desc": "Top 3 今日突破、大V思辨矩阵、5W1H 事实提炼、工具融合与中英语言纯度哨兵。",
    },
    "publishing": {
        "title": "静态发布与 SEO/GEO 引擎 (Static Publishing & Distribution)",
        "files": [
            "content_publisher.py",
            "tool_news_publisher.py",
            "build_flagship_articles.py",
            "seo_geo_engine.py",
            "indexnow_submitter.py",
            "fix_seo_titles.py",
            "generate_bilingual_compliance.py",
        ],
        "desc": "单篇静态落地页编译、首页 SSR 注入、分卷切片、Sitemap 生成与 IndexNow 秒级收录推送。",
    },
    "videos": {
        "title": "短视频与多模态实战层 (Video & Multimodal Engine)",
        "files": ["viral_video_engine.py", "prompts_and_videos.py"],
        "desc": "YouTube / Bilibili / TikTok 实战视频发现、24-48h 时效切片与提示词库。",
    },
    "frontend": {
        "title": "前端客户端与单页交互 (Frontend SPA, Theme & Monetization)",
        "files": CORE_JS_FILES,
        "desc": "极速弹窗阅读、分卷按需加载、联盟好物光学混合展示、主题/多语言切换与移动端自适应。",
    },
    "tools": {
        "title": "工程运维与自动化工具链 (DevOps, Index & Catalog Tools)",
        "pattern": r"^tools/(?!verify_code_integrity\.py$).*\.py$",
        "desc": "极速索引同步、免锁安全推送（safe_sync）、Firebase 版本清理、爬虫审计与联盟商品目录构建。",
    },
    "pipeline_scripts": {
        "title": "流水线核心辅助脚本 (Active Pipeline Scripts)",
        "files": CORE_PIPELINE_SCRIPTS,
        "desc": "CI/CD 与日常数据同步调用的榜单更新、工具配图本地化、分卷导出与 IndexNow 推送脚本。",
    },
    "quality_gates": {
        "title": "工程规范与数据质量门禁 (Quality Gates & Verification)",
        "pattern": r"^(tests/.*\.py|tools/verify_code_integrity\.py)$",
        "desc": "22 项数据质量硬性门禁、视频时效单元测试、27+ 爬虫单测与全工程防回退静态校验。",
    },
    "data_stores": {
        "title": "底层数据存储仓 (Data Stores & Cache Registries)",
        "kind": "data_json",
        "desc": "后端主库（latest_news.json）、全量归档（master_archive.json）、精选库与信源持久化缓存（仅索引元数据）。",
    },
}

# Full Source Crawler Registry (31 isolated crawlers + 3 platform producers)
SOURCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "bloomberg.com": {
        "source": "Bloomberg",
        "crawler_file": "crawlers/bloomberg_crawler.py",
        "entrypoint": "crawl_bloomberg",
        "url_matcher": "is_bloomberg_url",
        "test_file": "tests/test_bloomberg_crawler.py",
        "cache_file": "data/bloomberg_cache.json",
        "rule_section": "crawlers/AGENTS.md §5",
        "features": ["PerimeterX 穿透", "高清摄影本地化", "电讯质量加权打分", "熔断图注与分享栏"],
    },
    "forbes.com": {
        "source": "Forbes",
        "crawler_file": "crawlers/forbes_crawler.py",
        "entrypoint": "crawl_forbes",
        "url_matcher": "is_forbes_url",
        "test_file": "tools/audit_source_crawlers.py",
        "cache_file": "data/forbes_cache.json",
        "rule_section": "crawlers/AGENTS.md §2",
        "features": ["纯净标题去聚合前缀", "记者名片解析", "官方配图本地化"],
    },
    "tech.eu": {
        "source": "Tech.eu",
        "crawler_file": "crawlers/techeu_crawler.py",
        "entrypoint": "crawl_techeu",
        "url_matcher": "is_techeu_url",
        "test_file": "tools/audit_source_crawlers.py",
        "cache_file": "data/techeu_cache.json",
        "rule_section": "crawlers/AGENTS.md §3",
        "features": ["欧洲科技创投", "评论引导语过滤", "高清大图本地化"],
    },
    "deepmind.google": {
        "source": "Google DeepMind / Institute",
        "crawler_file": "crawlers/deepmind_crawler.py",
        "entrypoint": "crawl_deepmind",
        "url_matcher": "is_deepmind_url",
        "test_file": "tools/audit_source_crawlers.py",
        "cache_file": "data/deepmind_cache.json",
        "rule_section": "crawlers/AGENTS.md §4",
        "features": ["Sitemap 主动发现", "科学家署名解析", "学术前瞻高清大图"],
    },
    "anthropic.com": {
        "source": "Anthropic",
        "crawler_file": "crawlers/anthropic_crawler.py",
        "entrypoint": "crawl_anthropic",
        "url_matcher": "is_anthropic_url",
        "test_file": "tests/test_anthropic_crawler.py",
        "cache_file": "data/anthropic_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["官方研究与产品发布", "长文结构化分段"],
    },
    "openai.com": {
        "source": "OpenAI",
        "crawler_file": "crawlers/openai_crawler.py",
        "entrypoint": "crawl_openai",
        "url_matcher": "is_openai_url",
        "test_file": "tests/test_openai_crawler.py",
        "cache_file": "data/openai_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["官方研究与模型发布", "CDN 高清配图提取"],
    },
    "reuters.com": {
        "source": "Reuters",
        "crawler_file": "crawlers/reuters_crawler.py",
        "entrypoint": "crawl_reuters",
        "url_matcher": "is_reuters_url",
        "test_file": "tests/test_reuters_crawler.py",
        "cache_file": "data/reuters_cache.json",
        "rule_section": "AGENTS.md §1.1 & crawlers/AGENTS.md §1",
        "features": ["国际权威通讯社", "电讯前缀剥离", "图片本地化"],
    },
    "wsj.com": {
        "source": "Wall Street Journal",
        "crawler_file": "crawlers/wsj_crawler.py",
        "entrypoint": "crawl_wsj",
        "url_matcher": "is_wsj_url",
        "test_file": "tests/test_wsj_crawler.py",
        "cache_file": "data/wsj_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["付费墙电讯穿透", "Wayback 规范化"],
    },
    "ft.com": {
        "source": "Financial Times",
        "crawler_file": "crawlers/ft_crawler.py",
        "entrypoint": "crawl_ft",
        "url_matcher": "is_ft_url",
        "test_file": "tests/test_ft_crawler.py",
        "cache_file": "data/ft_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["财经深度报道", "付费墙穿透与大图本地化"],
    },
    "nytimes.com": {
        "source": "The New York Times",
        "crawler_file": "crawlers/nyt_crawler.py",
        "entrypoint": "crawl_nyt",
        "url_matcher": "is_nyt_url",
        "test_file": "tests/test_nyt_crawler.py",
        "cache_file": "data/nyt_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["权威特稿", "电讯穿透与正文净化"],
    },
    "washingtonpost.com": {
        "source": "The Washington Post",
        "crawler_file": "crawlers/wapo_crawler.py",
        "entrypoint": "crawl_wapo",
        "url_matcher": "is_wapo_url",
        "test_file": "tests/test_wapo_crawler.py",
        "cache_file": "data/wapo_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["科技政策与深度调查", "路径规范化"],
    },
    "washingtonsun.com": {
        "source": "The Washington Sun",
        "crawler_file": "crawlers/washsun_crawler.py",
        "entrypoint": "crawl_washsun",
        "url_matcher": "is_washsun_url",
        "test_file": "tests/test_wapo_crawler.py",
        "cache_file": "data/washsun_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["地区与行业快讯", "基础正文清洗"],
    },
    "fortune.com": {
        "source": "Fortune",
        "crawler_file": "crawlers/fortune_crawler.py",
        "entrypoint": "crawl_fortune",
        "url_matcher": "is_fortune_url",
        "test_file": "tests/test_fortune_crawler.py",
        "cache_file": "data/fortune_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["商业财经与融资深度", "本地缓存复用"],
    },
    "cnbc.com": {
        "source": "CNBC",
        "crawler_file": "crawlers/cnbc_crawler.py",
        "entrypoint": "crawl_cnbc",
        "url_matcher": "is_cnbc_url",
        "test_file": "tests/test_cnbc_crawler.py",
        "cache_file": "data/cnbc_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["芯片算力与美股科技财报", "正文清洗"],
    },
    "bbc.com": {
        "source": "BBC News",
        "crawler_file": "crawlers/bbc_crawler.py",
        "entrypoint": "crawl_bbc",
        "url_matcher": "is_bbc_url",
        "test_file": "tests/test_bbc_crawler.py",
        "cache_file": "data/bbc_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["全球科技与监管报道", "去无关图注"],
    },
    "cbsnews.com": {
        "source": "CBS News",
        "crawler_file": "crawlers/cbsnews_crawler.py",
        "entrypoint": "crawl_cbsnews",
        "url_matcher": "is_cbsnews_url",
        "test_file": "tests/test_cbsnews_crawler.py",
        "cache_file": "data/cbsnews_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["主流媒体科技报道", "多段保真"],
    },
    "nypost.com": {
        "source": "New York Post",
        "crawler_file": "crawlers/nypost_crawler.py",
        "entrypoint": "crawl_nypost",
        "url_matcher": "is_nypost_url",
        "test_file": "tests/test_nypost_crawler.py",
        "cache_file": "data/nypost_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["突发商业与行业热点", "正文过滤"],
    },
    "semafor.com": {
        "source": "Semafor",
        "crawler_file": "crawlers/semafor_crawler.py",
        "entrypoint": "crawl_semafor",
        "url_matcher": "is_semafor_url",
        "test_file": "tests/test_semafor_crawler.py",
        "cache_file": "data/semafor_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["深度独家简报", "去邮件订阅尾巴"],
    },
    "techcrunch.com": {
        "source": "TechCrunch",
        "crawler_file": "crawlers/techcrunch_crawler.py",
        "entrypoint": "crawl_techcrunch",
        "url_matcher": "is_techcrunch_url",
        "test_file": "tests/test_techcrunch_crawler.py",
        "cache_file": "data/techcrunch_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["创投融资", "AI 大模型发布"],
    },
    "theverge.com": {
        "source": "The Verge",
        "crawler_file": "crawlers/verge_crawler.py",
        "entrypoint": "crawl_verge",
        "url_matcher": "is_verge_url",
        "test_file": "tests/test_verge_crawler.py",
        "cache_file": "data/verge_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["消费电子与 AI 产品评测", "HTML 片段净化"],
    },
    "wired.com": {
        "source": "WIRED",
        "crawler_file": "crawlers/wired_crawler.py",
        "entrypoint": "crawl_wired",
        "url_matcher": "is_wired_url",
        "test_file": "tests/test_wired_crawler.py",
        "cache_file": "data/wired_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["长文深度特稿", "官方媒体资产本地化"],
    },
    "technologyreview.com": {
        "source": "MIT Technology Review",
        "crawler_file": "crawlers/mittr_crawler.py",
        "entrypoint": "crawl_mittr",
        "url_matcher": "is_mittr_url",
        "test_file": "tests/test_mittr_crawler.py",
        "cache_file": "data/mittr_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["前沿科研深度解析", "Post ID 规范化"],
    },
    "the-decoder.com": {
        "source": "The Decoder",
        "crawler_file": "crawlers/decoder_crawler.py",
        "entrypoint": "crawl_decoder",
        "url_matcher": "is_decoder_url",
        "test_file": "tests/test_decoder_crawler.py",
        "cache_file": "data/decoder_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["深度前沿报道", "结构化技术评测"],
    },
    "arstechnica.com": {
        "source": "Ars Technica",
        "crawler_file": "crawlers/arstechnica_crawler.py",
        "entrypoint": "crawl_arstechnica",
        "url_matcher": "is_arstechnica_url",
        "test_file": "tests/test_arstechnica_crawler.py",
        "cache_file": "data/arstechnica_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["深度硬核技术评测", "长文分段保真"],
    },
    "siliconangle.com": {
        "source": "SiliconANGLE",
        "crawler_file": "crawlers/siliconangle_crawler.py",
        "entrypoint": "crawl_siliconangle",
        "url_matcher": "is_siliconangle_url",
        "test_file": "tests/test_siliconangle_crawler.py",
        "cache_file": "data/siliconangle_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["企业级云与 AI 基础设施", "Slug 提取"],
    },
    "techfundingnews.com": {
        "source": "Tech Funding News",
        "crawler_file": "crawlers/techfundingnews_crawler.py",
        "entrypoint": "crawl_techfundingnews",
        "url_matcher": "is_techfundingnews_url",
        "test_file": "tests/test_techfundingnews_crawler.py",
        "cache_file": "data/techfundingnews_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["欧洲及全球 AI 创投融资", "正文净化"],
    },
    "coindesk.com": {
        "source": "CoinDesk",
        "crawler_file": "crawlers/coindesk_crawler.py",
        "entrypoint": "crawl_coindesk",
        "url_matcher": "is_coindesk_url",
        "test_file": "tests/test_coindesk_crawler.py",
        "cache_file": "data/coindesk_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["加密经济与 AI 算力资产化", "深度市场研判"],
    },
    "9to5mac.com": {
        "source": "9to5Mac",
        "crawler_file": "crawlers/nineto5mac_crawler.py",
        "entrypoint": "crawl_nineto5mac",
        "url_matcher": "is_nineto5mac_url",
        "test_file": "tests/test_nineto5mac_crawler.py",
        "cache_file": "data/nineto5mac_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["Apple Intelligence 与端侧芯片", "正文提取"],
    },
    "tomshardware.com": {
        "source": "Tom's Hardware",
        "crawler_file": "crawlers/tomshardware_crawler.py",
        "entrypoint": "crawl_tomshardware",
        "url_matcher": "is_tomshardware_url",
        "test_file": "tests/test_tomshardware_crawler.py",
        "cache_file": "data/tomshardware_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["GPU 算力与半导体评测", "正文清洗"],
    },
    "ifixit.com": {
        "source": "iFixit",
        "crawler_file": "crawlers/ifixit_crawler.py",
        "entrypoint": "crawl_ifixit",
        "url_matcher": "is_ifixit_url",
        "test_file": "tests/test_ifixit_crawler.py",
        "cache_file": "data/ifixit_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["AI 硬件拆解与工程分析", "高清图提取"],
    },
    "ign.com": {
        "source": "IGN",
        "crawler_file": "crawlers/ign_crawler.py",
        "entrypoint": "crawl_ign",
        "url_matcher": "is_ign_url",
        "test_file": "tests/test_ign_crawler.py",
        "cache_file": "data/ign_cache.json",
        "rule_section": "crawlers/AGENTS.md §1",
        "features": ["游戏产业与生成式 AI 动态", "多段正文解析"],
    },
    "youtube.com": {
        "source": "YouTube",
        "crawler_file": "viral_video_engine.py",
        "entrypoint": "fetch_trending_ai_videos",
        "url_matcher": "",
        "test_file": "tests/test_video_pipeline.py",
        "cache_file": "data/latest_news.json",
        "rule_section": "AGENTS.md §3.5 & docs/CODE_INDEX.md (断言 4, 18)",
        "features": ["24-48h 时效切片", "防虚假飙升标签", "去营销套壳标题"],
    },
    "x.com": {
        "source": "X (Twitter)",
        "crawler_file": "apify_crawler.py",
        "entrypoint": "fetch_incremental_tweets",
        "url_matcher": "",
        "test_file": "tests/test_data_quality_gate.py",
        "cache_file": "data/apify_crawler_state.json",
        "rule_section": "docs/CODE_INDEX.md (断言 5, 10, 11, 12)",
        "features": ["顶尖 AI 领袖动态", "多段推文无损排版", "币圈水军过滤"],
    },
    "arxiv.org": {
        "source": "arXiv",
        "crawler_file": "fetcher.py",
        "entrypoint": "fetch_arxiv_papers",
        "url_matcher": "",
        "test_file": "tests/test_data_quality_gate.py",
        "cache_file": "data/latest_news.json",
        "rule_section": "AGENTS.md §3.5",
        "features": ["前沿论文速览", "摘要精译与分类"],
    },
}


def _rel(path: str) -> str:
    """Returns repo-relative path normalized with forward slashes."""
    return os.path.relpath(path, ROOT_DIR).replace("\\", "/")


def _fmt_size(num_bytes: int) -> str:
    """Formats bytes into a compact human-readable string."""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def discover_unregistered_crawlers() -> List[str]:
    """Detects any crawlers/*_crawler.py not present in SOURCE_REGISTRY."""
    registered_files = {meta["crawler_file"] for meta in SOURCE_REGISTRY.values()}
    unregistered: List[str] = []
    for fp in sorted(glob.glob(os.path.join(ROOT_DIR, "crawlers", "*_crawler.py"))):
        rel = _rel(fp)
        if rel not in registered_files:
            unregistered.append(rel)
    return unregistered


def discover_rules_and_skills() -> Dict[str, Any]:
    """Indexes project-scoped AGENTS.md/GEMINI.md rules (with byte budgets) and .agents/skills/*."""
    rules: List[Dict[str, Any]] = []
    skills: List[Dict[str, Any]] = []

    skip_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        "backup_homepage",
        "scratch",
        "data",
        ".firebase",
        ".pytest_cache",
    }

    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = sorted(d for d in dirs if d not in skip_dirs)
        for fn in sorted(files):
            if fn in ("AGENTS.md", "GEMINI.md"):
                fp = os.path.join(root, fn)
                rel = _rel(fp)
                size_bytes = os.path.getsize(fp)
                scope_dir = os.path.dirname(rel) or "."
                title = ""
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        for line in f:
                            s = line.strip()
                            if s.startswith("# "):
                                title = s[2:].strip()
                                break
                except Exception:
                    pass
                status = "OK"
                if size_bytes > RULE_MAX_BYTES:
                    status = "OVER_BUDGET"
                elif size_bytes > RULE_WARN_BYTES:
                    status = "WARN"
                rules.append(
                    {
                        "file": rel,
                        "scope": scope_dir,
                        "title": title,
                        "bytes": size_bytes,
                        "budget_pct": round(size_bytes / RULE_MAX_BYTES * 100, 1),
                        "status": status,
                    }
                )

    for skill_md in sorted(glob.glob(os.path.join(ROOT_DIR, ".agents", "skills", "*", "SKILL.md"))):
        rel = _rel(skill_md)
        size_bytes = os.path.getsize(skill_md)
        name = os.path.basename(os.path.dirname(skill_md))
        desc = ""
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                txt = f.read()
            m_name = re.search(r"^name:\s*(.+)$", txt, re.M)
            if m_name:
                name = m_name.group(1).strip().strip("\"'")
            m_desc = re.search(r"^description:\s*(.+)$", txt, re.M)
            if m_desc:
                desc = m_desc.group(1).strip().strip("\"'")
        except Exception:
            pass
        skills.append(
            {
                "name": name,
                "file": rel,
                "bytes": size_bytes,
                "description": desc,
            }
        )

    return {"rules": rules, "skills": skills}


def discover_data_stores() -> Dict[str, List[Dict[str, Any]]]:
    """Indexes metadata (size only, zero content read) for data/*.json."""
    core_stores: List[Dict[str, Any]] = []
    crawler_caches: List[Dict[str, Any]] = []
    data_dir = os.path.join(ROOT_DIR, "data")
    if not os.path.isdir(data_dir):
        return {"core": core_stores, "caches": crawler_caches}

    for fn in sorted(os.listdir(data_dir)):
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(data_dir, fn)
        if not os.path.isfile(fp):
            continue
        entry = {
            "file": f"data/{fn}",
            "size": os.path.getsize(fp),
            "size_human": _fmt_size(os.path.getsize(fp)),
        }
        if fn.endswith("_cache.json"):
            crawler_caches.append(entry)
        else:
            core_stores.append(entry)

    # Also track public/data/latest_news.json (850 KB CI gate)
    pub_latest = os.path.join(ROOT_DIR, "public", "data", "latest_news.json")
    if os.path.isfile(pub_latest):
        sz = os.path.getsize(pub_latest)
        core_stores.append(
            {
                "file": "public/data/latest_news.json",
                "size": sz,
                "size_human": _fmt_size(sz),
            }
        )

    return {"core": core_stores, "caches": crawler_caches}


def extract_python_symbols(filepath: str) -> Dict[str, Any]:
    """Uses Python AST to extract classes, functions, aliases, and constants in milliseconds."""
    symbols: Dict[str, Any] = {
        "classes": {},
        "functions": {},
        "constants": [],
    }
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath)
    except Exception as e:
        symbols["parse_error"] = str(e)
        return symbols

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(
                        {
                            "name": item.name,
                            "line": item.lineno,
                            "args": [a.arg for a in item.args.args if a.arg != "self"],
                        }
                    )
            doc = ast.get_docstring(node) or ""
            symbols["classes"][node.name] = {
                "line": node.lineno,
                "doc": doc.split("\n")[0] if doc else "",
                "methods": methods,
            }
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            args = [a.arg for a in node.args.args]
            symbols["functions"][node.name] = {
                "line": node.lineno,
                "doc": doc.split("\n")[0] if doc else "",
                "args": args,
            }
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id.isupper():
                        symbols["constants"].append(target.id)
                    elif (
                        isinstance(node.value, ast.Name)
                        and node.value.id in symbols["functions"]
                        and target.id not in symbols["functions"]
                    ):
                        # Top-level function alias (e.g. crawl_anthropic = extract_anthropic_article)
                        aliased = symbols["functions"][node.value.id]
                        symbols["functions"][target.id] = {
                            "line": node.lineno,
                            "doc": f"alias -> {node.value.id}",
                            "args": aliased.get("args", []),
                        }

    return symbols


def extract_js_symbols(filepath: str) -> Dict[str, Any]:
    """Extracts functions, arrow bindings, and window/globalThis exports from core JS files."""
    symbols: Dict[str, Any] = {"functions": {}}
    if not os.path.exists(filepath):
        return symbols
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            # function name(...) / async function name(...)
            m_fn = re.search(r"(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)", line)
            if m_fn:
                name = m_fn.group(1)
                args = [a.strip() for a in m_fn.group(2).split(",") if a.strip()]
                if name not in symbols["functions"]:
                    symbols["functions"][name] = {"line": idx + 1, "args": args}
            # window.name = ... / globalThis.name = ... / const|let|var name = (...) =>
            m_win = re.search(
                r"(?:(?:window|globalThis)\.([a-zA-Z0-9_$]+)\s*=|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:function|\([^)]*\)\s*=>))",
                line,
            )
            if m_win:
                name = m_win.group(1) or m_win.group(2)
                if name and name not in symbols["functions"]:
                    symbols["functions"][name] = {"line": idx + 1, "args": []}
    except Exception:
        pass
    return symbols


def _collect_target_source_files() -> List[str]:
    """Returns deterministic sorted list of all source files tracked by the code index."""
    py_files = (
        glob.glob(os.path.join(ROOT_DIR, "*.py"))
        + glob.glob(os.path.join(ROOT_DIR, "crawlers", "*.py"))
        + glob.glob(os.path.join(ROOT_DIR, "tools", "*.py"))
        + glob.glob(os.path.join(ROOT_DIR, "tests", "*.py"))
    )
    script_files = [
        os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        for rel in CORE_PIPELINE_SCRIPTS
        if os.path.exists(os.path.join(ROOT_DIR, rel.replace("/", os.sep)))
    ]
    js_files = [
        os.path.join(ROOT_DIR, rel.replace("/", os.sep))
        for rel in CORE_JS_FILES
        if os.path.exists(os.path.join(ROOT_DIR, rel.replace("/", os.sep)))
    ]
    seen = set()
    ordered: List[str] = []
    for p in sorted(py_files) + sorted(script_files) + js_files:
        norm = os.path.normpath(p)
        if norm not in seen and os.path.isfile(norm):
            seen.add(norm)
            ordered.append(norm)
    return ordered


def _build_verified_source_registry() -> Dict[str, Dict[str, Any]]:
    """Builds the verified source registry and warns/auto-appends any unregistered crawlers."""
    registry: Dict[str, Dict[str, Any]] = {}
    for domain, meta in SOURCE_REGISTRY.items():
        item = dict(meta)
        t_path = item.get("test_file", "")
        if t_path and not os.path.exists(os.path.join(ROOT_DIR, t_path.replace("/", os.sep))):
            item["test_file"] = "tools/audit_source_crawlers.py"
        c_path = item.get("cache_file", "")
        item["cache_exists"] = bool(
            c_path and os.path.exists(os.path.join(ROOT_DIR, c_path.replace("/", os.sep)))
        )
        registry[domain] = item

    # Auto-register any newly created crawlers/*_crawler.py so index never misses them
    for rel in discover_unregistered_crawlers():
        stem = os.path.basename(rel).replace("_crawler.py", "")
        registry[f"{stem} (unregistered)"] = {
            "source": stem.title(),
            "crawler_file": rel,
            "entrypoint": f"crawl_{stem}",
            "url_matcher": f"is_{stem}_url",
            "test_file": f"tests/test_{stem}_crawler.py"
            if os.path.exists(os.path.join(ROOT_DIR, "tests", f"test_{stem}_crawler.py"))
            else "tools/audit_source_crawlers.py",
            "cache_file": f"data/{stem}_cache.json",
            "cache_exists": os.path.exists(os.path.join(ROOT_DIR, "data", f"{stem}_cache.json")),
            "rule_section": "crawlers/AGENTS.md §1",
            "features": ["自动发现爬虫（请补全 SOURCE_REGISTRY 域名元数据）"],
        }
    return registry


def build_codebase_index() -> Dict[str, Any]:
    """Compiles the full repository index across AST/JS symbols, crawlers, rules, skills, and data stores."""
    verified_registry = _build_verified_source_registry()
    rules_and_skills = discover_rules_and_skills()
    data_stores = discover_data_stores()

    index: Dict[str, Any] = {
        "version": "2.0.0",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_files": 0,
        "total_symbols": 0,
        "total_sources": len(verified_registry),
        "rules_and_skills": rules_and_skills,
        "source_registry": verified_registry,
        "data_stores": data_stores,
        "architectural_tiers": {},
        "file_index": {},
        "symbol_lookup": {},
    }

    all_target_files = _collect_target_source_files()
    index["total_files"] = len(all_target_files)

    # 1. Parse and index each source file
    for fpath in all_target_files:
        rel = _rel(fpath)
        is_py = fpath.endswith(".py")
        size = os.path.getsize(fpath)

        syms = extract_python_symbols(fpath) if is_py else extract_js_symbols(fpath)

        index["file_index"][rel] = {
            "size": size,
            "classes": syms.get("classes", {}),
            "functions": syms.get("functions", {}),
            "constants": syms.get("constants", []),
        }

        for cname, cdata in syms.get("classes", {}).items():
            entry = {"file": rel, "line": cdata["line"], "type": "class", "doc": cdata.get("doc", "")}
            index["symbol_lookup"].setdefault(cname, []).append(entry)
            index["total_symbols"] += 1
            for m in cdata.get("methods", []):
                m_entry = {
                    "file": rel,
                    "line": m["line"],
                    "type": "method",
                    "class": cname,
                    "args": m.get("args", []),
                }
                index["symbol_lookup"].setdefault(f"{cname}.{m['name']}", []).append(m_entry)
                index["symbol_lookup"].setdefault(m["name"], []).append(m_entry)
                index["total_symbols"] += 1

        for fname, fdata in syms.get("functions", {}).items():
            f_entry = {
                "file": rel,
                "line": fdata["line"],
                "type": "function",
                "args": fdata.get("args", []),
                "doc": fdata.get("doc", ""),
            }
            index["symbol_lookup"].setdefault(fname, []).append(f_entry)
            index["total_symbols"] += 1

    # 2. Build architectural tiers
    for tier_key, meta in TIER_MAPPING.items():
        matched_files: List[str] = []
        if meta.get("kind") == "data_json":
            matched_files = [d["file"] for d in data_stores["core"]]
        elif "files" in meta:
            matched_files = [
                f for f in meta["files"] if os.path.exists(os.path.join(ROOT_DIR, f.replace("/", os.sep)))
            ]
        elif "pattern" in meta:
            rx = re.compile(meta["pattern"], re.I)
            matched_files = [rel for rel in index["file_index"].keys() if rx.search(rel)]

        index["architectural_tiers"][tier_key] = {
            "title": meta["title"],
            "desc": meta["desc"],
            "files": matched_files,
        }

    # 3. Write compact structured JSON index (AGENTS.md §6.4 serialization rule)
    with open(INDEX_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    # 4. Generate Markdown cheat-sheet
    generate_markdown_index(index)
    return index


def _preview_symbols(f_data: Dict[str, Any], limit: int = 5) -> str:
    """Prefers public (non-underscore) exported symbols in Markdown previews."""
    classes = list(f_data.get("classes", {}).keys())
    funcs = list(f_data.get("functions", {}).keys())
    public_syms = classes + [fn for fn in funcs if not fn.startswith("_")]
    chosen = public_syms if public_syms else funcs
    if not chosen:
        consts = f_data.get("constants", [])
        if consts:
            return f"constants: {', '.join(consts[:limit])}" + ("..." if len(consts) > limit else "")
        return "No exported symbols"
    return ", ".join(chosen[:limit]) + ("..." if len(chosen) > limit else "")


def generate_markdown_index(index: Dict[str, Any]) -> None:
    """Generates an executive, highly readable Markdown architecture & rules index."""
    rules_info = index.get("rules_and_skills", {})
    rules = rules_info.get("rules", [])
    skills = rules_info.get("skills", [])
    data_stores = index.get("data_stores", {"core": [], "caches": []})

    lines: List[str] = [
        "# AI News Radar - 代码库架构、规则与符号极速索引 (Codebase Fast Index v2.0)",
        "",
        (
            f"> **生成时间**: `{index['updated_at']}` | **代码文件**: `{index['total_files']}` 个 | "
            f"**索引符号**: `{index['total_symbols']}` 个 | **注册信源**: `{index['total_sources']}` 个 | "
            f"**作用域规则**: `{len(rules)}` 个 | **本地技能**: `{len(skills)}` 个"
        ),
        "> **更新机制**: 由 `tools/fast_index.py` 驱动，经 `tools/verify_code_integrity.py` 与 `.git/hooks/pre-commit` 自动增量同步刷新。",
        "",
        "---",
        "",
        "## 1. 项目作用域规则与技能预算表 (Scoped Rules & Skills)",
        "",
        "| 规则文件 | 作用域 | 体积 / 上限 (24,000 B) | 预算占比 | 状态 |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for r in rules:
        lines.append(
            f"| [`{r['file']}`](../{r['file']}) | `{r['scope']}` | `{r['bytes']:,} B` | `{r['budget_pct']}%` | `{r['status']}` |"
        )

    lines.extend(
        [
            "",
            "| 工作区技能 (Skill) | 路径 | 体积 | 适用场景 |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )
    for sk in skills:
        desc_short = sk["description"][:110] + ("..." if len(sk["description"]) > 110 else "")
        lines.append(
            f"| **`{sk['name']}`** | [`{sk['file']}`](../{sk['file']}) | `{sk['bytes']:,} B` | {desc_short} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. 核心架构与功能分层 (Architectural Tiers)",
            "",
        ]
    )

    for tier_key, tier in index["architectural_tiers"].items():
        lines.append(f"### {tier['title']}")
        lines.append(f"*{tier['desc']}*")
        lines.append("")
        if tier_key == "data_stores":
            lines.append("**核心数据仓与公共分发：**")
            for ds in data_stores.get("core", []):
                lines.append(f"- **`{ds['file']}`** (`{ds['size_human']}`)")
            caches = data_stores.get("caches", [])
            if caches:
                total_cache_bytes = sum(c["size"] for c in caches)
                cache_names = ", ".join(os.path.basename(c["file"]).replace("_cache.json", "") for c in caches)
                lines.append(
                    f"- **信源独立缓存 (`data/*_cache.json`)**: 共 `{len(caches)}` 个文件，合计 `{_fmt_size(total_cache_bytes)}`（{cache_names}）"
                )
            lines.append("")
            continue

        for f in tier["files"]:
            f_data = index["file_index"].get(f, {})
            preview = _preview_symbols(f_data)
            lines.append(f"- [`{f}`](../{f}) ({_fmt_size(f_data.get('size', 0))}): `{preview}`")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            f"## 3. 全量权威信源与爬虫路由注册表 (Source Registry — {index['total_sources']} Sources)",
            "",
            "| 信源 / 域名 | 解析模块 | 调度入口 | 校验 / 单测 | 守则锚点 |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for domain, meta in index["source_registry"].items():
        cf = meta["crawler_file"]
        tf = meta.get("test_file", "-")
        rs = meta.get("rule_section", "-")
        lines.append(
            f"| **`{domain}`** ({meta['source']}) | [`{cf}`](../{cf}) | `{meta['entrypoint']}` | `{tf}` | `{rs}` |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. 极速索引检索指令 (Instant CLI Lookup Cheat-Sheet)",
            "",
            "```bash",
            "# 1. 符号定位（精确 O(1) + 大小写不敏感与模糊建议，支持函数别名与核心 JS）",
            "python tools/fast_index.py symbol crawl_bloomberg",
            "",
            "# 2. 信源路由查询（支持全部 31 爬虫 + YouTube/X/arXiv）",
            "python tools/fast_index.py source bloomberg",
            "",
            "# 3. 全局模糊检索（跨规则、技能、信源、文件与符号）",
            "python tools/fast_index.py search modal",
            "",
            "# 4. 数据仓分级内存直查（默认优先查轻量热仓，精确 ID 命中即停；加 --all 扫归档仓）",
            "python tools/fast_index.py data b86591fb2c47a91d",
            "",
            "# 5. 查看项目作用域规则预算（24 KB 红线）与本地技能",
            "python tools/fast_index.py rules",
            "",
            "# 6. 查看架构分层文件与导出符号",
            "python tools/fast_index.py tier frontend",
            "",
            "# 7. 校验索引时效、规则预算与爬虫注册表完整性",
            "python tools/fast_index.py --check",
            "",
            "# 8. 增量同步 / 全量重建索引",
            "python tools/fast_index.py --sync",
            "python tools/fast_index.py build",
            "```",
            "",
        ]
    )

    with open(INDEX_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _load_index() -> Dict[str, Any]:
    if not os.path.exists(INDEX_JSON_PATH):
        return build_codebase_index()
    with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def query_symbol(symbol_name: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Instant O(1) symbol lookup with case-insensitive fallback and partial suggestions."""
    idx = _load_index()
    lookup = idx.get("symbol_lookup", {})
    if symbol_name in lookup:
        return lookup[symbol_name], []

    low = symbol_name.lower()
    ci_matches: List[Dict[str, Any]] = []
    suggestions: List[str] = []
    for key, entries in lookup.items():
        kl = key.lower()
        if kl == low:
            for e in entries:
                ci_matches.append({"matched_name": key, **e})
        elif low in kl and len(suggestions) < 12:
            suggestions.append(key)

    return ci_matches, suggestions


def query_source(domain_or_name: str) -> List[Dict[str, Any]]:
    """Instant source registry lookup returning all matching registered sources."""
    idx = _load_index()
    registry = idx.get("source_registry", SOURCE_REGISTRY)
    low = domain_or_name.lower().strip()
    matches: List[Dict[str, Any]] = []
    for domain, meta in registry.items():
        haystack = " ".join(
            [
                domain.lower(),
                meta.get("source", "").lower(),
                meta.get("crawler_file", "").lower(),
                meta.get("entrypoint", "").lower(),
            ]
        )
        if low in haystack:
            matches.append({"domain": domain, **meta})
    return matches


def search_codebase(keyword: str) -> Dict[str, Any]:
    """Fast keyword search across rules, skills, sources, files, and symbols."""
    idx = _load_index()
    q = keyword.lower().strip()
    results: Dict[str, Any] = {
        "matched_rules": [],
        "matched_skills": [],
        "matched_sources": [],
        "matched_files": [],
        "matched_symbols": [],
    }

    rs = idx.get("rules_and_skills", {})
    for r in rs.get("rules", []):
        if q in r.get("file", "").lower() or q in r.get("title", "").lower() or q in r.get("scope", "").lower():
            results["matched_rules"].append(r)

    for sk in rs.get("skills", []):
        if q in sk.get("name", "").lower() or q in sk.get("description", "").lower():
            results["matched_skills"].append(sk)

    for domain, meta in idx.get("source_registry", {}).items():
        if q in domain.lower() or q in meta.get("source", "").lower() or q in meta.get("crawler_file", "").lower():
            results["matched_sources"].append({"domain": domain, **meta})

    for rel_path in idx.get("file_index", {}).keys():
        if q in rel_path.lower():
            results["matched_files"].append(rel_path)

    for sym_name, entries in idx.get("symbol_lookup", {}).items():
        if q in sym_name.lower():
            for e in entries:
                results["matched_symbols"].append({"name": sym_name, **e})
                if len(results["matched_symbols"]) >= 30:
                    break
        if len(results["matched_symbols"]) >= 30:
            break

    return results


def _item_matches(it: Dict[str, Any], q_raw: str, q_low: str) -> Tuple[bool, bool]:
    """Returns (matched, is_exact_id)."""
    item_id = str(it.get("id") or "")
    if item_id == q_raw:
        return True, True
    if q_low in str(it.get("url") or "").lower():
        return True, False
    if q_low in str(it.get("title_zh") or "").lower() or q_low in str(it.get("title") or "").lower():
        return True, False
    return False, False


def query_data(target_query: str, scan_archives: bool = False) -> List[Dict[str, Any]]:
    """Tiered in-memory lookup: fast hot stores first, archives on fallback or --all."""
    q_raw = target_query.strip()
    q_low = q_raw.lower()
    hot_targets = [
        "data/curated_column_highlights.json",
        "public/data/latest_news.json",
        "data/latest_news.json",
    ]
    archive_targets = [
        "data/archive_news.json",
        "data/master_archive.json",
    ]
    targets = hot_targets + archive_targets if scan_archives else hot_targets

    matches: List[Dict[str, Any]] = []
    seen_keys = set()
    exact_id_found = False

    def _scan_file(rel_p: str) -> None:
        nonlocal exact_id_found
        full_p = os.path.join(ROOT_DIR, rel_p.replace("/", os.sep))
        if not os.path.exists(full_p):
            return
        try:
            with open(full_p, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return

        if isinstance(d, dict) and "columns" in d:
            for col_name, col in d["columns"].items():
                h = col.get("headline_item") if isinstance(col, dict) else None
                if isinstance(h, dict):
                    ok, is_exact = _item_matches(h, q_raw, q_low)
                    if ok:
                        key = (rel_p, h.get("id"), f"col.{col_name}")
                        if key not in seen_keys:
                            seen_keys.add(key)
                            matches.append(
                                {
                                    "file": rel_p,
                                    "type": f"curated_column.{col_name}.headline_item",
                                    "id": h.get("id"),
                                    "title": h.get("title_zh") or h.get("title"),
                                    "cover_image": h.get("cover_image") or h.get("image_url"),
                                    "author": h.get("author"),
                                }
                            )
                        if is_exact:
                            exact_id_found = True

        # Check top-level items list
        items_list = d.get("items", []) if isinstance(d, dict) else (d if isinstance(d, list) else [])
        for it in items_list:
            if not isinstance(it, dict):
                continue
            ok, is_exact = _item_matches(it, q_raw, q_low)
            if ok:
                key = (rel_p, it.get("id"), "items")
                if key not in seen_keys:
                    seen_keys.add(key)
                    matches.append(
                        {
                            "file": rel_p,
                            "type": "item",
                            "id": it.get("id"),
                            "title": it.get("title_zh") or it.get("title"),
                            "cover_image": it.get("cover_image") or it.get("image_url"),
                            "author": it.get("author"),
                        }
                    )
                if is_exact:
                    exact_id_found = True
                if len(matches) >= 20:
                    return

        # Also check grouped dict in latest_news.json if not already matched
        if isinstance(d, dict) and isinstance(d.get("grouped"), dict) and len(matches) < 20:
            for cat, cat_items in d["grouped"].items():
                if not isinstance(cat_items, list):
                    continue
                for it in cat_items:
                    if not isinstance(it, dict):
                        continue
                    ok, is_exact = _item_matches(it, q_raw, q_low)
                    if ok:
                        key = (rel_p, it.get("id"), f"grouped.{cat}")
                        if key not in seen_keys:
                            seen_keys.add(key)
                            matches.append(
                                {
                                    "file": rel_p,
                                    "type": f"grouped.{cat}",
                                    "id": it.get("id"),
                                    "title": it.get("title_zh") or it.get("title"),
                                    "cover_image": it.get("cover_image") or it.get("image_url"),
                                    "author": it.get("author"),
                                }
                            )
                        if is_exact:
                            exact_id_found = True
                        if len(matches) >= 20:
                            return

    for rel_p in targets:
        _scan_file(rel_p)
        if exact_id_found and not scan_archives:
            break

    # Automatic archive fallback only if nothing found in hot stores
    if not matches and not scan_archives:
        for rel_p in archive_targets:
            _scan_file(rel_p)
            if exact_id_found or len(matches) >= 15:
                break

    return matches


def is_index_stale() -> bool:
    """Checks if any tracked code, rule, or skill file changed, was added, or was deleted."""
    if not os.path.exists(INDEX_JSON_PATH) or not os.path.exists(INDEX_MD_PATH):
        return True
    try:
        index_mtime = os.path.getmtime(INDEX_JSON_PATH)
        with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
            idx = json.load(f)
    except Exception:
        return True

    if idx.get("version") != "2.0.0":
        return True

    current_files = _collect_target_source_files()
    current_rels = {_rel(p) for p in current_files}
    indexed_rels = set(idx.get("file_index", {}).keys())
    if current_rels != indexed_rels:
        return True

    for fp in current_files:
        if os.path.getmtime(fp) > index_mtime:
            return True

    # Also check rules & skills mtime/count
    rs = discover_rules_and_skills()
    for r in rs["rules"]:
        rp = os.path.join(ROOT_DIR, r["file"].replace("/", os.sep))
        if os.path.getmtime(rp) > index_mtime:
            return True
    for sk in rs["skills"]:
        sp = os.path.join(ROOT_DIR, sk["file"].replace("/", os.sep))
        if os.path.getmtime(sp) > index_mtime:
            return True

    indexed_rules = {r["file"] for r in idx.get("rules_and_skills", {}).get("rules", [])}
    current_rules = {r["file"] for r in rs["rules"]}
    if indexed_rules != current_rules:
        return True

    indexed_skills = {s["file"] for s in idx.get("rules_and_skills", {}).get("skills", [])}
    current_skills = {s["file"] for s in rs["skills"]}
    if indexed_skills != current_skills:
        return True

    return False


def auto_sync_if_stale() -> bool:
    """Rebuilds index if any code, rule, or skill file was modified."""
    if is_index_stale():
        print("⚡ [FastIndex Auto-Sync] Code/rule modifications detected, rebuilding codebase index...")
        build_codebase_index()
        print("✅ [FastIndex Auto-Sync] Codebase index refreshed successfully.")
        return True
    return False


def run_health_check() -> Tuple[bool, List[str]]:
    """Validates rule byte budgets, crawler registry completeness, and index freshness."""
    issues: List[str] = []
    rs = discover_rules_and_skills()
    for r in rs["rules"]:
        if r["bytes"] > RULE_MAX_BYTES:
            issues.append(
                f"规则文件超限被截断: {r['file']} ({r['bytes']:,} B > {RULE_MAX_BYTES:,} B)"
            )
    unreg = discover_unregistered_crawlers()
    if unreg:
        issues.append(f"存在未登记到 fast_index.SOURCE_REGISTRY 的爬虫模块: {unreg}")
    if is_index_stale():
        issues.append("索引已过期，请运行: python tools/fast_index.py --sync")
    return len(issues) == 0, issues


def install_git_hook() -> bool:
    """Installs the git pre-commit hook to guarantee auto-sync on commit."""
    hook_dir = os.path.join(ROOT_DIR, ".git", "hooks")
    if not os.path.exists(hook_dir):
        print("⚠️ .git/hooks directory not found, skipping git hook installation.")
        return False
    hook_path = os.path.join(hook_dir, "pre-commit")
    hook_script = """#!/bin/sh
# AI Codebase Fast Index Auto-Sync Pre-Commit Hook
python tools/fast_index.py --sync
git add tools/codebase_index.json tools/CODEBASE_INDEX.md 2>/dev/null || true
exit 0
"""
    try:
        with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_script)
        try:
            import stat

            os.chmod(hook_path, os.stat(hook_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass
        print(f"✅ Git pre-commit hook installed successfully at: {hook_path}")
        return True
    except Exception as e:
        print(f"⚠️ Failed to write git hook: {e}")
        return False


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ["--build", "build"]:
        t0 = time.time()
        print("🚀 [FastIndex v2.0] Building codebase, rules & skills index...")
        idx = build_codebase_index()
        dt = time.time() - t0
        json_sz = _fmt_size(os.path.getsize(INDEX_JSON_PATH))
        print(
            f"✅ [FastIndex] Indexed {idx['total_files']} files, {idx['total_symbols']} symbols, "
            f"{idx['total_sources']} sources, {len(idx['rules_and_skills']['rules'])} rules, "
            f"{len(idx['rules_and_skills']['skills'])} skills in {dt:.2f}s "
            f"(JSON: {json_sz})"
        )
        return

    cmd = args[0]

    if cmd in ["--sync", "sync"]:
        auto_sync_if_stale()
        return

    if cmd in ["--check", "check"]:
        ok, issues = run_health_check()
        if ok:
            print("✅ [FastIndex Check] 规则体积预算、31+ 信源注册表与索引时效全部健康！")
            sys.exit(0)
        else:
            print("❌ [FastIndex Check] 检出异常:")
            for iss in issues:
                print(f"  • {iss}")
            sys.exit(1)

    if cmd in ["--install-hook", "install-hook"]:
        install_git_hook()
        return

    if cmd in ["rules", "-r"]:
        rs = discover_rules_and_skills()
        print("📜 Project-Scoped Rules (Per-File Cap: 24,000 B):")
        for r in rs["rules"]:
            print(
                f"  • [{r['status']:11s}] {r['file']:24s} | scope={r['scope']:10s} | "
                f"{r['bytes']:6,d} B ({r['budget_pct']:4.1f}%) | {r['title']}"
            )
        print("\n🧰 Workspace Skills (.agents/skills/):")
        for sk in rs["skills"]:
            print(f"  • {sk['name']:26s} | {sk['file']} ({sk['bytes']:,} B)")
        return

    if cmd in ["tier", "-t"]:
        idx = _load_index()
        tiers = idx.get("architectural_tiers", {})
        if len(args) < 2:
            print("🏗️ Architectural Tiers:")
            for k, t in tiers.items():
                print(f"  • {k:18s} ({len(t['files']):2d} files) — {t['title']}")
            return
        tkey = args[1].lower()
        t = tiers.get(tkey)
        if not t:
            print(f"❌ Unknown tier '{tkey}'. Available: {', '.join(tiers.keys())}")
            return
        print(f"🏗️ {t['title']} ({len(t['files'])} files):")
        if tkey == "data_stores":
            ds = idx.get("data_stores", {})
            for item in ds.get("core", []):
                print(f"  • {item['file']} ({item['size_human']})")
            caches = ds.get("caches", [])
            if caches:
                total_cache_bytes = sum(c["size"] for c in caches)
                print(f"  • data/*_cache.json ({len(caches)} crawler caches, total {_fmt_size(total_cache_bytes)})")
            return
        for f in t["files"]:
            f_data = idx.get("file_index", {}).get(f, {})
            print(f"  • {f} ({_fmt_size(f_data.get('size', 0))}) -> {_preview_symbols(f_data)}")
        return

    if cmd in ["symbol", "-s"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py symbol <symbol_name>")
            return
        sym = args[1]
        results, suggestions = query_symbol(sym)
        if results:
            print(f"🎯 Found {len(results)} matches for symbol '{sym}':")
            for r in results:
                line_str = f":{r.get('line')}" if r.get("line") else ""
                type_str = f"[{r.get('type')}]"
                doc_str = f" - {r.get('doc')}" if r.get("doc") else ""
                print(f"  • {r.get('file')}{line_str} {type_str}{doc_str}")
        else:
            print(f"❌ Symbol '{sym}' not found in index.")
            if suggestions:
                print(f"💡 Did you mean: {', '.join(suggestions[:8])}")
        return

    if cmd in ["source", "-c"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py source <domain_or_name>")
            return
        query = args[1]
        matches = query_source(query)
        if matches:
            print(f"📰 Found {len(matches)} source match(es) for '{query}':")
            for res in matches:
                print(f"  • Source Name : {res.get('source')} ({res.get('domain')})")
                print(f"    Crawler File: {res.get('crawler_file')} :: {res.get('entrypoint')}")
                print(f"    Unit Test   : {res.get('test_file', '-')}")
                print(f"    Cache File  : {res.get('cache_file', '-')} (exists={res.get('cache_exists', False)})")
                print(f"    Rule Anchor : {res.get('rule_section', '-')}")
                print(f"    Features    : {', '.join(res.get('features', []))}")
        else:
            print(f"❌ No registered source crawler found matching '{query}'.")
        return

    if cmd in ["data", "-d"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py data <id_or_keyword> [--all]")
            return
        q = args[1]
        scan_all = "--all" in args[2:]
        t0 = time.time()
        print(f"🔍 Searching data stores for '{q}' (scan_archives={scan_all})...")
        matches = query_data(q, scan_archives=scan_all)
        dt = time.time() - t0
        if matches:
            print(f"✅ Found {len(matches)} match(es) in {dt:.2f}s:")
            for m in matches:
                cov = m.get("cover_image") or "No image"
                print(
                    f"  • [{m.get('file')}::{m.get('type')}] ID: {m.get('id')} | "
                    f"Title: {m.get('title')} | Cover: {cov}"
                )
        else:
            print(f"❌ No items found in data stores matching '{q}' ({dt:.2f}s).")
        return

    if cmd in ["search", "-q"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py search <keyword>")
            return
        kw = args[1]
        res = search_codebase(kw)
        print(f"🔎 Search Results for '{kw}':")
        if res["matched_rules"]:
            print(f"  [Rules ({len(res['matched_rules'])})]")
            for r in res["matched_rules"]:
                print(f"    • {r['file']} ({r['bytes']:,} B) — {r['title']}")
        if res["matched_skills"]:
            print(f"  [Skills ({len(res['matched_skills'])})]")
            for sk in res["matched_skills"]:
                print(f"    • {sk['name']} -> {sk['file']}")
        if res["matched_sources"]:
            print(f"  [Sources ({len(res['matched_sources'])})]")
            for s in res["matched_sources"]:
                print(f"    • {s['source']} ({s['domain']}) -> {s['crawler_file']}::{s['entrypoint']}")
        if res["matched_files"]:
            print(f"  [Files ({len(res['matched_files'])})]")
            for f in res["matched_files"][:12]:
                print(f"    • {f}")
        if res["matched_symbols"]:
            print(f"  [Symbols ({len(res['matched_symbols'])})]")
            for s in res["matched_symbols"][:15]:
                print(f"    • {s['name']} -> {s['file']}:{s.get('line', '?')} [{s.get('type')}]")
        if not any(res.values()):
            print("  ❌ No matches found.")
        return

    print(
        "Usage: python tools/fast_index.py "
        "[build|--sync|--check|rules|tier|symbol|source|search|data|--install-hook]"
    )


if __name__ == "__main__":
    main()
