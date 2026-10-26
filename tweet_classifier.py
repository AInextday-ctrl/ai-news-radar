#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Radar 2.0 - High-Precision Tweet Semantic Classifier
=========================================================
Classifies AI celebrity and viral tweets into 6 core value categories:
1. tech_frontier:    🔬 前沿技术与突破 (Frontier Tech & Research)
2. practical_skills: 💡 AI实战技巧/咒语 (Practical Skills & Tutorials)
3. workplace_ai:     ⚡ 职场提效/岗位替代 (Workplace AI & Automation)
4. business_cases:   💼 商业经济落地案例 (Business Cases & Enterprise ROI)
5. promos_benefits:  🎁 算力福利/活动优惠 (Promos, Grants & Free Credits)
6. industry_news:    📰 业界动态/巨头格局 (Industry News & Dynamics)

Combines fast deterministic rules with Gemini 3.5 Flash-Lite structured output,
with persistent disk caching in data/tweet_tags_cache.json.
"""

import os
import sys
import json
import re
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "data", "tweet_tags_cache.json")

TAG_CONFIG = {
    "tech_frontier": {
        "id": "tech_frontier",
        "icon": "🔬",
        "label_zh": "前沿技术",
        "label_en": "Frontier Tech",
        "pill_zh": "🔬 前沿技术",
        "pill_en": "🔬 Frontier Tech",
        "color": "cyan",
        "badge_dark": "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
        "badge_light": "bg-cyan-50 text-cyan-700 border-cyan-200"
    },
    "practical_skills": {
        "id": "practical_skills",
        "icon": "💡",
        "label_zh": "实战技巧",
        "label_en": "Practical Skills",
        "pill_zh": "💡 实战技巧",
        "pill_en": "💡 Practical Skills",
        "color": "indigo",
        "badge_dark": "bg-indigo-500/15 text-indigo-300 border-indigo-500/30",
        "badge_light": "bg-indigo-50 text-indigo-700 border-indigo-200"
    },
    "workplace_ai": {
        "id": "workplace_ai",
        "icon": "⚡",
        "label_zh": "职场提效",
        "label_en": "Workplace AI",
        "pill_zh": "⚡ 职场提效",
        "pill_en": "⚡ Workplace AI",
        "color": "amber",
        "badge_dark": "bg-amber-500/15 text-amber-300 border-amber-500/30",
        "badge_light": "bg-amber-50 text-amber-800 border-amber-200"
    },
    "business_cases": {
        "id": "business_cases",
        "icon": "💼",
        "label_zh": "商业落地",
        "label_en": "Business Cases",
        "pill_zh": "💼 商业落地",
        "pill_en": "💼 Business Cases",
        "color": "emerald",
        "badge_dark": "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
        "badge_light": "bg-emerald-50 text-emerald-700 border-emerald-200"
    },
    "promos_benefits": {
        "id": "promos_benefits",
        "icon": "🎁",
        "label_zh": "算力福利",
        "label_en": "Promos & Credits",
        "pill_zh": "🎁 算力福利",
        "pill_en": "🎁 Promos & Credits",
        "color": "rose",
        "badge_dark": "bg-rose-500/15 text-rose-300 border-rose-500/30",
        "badge_light": "bg-rose-50 text-rose-700 border-rose-200"
    },
    "industry_news": {
        "id": "industry_news",
        "icon": "📰",
        "label_zh": "业界动态",
        "label_en": "Industry News",
        "pill_zh": "📰 业界动态",
        "pill_en": "📰 Industry News",
        "color": "sky",
        "badge_dark": "bg-sky-500/15 text-sky-300 border-sky-500/30",
        "badge_light": "bg-sky-50 text-sky-700 border-sky-200"
    }
}

VALID_TAGS = set(TAG_CONFIG.keys())

_TAGS_CACHE: Dict[str, Dict[str, Any]] = {}

def load_tags_cache() -> Dict[str, Dict[str, Any]]:
    global _TAGS_CACHE
    if _TAGS_CACHE:
        return _TAGS_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _TAGS_CACHE = json.load(f)
        except Exception as e:
            print(f"[tweet_classifier] Failed to load cache: {e}")
            _TAGS_CACHE = {}
    return _TAGS_CACHE

def save_tags_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_TAGS_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[tweet_classifier] Failed to save cache: {e}")

def detect_code_or_prompt(text_en: str, text_zh: str) -> bool:
    combined = f"{text_en} {text_zh}"
    if "```" in combined:
        return True
    if re.search(r'(?:^|\n)\s*(?:curl|pip install|git clone|npm install|npx|claude code|ollama run|docker run)\b', combined, re.I):
        return True
    if re.search(r'(?:paste this into|system prompt:|prompt:|act as a|try this prompt)\b', combined, re.I):
        return True
    return False

def rule_based_classify(text_en: str, text_zh: str, author_handle: str) -> str:
    combined = f"{author_handle} {text_en} {text_zh}".lower()
    
    # 1. Promos, Credits, Reset, Discounts
    if any(k in combined for k in [
        "reset", "rest and reset", "quota", "usage limit", "free credit", "free tier",
        "grant", "hackathon", "$150k grant", "discount", "coupon", "promo code", "giveaway",
        "算力", "重置", "配额", "免费额度", "优惠", "奖金", "限免", "折扣"
    ]):
        return "promos_benefits"
        
    # 2. Practical Skills & Tutorials
    if any(k in combined for k in [
        "prompt", "try this:", "how to", "tutorial", "step 1", "step 2", "bonus - learn",
        "system prompt", "cursor rule", "claude code", "vibe coding", "tips", "tricks",
        "workflow", "cheat sheet", "guide", "learn excel", "learn sql", "learn python",
        "提示词", "实战", "教程", "秘籍", "技巧", "怎么用", "指令", "心法", "指南"
    ]):
        return "practical_skills"
        
    # 3. Workplace AI & Task Replacement
    if any(k in combined for k in [
        "taking peoples jobs", "replace", "job loss", "automate", "productivity", "save hours",
        "office", "workplace", "layoffs", "harness", "doing work for", "agent buy", "buy something for me",
        "替代", "工作", "打工人", "职场", "失业", "提效", "自动化", "外包", "效率"
    ]):
        return "workplace_ai"
        
    # 4. Business Cases & ROI
    if any(k in combined for k in [
        "profit alert", "revenue", "roi", "arr", "enterprise", "market", "valuation", "fundraising",
        "billion", "million", "acquisition", "commercial", "pricing", "$/hr", "monetization",
        "利润", "营收", "商业", "企业落地", "变现", "估值", "出海", "市值", "投资"
    ]):
        return "business_cases"
        
    # 5. Tech Frontier & Research
    if any(k in combined for k in [
        "paper", "architecture", "benchmark", "weights", "parameters", "context window",
        "kv cache", "inference", "deepseek", "vllm", "sglang", "moe", "reasoning",
        "tokens/s", "gpu", "cuda", "transformer", "diffusion", "loss", "pre-training",
        "论文", "模型发布", "跑分", "基准", "架构", "参数", "推理", "权重", "前沿"
    ]):
        return "tech_frontier"
        
    # 6. Default to Industry News
    return "industry_news"

def enrich_tweet_with_tag(tweet: Dict[str, Any], tag: str, has_code: bool) -> Dict[str, Any]:
    if tag not in TAG_CONFIG:
        tag = "industry_news"
    cfg = TAG_CONFIG[tag]
    tweet["primary_tag"] = tag
    tweet["primary_tag_zh"] = cfg["pill_zh"]
    tweet["primary_tag_en"] = cfg["pill_en"]
    tweet["primary_tag_color"] = cfg["color"]
    tweet["has_code_or_prompt"] = has_code
    return tweet

def classify_tweets_batch(items: List[Dict[str, Any]], use_gemini: bool = True) -> List[Dict[str, Any]]:
    """
    Classify a batch of tweets with persistent caching and optional Gemini API refinement.
    """
    cache = load_tags_cache()
    to_gemini = []

    for it in items:
        # Check if already tagged
        tid = it.get("id") or it.get("url")
        if not tid:
            continue
            
        f_en = str(it.get("full_text_en") or it.get("title_en") or it.get("title") or "").strip()
        f_zh = str(it.get("full_text_zh") or it.get("title_zh") or "").strip()
        author = str(it.get("author_handle") or "").strip()
        has_code = detect_code_or_prompt(f_en, f_zh)

        if tid in cache and cache[tid].get("primary_tag") in VALID_TAGS:
            enrich_tweet_with_tag(it, cache[tid]["primary_tag"], has_code)
            continue

        # Fast deterministic classification
        rule_tag = rule_based_classify(f_en, f_zh, author)
        
        # If it's a very clear tag (promos, skills, workplace), save immediately
        if rule_tag in ("promos_benefits", "practical_skills", "workplace_ai"):
            cache[tid] = {"primary_tag": rule_tag, "has_code": has_code}
            enrich_tweet_with_tag(it, rule_tag, has_code)
        else:
            # Candidate for Gemini verification or default rule
            cache[tid] = {"primary_tag": rule_tag, "has_code": has_code}
            enrich_tweet_with_tag(it, rule_tag, has_code)
            if use_gemini:
                to_gemini.append((tid, author, f_en, f_zh, has_code, it))

    # Save cache
    save_tags_cache()

    # Optional Gemini batch refinement for ambiguous/news items
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if use_gemini and api_key and to_gemini:
        try:
            from google import genai
            from google.genai import types
            from pydantic import BaseModel, Field
            from typing import Literal

            class TweetClassification(BaseModel):
                id: str
                primary_tag: Literal[
                    "tech_frontier",
                    "practical_skills",
                    "workplace_ai",
                    "business_cases",
                    "promos_benefits",
                    "industry_news"
                ]

            class BatchClassificationResponse(BaseModel):
                results: List[TweetClassification]

            client = genai.Client(api_key=api_key)

            # Process in chunks of 15
            chunk_size = 15
            for i in range(0, min(len(to_gemini), 45), chunk_size):
                chunk = to_gemini[i:i + chunk_size]
                prompt_input = [
                    {"id": item[0], "author": item[1], "text": (item[2] or item[3])[:300]}
                    for item in chunk
                ]
                
                resp = client.models.generate_content(
                    model="gemini-3.5-flash-lite",
                    contents=(
                        "You are a premier AI tech editor. Classify each tweet into exactly one category:\n"
                        "- tech_frontier: Research papers, model architectures, benchmark runs, weights release, context window innovations.\n"
                        "- practical_skills: Specific AI tool guides, Claude Code / Cursor tricks, prompts, tutorials, developer workflows.\n"
                        "- workplace_ai: Automating jobs, replacing repetitive workplace tasks, AI productivity impact, agent task execution.\n"
                        "- business_cases: Commercial revenue, company deployment ROI, profit margins, monetization, enterprise AI.\n"
                        "- promos_benefits: Free quotas, reset credits, grants, hackathon prizes, discount coupons, giveaways.\n"
                        "- industry_news: Executive moves, ecosystem drama, general tech commentary, partnerships, regulations.\n\n"
                        f"Tweets:\n{json.dumps(prompt_input, ensure_ascii=False)}"
                    ),
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=BatchClassificationResponse,
                        temperature=0.1
                    )
                )

                if resp.text:
                    parsed = json.loads(resp.text)
                    for r in parsed.get("results", []):
                        cid = r.get("id")
                        c_tag = r.get("primary_tag")
                        if c_tag in VALID_TAGS:
                            cache[cid] = {"primary_tag": c_tag, "has_code": cache.get(cid, {}).get("has_code", False)}
                            # Update target item
                            for item in chunk:
                                if item[0] == cid:
                                    enrich_tweet_with_tag(item[5], c_tag, item[4])

            save_tags_cache()
        except Exception as e:
            print(f"[tweet_classifier] Gemini refinement skipped/error: {e}")

    return items

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    from dotenv import load_dotenv
    load_dotenv()
    test_items = [
        {"id": "1", "author_handle": "@thsottiaux", "full_text_en": "Day 21/ But today is a reset. Quotas refreshed!"},
        {"id": "2", "author_handle": "@karpathy", "full_text_en": "Here is a prompt trick for Claude Code that saves 50% tokens."},
        {"id": "3", "author_handle": "@sama", "full_text_en": "OpenAI reports $10B run-rate from enterprise deployments."}
    ]
    res = classify_tweets_batch(test_items, use_gemini=True)
    for r in res:
        print(r["id"], r["author_handle"], "->", r["primary_tag_zh"])
