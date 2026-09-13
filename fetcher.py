"""
Fetcher module - Fetches AI news and updates from free, public sources.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import hashlib
import time
from typing import List, Dict, Any
import httpx
import feedparser
from config import SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AI-Radar/1.0"
}


def make_id(url: str, title: str) -> str:
    """Generate a unique deterministic hash ID for an item."""
    raw = f"{url}-{title}".encode("utf-8")
    return hashlib.md5(raw).hexdigest()[:16]


def fetch_rss(source_key: str, max_items: int = 8) -> List[Dict[str, Any]]:
    """Fetch items from a standard RSS/Atom feed."""
    items = []
    cfg = SOURCES.get(source_key)
    if not cfg:
        return items

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=12) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                for entry in feed.entries[:max_items]:
                    title = entry.get("title", "").strip()
                    if not title:
                        continue
                    url = entry.get("link", "")
                    author = entry.get("author", cfg["name"])
                    published = entry.get("published") or entry.get("updated", "")
                    summary = entry.get("summary") or entry.get("description", "")
                    # 简单去除部分 html 标签
                    clean_summary = summary.split("<")[0][:250] if "<" in summary else summary[:250]

                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "url": url,
                        "source": cfg["name"],
                        "author": author,
                        "raw_published_at": published,
                        "metrics": {},
                        "content_snippet": clean_summary or f"From {cfg['name']}",
                        "default_category": cfg["default_category"]
                    })
    except Exception as e:
        print(f"  ❌ [{cfg['name']}] 抓取失败: {e}")
    return items


def fetch_hacker_news() -> List[Dict[str, Any]]:
    """Fetch AI stories from Hacker News using Algolia's free search API."""
    items = []
    cfg = SOURCES["hacker_news"]
    try:
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("hits", []):
                    title = hit.get("title")
                    if not title:
                        continue
                    url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    points = hit.get("points") or 0
                    comments = hit.get("num_comments") or 0
                    items.append({
                        "id": make_id(url, title),
                        "title": title,
                        "url": url,
                        "source": "Hacker News",
                        "author": hit.get("author", "HN User"),
                        "raw_published_at": hit.get("created_at", ""),
                        "metrics": {"score": points, "comments": comments},
                        "content_snippet": f"HN 热度: {points} 点赞, {comments} 评论",
                        "default_category": cfg["default_category"]
                    })
    except Exception as e:
        print(f"  ❌ [Hacker News] 抓取失败: {e}")
    return items


def fetch_hf_trending() -> List[Dict[str, Any]]:
    """Fetch trending items from Hugging Face."""
    items = []
    cfg = SOURCES["huggingface_trending"]
    try:
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                data = resp.json()
                trending_list = data if isinstance(data, list) else data.get("recentlyTrending", [])
                for item in trending_list[:8]:
                    repo_data = item.get("repoData", item)
                    repo_id = repo_data.get("id") or repo_data.get("_id")
                    if not repo_id:
                        continue
                    repo_type = item.get("repoType", "model")
                    url = f"https://huggingface.co/{repo_id}"
                    likes = repo_data.get("likes", 0)
                    items.append({
                        "id": make_id(url, repo_id),
                        "title": f"[{repo_type.capitalize()}] {repo_id}",
                        "url": url,
                        "source": "Hugging Face",
                        "author": repo_id.split("/")[0] if "/" in repo_id else "Hugging Face",
                        "raw_published_at": "",
                        "metrics": {"likes": likes},
                        "content_snippet": f"Hugging Face 趋势 ({repo_type}) · {likes} 喜欢",
                        "default_category": cfg["default_category"]
                    })
    except Exception as e:
        print(f"  ❌ [Hugging Face] 抓取失败: {e}")
    return items


def fetch_github_trending() -> List[Dict[str, Any]]:
    """Fetch top new/trending AI repositories from GitHub API."""
    items = []
    cfg = SOURCES["github_trending"]
    try:
        with httpx.Client(headers=HEADERS, timeout=12) as client:
            resp = client.get(cfg["url"])
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get("items", [])[:8]:
                    full_name = repo.get("full_name", "")
                    description = repo.get("description") or "No description provided."
                    stars = repo.get("stargazers_count", 0)
                    url = repo.get("html_url", "")
                    items.append({
                        "id": make_id(url, full_name),
                        "title": f"GitHub: {full_name}",
                        "url": url,
                        "source": "GitHub",
                        "author": repo.get("owner", {}).get("login", "GitHub"),
                        "raw_published_at": repo.get("created_at", ""),
                        "metrics": {"stars": stars},
                        "content_snippet": f"⭐ {stars} stars | {description[:180]}",
                        "default_category": cfg["default_category"]
                    })
    except Exception as e:
        print(f"  ❌ [GitHub] 抓取失败: {e}")
    return items


def fetch_all_sources() -> List[Dict[str, Any]]:
    """Fetch and aggregate raw items from all configured public sources."""
    print("🚀 开始抓取各大平台最新 AI 动态...")
    all_items = []

    # 1. TechCrunch AI
    tc_items = fetch_rss("techcrunch_ai", max_items=6)
    print(f"  ✓ TechCrunch AI: 获取到 {len(tc_items)} 条")
    all_items.extend(tc_items)

    # 2. The Verge AI
    vg_items = fetch_rss("theverge_ai", max_items=6)
    print(f"  ✓ The Verge AI: 获取到 {len(vg_items)} 条")
    all_items.extend(vg_items)

    # 3. Hacker News AI
    hn_items = fetch_hacker_news()
    print(f"  ✓ Hacker News: 获取到 {len(hn_items)} 条")
    all_items.extend(hn_items)

    # 4. Reddit LocalLLaMA
    rd_items = fetch_rss("reddit_localllama", max_items=8)
    print(f"  ✓ Reddit LocalLLaMA: 获取到 {len(rd_items)} 条")
    all_items.extend(rd_items)

    # 5. Hugging Face Trending
    hf_items = fetch_hf_trending()
    print(f"  ✓ Hugging Face: 获取到 {len(hf_items)} 条")
    all_items.extend(hf_items)

    # 6. GitHub AI Trending
    gh_items = fetch_github_trending()
    print(f"  ✓ GitHub Trending: 获取到 {len(gh_items)} 条")
    all_items.extend(gh_items)

    # 7. ArXiv CS.AI
    ax_items = fetch_rss("arxiv_ai", max_items=6)
    print(f"  ✓ ArXiv AI: 获取到 {len(ax_items)} 条")
    all_items.extend(ax_items)

    # 去重
    seen_ids = set()
    unique_items = []
    for it in all_items:
        if it["id"] not in seen_ids:
            seen_ids.add(it["id"])
            unique_items.append(it)

    print(f"🎉 抓取完成！共收集到 {len(unique_items)} 条有效动态。\n")
    return unique_items


if __name__ == "__main__":
    items = fetch_all_sources()
    print("前 3 条样本数据：")
    for item in items[:3]:
        print(f"- [{item['source']}] {item['title']} -> {item['url']}")
