"""
Processor module - Uses Google Gemini API to clean, translate, summarize and categorize AI news.
Includes automatic free translation fallback to guarantee Chinese translation out of the box.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import re
import json
from typing import List, Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# 翻译内存缓存，避免重复请求
_TRANSLATION_CACHE = {}


def free_translate_zh(text: str) -> str:
    """Free, no-auth translation fallback to ensure Chinese content is always available."""
    if not text:
        return ""
    # 如果已经包含较多中文，直接返回
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    if zh_chars > len(text) * 0.3:
        return text

    clean_text = text.strip()[:200]
    if clean_text in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[clean_text]

    try:
        url = "https://api.mymemory.translated.net/get"
        params = {"q": clean_text, "langpair": "en|zh"}
        with httpx.Client(timeout=6) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                translated = data.get("responseData", {}).get("translatedText", "")
                if translated and "MYMEMORY WARNING" not in translated:
                    _TRANSLATION_CACHE[clean_text] = translated
                    return translated
    except Exception:
        pass
    return text


def get_gemini_client():
    """Initialize Google GenAI client if key is configured."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[Warning] Failed to initialize Gemini client: {e}")
        return None


def generate_smart_fallback_summary(item: Dict[str, Any], title_zh: str) -> str:
    """Generate a clean Chinese takeaway when Gemini is offline."""
    source = item.get("source", "")
    category = item.get("category") or item.get("default_category", "news")
    snippet = item.get("content_snippet", "")
    
    if category == "celebrity":
        return f"聚焦行业领袖最新发声与公开动态。{free_translate_zh(snippet[:70])}"
    elif category == "tools":
        return f"落地实用新工具，推荐关注尝试。{free_translate_zh(snippet[:70])}"
    elif category == "videos":
        if item.get("is_prompt"):
            return f"即抄即用的高阶实战提示词神咒：{snippet[:80]}"
        return f"YouTube 爆款 AI 实操演示精讲：{free_translate_zh(snippet[:70])}"
    else:
        return f"来自 {source} 的行业前沿报道：{free_translate_zh(snippet[:70])}"


def process_items_batch(items: List[Dict[str, Any]], batch_size: int = 8) -> List[Dict[str, Any]]:
    """
    Process a list of items with Gemini in batches to maximize throughput.
    Falls back to automated translation if Gemini is not configured.
    """
    client = get_gemini_client()

    if not client:
        print("💡 未检测到 GEMINI_API_KEY，启用内置全自动智能中文翻译器...")
        processed = []
        for item in items:
            p_item = dict(item)
            cat = item.get("category") or item.get("default_category", "news")
            p_item["category"] = cat
            title_zh = free_translate_zh(item["title"])
            p_item["title_zh"] = title_zh
            p_item["summary_zh"] = generate_smart_fallback_summary(item, title_zh)
            p_item["hot_score"] = 4 if cat in ["celebrity", "videos"] else 3
            p_item["tags"] = item.get("tags") or [item["source"]]
            processed.append(p_item)
        print("  ✓ 中文自动化翻译与看点生成完毕！")
        return processed

    print(f"🤖 正在调用 Google Gemini 进行批量智能翻译、提炼与分类...")

    results = []
    models_to_try = [MODEL_NAME, "gemini-2.0-flash", "gemini-1.5-flash"]

    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        simplified_chunk = [
            {
                "index": idx,
                "title": it["title"],
                "source": it["source"],
                "content": it["content_snippet"][:300],
                "suggested_category": it["default_category"]
            }
            for idx, it in enumerate(chunk)
        ]

        prompt = f"""
你是一个顶级 AI 资讯雷达站的资深主编。请对以下最新 AI 资讯进行精炼分析、纯正中文翻译和价值提炼。

【分类规则】：
- "news": 行业大事件、技术突破、官方重磅发布
- "celebrity": 马斯克、奥特曼、LeCun、Karpathy、Tibo、黄仁勋等名人大V言论或专访
- "tools": 新开源工具、GitHub高星项目、实用AI新模型/新框架
- "insights": 极客实操、本地部署避坑、Prompt技巧、深度论文研究

【输出要求】：
请以纯 JSON Array 形式输出（不要带有 ```json 标记），数组内每个元素格式如下：
{{
  "index": 对应的序号,
  "title_zh": "自然流畅精炼的中文标题(25字以内)",
  "summary_zh": "一句话核心看点或实际价值(30-50字，讲清楚为什么值得看或怎么用)",
  "category": "news | celebrity | tools | insights",
  "hot_score": 1到5的整数热度评分,
  "tags": ["标签1", "标签2"]
}}

待处理资讯：
{json.dumps(simplified_chunk, ensure_ascii=False, indent=2)}
"""

        try:
            response = None
            last_err = None
            for m in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    if response and response.text:
                        break
                except Exception as m_err:
                    last_err = m_err
                    continue

            if not response or not response.text:
                raise last_err or Exception("All Gemini models failed")

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed_chunk = json.loads(raw_text.strip())
            parsed_dict = {entry["index"]: entry for entry in parsed_chunk}

            for idx, orig_item in enumerate(chunk):
                ai_data = parsed_dict.get(idx, {})
                merged = dict(orig_item)
                merged["title_zh"] = ai_data.get("title_zh") or free_translate_zh(orig_item["title"])
                merged["summary_zh"] = ai_data.get("summary_zh") or orig_item["content_snippet"]
                merged["category"] = ai_data.get("category") or orig_item["default_category"]
                merged["hot_score"] = ai_data.get("hot_score", 3)
                merged["tags"] = ai_data.get("tags", [orig_item["source"]])
                results.append(merged)

            print(f"  ✓ 已完成 {min(i + batch_size, len(items))}/{len(items)} 条")

        except Exception as e:
            print(f"  ❌ Gemini 处理异常: {e}，启用智能中文备用翻译")
            for orig_item in chunk:
                fallback = dict(orig_item)
                title_zh = free_translate_zh(orig_item["title"])
                fallback["title_zh"] = title_zh
                fallback["summary_zh"] = generate_smart_fallback_summary(orig_item, title_zh)
                fallback["category"] = orig_item["default_category"]
                fallback["hot_score"] = 3
                fallback["tags"] = [orig_item["source"]]
                results.append(fallback)

    return results
