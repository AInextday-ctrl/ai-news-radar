#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apify X (Twitter) 真实增量抓取器 (Apify Incremental Twitter Scraper)
===================================================================
1. 真实性保障:
   - 彻底告别虚构推文与 404 伪造 URL，直接调用 Apify 官方认证 Actor (优先 xquik/x-tweet-scraper，备用 apidojo/tweet-scraper)；
   - 抓取真实发布的原文、真实的媒体配图、以及官方原帖 URL (https://x.com/{user}/status/{id})；
   - 实时同步真实的点赞数 (likes)、转推数 (retweets)、回复数 (replies)、浏览量 (views)。

2. 严格去重与按时间增量采集 (Incremental Crawl):
   - 维护持久化增量游标 (data/apify_crawler_state.json)；
   - 记录已抓取的 status_id 与各大V的最新发布时间戳 (watermark)；
   - 绝不重复采集已有推文，对已采集推文仅刷新其实时互动指标；
   - 仅对比游标时间戳更新的最新推文进行解析、翻译并增量归入库中。
"""

import os
import sys
import json
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx

# 导入翻译与规格提取器
try:
    from processor import free_translate_zh
except ImportError:
    def free_translate_zh(text: str) -> str:
        return text

try:
    from fetcher import match_celebrity_profile, extract_tech_specs
except ImportError:
    def match_celebrity_profile(handle: str) -> Optional[Dict[str, Any]]:
        return None
    def extract_tech_specs(title: str, snippet: str = "") -> List[str]:
        return ["前沿发声"]

# 状态记录文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "data", "apify_crawler_state.json")
LATEST_NEWS_FILE = os.path.join(BASE_DIR, "data", "latest_news.json")
PUBLIC_NEWS_FILE = os.path.join(BASE_DIR, "public", "data", "latest_news.json")

# 重点追踪的全球 AI 顶尖实验室与领袖大V分组
LEADER_HANDLES = [
    "sama",
    "karpathy",
    "ylecun",
    "demishassabis",
    "DrJimFan",
    "OfficialLoganK",
    "gdb",
    "thsottiaux",
    "danshipper"
]

LAB_HANDLES = [
    "OpenAI",
    "AnthropicAI",
    "ClaudeAI",
    "deepseek_ai",
    "GoogleDeepMind",
    "cursor_ai",
    "huggingface",
    "ArtificialAnlys"
]


def get_apify_token() -> Optional[str]:
    """获取 Apify API Token (优先环境变量，其次 .env 文件)"""
    token = os.getenv("APIFY_API_TOKEN")
    if token and token.strip():
        return token.strip()

    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APIFY_API_TOKEN="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return None


def load_crawler_state() -> Dict[str, Any]:
    """读取增量采集状态与游标"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_crawl_utc": None,
        "known_status_ids": [],
        "author_watermarks": {}
    }


def save_crawler_state(state: Dict[str, Any]):
    """持久化保存增量游标"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def format_metric_count(val: Any) -> str:
    """将数字格式化为 k/M 紧凑展示 (例如 4943 -> 4.9k, 681495 -> 681.5k)"""
    if val is None or val == "":
        return ""
    try:
        num = float(val)
        if num <= 0:
            return "0"
        if num < 1000:
            return str(int(num))
        if num < 1000000:
            return f"{num / 1000.0:.1f}k"
        return f"{num / 1000000.0:.1f}M"
    except (ValueError, TypeError):
        return str(val)


def parse_twitter_created_at(time_str: str) -> Optional[datetime]:
    """解析 Twitter 原生时间格式 (例如 'Tue Sep 22 21:38:07 +0000 2026' 或 ISO 格式)"""
    if not time_str:
        return None
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except Exception:
        pass
    try:
        return datetime.strptime(time_str, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        pass
    return None


def _call_apify_actor(token: str, query: str, max_items: int = 20) -> List[Dict[str, Any]]:
    """
    通过 Apify 执行搜索查询，优先使用无配额限制的 xquik~x-tweet-scraper
    """
    # 方案 1: xquik~x-tweet-scraper (极速、低成本、无月度免费限制)
    url_xquik = f"https://api.apify.com/v2/acts/xquik~x-tweet-scraper/run-sync-get-dataset-items?token={token}"
    payload_xquik = {
        "searchTerms": [query],
        "maxItems": max_items,
        "queryType": "Latest"
    }

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(url_xquik, json=payload_xquik)
            if resp.status_code in [200, 201]:
                data = resp.json()
                if isinstance(data, list):
                    # 过滤掉 noResults 占位
                    valid = [d for d in data if isinstance(d, dict) and not d.get("noResults") and d.get("id")]
                    if valid:
                        return valid
            else:
                print(f"  ⚠️ [xquik] HTTP {resp.status_code}: {resp.text[:120]}")
    except Exception as e:
        print(f"  ⚠️ [xquik] 异常: {e}")

    # 方案 2: apidojo~tweet-scraper 作为备用
    url_apidojo = f"https://api.apify.com/v2/acts/apidojo~tweet-scraper/run-sync-get-dataset-items?token={token}"
    payload_apidojo = {
        "searchTerms": [query],
        "maxItems": max_items,
        "sort": "Latest"
    }
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(url_apidojo, json=payload_apidojo)
            if resp.status_code in [200, 201]:
                data = resp.json()
                if isinstance(data, list):
                    valid = [d for d in data if isinstance(d, dict) and not d.get("noResults") and d.get("id")]
                    if valid:
                        return valid
    except Exception as e:
        print(f"  ⚠️ [apidojo] 备用通道异常: {e}")

    return []


def fetch_incremental_tweets(
    force_update: bool = False
) -> List[Dict[str, Any]]:
    """
    通过 Apify 官方 Actor 进行非重复、按时间增量采集最新真实推文。
    严格执行:
    1. 绝不重复采集已有推文 (去重校验 + 游标水印)
    2. 已有推文仅实时同步互动量 (likes, retweets, views)
    3. 全新推文执行翻译与结构化归入
    """
    token = get_apify_token()
    if not token:
        print("  ⚠️ [Apify 增量采集器] 未检测到 APIFY_API_TOKEN，跳过 Apify 抓取通道。")
        return []

    state = load_crawler_state()
    known_ids = set(state.get("known_status_ids", []))
    watermarks = state.get("author_watermarks", {})

    # 也从本地数据库加载已收录的推文 ID
    existing_file_ids = set()
    for fp in [LATEST_NEWS_FILE, PUBLIC_NEWS_FILE]:
        if os.path.exists(fp):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    for item in cdata.get("celebrity", []):
                        sid = str(item.get("status_id") or "").strip()
                        if sid:
                            existing_file_ids.add(sid)
                            known_ids.add(sid)
            except Exception:
                pass

    print(f"  🚀 [Apify 增量采集器] 启动增量抓取: 监控领袖与实验室大V，已收录历史真实推文 {len(known_ids)} 篇...")

    # 分组构建精准搜索查询
    q_leaders = "(" + " OR ".join([f"from:{h}" for h in LEADER_HANDLES]) + ")"
    q_labs = "(" + " OR ".join([f"from:{h}" for h in LAB_HANDLES]) + ")"

    raw_items = []
    # 抓取领袖推文
    res1 = _call_apify_actor(token, q_leaders, max_items=20)
    raw_items.extend(res1)
    # 抓取官方实验室推文
    res2 = _call_apify_actor(token, q_labs, max_items=20)
    raw_items.extend(res2)

    print(f"  📥 [Apify 增量采集器] 云端抓取完成，共返回 {len(raw_items)} 条原生推文，开始执行时间增量校验与去重过滤...")

    now_utc = datetime.now(timezone.utc)
    new_items = []
    skipped_known = 0
    updated_metrics_count = 0
    live_metrics_map = {}

    for it in raw_items:
        tweet_id = str(it.get("id") or "").strip()
        if not tweet_id:
            continue

        author_obj = it.get("author") or {}
        user_name = (author_obj.get("username") or author_obj.get("userName") or "").strip()
        if not user_name:
            u_match = re.search(r'x\.com/([^/]+)/status', it.get("url") or "")
            user_name = u_match.group(1) if u_match else "unknown"

        canonical_url = f"https://x.com/{user_name}/status/{tweet_id}"

        # 解析时间
        created_raw = it.get("createdAt")
        dt = parse_twitter_created_at(created_raw) or now_utc
        iso_time = dt.isoformat()

        # 提取真实互动指标
        views_raw = it.get("viewCount")
        likes_raw = it.get("likeCount")
        comments_raw = it.get("replyCount")
        retweets_raw = it.get("retweetCount")

        metrics = {
            "views": format_metric_count(views_raw),
            "likes": format_metric_count(likes_raw),
            "comments": format_metric_count(comments_raw),
            "retweets": format_metric_count(retweets_raw),
            "platform": "x",
            "verified": bool(author_obj.get("isBlueVerified") or author_obj.get("isVerified"))
        }

        # 记录指标映射以供刷新现有推文
        live_metrics_map[tweet_id] = metrics

        # 1. 如果已存在该推文：严格跳过，不要重复采集
        if tweet_id in known_ids and not force_update:
            skipped_known += 1
            continue

        # 2. 检查作者时间游标 (按时间进行增加采集)
        author_mark = watermarks.get(user_name, {})
        last_dt_str = author_mark.get("latest_created_at")
        if last_dt_str:
            try:
                last_dt = datetime.fromisoformat(last_dt_str)
                if dt <= last_dt and not force_update:
                    skipped_known += 1
                    continue
            except Exception:
                pass

        # 3. 过滤低价值无意义单句短回复 (例如纯 @ 闲聊且点赞不足 100)
        tweet_text = (it.get("text") or it.get("fullText") or "").strip()
        if not tweet_text:
            continue
        is_reply = it.get("isReply") or False
        if is_reply and len(tweet_text) < 30 and (likes_raw is None or int(likes_raw or 0) < 100):
            continue

        # 媒体配图解析
        image_url = None
        media_list = it.get("media") or []
        if isinstance(media_list, list) and len(media_list) > 0:
            first_media = media_list[0]
            if isinstance(first_media, str) and first_media.startswith("http"):
                image_url = first_media
            elif isinstance(first_media, dict):
                image_url = first_media.get("media_url_https") or first_media.get("url")

        # 资料与认证匹配
        profile = match_celebrity_profile(user_name)
        author_name = profile.get("name") if profile else (author_obj.get("name") or user_name)
        author_handle = f"@{user_name}"
        author_avatar = profile.get("avatar") if profile else (author_obj.get("profilePicture") or f"https://unavatar.io/x/{user_name}")
        author_role = profile.get("role") if profile else (author_obj.get("description") or "AI 前沿领袖 / 核心开发者")
        entity_type = profile.get("entity_type") if profile else ("company" if user_name.lower() in ["openai", "anthropicai", "deepseek_ai", "googledeepmind", "cursor_ai", "huggingface"] else "person")

        # 规格标签与高亮翻译
        spec_tags = extract_tech_specs(tweet_text, "") or (["硅谷前沿原声", "大V发声"] if entity_type == "person" else ["官方发布", "模型突破"])

        # 智能翻译中文
        trans_zh = free_translate_zh(tweet_text)

        # 唯一 ID
        id_hash = hashlib.md5(f"apify_x_{tweet_id}".encode("utf-8")).hexdigest()[:16]

        news_item = {
            "id": id_hash,
            "status_id": tweet_id,
            "category": "celebrity",
            "sub_category": "viral_post" if (likes_raw and int(likes_raw) >= 3000) else None,
            "title": tweet_text[:120],
            "title_en": tweet_text,
            "title_zh": trans_zh[:120] if trans_zh else None,
            "quote_en": tweet_text,
            "quote_zh": trans_zh,
            "full_text_en": tweet_text,
            "full_text_zh": trans_zh,
            "url": canonical_url,
            "image_url": image_url,
            "source": f"𝕏 (Twitter) · {author_handle}",
            "author": author_name,
            "author_handle": author_handle,
            "author_avatar": author_avatar,
            "author_role": author_role,
            "entity_type": entity_type,
            "platform": "x",
            "raw_published_at": iso_time,
            "metrics": metrics,
            "spec_tags": spec_tags,
            "content_snippet": tweet_text,
            "summary_en": tweet_text,
            "summary_zh": trans_zh,
            "is_viral": bool(likes_raw and int(likes_raw) >= 3000),
            "is_pinned": False,
            "tags": ["𝕏领袖观点", "前沿发声"] if entity_type == "person" else ["官方动态", "模型发布"]
        }

        new_items.append(news_item)
        known_ids.add(tweet_id)

        # 更新作者游标
        current_watermark = watermarks.get(user_name, {})
        current_watermark["latest_status_id"] = tweet_id
        current_watermark["latest_created_at"] = iso_time
        watermarks[user_name] = current_watermark

    # 保存状态
    state["last_crawl_utc"] = now_utc.isoformat()
    state["known_status_ids"] = list(known_ids)[-1000:]
    state["author_watermarks"] = watermarks
    save_crawler_state(state)

    # 4. 刷新已有推文的实时指标并合并新增推文入库
    updated_metrics_count = update_existing_tweet_metrics(live_metrics_map)

    print(f"  ✨ [Apify 增量采集器] 增量捕获新推文: {len(new_items)} 篇，跳过已有推文: {skipped_known} 篇，刷新已有推文指标: {updated_metrics_count} 条。")
    return new_items


def update_existing_tweet_metrics(live_metrics_map: Dict[str, Dict[str, Any]]) -> int:
    """对已存在的推文同步刷新最新的实时互动量 (likes, retweets, views, comments)"""
    if not live_metrics_map:
        return 0

    updated = 0
    for target_path in [LATEST_NEWS_FILE, PUBLIC_NEWS_FILE]:
        if not os.path.exists(target_path):
            continue
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            celebs = data.get("celebrity", [])
            modified = False
            for item in celebs:
                sid = str(item.get("status_id") or "").strip()
                if not sid:
                    m = re.search(r'/status/(\d+)', item.get("url") or "")
                    if m:
                        sid = m.group(1)
                        item["status_id"] = sid
                        modified = True

                if sid and sid in live_metrics_map:
                    new_m = live_metrics_map[sid]
                    # 更新真实指标
                    item["metrics"] = new_m
                    # 同步更新爆款标志
                    likes_str = new_m.get("likes", "")
                    try:
                        if "k" in likes_str:
                            lval = float(likes_str.replace("k", "")) * 1000
                        elif "M" in likes_str:
                            lval = float(likes_str.replace("M", "")) * 1000000
                        else:
                            lval = float(likes_str or 0)
                        if lval >= 3000:
                            item["is_viral"] = True
                            item["sub_category"] = "viral_post"
                    except Exception:
                        pass
                    modified = True
                    updated += 1

            if modified:
                if "grouped" in data and isinstance(data["grouped"], dict):
                    data["grouped"]["celebrity"] = celebs
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ 刷新 {target_path} 指标异常: {e}")

    return updated


def merge_apify_tweets_into_database(new_tweets: List[Dict[str, Any]]):
    """将全新抓取的真实推文增量并入本地与公开 latest_news.json 数据库"""
    if not new_tweets:
        return

    for target_path in [LATEST_NEWS_FILE, PUBLIC_NEWS_FILE]:
        if not os.path.exists(target_path):
            continue
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            existing_celebs = data.get("celebrity", [])
            seen_ids = set()
            merged = []

            # 1. 优先放入新增真实推文
            for nt in new_tweets:
                s_id = nt.get("status_id") or nt.get("url")
                if s_id not in seen_ids:
                    seen_ids.add(s_id)
                    merged.append(nt)

            # 2. 追加已有推文（去重）
            for ec in existing_celebs:
                s_id = ec.get("status_id") or ec.get("url")
                if s_id not in seen_ids:
                    seen_ids.add(s_id)
                    merged.append(ec)

            # 3. 按发布时间倒序排序 (最新在最前)
            merged.sort(key=lambda x: x.get("raw_published_at") or "", reverse=True)

            data["celebrity"] = merged
            if "grouped" in data and isinstance(data["grouped"], dict):
                data["grouped"]["celebrity"] = merged

            # 同样同步主 items 列表中的 celebrity
            if "items" in data and isinstance(data["items"], list):
                non_celeb = [it for it in data["items"] if it.get("category") != "celebrity"]
                all_combined = non_celeb + merged
                all_combined.sort(key=lambda x: x.get("raw_published_at") or "", reverse=True)
                data["items"] = all_combined

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 成功将 {len(new_tweets)} 篇真实增量推文同步并入 {target_path}")
        except Exception as e:
            print(f"  ❌ 合并数据至 {target_path} 异常: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("   AI News Radar - Apify 真实推文增量采集与去重流水线")
    print("=" * 60)
    tweets = fetch_incremental_tweets()
    if tweets:
        merge_apify_tweets_into_database(tweets)
        print(f"\n🎉 采集成功！共新增 {len(tweets)} 篇 100% 真实推文。")
        for i, t in enumerate(tweets[:8]):
            print(f"  [{i+1}] {t['author']} ({t['author_handle']}): {t['quote_en'][:60]}... | ❤️ {t['metrics']['likes']} | 🔗 {t['url']}")
    else:
        print("\n✅ 当前没有产生更新的增量推文（已是最新，无重复推文）。")
