import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import httpx
import feedparser

feeds = {
    "ArXiv AI": "https://rss.arxiv.org/rss/cs.AI",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Reddit RSS": "https://www.reddit.com/r/LocalLLaMA/.rss"
}

headers = {
    "User-Agent": "AI-Radar-Aggregator/1.0 (contact: info@example.com)"
}

for name, url in feeds.items():
    try:
        with httpx.Client(headers=headers, follow_redirects=True, timeout=10) as client:
            resp = client.get(url)
            print(f"[{name}] Status: {resp.status_code}")
            if resp.status_code == 200:
                feed = feedparser.parse(resp.text)
                print(f"  -> Parsed {len(feed.entries)} entries. Top: {feed.entries[0].title[:50] if feed.entries else 'None'}")
    except Exception as e:
        print(f"[{name}] Error: {e}")
