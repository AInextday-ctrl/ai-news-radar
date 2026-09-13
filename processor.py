"""
Processor module - Uses Google Gemini API to clean, translate, summarize and categorize AI news.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os

import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


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


def process_items_batch(items: List[Dict[str, Any]], batch_size: int = 8) -> List[Dict[str, Any]]:
    """
    Process a list of items with Gemini in batches to maximize throughput and minimize quota usage.
    """
    client = get_gemini_client()

    if not client:
        print("⚠️ 未检测到 GEMINI_API_KEY，将使用原始数据直出模式（可在 .env 中填入 API Key 开启 AI 深度提炼）。")
        # 降级处理：保留原样，简单填充中文缺省
        processed = []
        for item in items:
            p_item = dict(item)
            p_item["title_zh"] = item["title"]
            p_item["summary_zh"] = item["content_snippet"] or "暂无AI总结"
            p_item["category"] = item["default_category"]
            p_item["hot_score"] = 3
            p_item["tags"] = [item["source"]]
            processed.append(p_item)
        return processed

    print(f"🤖 正在调用 Google Gemini ({MODEL_NAME}) 进行批量智能翻译、提炼与分类...")

    results = []
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
你是一个顶级 AI 资讯雷达站的资深编辑。请对以下这批最新 AI 资讯进行分析、翻译和价值提炼。

【分类规则】：
- "news": 突发行业大事件、新突破、大厂官方发布
- "celebrity": 马斯克、奥特曼、LeCun、Karpathy、Tibo 等名人博文或观点
- "tools": 新开源工具、GitHub高赞项目、实用AI插件或新模型
- "insights": 使用心得、深度长视频、Prompt技巧、最佳实操经验

【输出格式要求】：
请以纯 JSON Array 形式输出（不要带有 ```json 代码块外围文字），数组内每个元素格式如下：
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
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            raw_text = response.text.strip()
            # 去除可能的 markdown 标记
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
                merged["title_zh"] = ai_data.get("title_zh") or orig_item["title"]
                merged["summary_zh"] = ai_data.get("summary_zh") or orig_item["content_snippet"]
                merged["category"] = ai_data.get("category") or orig_item["default_category"]
                merged["hot_score"] = ai_data.get("hot_score", 3)
                merged["tags"] = ai_data.get("tags", [orig_item["source"]])
                results.append(merged)

            print(f"  ✓ 已完成 {min(i + batch_size, len(items))}/{len(items)} 条")

        except Exception as e:
            print(f"  ❌ Gemini 批量处理异常: {e}，回退使用原始数据")
            for orig_item in chunk:
                fallback = dict(orig_item)
                fallback["title_zh"] = orig_item["title"]
                fallback["summary_zh"] = orig_item["content_snippet"]
                fallback["category"] = orig_item["default_category"]
                fallback["hot_score"] = 3
                fallback["tags"] = [orig_item["source"]]
                results.append(fallback)

    return results
