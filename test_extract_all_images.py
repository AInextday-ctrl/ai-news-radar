import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import feedparser

# Test Reddit image extraction
reddit_feed = feedparser.parse("https://www.reddit.com/r/singularity/.rss", request_headers={"User-Agent": "AI-Radar/2.0"})
print(f"Reddit items: {len(reddit_feed.entries)}")
for e in reddit_feed.entries[:5]:
    img = None
    if hasattr(e, "media_thumbnail") and e.media_thumbnail:
        img = e.media_thumbnail[0]["url"]
    if not img and hasattr(e, "content"):
        m = re.search(r'<img[^>]+src=["\'](https?://[^"\'>]+)["\']', e.content[0].value)
        if m:
            img = m.group(1)
    print(f"  [{e.title[:30]}] Image found: {bool(img)} -> {img[:60] if img else 'None'}")

# Test Ars Technica image extraction
ars_feed = feedparser.parse("https://feeds.arstechnica.com/arstechnica/technology-lab")
print(f"\nArs Technica items: {len(ars_feed.entries)}")
for e in ars_feed.entries[:5]:
    img = None
    if hasattr(e, "media_content") and e.media_content:
        img = e.media_content[0].get("url")
    if not img and hasattr(e, "summary"):
        m = re.search(r'<img[^>]+src=["\'](https?://[^"\'>]+)["\']', e.summary)
        if m:
            img = m.group(1)
    print(f"  [{e.title[:30]}] Image found: {bool(img)} -> {img[:60] if img else 'None'}")
