#!/usr/bin/env python3
"""
tools/update_videos_feed.py
Performs targeted update of video channels (YouTube Shorts, YouTube Tutorials, TikTok)
and refreshes data/latest_news.json and public/data/latest_news.json.
"""
from __future__ import annotations
import os
import sys
import json
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fetcher import fetch_youtube_videos, fetch_tiktok_trending_videos, extract_clean_video_id
from viral_video_engine import interleave_videos_by_creator
DATA_LATEST = os.path.join(ROOT, "data", "latest_news.json")
PUBLIC_LATEST = os.path.join(ROOT, "public", "data", "latest_news.json")
PUBLIC_ARCHIVE_VIDEOS = os.path.join(ROOT, "public", "data", "archive_videos.json")

def main():
    print("▶ Harvesting fresh YouTube videos and Shorts...")
    yt_vids = fetch_youtube_videos()
    print(f"  ✓ Fetched {len(yt_vids)} YouTube videos")

    print("▶ Harvesting fresh TikTok videos...")
    tt_vids = fetch_tiktok_trending_videos()
    print(f"  ✓ Fetched {len(tt_vids)} TikTok videos")

    all_harvested = yt_vids + tt_vids
    print(f"  Total harvested videos: {len(all_harvested)}")

    # Load existing data/latest_news.json
    with open(DATA_LATEST, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    existing_vids = master_data.get("grouped", {}).get("videos", [])
    seen_ids = set()
    merged = []

    # New harvested videos first
    for v in all_harvested:
        vid = v.get("id") or v.get("video_id")
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            merged.append(v)

    # Then existing videos
    for v in existing_vids:
        vid = v.get("id") or v.get("video_id")
        if vid and vid not in seen_ids:
            seen_ids.add(vid)
            merged.append(v)

    print(f"  Merged unique video pool: {len(merged)}")
    balanced_vids = interleave_videos_by_creator(merged)
    master_data["grouped"]["videos"] = balanced_vids
    master_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save data/latest_news.json
    with open(DATA_LATEST, "w", encoding="utf-8") as f:
        json.dump(master_data, f, ensure_ascii=False, separators=(',', ':'))
    print("  ✓ Saved data/latest_news.json")

    # Load public/data/latest_news.json
    with open(PUBLIC_LATEST, "r", encoding="utf-8") as f:
        public_data = json.load(f)

    # Slice public videos with quota guarantee: 16 horizontal + 8 vertical = 24 items
    verts = [x for x in balanced_vids if x.get("aspect_ratio") == "9:16" or x.get("platform") in ("shorts", "tiktok")]
    horizs = [x for x in balanced_vids if x not in verts]
    selected_videos = horizs[:16] + verts[:8]
    if len(selected_videos) < 24:
        rem = [x for x in balanced_vids if x not in selected_videos]
        selected_videos.extend(rem[:24 - len(selected_videos)])

    public_data.setdefault("grouped", {})["videos"] = selected_videos[:24]
    public_data["updated_at"] = master_data["updated_at"]

    with open(PUBLIC_LATEST, "w", encoding="utf-8") as f:
        json.dump(public_data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"  ✓ Saved public/data/latest_news.json ({len(selected_videos[:24])} videos, size: {os.path.getsize(PUBLIC_LATEST)/1024:.1f} KB)")

    # Save public/data/archive_videos.json
    with open(PUBLIC_ARCHIVE_VIDEOS, "w", encoding="utf-8") as f:
        json.dump(balanced_vids[:300], f, ensure_ascii=False, separators=(',', ':'))
    print(f"  ✓ Saved public/data/archive_videos.json ({len(balanced_vids[:300])} videos)")

    # Print breakdown of public videos
    pub_v = public_data["grouped"]["videos"]
    pub_verts = [x for x in pub_v if x.get("aspect_ratio") == "9:16" or x.get("platform") in ("shorts", "tiktok")]
    pub_horiz = [x for x in pub_v if x not in pub_verts]
    print(f"\n📊 Public Video Slice Breakdown:")
    print(f"  Total Public Videos: {len(pub_v)}")
    print(f"  16:9 Horizontal Tutorials: {len(pub_horiz)}")
    print(f"  9:16 Vertical Shorts/TikTok: {len(pub_verts)}")
    for idx, v in enumerate(pub_verts):
        print(f"    [{idx+1}] {v.get('platform')} | {v.get('views')} | {v.get('title')[:40]}")

if __name__ == "__main__":
    main()
