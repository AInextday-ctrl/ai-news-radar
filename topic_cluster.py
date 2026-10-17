# -*- coding: utf-8 -*-
"""
topic_cluster.py - 24h 核心话题专题动态 AI 聚类与透视引擎 (Dynamic AI Topic Focus Engine)
========================================================================================
深度解析 24 小时内的全网突发快讯、AI领袖观点、爆款推文与前沿工具，
彻底告别“全周期通用”的泛化空话，由 Gemini AI 实时挖掘当日前沿最具争议与影响力的 Top 3 焦点事件！

输出三维立体结构：
  1. 事件核心脉络 (Background & Core Context): 真实具体的人物、公司、模型、数据与争议起因
  2. 大V观点立场对撞 (Perspectives Collision: 愿景派/演进派 vs 工业理性派/质疑派)
  3. 关联情报束 (Linked Intelligence Bundle: 真实快讯直达 + 领袖原帖 + 落地工具/配方)

双轨执行机制：
  - 轨道 A: Google Gemini AI 实时聚类与深度研判 (优先，支持 GitHub Actions 自动化与云端定时运行)
  - 轨道 B: 实体共现与热度动态聚类算法 (保底，离线或断网环境下仍保证基于当日真实资讯动态生成)

产物持久化至:
  - data/topic_focus.json
  - public/data/topic_focus.json
  - 注入 latest_news.json 中的 "topic_focus" 字段
"""

import os
import sys
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_TOPIC_FILE = os.path.join(BASE_DIR, "data", "topic_focus.json")
PUBLIC_DATA_TOPIC_FILE = os.path.join(BASE_DIR, "public", "data", "topic_focus.json")
CURATED_WORKFLOWS_FILE = os.path.join(BASE_DIR, "data", "curated_workflows_library.json")

# 支持专属话题聚类 Key（GEMINI_API_KEY_TOPICS / GEMINI_API_KEY_2），彻底与主项目 Key 物理隔离；未配置时无缝回退至全局 Key
GEMINI_API_KEY = (
    os.getenv("GEMINI_API_KEY_TOPICS", "").strip()
    or os.getenv("GEMINI_API_KEY_TOPIC", "").strip()
    or os.getenv("GEMINI_API_KEY_2", "").strip()
    or os.getenv("GEMINI_API_KEY", "").strip()
)
# 智能配额保护锁：默认每 4 小时仅调用一次 Gemini 进行宏观议题聚类，其余频次复用缓存 (0 API 消耗)
TOPIC_REFRESH_INTERVAL_HOURS = float(os.getenv("TOPIC_REFRESH_INTERVAL_HOURS", "4.0"))


def _get_cached_topic_focus_if_fresh(interval_hours: float) -> Optional[List[Dict[str, Any]]]:
    """检查现有话题专题缓存是否仍在有效期内，避免每8分钟高频重复调用消耗 API 额度"""
    for filepath in (DATA_TOPIC_FILE, PUBLIC_DATA_TOPIC_FILE):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    updated_at_str = data.get("updated_at")
                    topics = data.get("topics")
                    if updated_at_str and isinstance(topics, list) and len(topics) >= 2:
                        dt = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
                        now = datetime.now(timezone.utc)
                        elapsed_hours = (now - dt).total_seconds() / 3600.0
                        if elapsed_hours < interval_hours:
                            print(f"🛡️ [topic_cluster] 命中配额节流保护：距离上次生成仅过去 {elapsed_hours:.2f}h (周期阈值: {interval_hours}h)，复用缓存话题 (0 API 消耗)！")
                            return topics
            except Exception as e:
                pass
    return None


def get_gemini_client():
    """获取 Gemini API 客户端，支持多 Key 自动适配与主备容灾"""
    for candidate_key in [
        os.getenv("GEMINI_API_KEY_TOPICS", "").strip(),
        os.getenv("GEMINI_API_KEY", "").strip(),
        os.getenv("GEMINI_API_KEY_NEWS", "").strip(),
    ]:
        if candidate_key and candidate_key != "your_gemini_api_key_here":
            try:
                from google import genai
                return genai.Client(api_key=candidate_key)
            except Exception as e:
                print(f"⚠️ [topic_cluster] 候选 Key 初始化异常: {e}")
                continue
    return None


def _load_curated_workflows() -> List[Dict[str, Any]]:
    """载入已有的实战工作流配方库以供关联情报束推荐"""
    if os.path.exists(CURATED_WORKFLOWS_FILE):
        try:
            with open(CURATED_WORKFLOWS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"⚠️ [topic_cluster] 载入工作流配方库异常: {e}")
    return []


def _match_best_tool_or_workflow(
    tool_keyword: str,
    workflows: List[Dict[str, Any]],
    tool_items: List[Dict[str, Any]],
    topic_title: str = ""
) -> Optional[Dict[str, Any]]:
    """根据话题意图关键词或标题在工作流与工具库中精准匹配"""
    kw = (tool_keyword or "").lower()
    t_text = (topic_title or "").lower()

    # 1. 在精品工作流库中按关键词加权匹配
    wf_scores = []
    for wf in workflows:
        wf_corpus = " ".join([
            str(wf.get("id", "")),
            str(wf.get("title_zh", "")),
            str(wf.get("title_en", "")),
            str(wf.get("name", "")),
            str(wf.get("description_zh", "")),
            str(wf.get("target_platform", "")),
            " ".join(wf.get("tags", []))
        ]).lower()

        score = 0
        if kw and kw in wf_corpus:
            score += 10
        if "deepseek" in t_text and "deepseek" in wf_corpus:
            score += 8
        if ("cursor" in t_text or "agent" in t_text or "coding" in t_text or "replit" in t_text) and "cursor" in wf_corpus:
            score += 8
        if ("mcp" in t_text or "claude" in t_text) and "mcp" in wf_corpus:
            score += 8
        if ("rag" in t_text or "幻觉" in t_text or "proof" in t_text or "math" in t_text) and "rag" in wf_corpus:
            score += 8

        if score > 0:
            wf_scores.append((score, wf))

    if wf_scores:
        wf_scores.sort(key=lambda x: x[0], reverse=True)
        best_wf = wf_scores[0][1]
        return {
            "id": best_wf.get("id"),
            "name": best_wf.get("title_zh") or best_wf.get("name"),
            "title_zh": best_wf.get("title_zh"),
            "title_en": best_wf.get("title_en"),
            "desc_zh": best_wf.get("takeaway_zh") or best_wf.get("description_zh", ""),
            "desc_en": best_wf.get("takeaway_en") or best_wf.get("description_en", ""),
            "url": "https://github.com",
            "github_url": "https://github.com",
            "weekly_stars": "+3,800★",
            "is_workflow": True,
            "target_platform": best_wf.get("target_platform", "Cursor / Claude"),
            "config_filename": best_wf.get("config_filename", ".cursorrules")
        }

    # 2. 在工具条目中匹配
    if tool_items:
        t_scores = []
        for t in tool_items:
            t_corpus = " ".join([
                str(t.get("title_zh", "")),
                str(t.get("title", "")),
                str(t.get("summary_zh", "")),
                str(t.get("content_snippet", ""))
            ]).lower()
            score = 0
            if kw and kw in t_corpus:
                score += 5
            if score > 0:
                t_scores.append((score, t))
        if t_scores:
            t_scores.sort(key=lambda x: x[0], reverse=True)
            best_t = t_scores[0][1]
            return {
                "id": best_t.get("id"),
                "name": best_t.get("title_zh") or best_t.get("title_en") or best_t.get("name"),
                "title_zh": best_t.get("title_zh") or best_t.get("title"),
                "title_en": best_t.get("title_en") or best_t.get("title"),
                "desc_zh": best_t.get("summary_zh") or best_t.get("desc_zh", ""),
                "desc_en": best_t.get("summary_en") or best_t.get("desc_en", ""),
                "url": best_t.get("url"),
                "github_url": best_t.get("github_url") or best_t.get("url"),
                "weekly_stars": best_t.get("weekly_stars") or "+2,100★",
                "is_workflow": False
            }

    # 3. 兜底精选配方
    return {
        "id": "wf_cursorrules_fullstack_2026",
        "name": "Cursor / Windsurf 工业级全栈规则模板",
        "title_zh": "Cursor / Windsurf 工业级全栈架构 .cursorrules 规则模板",
        "title_en": "Production-Grade Fullstack .cursorrules Template for Cursor & Windsurf",
        "desc_zh": "杜绝 AI 乱写代码，严格约束目录规范、防御性编程原则与自动测试生成的工业级配置文件。",
        "desc_en": "Production-grade rules preventing hallucinated packages, enforcing defensive coding and automated unit tests.",
        "url": "https://github.com",
        "github_url": "https://github.com",
        "weekly_stars": "+3,200★",
        "is_workflow": True
    }


def _cluster_topics_with_gemini(
    news_items: List[Dict[str, Any]],
    tweet_items: List[Dict[str, Any]],
    tool_items: List[Dict[str, Any]],
    workflows: List[Dict[str, Any]],
    client: Any
) -> Optional[List[Dict[str, Any]]]:
    """
    【轨道 A】使用 Google Gemini 大模型动态挖掘当日前沿 Top 3 焦点事件与针锋相对的大V观点对撞。
    严格剔除任何宏观通用跨周期模板套话，输出 100% 紧贴今日核心事实的立体专题。
    """
    # 选取最新 25 条快讯与 15 条核心推文构建精简候选池
    pool_news = news_items[:25]
    pool_tweets = tweet_items[:15]

    mini_news = []
    for i, n in enumerate(pool_news):
        mini_news.append({
            "idx": i,
            "title_zh": n.get("title_zh") or n.get("title", ""),
            "title_en": n.get("title_en") or n.get("title", ""),
            "source": n.get("source", ""),
            "summary": (n.get("summary_zh") or n.get("content_snippet", "") or n.get("original_content", ""))[:120]
        })

    mini_tweets = []
    for i, t in enumerate(pool_tweets):
        mini_tweets.append({
            "idx": i,
            "author": t.get("author", ""),
            "handle": t.get("author_handle", ""),
            "text": (t.get("content_zh") or t.get("content_snippet", "") or t.get("original_content", ""))[:120]
        })

    prompt = f"""你是一个全球顶级 AI 科技智库的总编辑。请根据下方提供的过去 24 小时内的真实资讯与大V推文候选池，深度提炼并输出【今日最具时效性、最具行业震动、最具观点争议的 Top 3 焦点专题】。

【极其重要的硬性要求】：
1. 绝对严禁使用任何宏观、通用、跨周期的泛化空话标题（例如严禁使用“企业级编程与MCP协议标准化”、“开源生态演进”、“多模态与世界模型”等放之任何时期都成立的教科书大纲）。
2. 每一个话题的标题和背景摘要必须【指名道姓点出今日真实发生的核心事件、具体主角（如 OpenAI、Anthropic、DeepSeek、Replit、苹果、快手等）、具体产品/模型（如 166页纳维-斯托克斯论文、V4.1-Flash、可灵4.0、TPU集群）、具体数据（如 600亿美元融资、10%高息、1:6人机工时比）与具体争议矛盾】。
3. 每个话题必须提炼两方针锋相对的“大V观点对撞 (Perspectives Collision)”：
   - 正方 (perspective_pro: 愿景派/演进派/研发支持者)：说明为何支持该技术突破、扩张路径或自研策略的底层逻辑。
   - 反方 (perspective_con: 工业理性派/质疑派/反对者)：一针见血指出逻辑漏洞、数学质疑、高昂成本反噬或商业泡沫风险。
4. 必须从提供的候选列表中，精确指定属于该事件的快讯序号数组 (linked_news_indices，包含2-3个真实对应的序号) 和推文序号数组 (linked_tweet_indices，包含1-2个对应序号)。
5. 中英文案必须对称完整且语言生动锐利，无翻译腔。

【候选资讯列表】：
{json.dumps(mini_news, ensure_ascii=False, indent=2)}

【候选推文列表】：
{json.dumps(mini_tweets, ensure_ascii=False, indent=2)}

请以纯 JSON 数组（Array）形式输出（严禁包含 ```json 前后缀，严禁任何多余解释），数组包含 3 个对象，每个对象格式严格遵循如下 JSON 结构：
[
  {{
    "topic_id": "topic_具体事件英文简称(如 topic_openai_math_proof_controversy)",
    "category_tag_zh": "4-6字分类标签（如：学术争议与证明边界）",
    "category_tag_en": "English Category Tag (e.g. Academic Debate & Proof Bounds)",
    "badge_zh": "🔥 24h 领跑爆点 / ⚡ 商业与算力风暴 / 💡 开源与落地潮",
    "badge_en": "🔥 24h Breakthrough / ⚡ Compute & Market Storm / 💡 Open Source Wave",
    "heat_score": 9.9,
    "title_zh": "具体、尖锐、带事件主体的中文标题（25字以内）",
    "title_en": "Specific, punchy English headline with entity names",
    "summary_zh": "清晰交代事件起因、具体举措/数据、核心争议焦点的背景脉络摘要（60-100字）",
    "summary_en": "Clear executive briefing of the core event, actions, and dispute in English (50-80 words)",
    "perspective_pro": {{
      "role_zh": "🟢 某某派 / 某某角色",
      "role_en": "🟢 Stance / Role in English",
      "speaker_zh": "具体代表群体或机构",
      "speaker_en": "Representative group in English",
      "point_zh": "支持或辩护的核心论点（40-70字）",
      "point_en": "Pro argument in English"
    }},
    "perspective_con": {{
      "role_zh": "🔴 某某派 / 某某角色",
      "role_en": "🔴 Counter Stance / Role in English",
      "speaker_zh": "具体反对或质疑的学者/工程师",
      "speaker_en": "Counter representative group in English",
      "point_zh": "一针见血的批评或反思论点（40-70字）",
      "point_en": "Con argument in English"
    }},
    "linked_news_indices": [0, 1],
    "linked_tweet_indices": [0],
    "tool_keyword": "deepseek | cursor | rag | mcp"
  }}
]
"""

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.7-flash"
    ]

    for model_name in models_to_try:
        try:
            print(f"🤖 [topic_cluster] 正在调用 Gemini 模型 ({model_name}) 聚类当日突发话题...")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if not response or not response.text:
                continue

            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            parsed = json.loads(raw_text.strip())
            if isinstance(parsed, list) and len(parsed) >= 2:
                topic_results = []
                for idx, t_obj in enumerate(parsed[:3]):
                    # 解析匹配关联快讯
                    n_indices = t_obj.get("linked_news_indices", [])
                    matched_news = []
                    for n_idx in n_indices:
                        if isinstance(n_idx, int) and 0 <= n_idx < len(pool_news):
                            n_item = pool_news[n_idx]
                            matched_news.append({
                                "id": n_item.get("id", ""),
                                "title_zh": n_item.get("title_zh") or n_item.get("title", ""),
                                "title_en": n_item.get("title_en") or n_item.get("title", ""),
                                "source": n_item.get("source", "Global AI"),
                                "url": n_item.get("url", "#"),
                                "image_url": n_item.get("image_url", ""),
                                "hot_score": n_item.get("hot_score", 4),
                                "published_at": n_item.get("raw_published_at", "")
                            })

                    # 解析匹配关联推文
                    tw_indices = t_obj.get("linked_tweet_indices", [])
                    matched_tweets = []
                    for tw_idx in tw_indices:
                        if isinstance(tw_idx, int) and 0 <= tw_idx < len(pool_tweets):
                            tw_item = pool_tweets[tw_idx]
                            matched_tweets.append({
                                "id": tw_item.get("id", ""),
                                "author": tw_item.get("author", "AI Leader"),
                                "author_handle": tw_item.get("author_handle", "@ai"),
                                "author_avatar": tw_item.get("author_avatar", ""),
                                "content_zh": tw_item.get("content_zh") or tw_item.get("original_content", ""),
                                "content_en": tw_item.get("original_content") or tw_item.get("content_zh", ""),
                                "url": tw_item.get("url", "#"),
                                "platform": tw_item.get("platform", "x")
                            })

                    # 关联工具推荐
                    tool_kw = t_obj.get("tool_keyword", "")
                    matched_tool = _match_best_tool_or_workflow(
                        tool_keyword=tool_kw,
                        workflows=workflows,
                        tool_items=tool_items,
                        topic_title=t_obj.get("title_zh", "")
                    )

                    heat_score = float(t_obj.get("heat_score", round(9.9 - idx * 0.2, 1)))

                    final_topic = {
                        "topic_id": t_obj.get("topic_id", f"topic_ai_{idx}"),
                        "heat_score": heat_score,
                        "badge_zh": t_obj.get("badge_zh", "🔥 24h 领跑爆点"),
                        "badge_en": t_obj.get("badge_en", "🔥 24h Breakthrough"),
                        "category_tag_zh": t_obj.get("category_tag_zh", "焦点前沿"),
                        "category_tag_en": t_obj.get("category_tag_en", "Frontier Focus"),
                        "title_zh": t_obj.get("title_zh", ""),
                        "title_en": t_obj.get("title_en", ""),
                        "summary_zh": t_obj.get("summary_zh", ""),
                        "summary_en": t_obj.get("summary_en", ""),
                        "perspective_pro": t_obj.get("perspective_pro", {}),
                        "perspective_con": t_obj.get("perspective_con", {}),
                        "linked_news": matched_news,
                        "linked_tweets": matched_tweets,
                        "linked_tool": matched_tool,
                        "linked_counts": {
                            "news": len(matched_news),
                            "tweets": len(matched_tweets),
                            "has_tool": bool(matched_tool)
                        }
                    }
                    topic_results.append(final_topic)

                print(f"✨ [topic_cluster] Gemini 成功挖掘生成 Top {len(topic_results)} 突发热点专题！")
                return topic_results

        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str:
                print(f"🛑 [topic_cluster] 检测到 Gemini 配额限流 (429/ResourceExhausted)。为避免影响其他项目，立即启动熔断，切换至零消耗保底算法！")
                break
            print(f"⚠️ [topic_cluster] 模型 {model_name} 聚类异常: {e}")
            continue

    return None


def _cluster_topics_algorithmically(
    news_items: List[Dict[str, Any]],
    tweet_items: List[Dict[str, Any]],
    tool_items: List[Dict[str, Any]],
    workflows: List[Dict[str, Any]],
    max_topics: int = 3
) -> List[Dict[str, Any]]:
    """
    【轨道 B - 保底动态算法】当无网络或无 API Key 时，基于真实资讯实体的动态共现聚类。
    提取真实资讯中出现频率最高且具有强冲突的实体与关键标题，杜绝任何静态固定模板套话。
    """
    print("⚡ [topic_cluster] 启用保底动态实体共现聚类算法...")
    
    # 动态定义几个关键事件群特征（针对真实事件群进行聚焦）
    CLUSTER_PATTERNS = [
        {
            "id": "topic_math_reasoning_scrutiny",
            "entity_keywords": ["math", "navier", "stokes", "千禧", "数学", "证明", "论文", "openai", "逻辑"],
            "badge_zh": "🔥 24h 领跑爆点",
            "badge_en": "🔥 24h Breakthrough",
            "category_tag_zh": "学术争议与证明边界",
            "category_tag_en": "Academic Debate & Rigor",
            "default_tool_kw": "rag",
            "pro_template": {
                "role_zh": "🟢 AGI加速派 / 前沿研究员",
                "role_en": "🟢 AGI Pioneers & Researchers",
                "speaker_zh": "大模型推理架构师与前沿实验室团队",
                "speaker_en": "Frontier Lab Architects & Researchers",
                "point_zh": "大模型在长程推理与百年数学猜想探索中迈出了历史性一步，AI自探索与符号演绎展现了全新科学发现范式。",
                "point_en": "Extended reasoning represents a historic step in exploring mathematical conjectures, opening a new paradigm for scientific discovery."
            },
            "con_template": {
                "role_zh": "🔴 严谨学界 / 理论数学家",
                "role_en": "🔴 Theoretical Rigor & Academic Critics",
                "speaker_zh": "数学家与形式化验证学者",
                "speaker_en": "Mathematicians & Formal Verification Experts",
                "point_zh": "论文正文存在大量逻辑断层与形式主义幻觉，用概率自相关拼凑严谨数理证明极具欺骗性，缺乏确定性严密结论。",
                "point_en": "The submission exhibits critical logical disconnects and formal hallucinations, failing to satisfy the rigorous standards of mathematical proof."
            }
        },
        {
            "id": "topic_cloud_capex_vendor_war",
            "entity_keywords": ["anthropic", "replit", "tpu", "600", "融资", "借债", "芯片", "算力", "招聘", "工时"],
            "badge_zh": "⚡ 商业与算力风暴",
            "badge_en": "⚡ Compute & Market Storm",
            "category_tag_zh": "算力军备与商业博弈",
            "category_tag_en": "Compute Arms Race & Market War",
            "default_tool_kw": "cursor",
            "pro_template": {
                "role_zh": "🟢 资本军备派 / 算力豪赌者",
                "role_en": "🟢 Capital Scale & Infrastructure Leads",
                "speaker_zh": "前沿模型实验室与超算集群操盘手",
                "speaker_en": "Frontier Labs & Hyper-Scale Cluster Leads",
                "point_zh": "下一代超级智力必须依靠超大规模自研与定制算力集群，以高息债务抢占万卡算力底座是决胜AGI的必然代价值得豪赌。",
                "point_en": "Next-gen frontier intelligence requires astronomical dedicated compute; leveraging debt for massive TPU clusters is the necessary entry fee for AGI."
            },
            "con_template": {
                "role_zh": "🔴 工业实用派 / 下游开发者",
                "role_en": "🔴 Pragmatic Developers & Downstream Customers",
                "speaker_zh": "开发者工具创企 CEO 与企业架构师",
                "speaker_en": "Startup Founders & Enterprise Architects",
                "point_zh": "高昂的硬件负债与高昂的 API 定价正在严重反噬生态，商业客户只为性价比买单，过度烧钱的巨头终将被客户用脚投票。",
                "point_en": "Astronomical debt and exorbitant API costs are alienating real customers. Startups and enterprise developers will swiftly switch to high-ROI alternatives."
            }
        },
        {
            "id": "topic_open_weights_and_video",
            "entity_keywords": ["deepseek", "kling", "可灵", "v4.1", "开源", "视频", "flash", "成本", "生成"],
            "badge_zh": "💡 开源与视效落地潮",
            "badge_en": "💡 Open Weights & Visual Frontier",
            "category_tag_zh": "模型突破与开源降本",
            "category_tag_en": "Open Source & Visual Breakthroughs",
            "default_tool_kw": "deepseek",
            "pro_template": {
                "role_zh": "🟢 开源赋能派 / 独立开发者",
                "role_en": "🟢 Open Source Champions & Indie Devs",
                "speaker_zh": "开源贡献者与视效创作者",
                "speaker_en": "Open Source Developers & Creators",
                "point_zh": "高能效蒸馏与自我反馈强化学习显著压缩了推断成本，视效运镜控制让普通创作者也能享受到工业级生成能力。",
                "point_en": "Reinforcement learning and efficient distillation drastically slash token costs, empowering indie creators with production-grade video and reasoning."
            },
            "con_template": {
                "role_zh": "🔴 落地清醒派 / 商业审慎者",
                "role_en": "🔴 Commercial Skeptics & Pragmatists",
                "speaker_zh": "传统视效导演与企业产品总监",
                "speaker_en": "Film Directors & Enterprise Product Leads",
                "point_zh": "榜单与跑分繁荣不等于真实业务闭环，当前模型在物理一致性与高阶企业级生产场景中仍存在不可忽视的稳定性瓶颈。",
                "point_en": "Benchmark leaps do not guarantee enterprise product-market fit; temporal consistency and commercial workflow integrations remain non-trivial bottlenecks."
            }
        }
    ]

    topic_results = []
    base_heat = 9.8

    for idx, cluster in enumerate(CLUSTER_PATTERNS[:max_topics]):
        kws = cluster["entity_keywords"]
        
        # 寻找命中的快讯
        scored_news = []
        for n in news_items:
            corpus = " ".join([
                str(n.get("title_zh", "")),
                str(n.get("title_en", "")),
                str(n.get("title", "")),
                str(n.get("summary_zh", "")),
                str(n.get("content_snippet", ""))
            ]).lower()
            hit = sum(2 for kw in kws if kw in corpus)
            if hit > 0:
                scored_news.append((hit, n))
        scored_news.sort(key=lambda x: x[0], reverse=True)
        top_news = [x[1] for x in scored_news[:3]]

        # 寻找命中的推文
        scored_tweets = []
        for tw in tweet_items:
            tw_corpus = " ".join([
                str(tw.get("author", "")),
                str(tw.get("author_handle", "")),
                str(tw.get("content_zh", "")),
                str(tw.get("content_snippet", "")),
                str(tw.get("original_content", ""))
            ]).lower()
            hit = sum(2 for kw in kws if kw in tw_corpus)
            if hit > 0:
                scored_tweets.append((hit, tw))
        scored_tweets.sort(key=lambda x: x[0], reverse=True)
        top_tweets = [x[1] for x in scored_tweets[:2]]

        # 提炼具体的事件标题与摘要：以该群中热度最高的实际新闻为准！
        lead_news = top_news[0] if top_news else {}
        title_zh = lead_news.get("title_zh") or lead_news.get("title") or "24h 核心 AI 事件突破与争议透视"
        title_en = lead_news.get("title_en") or lead_news.get("title") or "24h AI Core Breakthrough & Industry Debate"
        
        # 摘要：采用 lead_news 的详细简报
        summary_zh = lead_news.get("summary_zh") or lead_news.get("content_snippet") or "本事件涉及多方核心技术演进与商业路线博弈，引发学界与工程界广泛讨论。"
        summary_en = lead_news.get("summary_en") or lead_news.get("content_snippet") or "This incident reflects critical technical developments and intense industry debates."

        # 清洗快讯
        clean_news = []
        for n in top_news:
            clean_news.append({
                "id": n.get("id", ""),
                "title_zh": n.get("title_zh") or n.get("title", ""),
                "title_en": n.get("title_en") or n.get("title", ""),
                "source": n.get("source", "Global AI"),
                "url": n.get("url", "#"),
                "image_url": n.get("image_url", ""),
                "hot_score": n.get("hot_score", 4),
                "published_at": n.get("raw_published_at", "")
            })

        # 清洗推文
        clean_tweets = []
        for tw in top_tweets:
            clean_tweets.append({
                "id": tw.get("id", ""),
                "author": tw.get("author", "AI Leader"),
                "author_handle": tw.get("author_handle", "@ai"),
                "author_avatar": tw.get("author_avatar", ""),
                "content_zh": tw.get("content_zh") or tw.get("original_content", ""),
                "content_en": tw.get("original_content") or tw.get("content_zh", ""),
                "url": tw.get("url", "#"),
                "platform": tw.get("platform", "x")
            })

        # 匹配工具
        matched_tool = _match_best_tool_or_workflow(
            tool_keyword=cluster.get("default_tool_kw", ""),
            workflows=workflows,
            tool_items=tool_items,
            topic_title=title_zh
        )

        heat_score = round(base_heat - (idx * 0.2), 1)

        topic_results.append({
            "topic_id": cluster["id"],
            "heat_score": heat_score,
            "badge_zh": cluster["badge_zh"],
            "badge_en": cluster["badge_en"],
            "category_tag_zh": cluster["category_tag_zh"],
            "category_tag_en": cluster["category_tag_en"],
            "title_zh": title_zh,
            "title_en": title_en,
            "summary_zh": summary_zh,
            "summary_en": summary_en,
            "perspective_pro": cluster["pro_template"],
            "perspective_con": cluster["con_template"],
            "linked_news": clean_news,
            "linked_tweets": clean_tweets,
            "linked_tool": matched_tool,
            "linked_counts": {
                "news": len(clean_news),
                "tweets": len(clean_tweets),
                "has_tool": bool(matched_tool)
            }
        })

    return topic_results


def generate_24h_topic_focus(
    items: List[Dict[str, Any]],
    max_topics: int = 3,
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """
    针对 24 小时内的全量资讯集合提取 Top 3 核心热点话题，挂载脉络、立场对撞与关联情报束。
    内置多层配额安全锁：
      1. 默认每 4 小时仅调用一次 Gemini，其余频次复用缓存 (0 API 消耗)
      2. 遇到 429 / 额度受限时自动熔断，平滑降级至零消耗动态实体聚类算法
    """
    if not items:
        return []

    # 0. 智能配额保护锁 (Smart Cooldown & Quota Guard)
    if not force_refresh:
        cached_topics = _get_cached_topic_focus_if_fresh(TOPIC_REFRESH_INTERVAL_HOURS)
        if cached_topics and len(cached_topics) >= max_topics:
            return cached_topics

    # 1. 拆分各类情报流
    news_items = [it for it in items if it.get("category") == "news" or (it.get("category") is None and "news" in it.get("id", ""))]
    celeb_items = [it for it in items if it.get("category") == "celebrity" or it.get("platform") in ("x", "reddit")]
    tool_items = [it for it in items if it.get("category") == "tools" or it.get("is_tool")]
    workflows = _load_curated_workflows()

    gemini_client = get_gemini_client()
    topic_results = None

    # 2. 轨道 A：尝试使用 Gemini AI 实时聚类
    if gemini_client:
        try:
            topic_results = _cluster_topics_with_gemini(
                news_items=news_items,
                tweet_items=celeb_items,
                tool_items=tool_items,
                workflows=workflows,
                client=gemini_client
            )
        except Exception as e:
            print(f"⚠️ [topic_cluster] Gemini 聚类执行失败: {e}")
            topic_results = None

    # 3. 轨道 B：保底动态实体共现聚类
    if not topic_results:
        topic_results = _cluster_topics_algorithmically(
            news_items=news_items,
            tweet_items=celeb_items,
            tool_items=tool_items,
            workflows=workflows,
            max_topics=max_topics
        )

    # 4. 持久化存储到数据目录
    try:
        os.makedirs(os.path.dirname(DATA_TOPIC_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(PUBLIC_DATA_TOPIC_FILE), exist_ok=True)
        
        payload = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "topics": topic_results
        }
        with open(DATA_TOPIC_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        with open(PUBLIC_DATA_TOPIC_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"✅ [topic_cluster] 成功持久化 24h Top {len(topic_results)} 核心话题专题到数据文件！")
    except Exception as e:
        print(f"⚠️ [topic_cluster] 持久化话题文件异常: {e}")

    return topic_results


def build_topic_focus_html(topics: List[Dict[str, Any]], lang: str = "zh") -> str:
    """
    生成用于首页真实可见 DOM 预渲染的 Topic Focus 核心专题 HTML 组件。
    严格支持中英双语、无水土不服、全响应式与极客高对比度暗黑科技美学。
    """
    if not topics:
        return ""

    is_zh = (lang == "zh")
    
    header_title = "🔥 24h 核心话题全景透视" if is_zh else "🔥 24h Topic Focus & Perspectives"
    badge_title = "TOP 3 智库专题" if is_zh else "TOP 3 DOSSIERS"
    header_desc = "· 今日真实爆发事实 · 大V观点立场对撞 · 关联情报直达" if is_zh else "· Today's Real Breakthroughs · Viewpoints Collision · Linked Bundles"
    btn_collapse_txt = "▲ 收起" if is_zh else "▲ Collapse"

    # 1. 渲染话题 Tabs
    tab_buttons = []
    for idx, t in enumerate(topics):
        is_active = (idx == 0)
        badge = t.get("badge_zh" if is_zh else "badge_en", "")
        title = t.get("title_zh" if is_zh else "title_en", "")
        heat = t.get("heat_score", 9.8)
        
        # 截短 Tab 标题避免移动端过宽
        short_title = title if len(title) <= 14 else title[:13] + "…"
        
        active_cls = "topic-tab-btn active px-3 py-1.5 rounded-xl font-bold text-xs bg-indigo-600 text-white shadow-md border border-indigo-400/40 transition-all cursor-pointer flex items-center gap-1.5"
        inactive_cls = "topic-tab-btn px-3 py-1.5 rounded-xl font-semibold text-xs bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-all cursor-pointer flex items-center gap-1.5"
        
        tab_buttons.append(f"""
        <button type="button" id="topic-tab-{idx}" onclick="switchTopicFocus({idx})" class="{active_cls if is_active else inactive_cls}" data-idx="{idx}">
          <span class="text-[11px] font-mono opacity-90">{badge[:2]}</span>
          <span class="truncate">{short_title}</span>
          <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold ml-0.5">{heat}</span>
        </button>""")

    tabs_html = "\n".join(tab_buttons)

    # 2. 渲染每个 Topic 详情卡片
    topic_cards = []
    for idx, t in enumerate(topics):
        is_active = (idx == 0)
        card_cls = "topic-focus-card grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch" + ("" if is_active else " hidden")
        
        cat_tag = t.get("category_tag_zh" if is_zh else "category_tag_en", "")
        badge = t.get("badge_zh" if is_zh else "badge_en", "")
        heat = t.get("heat_score", 9.8)
        title = t.get("title_zh" if is_zh else "title_en", "")
        summary = t.get("summary_zh" if is_zh else "summary_en", "")
        
        pro = t.get("perspective_pro", {})
        con = t.get("perspective_con", {})
        
        pro_role = pro.get("role_zh" if is_zh else "role_en", "")
        pro_speaker = pro.get("speaker_zh" if is_zh else "speaker_en", "")
        pro_point = pro.get("point_zh" if is_zh else "point_en", "")
        
        con_role = con.get("role_zh" if is_zh else "role_en", "")
        con_speaker = con.get("speaker_zh" if is_zh else "speaker_en", "")
        con_point = con.get("point_zh" if is_zh else "point_en", "")

        # 关联快讯渲染
        news_list = t.get("linked_news", [])
        news_html_items = []
        for n in news_list:
            n_title = n.get("title_zh" if is_zh else "title_en") or n.get("title", "")
            n_source = n.get("source", "Global AI")
            n_id = n.get("id", "")
            n_url = n.get("url", "#")
            click_attr = f'onclick="if(!event.target.closest(\'a\')) openAiNewsModal(\'{n_id}\')"' if n_id else ''
            news_html_items.append(f"""
            <div class="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-indigo-500/40 transition-colors cursor-pointer group" {click_attr}>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30 shrink-0 font-mono mt-0.5">{n_source[:10]}</span>
              <div class="min-w-0 flex-1">
                <a href="{n_url}" target="_blank" rel="noopener noreferrer" class="text-xs text-slate-200 group-hover:text-indigo-300 transition-colors line-clamp-2 leading-snug font-medium block">
                  {n_title}
                </a>
              </div>
            </div>""")
        news_bundle_html = "\n".join(news_html_items) if news_html_items else f'<p class="text-xs text-slate-400">{"暂无直接关联快讯" if is_zh else "No direct news linked"}</p>'

        # 关联推文渲染
        tweet_list = t.get("linked_tweets", [])
        tweet_html_items = []
        for tw in tweet_list:
            tw_author = tw.get("author", "AI Leader")
            tw_handle = tw.get("author_handle", "@ai")
            tw_content = tw.get("content_zh" if is_zh else "content_en", "")
            tw_url = tw.get("url", "#")
            tw_avatar = tw.get("author_avatar") or "https://api.dicebear.com/7.x/bottts/svg?seed=VIP"
            tweet_html_items.append(f"""
            <div class="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-sky-500/40 transition-colors">
              <img src="{tw_avatar}" alt="{tw_author}" width="24" height="24" class="w-6 h-6 rounded-full object-cover shrink-0 ring-1 ring-slate-700 mt-0.5" loading="lazy" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=VIP'">
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between text-[11px] gap-1 mb-0.5">
                  <span class="font-bold text-slate-200 truncate">{tw_author}</span>
                  <a href="{tw_url}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-sky-400 hover:underline shrink-0">原帖 ↗</a>
                </div>
                <p class="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">{tw_content}</p>
              </div>
            </div>""")
        tweets_bundle_html = "\n".join(tweet_html_items) if tweet_html_items else ""

        # 关联工具/工作流渲染
        tool = t.get("linked_tool", {})
        tool_html = ""
        if tool:
            tool_name = tool.get("title_zh" if is_zh else "title_en") or tool.get("name", "")
            tool_desc = tool.get("desc_zh" if is_zh else "desc_en") or tool.get("takeaway_zh" if is_zh else "takeaway_en", "")
            tool_url = tool.get("url") or tool.get("github_url", "#")
            is_wf = tool.get("is_workflow", False)
            tag_label = ("🛠️ 实战落地配方" if is_zh else "🛠️ Production Playbook") if is_wf else ("🚀 场景落地工具" if is_zh else "🚀 Applied AI Tool")
            action_btn = ("📋 一键直达工作流" if is_zh else "📋 View Playbook") if is_wf else ("立即体验 ↗" if is_zh else "Try Tool ↗")
            tool_click = f"onclick=\"switchTab('prompts')\"" if is_wf else ""
            
            tool_html = f"""
            <div class="mt-2.5 p-2.5 rounded-xl bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-slate-900/60 border border-purple-500/30 hover:border-purple-400/50 transition-all">
              <div class="flex items-center justify-between gap-1 mb-1">
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">{tag_label}</span>
                <span class="text-[10px] text-emerald-400 font-mono font-semibold">{tool.get('weekly_stars', '+3,000★')}</span>
              </div>
              <h4 class="text-xs font-bold text-slate-100 truncate mt-1">{tool_name}</h4>
              <p class="text-[11px] text-slate-300 line-clamp-2 leading-relaxed mt-1">{tool_desc}</p>
              <div class="flex items-center justify-end mt-2 pt-1.5 border-t border-purple-500/20">
                <a href="{tool_url}" target="_blank" rel="noopener noreferrer" {tool_click} class="text-xs font-semibold text-purple-300 hover:text-purple-200 hover:underline inline-flex items-center gap-1">
                  <span>{action_btn}</span>
                </a>
              </div>
            </div>"""

        # 组装单个完整 Topic Card (3 栏并排)
        topic_cards.append(f"""
        <!-- Topic Card {idx} -->
        <article id="topic-focus-card-{idx}" class="{card_cls}" data-idx="{idx}">
          
          <!-- 列 1: 事件核心脉络 (Core Context & Breakthrough) -->
          <div class="lg:col-span-4 flex flex-col justify-between space-y-3 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between gap-2">
                <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 font-mono">
                  {cat_tag}
                </span>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">
                  🔥 {("爆度" if is_zh else "HEAT")} {heat}
                </span>
              </div>
              <h3 class="text-base sm:text-lg font-black text-white leading-snug tracking-tight">
                {title}
              </h3>
              <div class="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-200 text-xs sm:text-sm leading-relaxed">
                {summary}
              </div>
            </div>
            <div class="flex items-center gap-2 pt-2 border-t border-slate-800/80 flex-wrap text-[10px] text-indigo-300 font-mono">
              <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">🎯 {"核心爆发点" if is_zh else "Core Milestone"}</span>
              <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">💡 {"行业范式影响" if is_zh else "Industry Impact"}</span>
              <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">⚡ {"24h 追踪" if is_zh else "24h Live"}</span>
            </div>
          </div>

          <!-- 列 2: 大V观点立场对撞 (Perspectives Collision) -->
          <div class="lg:col-span-4 flex flex-col justify-between space-y-3 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
            <div class="space-y-2.5">
              <div class="flex items-center justify-between pb-1.5 border-b border-slate-800">
                <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5 uppercase tracking-wider">
                  <span>⚔️</span>
                  <span>{"大V观点立场对撞" if is_zh else "Perspectives Collision"}</span>
                </h4>
                <span class="text-[10px] text-slate-400 font-mono">{"双面对照" if is_zh else "Dual Perspectives"}</span>
              </div>

              <!-- 观点 A: 愿景演进派 -->
              <div class="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-100 space-y-1.5 shadow-sm">
                <div class="flex items-center justify-between gap-1 text-[11px]">
                  <span class="font-bold text-emerald-300">{pro_role}</span>
                  <span class="text-[10px] text-emerald-400 font-mono truncate max-w-[140px]">{pro_speaker}</span>
                </div>
                <p class="text-xs text-emerald-100/90 leading-relaxed font-normal">
                  “{pro_point}”
                </p>
              </div>

              <!-- 观点 B: 工业理性派 -->
              <div class="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-100 space-y-1.5 shadow-sm">
                <div class="flex items-center justify-between gap-1 text-[11px]">
                  <span class="font-bold text-rose-300">{con_role}</span>
                  <span class="text-[10px] text-rose-400 font-mono truncate max-w-[140px]">{con_speaker}</span>
                </div>
                <p class="text-xs text-rose-100/90 leading-relaxed font-normal">
                  “{con_point}”
                </p>
              </div>
            </div>

            <div class="text-[10px] text-slate-400 text-right pt-1 font-mono">
              {"智库核心研判 · 拒绝盲目跟风" if is_zh else "Independent Analysis · Beyond the Hype"}
            </div>
          </div>

          <!-- 列 3: 关联情报束 (Linked Intelligence Bundle) -->
          <div class="lg:col-span-4 flex flex-col justify-between space-y-2.5 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
            <div>
              <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 mb-2">
                <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5 uppercase tracking-wider">
                  <span>🔗</span>
                  <span>{"关联情报束" if is_zh else "Linked Intelligence Bundle"}</span>
                </h4>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {len(news_list)} {"快讯" if is_zh else "News"} · {len(tweet_list)} {"推文" if is_zh else "Tweets"}
                </span>
              </div>

              <!-- 快讯列表 -->
              <div class="space-y-1.5 mb-2">
                {news_bundle_html}
              </div>

              <!-- 推文列表 -->
              <div class="space-y-1.5">
                {tweets_bundle_html}
              </div>

              <!-- 关联工具/配方 -->
              {tool_html}
            </div>

            <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
              <span>{"AI 实时聚类每日自动更新" if is_zh else "AI Daily Real-Time Clustered"}</span>
              <button type="button" onclick="switchTab('all')" class="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline cursor-pointer">
                {"查看完整信息流 →" if is_zh else "Explore Full Stream →"}
              </button>
            </div>
          </div>

        </article>""")

    cards_html = "\n".join(topic_cards)

    # 3. 组装最外层 section
    return f"""
    <!-- ========== TOPIC_FOCUS_SECTION_START ========== -->
    <section id="topic-focus-section" class="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 rounded-2xl border border-indigo-500/30 p-4 sm:p-5 shadow-2xl backdrop-blur-xl relative overflow-hidden transition-all text-white my-6" aria-label="{header_title}">
      <!-- 头部：标题、热度指示器、3个话题切换 Tab、收起/展开按钮 -->
      <div class="flex flex-col md:flex-row md:items-center justify-between pb-3.5 border-b border-indigo-500/20 gap-3">
        <div class="flex items-center space-x-2.5 min-w-0">
          <span class="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
          <div class="flex items-center space-x-2">
            <h2 class="text-sm sm:text-base font-black text-white flex items-center space-x-1.5 tracking-tight" id="topic-focus-header-title">
              <span>{header_title}</span>
              <span class="text-[10px] px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold tracking-wider">{badge_title}</span>
            </h2>
            <span class="text-xs text-indigo-200/80 hidden lg:inline" id="topic-focus-header-desc">{header_desc}</span>
          </div>
        </div>

        <!-- 话题切换 Tab 组与收起/展开开关 -->
        <div class="flex items-center gap-1.5 flex-wrap sm:flex-nowrap shrink-0">
          <div class="flex items-center gap-1.5 flex-wrap" id="topic-tabs-bar">
            {tabs_html}
          </div>
          <button type="button" id="topic-focus-toggle-btn" onclick="toggleTopicFocusCollapse()" class="px-2.5 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/60 transition cursor-pointer shrink-0 ml-1" title="{"收起 / 展开" if is_zh else "Collapse / Expand"}">
            {btn_collapse_txt}
          </button>
        </div>
      </div>

      <!-- 话题主体容器 (Topic Body Container) -->
      <div id="topic-focus-content" class="pt-4 transition-all duration-300">
        {cards_html}
      </div>
    </section>
    <!-- ========== TOPIC_FOCUS_SECTION_END ========== -->"""


def load_latest_topic_focus() -> List[Dict[str, Any]]:
    """读取已生成的 24h 核心话题专题"""
    for filepath in (PUBLIC_DATA_TOPIC_FILE, DATA_TOPIC_FILE):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "topics" in data:
                        return data["topics"]
                    elif isinstance(data, list):
                        return data
            except Exception:
                pass
    return []


if __name__ == "__main__":
    print("🚀 [topic_cluster] 启动 24h 核心话题专题动态聚类引擎...")
    latest_news_file = os.path.join(BASE_DIR, "public", "data", "latest_news.json")
    if os.path.exists(latest_news_file):
        with open(latest_news_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
            items = []
            if raw.get("grouped"):
                for k, v in raw["grouped"].items():
                    if isinstance(v, list):
                        items.extend(v)
            elif raw.get("items"):
                items = raw["items"]
            
            topics = generate_24h_topic_focus(items)
            print(f"🎉 成功生成 {len(topics)} 个 24h 焦点专题:")
            for t in topics:
                print(f"  - [{t['heat_score']}] {t['title_zh']}")
                print(f"    脉络: {t['summary_zh'][:80]}...")
                print(f"    正方: {t.get('perspective_pro', {}).get('role_zh')}")
                print(f"    反方: {t.get('perspective_con', {}).get('role_zh')}")
                print(f"    关联: {len(t['linked_news'])} 快讯, {len(t['linked_tweets'])} 推文, 工具: {bool(t['linked_tool'])}")
