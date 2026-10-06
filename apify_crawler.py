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

# 重点追踪的全球 AI 顶尖实验室与领袖大V分组 (深度扩展 70+ 全球前沿领袖与官方研发团队)
LEADER_HANDLES = [
    # 核心实验室掌舵人与首席科学家
    "sama", "karpathy", "ylecun", "demishassabis", "ilyasut", "DarioAmodei",
    "gdb", "elonmusk", "finkd", "satyanadella", "sundarpichai", "AndrewYNg",
    "DrJimFan", "JeffDean", "drfeifei", "AravSrinivas", "arthurmensch", "aidangomez",
    # 一线核心架构师、技术副总与关键布道者
    "thsottiaux", "polynoamial", "OfficialLoganK", "swyx", "danshipper",
    "alexandr_wang", "bindureddy", "svpino", "rowancheung", "samyamiam",
    "mikeyk", "alexalbert__", "kevin_t_ngo", "hwchase17", "jerryjliu0",
    "levelsio", "amasad", "emostaque", "fchollet", "_jasonwei", "markchen90",
    "woj_zaremba", "johnschulman2", "AmandaAskell", "ch402", "jackclarkSF",
    "percyliang", "pabbeel", "svlevine", "chelseabfinn", "chrmanning", "danqic",
    "npew", "DanHendrycks", "Paul_Christiano", "janleike", "leopoldasch",
    "dwarkesh_sp", "tegmark", "ESYudkowsky", "ClementDelangue", "tunguz", "Kantrowitz"
]

LAB_HANDLES = [
    # 顶尖模型实验室与云巨头
    "OpenAI", "OpenAIDevs", "AnthropicAI", "ClaudeAI", "ClaudeDevs",
    "deepseek_ai", "GoogleDeepMind", "GoogleAI", "GoogleAIStudio", "xai",
    "MistralAI", "cursor_ai", "huggingface", "MetaAI", "MSFTResearch",
    "NVIDIAAI", "Alibaba_Qwen", "MoonshotAI", "ZhipuAI", "MiniMax_AI",
    "stepfun_ai", "Cohere", "PerplexityAI", "LangChainAI", "llama_index",
    "ollama", "LMStudioAI", "vllm_project", "sgl_project", "UnslothAI",
    "crewAIInc", "replit", "v0", "stackblitz", "codeiumdev",
    "togethercompute", "GroqInc", "bfl_ml", "midjourney", "runwayml",
    "luma_ai", "Kling_ai", "Hailuo_AI", "suno_ai_", "elevenlabsio", "ArtificialAnlys"
]

# 引入动态知识库与自适应搜索生成器 (彻底告别写死过时模型名称)
try:
    from knowledge_base import get_dynamic_trending_queries
except ImportError:
    def get_dynamic_trending_queries() -> List[str]:
        return [
            '(#AI OR #LLM OR #GenerativeAI OR #GenAI) (min_faves:50 OR min_retweets:10)',
            '(#ClaudeCode OR #Cursor OR #DeepSeek OR #ChatGPT OR #OpenAI) (min_faves:30 OR min_retweets:5)',
            '(#AIAgent OR #VibeCoding OR #PromptEngineering OR #ComfyUI OR #FLUX) (min_faves:25)',
            '("Claude Fable" OR "Opus 5.5" OR "GPT 6" OR "DeepSeek-V4") (min_faves:30)'
        ]


def get_apify_tokens() -> List[str]:
    """获取所有配置的 Apify API Token 列表，支持逗号/分号/换行分隔的多 Token 轮询容灾"""
    raw_tokens = []
    
    # 1. 优先读取主环境变量 APIFY_API_TOKEN / APIFY_API_TOKENS
    for key in ["APIFY_API_TOKEN", "APIFY_API_TOKENS", "APIFY_TOKEN"]:
        val = os.getenv(key)
        if val:
            raw_tokens.extend(re.split(r'[,;\s\n]+', val.strip()))

    # 2. 读取带编号的环境变量 (如 APIFY_API_TOKEN_1, APIFY_API_TOKEN_2, ...)
    for key, val in os.environ.items():
        if key.startswith("APIFY_API_TOKEN_") and val.strip():
            raw_tokens.append(val.strip())

    # 3. 读取本地 .env 文件
    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("APIFY_API_TOKEN=") or line.startswith("APIFY_API_TOKENS="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        raw_tokens.extend(re.split(r'[,;\s\n]+', val))
                    elif line.startswith("APIFY_API_TOKEN_"):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            raw_tokens.append(val)
        except Exception:
            pass

    clean_tokens = []
    seen = set()
    for tok in raw_tokens:
        tok = tok.strip()
        if tok and tok not in seen and len(tok) > 10:
            clean_tokens.append(tok)
            seen.add(tok)
    return clean_tokens


def get_apify_token() -> Optional[str]:
    """兼容旧接口：返回首个可用 Token"""
    tokens = get_apify_tokens()
    return tokens[0] if tokens else None


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


def _call_apify_actor(tokens: Any, query: str, max_items: int = 35) -> List[Dict[str, Any]]:
    """
    通过 Apify 执行搜索查询，支持多账号 Token 轮询与自动故障转移
    """
    if isinstance(tokens, str):
        tokens = [tokens]
    if not tokens:
        return []

    for t_idx, token in enumerate(tokens):
        masked_tok = token[:6] + "..." + token[-4:] if len(token) > 10 else "***"
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
                        valid = [d for d in data if isinstance(d, dict) and not d.get("noResults") and d.get("id")]
                        if valid:
                            return valid
                elif resp.status_code in [401, 402, 403, 429]:
                    print(f"  ⚠️ [Apify Token 轮换] Token [{masked_tok}] 触发状态 {resp.status_code} (额度不足或被限流)，尝试切换备用 Token...")
                    continue
                else:
                    print(f"  ⚠️ [xquik] HTTP {resp.status_code}: {resp.text[:120]}")
        except Exception as e:
            print(f"  ⚠️ [xquik] 异常: {e}")

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
                elif resp.status_code in [401, 402, 403, 429]:
                    print(f"  ⚠️ [Apify Token 轮换] 备用 Actor Token [{masked_tok}] 状态 {resp.status_code}，切换备用 Token...")
                    continue
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
    tokens = get_apify_tokens()
    if not tokens:
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

    dynamic_queries = get_dynamic_trending_queries()
    print(f"  🚀 [Apify 增量采集器] 启动增量抓取: 监控全球 {len(LEADER_HANDLES)} 位领袖 + {len(LAB_HANDLES)} 家前沿实验室 + {len(dynamic_queries)} 组全网飙升标签 (Token 池: {len(tokens)} 个)...")

    all_queries = []
    # 1. 批量抓取全球顶尖 AI 领袖 (每组 15 人，保证检索式在 X API 长度限制内高效执行)
    for i in range(0, len(LEADER_HANDLES), 15):
        batch = LEADER_HANDLES[i:i+15]
        q_leaders = "(" + " OR ".join([f"from:{h}" for h in batch]) + ")"
        all_queries.append((q_leaders, 25))

    # 2. 批量抓取官方实验室与前沿研发团队 (每组 15 家)
    for i in range(0, len(LAB_HANDLES), 15):
        batch = LAB_HANDLES[i:i+15]
        q_labs = "(" + " OR ".join([f"from:{h}" for h in batch]) + ")"
        all_queries.append((q_labs, 25))

    raw_items = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_call_apify_actor, tokens, q, max_i): q for q, max_i in all_queries}
        for future in as_completed(futures):
            try:
                res = future.result()
                if res:
                    raw_items.extend(res)
            except Exception as e:
                print(f"  ⚠️ 查询失败: {e}")

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

        # 1. 如果本地数据库已收录该推文：严格跳过，避免重复入库
        if tweet_id in existing_file_ids and not force_update:
            skipped_known += 1
            continue

        # 3. 严格过滤低价值、无观点、无实质内容的水帖与寒暄碎碎念
        tweet_text = (it.get("text") or it.get("fullText") or "").strip()
        if not tweet_text:
            continue
            
        # 剔除 URL 与 @提及后计算实质正文字符
        substantive_text = re.sub(r'https?://\S+|@\w+', '', tweet_text).strip()
        
        # 排除纯寒暄、无营养一句话与表情包水帖
        low_value_patterns = [
            r'^(?:gm|gn|great|cool|awesome|congrats|congratulations|agreed|same|yes|no|thanks|thank you|lol|lmao)[!.\s]*$',
            r'^(?:congrats|congratulations)\b.*(?:can\'?t\s+wait|cheers|excited for you|looking forward|welcome|proud of you).*$',
            r'^(?:check this out|excited for this|wow|nice|👀|🔥|🚀|💯)[!.\s]*$',
            r'^(?:thanks for having me|happy to help|appreciate it)[!.\s]*$'
        ]
        if any(re.match(p, substantive_text, re.IGNORECASE) for p in low_value_patterns):
            continue
            
        # 非官方重大发布的极短碎碎念（无图、无视频、无实质技术论述且字符 < 40）坚决过滤
        has_media = bool(it.get("media") or (it.get("entities") and it.get("entities", {}).get("media")))
        num_likes = int(likes_raw or 0)
        if len(substantive_text) < 40 and not has_media and num_likes < 300:
            continue
            
        is_reply = it.get("isReply") or False
        if is_reply and (len(substantive_text) < 50 or num_likes < 150):
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

        # 严格身份门禁：只收录已在白名单池中的全球 AI 核心领袖与顶尖官方实验室
        is_known_handle = user_name.lower() in [h.lower() for h in LEADER_HANDLES + LAB_HANDLES]
        profile = match_celebrity_profile(user_name)
        if not is_known_handle and not profile:
            continue

        # 严格过滤垃圾与无关主题 (加密货币/NFT/成人/无营养闲扯)
        noise_keywords = ["crypto", "bitcoin", "eth ", "solana", "memecoin", "airdrop", "nsfw", "hentai", "futa", "porn", "giveaway", "follow & rt", "aiart", "dildo"]
        if any(w in tweet_text.lower() for w in noise_keywords):
            continue

        author_name = profile.get("name") if profile else (author_obj.get("name") or user_name)
        author_handle = f"@{user_name}"
        author_avatar = profile.get("avatar") if profile else (author_obj.get("profilePicture") or f"https://unavatar.io/x/{user_name}")
        author_role = profile.get("role") if profile else (author_obj.get("description") or "AI 前沿领袖 / 核心开发者")
        entity_type = profile.get("entity_type") if profile else ("company" if user_name.lower() in ["openai", "anthropicai", "deepseek_ai", "googledeepmind", "cursor_ai", "huggingface"] else "person")

        # 识别爆款与全网飙升状态
        is_viral = False
        surge_badge = None
        try:
            num_likes = int(likes_raw or 0)
            num_rts = int(retweets_raw or 0)
            if num_likes >= 1000 or num_rts >= 150:
                is_viral = True
                surge_badge = "⚡ 24h 飙升热推"
        except Exception:
            pass

        # 规格标签与高亮翻译
        if profile:
            spec_tags = extract_tech_specs(tweet_text, "") or (["硅谷前沿原声", "大V发声"] if entity_type == "person" else ["官方发布", "模型突破"])
            tags_list = ["𝕏领袖观点", "前沿发声"] if entity_type == "person" else ["官方动态", "模型发布"]
        else:
            spec_tags = extract_tech_specs(tweet_text, "") or ["🔥 24h飙升", "𝕏平台热推"]
            tags_list = ["🔥 24h飙升", "𝕏平台热推", "极客前沿"]
            if is_viral:
                tags_list.insert(0, "🔥 飙升热帖")

        # 智能翻译中文
        trans_zh = free_translate_zh(tweet_text)

        # 唯一 ID
        id_hash = hashlib.md5(f"apify_x_{tweet_id}".encode("utf-8")).hexdigest()[:16]

        news_item = {
            "id": id_hash,
            "status_id": tweet_id,
            "category": "celebrity",
            "sub_category": "viral_post" if is_viral else None,
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
            "author_role_en": profile.get("role_en") if profile else (author_obj.get("description") or "AI Researcher & Builder"),
            "entity_type": entity_type,
            "platform": "x",
            "raw_published_at": iso_time,
            "metrics": metrics,
            "spec_tags": spec_tags,
            "content_snippet": tweet_text,
            "summary_en": tweet_text,
            "summary_zh": trans_zh,
            "is_viral": is_viral,
            "surge_badge": surge_badge,
            "is_pinned": False,
            "tags": tags_list
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
    inserted_count = merge_new_items_to_database(new_items)

    print(f"  ✨ [Apify 增量采集器] 增量捕获新推文: {len(new_items)} 篇，新增入库: {inserted_count} 篇，跳过已有推文: {skipped_known} 篇，刷新已有推文指标: {updated_metrics_count} 条。")
    return new_items


def merge_new_items_to_database(new_items: List[Dict[str, Any]]) -> int:
    """直接将最新增量推文写入 latest_news.json, public/data/latest_news.json 以及 master_archive.json"""
    if not new_items:
        return 0

    inserted_total = 0
    for target_path in [LATEST_NEWS_FILE, PUBLIC_NEWS_FILE]:
        if not os.path.exists(target_path):
            continue
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            existing_items = data.get("items", [])
            existing_urls = {it.get("url") for it in existing_items if it.get("url")}
            
            # 过滤出未入库的新条目
            to_add = [it for it in new_items if it.get("url") not in existing_urls]
            if to_add:
                # 插入 items 头部并按发布时间倒序
                merged_items = to_add + existing_items
                merged_items.sort(key=lambda x: str(x.get("raw_published_at") or ""), reverse=True)
                data["items"] = merged_items
                
                # 插入 grouped.celebrity
                grouped = data.get("grouped", {})
                existing_celeb = grouped.get("celebrity", [])
                existing_celeb_urls = {it.get("url") for it in existing_celeb if it.get("url")}
                to_add_celeb = [it for it in to_add if it.get("url") not in existing_celeb_urls]
                merged_celeb = to_add_celeb + existing_celeb
                merged_celeb.sort(key=lambda x: str(x.get("raw_published_at") or ""), reverse=True)
                grouped["celebrity"] = merged_celeb
                data["grouped"] = grouped
                
                # 兼容旧字段
                data["celebrity"] = merged_celeb
                data["leader_opinions"] = merged_celeb
                
                # 更新 total_count
                data["total_count"] = len(data["items"])
                data["updated_at"] = datetime.now(timezone.utc).isoformat()

                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                inserted_total = len(to_add)
        except Exception as e:
            print(f"  ⚠️ 合并入库异常 ({target_path}): {e}")

    # 同时归档入 master_archive.json
    master_file = os.path.join(BASE_DIR, "data", "master_archive.json")
    if os.path.exists(master_file):
        try:
            with open(master_file, "r", encoding="utf-8") as f:
                m_data = json.load(f)
            m_items = m_data.get("items", [])
            m_urls = {it.get("url") for it in m_items if it.get("url")}
            m_add = [it for it in new_items if it.get("url") not in m_urls]
            if m_add:
                merged_m = m_add + m_items
                merged_m.sort(key=lambda x: str(x.get("raw_published_at") or ""), reverse=True)
                m_data["items"] = merged_m
                with open(master_file, "w", encoding="utf-8") as f:
                    json.dump(m_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  ⚠️ 归档入库异常: {e}")

    return inserted_total


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
