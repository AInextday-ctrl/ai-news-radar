#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Codebase Fast Index & Auto-Sync Engine (AI 代码极速索引与全自动同步系统)
------------------------------------------------------------------------
专为 AI 辅助开发与自动化流水线设计的极速索引引擎：
1. 毫秒级符号与模块倒排索引 (AST-based Symbol & Module Inverted Index)
2. 专有信源与爬虫路由注册表 (Source Domain & Crawler Registry)
3. 数据存储仓结构与键值直查 ($O(1) Data & Storage Key Lookup)
4. 代码修改全自动增量同步 (Auto-Sync Hook & Integrity Integration)
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

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_JSON_PATH = os.path.join(ROOT_DIR, "tools", "codebase_index.json")
INDEX_MD_PATH = os.path.join(ROOT_DIR, "tools", "CODEBASE_INDEX.md")

# 架构分层规则 (Architectural Tiers)
TIER_MAPPING = {
    "crawlers": {
        "title": "信源抓取与解析层 (Dedicated Source Crawlers)",
        "pattern": r"^crawlers[\\/].*_crawler\.py$",
        "desc": "负责各权威信源（Bloomberg, Forbes, Reuters, DeepMind 等）的定向穿透、授权配图提取与正文清洗。"
    },
    "core": {
        "title": "流水线核心调度层 (Core Pipeline & Orchestration)",
        "files": ["main.py", "processor.py", "fetcher.py", "article_extractor.py", "config.py", "knowledge_base.py"],
        "desc": "系统中央调度、信源分发、多模态事实提取与去重清洗管道。"
    },
    "curation": {
        "title": "研判精选与头条矩阵 (Curator & Intelligence Highlights)",
        "files": ["curator_engine.py", "topic_cluster.py", "language_sentinel.py", "tweet_classifier.py"],
        "desc": "负责 Top 3 今日核心突破、大V思辨矩阵、5W1H 事实提炼与中英高保真本地化。"
    },
    "publishing": {
        "title": "静态发布与 SEO/GEO 引擎 (Static Publishing & Distribution)",
        "files": ["content_publisher.py", "tool_news_publisher.py", "build_flagship_articles.py", "seo_geo_engine.py", "indexnow_submitter.py"],
        "desc": "单篇静态落地页编译、首页 SSR 注入、分卷切片、Sitemap 生成与 IndexNow 秒级收录推送。"
    },
    "videos": {
        "title": "短视频与多模态实战层 (Video & Multimodal Engine)",
        "files": ["viral_video_engine.py", "prompts_and_videos.py"],
        "desc": "YouTube / Bilibili / TikTok 实战视频发现、24-48h 时效切片与去套壳清洗。"
    },
    "frontend": {
        "title": "前端客户端与单页交互 (Frontend SPA & Mobile App)",
        "files": ["public/js/app.js", "public/m/js/mobile.js", "public/js/monetization.js", "public/js/chinese_converter.js"],
        "desc": "极速弹窗阅读、分卷动态加载、移动端自适应布局与多语言热切换交互。"
    },
    "quality_gates": {
        "title": "工程规范与数据质量门禁 (Quality Gates & Verification)",
        "pattern": r"^(tests[\\/].*|tools[\\/]verify_code_integrity\.py)$",
        "desc": "21 项数据质量硬性门禁、视频时效断言与全工程代码规范防回退静态校验。"
    },
    "data_stores": {
        "title": "底层数据存储仓 (Data Stores & Cache Registries)",
        "pattern": r"^data[\\/].*\.json$",
        "desc": "公共数据仓（latest_news.json）、全量归档（master_archive.json）与信源独立持久化缓存。"
    }
}

# 权威信源已知路由对照表 (Source Crawler Registry)
SOURCE_REGISTRY = {
    "bloomberg.com": {
        "source": "Bloomberg",
        "crawler_file": "crawlers/bloomberg_crawler.py",
        "entrypoint": "crawl_bloomberg",
        "test_file": "tests/test_bloomberg_crawler.py",
        "cache_file": "data/bloomberg_cache.json",
        "rule_section": "AGENTS.md Section 12",
        "features": ["PerimeterX 穿透", "高清摄影本地化", "电讯质量加权打分", "熔断图注与分享栏"]
    },
    "forbes.com": {
        "source": "Forbes",
        "crawler_file": "crawlers/forbes_crawler.py",
        "entrypoint": "crawl_forbes",
        "test_file": "tests/test_forbes_crawler.py",
        "cache_file": "data/forbes_cache.json",
        "rule_section": "AGENTS.md Section 9",
        "features": ["纯净标题去聚合前缀", "记者名片解析", "官方配图本地化"]
    },
    "tech.eu": {
        "source": "Tech.eu",
        "crawler_file": "crawlers/techeu_crawler.py",
        "entrypoint": "crawl_techeu",
        "test_file": "tests/test_techeu_crawler.py",
        "cache_file": "data/techeu_cache.json",
        "rule_section": "AGENTS.md Section 10",
        "features": ["欧洲科技创投", "评论引导语过滤", "高清大图本地化"]
    },
    "deepmind.google": {
        "source": "Google DeepMind / Institute",
        "crawler_file": "crawlers/deepmind_crawler.py",
        "entrypoint": "crawl_deepmind",
        "test_file": "tests/test_deepmind_crawler.py",
        "cache_file": "data/deepmind_cache.json",
        "rule_section": "AGENTS.md Section 11",
        "features": ["Sitemap 主动发现", "科学家署名解析", "学术前瞻高清大图"]
    },
    "the-decoder.com": {
        "source": "The Decoder",
        "crawler_file": "crawlers/decoder_crawler.py",
        "entrypoint": "crawl_decoder",
        "test_file": "tests/test_decoder_crawler.py",
        "features": ["深度前沿报道", "结构化技术评测"]
    },
    "techcrunch.com": {
        "source": "TechCrunch",
        "crawler_file": "crawlers/techcrunch_crawler.py",
        "entrypoint": "crawl_techcrunch",
        "test_file": "tests/test_techcrunch_crawler.py",
        "features": ["创投融资", "AI 大模型发布"]
    },
    "reuters.com": {
        "source": "Reuters",
        "crawler_file": "crawlers/reuters_crawler.py",
        "entrypoint": "crawl_reuters",
        "test_file": "tests/test_reuters_crawler.py",
        "features": ["国际权威通讯社", "电讯前缀剥离"]
    },
    "arstechnica.com": {
        "source": "Ars Technica",
        "crawler_file": "crawlers/arstechnica_crawler.py",
        "entrypoint": "crawl_arstechnica",
        "test_file": "tests/test_arstechnica_crawler.py",
        "features": ["深度硬核技术评测", "长文分段保真"]
    },
    "coindesk.com": {
        "source": "CoinDesk",
        "crawler_file": "crawlers/coindesk_crawler.py",
        "entrypoint": "crawl_coindesk",
        "test_file": "tests/test_coindesk_crawler.py",
        "features": ["加密经济与 AI 算力资产化", "深度市场研判"]
    },
    "youtube.com": {
        "source": "YouTube",
        "crawler_file": "viral_video_engine.py",
        "entrypoint": "fetch_trending_ai_videos",
        "test_file": "tests/test_video_pipeline.py",
        "rule_section": "AGENTS.md Rule 3.5 & Rule 18",
        "features": ["24-48h 时效切片", "防虚假飙升标签", "去营销套壳标题"]
    },
    "twitter.com": {
        "source": "𝕏 (Twitter)",
        "crawler_file": "crawlers/twitter_crawler.py",
        "entrypoint": "crawl_twitter",
        "features": ["顶尖 AI 领袖动态", "多段推文无损排版", "币圈水军过滤"]
    },
    "arxiv.org": {
        "source": "arXiv",
        "crawler_file": "fetcher.py",
        "entrypoint": "fetch_arxiv_papers",
        "features": ["前沿论文速览", "摘要精译与分类"]
    }
}


def _rel(path: str) -> str:
    """Returns repo-relative path normalized with forward slashes."""
    r = os.path.relpath(path, ROOT_DIR)
    return r.replace("\\", "/")


def extract_python_symbols(filepath: str) -> Dict[str, Any]:
    """Uses Python AST to extract functions, classes, and constants in milliseconds."""
    rel_path = _rel(filepath)
    symbols: Dict[str, Any] = {
        "classes": {},
        "functions": {},
        "constants": []
    }
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code, filename=filepath)
    except Exception as e:
        symbols["parse_error"] = str(e)
        return symbols

    for node in tree.body:
        # Classes
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append({
                        "name": item.name,
                        "line": item.lineno,
                        "args": [a.arg for a in item.args.args if a.arg != "self"]
                    })
            doc = ast.get_docstring(node) or ""
            symbols["classes"][node.name] = {
                "line": node.lineno,
                "doc": doc.split("\n")[0] if doc else "",
                "methods": methods
            }
        # Top-level Functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            args = [a.arg for a in node.args.args]
            symbols["functions"][node.name] = {
                "line": node.lineno,
                "doc": doc.split("\n")[0] if doc else "",
                "args": args
            }
        # Top-level Constants
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    symbols["constants"].append(target.id)

    return symbols


def extract_js_symbols(filepath: str) -> Dict[str, Any]:
    """Extracts top-level functions and event handlers from core JS files."""
    symbols = {"functions": {}}
    if not os.path.exists(filepath):
        return symbols
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            # function name(...)
            m_fn = re.search(r'function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)', line)
            if m_fn:
                name = m_fn.group(1)
                args = [a.strip() for a in m_fn.group(2).split(',') if a.strip()]
                symbols["functions"][name] = {"line": idx + 1, "args": args}
            # window.name = function(...) or const name = (...) =>
            m_win = re.search(r'(?:window\.|(?:const|let|var)\s+)([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:function|\([^)]*\)\s*=>)', line)
            if m_win:
                name = m_win.group(1)
                if name not in symbols["functions"]:
                    symbols["functions"][name] = {"line": idx + 1, "args": []}
    except Exception:
        pass
    return symbols


def build_codebase_index() -> Dict[str, Any]:
    """Compiles the full repository index across AST symbols, crawler registry, and architecture."""
    t0 = time.time()
    index: Dict[str, Any] = {
        "version": "1.0.0",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_files": 0,
        "total_symbols": 0,
        "source_registry": SOURCE_REGISTRY,
        "architectural_tiers": {},
        "file_index": {},
        "symbol_lookup": {}  # symbol_name -> list of {file, line, type, args}
    }

    # Discover target files
    py_files = sorted(glob.glob(os.path.join(ROOT_DIR, "*.py")) +
                      glob.glob(os.path.join(ROOT_DIR, "crawlers", "*.py")) +
                      glob.glob(os.path.join(ROOT_DIR, "tools", "*.py")) +
                      glob.glob(os.path.join(ROOT_DIR, "tests", "*.py")))
    
    js_files = [
        os.path.join(ROOT_DIR, "public", "js", "app.js"),
        os.path.join(ROOT_DIR, "public", "m", "js", "mobile.js")
    ]

    all_target_files = py_files + [j for j in js_files if os.path.exists(j)]
    index["total_files"] = len(all_target_files)

    # 1. Parse and index each file
    for fpath in all_target_files:
        rel = _rel(fpath)
        is_py = fpath.endswith(".py")
        size = os.path.getsize(fpath)
        mtime = os.path.getmtime(fpath)

        if is_py:
            syms = extract_python_symbols(fpath)
        else:
            syms = extract_js_symbols(fpath)

        index["file_index"][rel] = {
            "size": size,
            "mtime": mtime,
            "classes": syms.get("classes", {}),
            "functions": syms.get("functions", {}),
            "constants": syms.get("constants", [])
        }

        # Invert symbols for O(1) lookup
        for cname, cdata in syms.get("classes", {}).items():
            entry = {"file": rel, "line": cdata["line"], "type": "class", "doc": cdata.get("doc", "")}
            index["symbol_lookup"].setdefault(cname, []).append(entry)
            index["total_symbols"] += 1
            for m in cdata.get("methods", []):
                m_entry = {"file": rel, "line": m["line"], "type": "method", "class": cname, "args": m.get("args", [])}
                index["symbol_lookup"].setdefault(f"{cname}.{m['name']}", []).append(m_entry)
                index["symbol_lookup"].setdefault(m['name'], []).append(m_entry)
                index["total_symbols"] += 1

        for fname, fdata in syms.get("functions", {}).items():
            f_entry = {"file": rel, "line": fdata["line"], "type": "function", "args": fdata.get("args", []), "doc": fdata.get("doc", "")}
            index["symbol_lookup"].setdefault(fname, []).append(f_entry)
            index["total_symbols"] += 1

    # 2. Build architectural tiers
    for tier_key, meta in TIER_MAPPING.items():
        matched_files = []
        if "files" in meta:
            matched_files = [f for f in meta["files"] if os.path.exists(os.path.join(ROOT_DIR, f))]
        elif "pattern" in meta:
            rx = re.compile(meta["pattern"], re.I)
            matched_files = [rel for rel in index["file_index"].keys() if rx.search(rel)]

        index["architectural_tiers"][tier_key] = {
            "title": meta["title"],
            "desc": meta["desc"],
            "files": matched_files
        }

    # 3. Write structured JSON index
    with open(INDEX_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # 4. Generate Markdown cheat-sheet
    generate_markdown_index(index)

    duration = time.time() - t0
    return index


def generate_markdown_index(index: Dict[str, Any]):
    """Generates an executive, highly readable Markdown architecture index."""
    lines = [
        "# AI News Radar - 代码库架构与符号极速索引 (Codebase Fast Index)",
        "",
        f"> **生成时间**: `{index['updated_at']}` | **收录文件**: `{index['total_files']}` 个 | **索引符号**: `{index['total_symbols']}` 个",
        "> **更新机制**: 由 `tools/fast_index.py` 驱动，在每次代码修改、测试门禁校验与提交前自动增量同步刷新。",
        "",
        "---",
        "",
        "## 1. 核心架构与功能分层 (Architectural Tiers)",
        ""
    ]

    for tier_key, tier in index["architectural_tiers"].items():
        lines.append(f"### {tier['title']}")
        lines.append(f"*{tier['desc']}*")
        lines.append("")
        for f in tier["files"]:
            f_data = index["file_index"].get(f, {})
            funcs = list(f_data.get("functions", {}).keys())
            classes = list(f_data.get("classes", {}).keys())
            top_syms = classes + funcs
            preview = ", ".join(top_syms[:5]) + ("..." if len(top_syms) > 5 else "")
            lines.append(f"- **`{f}`** ({f_data.get('size', 0):,} bytes): `{preview or 'No exported symbols'}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 2. 权威信源与爬虫路由注册表 (Source Crawler Registry)")
    lines.append("")
    lines.append("| 信源标识 / 域名 | 对应解析模块 | 核心调度入口 | 单元测试文件 | 守则规范锚点 |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for domain, meta in index["source_registry"].items():
        lines.append(f"| **`{domain}`** ({meta['source']}) | [`{meta['crawler_file']}`]({meta['crawler_file']}) | `{meta['entrypoint']}` | `{meta.get('test_file', '-')}` | `{meta.get('rule_section', '-')}` |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. 极速索引检索指令 (Instant CLI Lookup Cheat-Sheet)")
    lines.append("")
    lines.append("AI 模型或开发人员无需全盘慢扫描，可直接在终端秒级查阅任意符号、信源或数据：")
    lines.append("```bash")
    lines.append("# 1. 秒查符号定位 (函数/类名直达代码行号)")
    lines.append("python tools/fast_index.py symbol crawl_bloomberg")
    lines.append("")
    lines.append("# 2. 秒查权威信源 (获取对应爬虫文件、入口函数与规则)")
    lines.append("python tools/fast_index.py source bloomberg")
    lines.append("")
    lines.append("# 3. 全局模糊检索 (在毫秒内检索函数名、模块及架构说明)")
    lines.append("python tools/fast_index.py search modal")
    lines.append("")
    lines.append("# 4. 数据仓内存直查 (0.05秒查找特定资讯 ID/URL，杜绝无脑 Select-String 假死)")
    lines.append("python tools/fast_index.py data b86591fb2c47a91d")
    lines.append("")
    lines.append("# 5. 增量重新构建索引")
    lines.append("python tools/fast_index.py build")
    lines.append("```")
    lines.append("")

    with open(INDEX_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def query_symbol(symbol_name: str) -> List[Dict[str, Any]]:
    """Instant O(1) symbol lookup."""
    if not os.path.exists(INDEX_JSON_PATH):
        build_codebase_index()
    with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
        idx = json.load(f)
    lookup = idx.get("symbol_lookup", {})
    return lookup.get(symbol_name, [])


def query_source(domain_or_name: str) -> Optional[Dict[str, Any]]:
    """Instant source registry lookup."""
    low = domain_or_name.lower().strip()
    for domain, meta in SOURCE_REGISTRY.items():
        if low in domain or low in meta["source"].lower():
            return {"domain": domain, **meta}
    return None


def search_codebase(keyword: str) -> Dict[str, Any]:
    """Fast keyword search across symbols, files, and tiers."""
    if not os.path.exists(INDEX_JSON_PATH):
        build_codebase_index()
    with open(INDEX_JSON_PATH, "r", encoding="utf-8") as f:
        idx = json.load(f)

    q = keyword.lower().strip()
    results = {
        "matched_sources": [],
        "matched_files": [],
        "matched_symbols": []
    }

    # 1. Sources
    for domain, meta in idx.get("source_registry", {}).items():
        if q in domain.lower() or q in meta["source"].lower():
            results["matched_sources"].append({"domain": domain, **meta})

    # 2. Files
    for rel_path, fdata in idx.get("file_index", {}).items():
        if q in rel_path.lower():
            results["matched_files"].append(rel_path)

    # 3. Symbols
    for sym_name, entries in idx.get("symbol_lookup", {}).items():
        if q in sym_name.lower():
            for e in entries:
                results["matched_symbols"].append({"name": sym_name, **e})
                if len(results["matched_symbols"]) >= 30:
                    break
        if len(results["matched_symbols"]) >= 30:
            break

    return results


def query_data(target_query: str) -> List[Dict[str, Any]]:
    """Instant in-memory hash scan of primary data files."""
    q = target_query.strip()
    data_targets = [
        "data/curated_column_highlights.json",
        "data/latest_news.json",
        "data/archive_news.json",
        "data/master_archive.json"
    ]
    matches = []
    for rel_p in data_targets:
        full_p = os.path.join(ROOT_DIR, rel_p)
        if not os.path.exists(full_p):
            continue
        try:
            with open(full_p, "r", encoding="utf-8") as f:
                d = json.load(f)
            # Check headline item
            if "columns" in d:
                for col_name, col in d["columns"].items():
                    h = col.get("headline_item")
                    if h and (h.get("id") == q or q in h.get("url", "") or q in (h.get("title_zh") or "") or q in (h.get("title") or "")):
                        matches.append({
                            "file": rel_p,
                            "type": f"curated_column.{col_name}.headline_item",
                            "id": h.get("id"),
                            "title": h.get("title_zh") or h.get("title"),
                            "cover_image": h.get("cover_image"),
                            "author": h.get("author")
                        })
            # Check items list
            for it in d.get("items", []):
                if it.get("id") == q or q in it.get("url", "") or q in (it.get("title_zh") or "") or q in (it.get("title") or ""):
                    matches.append({
                        "file": rel_p,
                        "type": "item",
                        "id": it.get("id"),
                        "title": it.get("title_zh") or it.get("title"),
                        "cover_image": it.get("cover_image") or it.get("image_url"),
                        "author": it.get("author")
                    })
                    if len(matches) >= 15:
                        break
        except Exception:
            pass
    return matches


def is_index_stale() -> bool:
    """Checks if any codebase file is newer than the index file."""
    if not os.path.exists(INDEX_JSON_PATH):
        return True
    index_mtime = os.path.getmtime(INDEX_JSON_PATH)
    target_patterns = ["*.py", "crawlers/*.py", "tools/*.py", "tests/*.py", "public/js/app.js", "public/m/js/mobile.js"]
    for pat in target_patterns:
        for f in glob.glob(os.path.join(ROOT_DIR, pat)):
            if os.path.getmtime(f) > index_mtime:
                return True
    return False


def auto_sync_if_stale() -> bool:
    """Rebuilds index if any code file was modified."""
    if is_index_stale():
        print("⚡ [FastIndex Auto-Sync] Code modifications detected, rebuilding codebase index...")
        build_codebase_index()
        print("✅ [FastIndex Auto-Sync] Codebase index refreshed successfully.")
        return True
    return False


def install_git_hook():
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
        # make executable on posix if possible
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


def main():
    args = sys.argv[1:]
    if not args or args[0] in ["--build", "build"]:
        print("🚀 [FastIndex] Building codebase index...")
        idx = build_codebase_index()
        print(f"✅ [FastIndex] Indexed {idx['total_files']} files ({idx['total_symbols']} symbols) -> {INDEX_JSON_PATH} & {INDEX_MD_PATH}")
        return

    cmd = args[0]

    if cmd in ["--sync", "sync"]:
        auto_sync_if_stale()
        return

    if cmd in ["--install-hook", "install-hook"]:
        install_git_hook()
        return

    if cmd in ["symbol", "-s"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py symbol <symbol_name>")
            return
        sym = args[1]
        results = query_symbol(sym)
        if results:
            print(f"🎯 Found {len(results)} matches for symbol '{sym}':")
            for r in results:
                line_str = f":{r.get('line')}" if r.get('line') else ""
                type_str = f"[{r.get('type')}]"
                doc_str = f" - {r.get('doc')}" if r.get('doc') else ""
                print(f"  • {r.get('file')}{line_str} {type_str}{doc_str}")
        else:
            print(f"❌ Symbol '{sym}' not found in index.")

    elif cmd in ["source", "-c"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py source <domain_or_name>")
            return
        query = args[1]
        res = query_source(query)
        if res:
            print(f"📰 Source Registry Match for '{query}':")
            print(f"  • Source Name : {res.get('source')} ({res.get('domain')})")
            print(f"  • Crawler File: {res.get('crawler_file')}")
            print(f"  • Entrypoint  : {res.get('entrypoint')}")
            print(f"  • Unit Test   : {res.get('test_file', '-')}")
            print(f"  • Rule Section: {res.get('rule_section', '-')}")
            print(f"  • Features    : {', '.join(res.get('features', []))}")
        else:
            print(f"❌ No registered source crawler found matching '{query}'.")

    elif cmd in ["data", "-d"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py data <id_or_keyword>")
            return
        q = args[1]
        print(f"🔍 Searching data stores for '{q}'...")
        matches = query_data(q)
        if matches:
            print(f"✅ Found {len(matches)} data store matches:")
            for m in matches:
                cov = m.get('cover_image') or 'No image'
                print(f"  • [{m.get('file')}] ID: {m.get('id')} | Title: {m.get('title')} | Cover: {cov}")
        else:
            print(f"❌ No items found in data stores matching '{q}'.")

    elif cmd in ["search", "-q"]:
        if len(args) < 2:
            print("Usage: python tools/fast_index.py search <keyword>")
            return
        kw = args[1]
        res = search_codebase(kw)
        print(f"🔎 Search Results for '{kw}':")
        if res["matched_sources"]:
            print(f"  [Sources ({len(res['matched_sources'])})]")
            for s in res["matched_sources"]:
                print(f"    • {s['source']} ({s['domain']}) -> {s['crawler_file']}::{s['entrypoint']}")
        if res["matched_files"]:
            print(f"  [Files ({len(res['matched_files'])})]")
            for f in res["matched_files"][:10]:
                print(f"    • {f}")
        if res["matched_symbols"]:
            print(f"  [Symbols ({len(res['matched_symbols'])})]")
            for s in res["matched_symbols"][:15]:
                print(f"    • {s['name']} -> {s['file']}:{s.get('line', '?')} [{s.get('type')}]")
        if not (res["matched_sources"] or res["matched_files"] or res["matched_symbols"]):
            print("  ❌ No matches found.")


if __name__ == "__main__":
    main()
