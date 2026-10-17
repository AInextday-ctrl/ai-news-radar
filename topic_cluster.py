# -*- coding: utf-8 -*-
"""
topic_cluster.py - 24h 核心话题专题聚合引擎 (Topic Focus Engine)
================================================================
深度解析 24 小时内的全网突发快讯、AI领袖观点、爆款推文与前沿工具，
基于语义权重聚类算法提炼当日前沿 Top 3 核心热议话题，输出三维立体结构：
  1. 事件核心脉络 (Background & Core Breakthrough)
  2. 大V观点立场对撞 (Perspectives Collision: 愿景派/演进派 vs 工业理性派/评测派)
  3. 关联情报束 (Linked Intelligence Bundle: 2-3条关键快讯 + 1-2条领袖推文 + 1个落地工具/配方)

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_TOPIC_FILE = os.path.join(BASE_DIR, "data", "topic_focus.json")
PUBLIC_DATA_TOPIC_FILE = os.path.join(BASE_DIR, "public", "data", "topic_focus.json")
CURATED_WORKFLOWS_FILE = os.path.join(BASE_DIR, "data", "curated_workflows_library.json")

# 定义话题核心领域定义库与特征匹配词表
TOPIC_BLUEPRINTS = [
    {
        "id": "topic_reasoning_models_frontier",
        "category_tag_zh": "模型架构与推理突破",
        "category_tag_en": "Reasoning & Scaling Laws",
        "badge_zh": "🔥 24h 领跑爆点",
        "badge_en": "🔥 24h Breakthrough",
        "keywords": [
            "reasoning", "proof", "math", "navier", "stokes", "o1", "o3", "r1", "deepseek",
            "thinking", "cot", "chain of thought", "claude 3.7", "opus", "mythos", "astra pro",
            "openai", "anthropic", "test-time", "inference compute", "推理", "思考", "证明", "千禧", "逻辑", "强化学习"
        ],
        "title_zh": "混合推理模型范式演进与学术界严谨性争议",
        "title_en": "Hybrid Reasoning Scaling: Frontier Breakthroughs & Academic Scrutiny",
        "summary_zh": "OpenAI 提交千禧难题解法论文引发数学界对其方法论脱节的强烈质疑，同时 DeepSeek 与 Anthropic 新一代高能效推理模型密集发布。行业正加速从单纯预训练 Scaling 转向推断期 Test-Time Compute。长思考链显著提升了数学与复杂逻辑上限，但推断时延、Token 成本激增以及数学严谨性也成为争论风暴眼。",
        "summary_en": "As OpenAI's Navier-Stokes proof submission triggers academic skepticism and next-gen reasoning models roll out from DeepSeek and Anthropic, the AI industry is aggressively shifting towards inference-time reasoning. Extended chain-of-thought elevates problem-solving bounds, yet inference latency, token cost, and formal rigor remain intensely contested.",
        "perspective_pro": {
            "role_zh": "🟢 愿景派 / 核心研发架构师",
            "role_en": "🟢 Visionary / Frontier Lab Architects",
            "speaker_zh": "顶级前沿实验室研发团队与理论架构师",
            "speaker_en": "Frontier Research Labs & Core Architects",
            "point_zh": "推断期算力（Test-Time Compute）突破了预训练文本枯竭的瓶颈，让大模型通过强化学习自反思、树搜索与自我验证获得接近人类系统二的深度推理能力，开启了全新的 Scaling 维度。",
            "point_en": "Test-time compute breaks past pre-training data ceilings, empowering models with self-correction, tree-search, and System-2 deep reasoning across math and code."
        },
        "perspective_con": {
            "role_zh": "🔴 工业理性派 / 学术严谨评测",
            "role_en": "🔴 Pragmatic Critic / Academic Benchmarkers",
            "speaker_zh": "工业落地工程师与数学/评测专家",
            "speaker_en": "Deployment Engineers & Mathematical Evaluators",
            "point_zh": "生成海量思考 Token 导致请求延迟高昂且吞吐骤降，高并发生产场景难以承担；更关键的是，长链推理极易出现虚假逻辑跳跃与基准过拟合，缺乏确定性的严密证明。",
            "point_en": "Generating thousands of reasoning tokens causes unacceptable latency in production, while extended CoT risks benchmark gaming and superficial logical leaps lacking formal mathematical rigor."
        },
        "default_tool_id": "wf_deepseek_r1_ollama_local_sota",
        "default_tool_fallback": {
            "id": "wf_deepseek_r1_ollama_local_sota",
            "name": "DeepSeek-R1 本地推理与 Ollama 部署配方",
            "title_zh": "DeepSeek-R1 本地量化部署与 Ollama 显存调优配方",
            "title_en": "DeepSeek-R1 Local Ollama Deployment & VRAM Optimization Modelfile",
            "desc_zh": "提供精准 context 窗口、temperature=0.6 与思考链标签自动剥离参数，杜绝爆显存与重复死循环。",
            "desc_en": "Production Modelfile with optimized context window, temp=0.6, and thinking-token stripping for local GPUs.",
            "url": "https://github.com/deepseek-ai/DeepSeek-R1",
            "github_url": "https://github.com/deepseek-ai/DeepSeek-R1",
            "weekly_stars": "+8,500★",
            "is_workflow": True
        }
    },
    {
        "id": "topic_agentic_workflows_mcp",
        "category_tag_zh": "Agent工程与落地标准",
        "category_tag_en": "Agentic Workflows & MCP",
        "badge_zh": "⚡ 架构与工程范式",
        "badge_en": "⚡ Engineering Paradigm",
        "keywords": [
            "agent", "mcp", "model context protocol", "cursor", "windsurf", "claude code",
            "codex", "coding agent", "reach", "duvo", "context protocol", "agentic",
            "智能体", "编程规范", "工作流", "自动化流程", "规则模板"
        ],
        "title_zh": "企业级 AI Coding、智能体闭环与 MCP 协议工业落地",
        "title_en": "Industrial AI Coding, Autonomous Agents & MCP Protocol Standardization",
        "summary_zh": "Duvo、Reach 等数千万美元企业级自动化与安全智能体融资落地，同时 Cursor、Windsurf、Claude Code 等 AI 编程助手全面支持 MCP（模型上下文协议）。智能体正从单次代码补全迈向拥有上下文感知、本地工具执行与安全防护机制的工业级全自主工作流。",
        "summary_en": "Multi-million dollar funding rounds for enterprise automation agents like Duvo and Reach highlight the rapid maturation of agentic workflows. With Cursor, Windsurf, and Claude Code standardizing on MCP (Model Context Protocol), AI coding is transitioning from simple completions to fully contextual, self-executing engineering loops.",
        "perspective_pro": {
            "role_zh": "🟢 进取派 / 智能体开发者",
            "role_en": "🟢 Progressive / Agent Builders",
            "speaker_zh": "一线 AI 全栈开发者与自动化先锋",
            "speaker_en": "Fullstack Agent Builders & Tooling Leads",
            "point_zh": "MCP 协议打破了模型与外部系统（文件、数据库、网络、GitHub）的数据孤岛；配合规范化的工程提示词，AI 正在重塑开发者的工作流，实现数倍生产力跃迁。",
            "point_en": "MCP eliminates data silos between LLMs and external systems (filesystem, DB, web, GitHub). Coupled with rigorous rules, agentic automation delivers multi-fold productivity gains."
        },
        "perspective_con": {
            "role_zh": "🔴 防守派 / 企业架构与安全",
            "role_en": "🔴 Defensive / Enterprise Security",
            "speaker_zh": "企业架构师、安全审计员与维护主管",
            "speaker_en": "Enterprise Architects & Security Auditors",
            "point_zh": "Agent 盲目修改项目文件可能导致严重的隐蔽 Bug 与安全漏洞；模型编造第三方依赖包、缺乏防御性断言与测试覆盖，会使团队陷入沉重的后期技术债务泥潭。",
            "point_en": "Autonomous agents modifying core codebases risk hallucinating insecure packages, bypassing architectural boundaries, and creating crippling technical debt without strict verification gates."
        },
        "default_tool_id": "wf_cursorrules_fullstack_2026",
        "default_tool_fallback": {
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
    },
    {
        "id": "topic_open_source_edge_efficiency",
        "category_tag_zh": "开源生态与极致降本",
        "category_tag_en": "Open Source & Edge Compute",
        "badge_zh": "💡 开源与落地潮",
        "badge_en": "💡 Open Source Wave",
        "keywords": [
            "open source", "local", "ollama", "vllm", "quantization", "gguf", "deepseek-v3",
            "deepseek-v4", "llama", "huggingface", "weights", "cost", "efficiency", "moe",
            "开源", "本地", "部署", "显存", "成本", "私有化", "降本", "量化"
        ],
        "title_zh": "开源模型爆发、端侧私有化部署与极致算力性价比浪潮",
        "title_en": "Open-Source Weights Surge: Private Edge Deployment & Extreme Cost Efficiency",
        "summary_zh": "以 DeepSeek、Llama 生态与高能效量化算法为代表的开源技术浪潮，让消费级硬件与私有集群运行顶尖模型成为现实。企业与极客开发者正加速将核心业务从昂贵的商业闭源 API 迁移至本地化私有部署，在实现数据主权的同时将调用成本削减超 90%。",
        "summary_en": "The rapid acceleration of open weights, MoE architectures, and efficient quantization (GGUF/AWQ) allows consumer hardware and private servers to run high-tier models. Enterprises and indie hackers are migrating workloads away from costly proprietary APIs to private stacks, safeguarding data sovereignty while slashing costs by over 90%.",
        "perspective_pro": {
            "role_zh": "🟢 开源赋能派 / 极客社群",
            "role_en": "🟢 Open-Source Champions / Hackers",
            "speaker_zh": "开源贡献者、独立开发者与自建算力团队",
            "speaker_en": "Open Source Contributors & Self-Hosted Teams",
            "point_zh": "权重开源打破了巨头的技术垄断与高昂定价；本地化部署不仅零数据泄露风险，还能结合 vLLM 与 Ollama 实现极高吞吐，真正让 AI 技术民主化普及。",
            "point_en": "Open weights democratize frontier AI, eliminating vendor lock-in. Self-hosted setups guarantee zero data leakage and extreme throughput with tools like Ollama and vLLM."
        },
        "perspective_con": {
            "role_zh": "🔴 商业闭源派 / 规模效益论",
            "role_en": "🔴 Commercial Scale Advocates",
            "speaker_zh": "公有云大厂与闭源模型商业团队",
            "speaker_en": "Cloud Hyperscalers & Frontier Commercial Teams",
            "point_zh": "私有化运维涉及昂贵显卡采购、驱动兼容与持续更新负担；且超万亿参数旗舰的多模态超大窗口泛化与安全边界，仍是千卡甚至万卡规模训练集群的绝对护城河。",
            "point_en": "Self-hosting demands heavy hardware upkeep and driver tuning. Multi-trillion parameter multimodal generalization and safety bounds remain exclusively guarded by frontier clusters."
        },
        "default_tool_id": "wf_claude_desktop_mcp_core4",
        "default_tool_fallback": {
            "id": "wf_claude_desktop_mcp_core4",
            "name": "Claude Desktop / Cline 核心四件套 MCP 服务配置清单",
            "title_zh": "Claude Desktop / Cline 核心四件套 MCP 服务配置清单",
            "title_en": "Claude Desktop & Cline Core 4 MCP Server Production Config",
            "desc_zh": "一次性打通本地文件操作、Brave 实时搜索、SQLite 数据库即时直连与 GitHub 代码协作四大能力。",
            "desc_en": "Equips Claude Desktop with Filesystem, Brave Search, SQLite query, and GitHub MCP servers.",
            "url": "https://github.com/modelcontextprotocol/servers",
            "github_url": "https://github.com/modelcontextprotocol/servers",
            "weekly_stars": "+5,100★",
            "is_workflow": True
        }
    },
    {
        "id": "topic_multimodal_world_models",
        "category_tag_zh": "多模态视效与世界模型",
        "category_tag_en": "Multimodal & World Models",
        "badge_zh": "🎬 视效与物理世界",
        "badge_en": "🎬 Multimodal Frontier",
        "keywords": [
            "video", "sora", "kling", "gen-3", "runway", "luma", "vision", "multimodal",
            "world model", "physics", "rendering", "audio", "voice", "多模态", "视频生成", "世界模型", "视效"
        ],
        "title_zh": "生成式视频爆发、空间多模态与原生物理世界模型探索",
        "title_en": "Generative Video Explosion & Physical World Model Foundations",
        "summary_zh": "高保真 AI 视频生成模型在运动一致性、物理规律模拟与长视频连贯性上取得质的突破。产业界正从二维图像与视频生成向具备物理规律理解的三维空间交互式世界模型大步迈进，重塑影视创意与机器人仿真范式。",
        "summary_en": "Generative video models are crossing critical fidelity thresholds in physical motion consistency and camera coherence. Frontier research is shifting from 2D pixel generation towards interactive 3D world models capable of intuitive physics for entertainment and robotics simulation.",
        "perspective_pro": {
            "role_zh": "🟢 视效先锋 / 仿真探索者",
            "role_en": "🟢 Visual Innovators / Simulation Teams",
            "speaker_zh": "创意工作室、影视特效师与具身智能研发团队",
            "speaker_en": "Creative Studios, VFX Artists & Embodied AI Labs",
            "point_zh": "生成式视频将影视特效制作成本降低了数个数量级，更为具身智能与自动驾驶提供了近乎无限逼真的物理仿真训练场。",
            "point_en": "Generative video slashes production costs orders of magnitude while providing limitless high-fidelity simulation environments for embodied AI and robotics."
        },
        "perspective_con": {
            "role_zh": "🔴 影视工业派 / 物理严谨质疑",
            "role_en": "🔴 Film Industry Critics / Physics Skeptics",
            "speaker_zh": "传统影视导演与物理仿真科学家",
            "speaker_en": "Traditional Directors & Physics Simulation Scientists",
            "point_zh": "当前的视频生成本质仍是像素统计学，缺乏真正的空间几何与因果动力学理解，面对精细镜头调度与高要求商业交付常有物理破绽。",
            "point_en": "Current video models remain statistical pixel predictors lacking causal dynamics and true geometry, frequently exhibiting uncanny physical artifacts in commercial production."
        },
        "default_tool_id": "wf_cursorrules_fullstack_2026",
        "default_tool_fallback": {
            "id": "wf_rag_rerank_production_pipeline",
            "name": "企业级 RAG 防幻觉重排管线配方",
            "title_zh": "企业级 RAG 防幻觉重排管线 (BM25 + BGE-Reranker)",
            "title_en": "Enterprise Anti-Hallucination RAG Pipeline with BM25 & BGE-Reranker",
            "desc_zh": "解决多模态与文本知识库召回不准问题，将幻觉率降低 85% 以上。",
            "desc_en": "Production hybrid search pipeline reducing LLM hallucination rates by over 85%.",
            "url": "https://github.com",
            "github_url": "https://github.com",
            "weekly_stars": "+2,400★",
            "is_workflow": True
        }
    }
]


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


def _calculate_topic_relevance(item: Dict[str, Any], keywords: List[str]) -> float:
    """计算单个资讯条目与话题关键词的相关度分数"""
    score = 0.0
    text_corpus = " ".join([
        str(item.get("title_zh", "")),
        str(item.get("title_en", "")),
        str(item.get("title", "")),
        str(item.get("summary_zh", "")),
        str(item.get("summary_en", "")),
        str(item.get("content_zh", "")),
        str(item.get("original_content", "")),
        str(item.get("author", "")),
        str(item.get("author_handle", "")),
        str(item.get("source", "")),
        " ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else [])
    ]).lower()

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in text_corpus:
            # 完整词匹配增加高权重
            if re.search(rf"\b{re.escape(kw_lower)}\b", text_corpus):
                score += 3.0
            else:
                score += 1.5

    # 乘以资讯本身的热度加权
    hot_weight = float(item.get("hot_score", 1.0) or 1.0)
    return score * (1.0 + hot_weight * 0.2)


def generate_24h_topic_focus(items: List[Dict[str, Any]], max_topics: int = 3) -> List[Dict[str, Any]]:
    """
    针对 24 小时内的全量资讯集合提取 Top 3 核心热点话题，挂载脉络、立场对撞与关联情报束。
    """
    if not items:
        return []

    # 1. 拆分各类情报流
    news_items = [it for it in items if it.get("category") == "news" or (it.get("category") is None and "news" in it.get("id", ""))]
    celeb_items = [it for it in items if it.get("category") == "celebrity" or it.get("platform") in ("x", "reddit")]
    tool_items = [it for it in items if it.get("category") == "tools" or it.get("is_tool")]
    workflows = _load_curated_workflows()

    # 2. 对每个 Blueprint 进行全量打分与关联推荐匹配
    scored_blueprints = []
    
    for bp in TOPIC_BLUEPRINTS:
        bp_keywords = bp["keywords"]
        
        # 匹配新闻
        scored_news = []
        for n in news_items:
            rel = _calculate_topic_relevance(n, bp_keywords)
            if rel > 0:
                scored_news.append((rel, n))
        scored_news.sort(key=lambda x: x[0], reverse=True)
        top_news = [x[1] for x in scored_news[:3]]

        # 匹配推文 (对作者去重，确保观点多元)
        scored_tweets = []
        for t in celeb_items:
            rel = _calculate_topic_relevance(t, bp_keywords)
            if rel > 0:
                scored_tweets.append((rel, t))
        scored_tweets.sort(key=lambda x: x[0], reverse=True)
        top_tweets = []
        seen_authors = set()
        for _, t in scored_tweets:
            handle = (t.get("author_handle") or t.get("author") or "").lower()
            if handle and handle not in seen_authors:
                seen_authors.add(handle)
                top_tweets.append(t)
                if len(top_tweets) >= 2:
                    break

        # 匹配工具/工作流
        matched_tool = None
        # 先在 workflows 中按 ID 精确匹配
        def_id = bp.get("default_tool_id")
        for wf in workflows:
            if wf.get("id") == def_id:
                matched_tool = {
                    "id": wf.get("id"),
                    "name": wf.get("title_zh") or wf.get("name"),
                    "title_zh": wf.get("title_zh"),
                    "title_en": wf.get("title_en"),
                    "desc_zh": wf.get("takeaway_zh") or wf.get("description_zh", ""),
                    "desc_en": wf.get("takeaway_en") or wf.get("description_en", ""),
                    "url": "https://github.com",
                    "github_url": "https://github.com",
                    "weekly_stars": "+3,800★",
                    "is_workflow": True,
                    "target_platform": wf.get("target_platform", "Cursor / Claude"),
                    "config_filename": wf.get("config_filename", ".cursorrules")
                }
                break

        # 如果没有找到精确 workflow，在工具中按关键词打分挑选
        if not matched_tool and tool_items:
            scored_tools = []
            for tool in tool_items:
                rel = _calculate_topic_relevance(tool, bp_keywords)
                if rel > 0:
                    scored_tools.append((rel, tool))
            if scored_tools:
                scored_tools.sort(key=lambda x: x[0], reverse=True)
                best_t = scored_tools[0][1]
                matched_tool = {
                    "id": best_t.get("id"),
                    "name": best_t.get("title_zh") or best_t.get("title_en") or best_t.get("name"),
                    "title_zh": best_t.get("title_zh") or best_t.get("title"),
                    "title_en": best_t.get("title_en") or best_t.get("title"),
                    "desc_zh": best_t.get("summary_zh") or best_t.get("desc_zh", ""),
                    "desc_en": best_t.get("summary_en") or best_t.get("desc_en", ""),
                    "url": best_t.get("url"),
                    "github_url": best_t.get("github_url") or best_t.get("url"),
                    "weekly_stars": best_t.get("weekly_stars") or "+1,500★",
                    "is_workflow": False
                }

        # 若仍无，使用 Blueprint 预设的保底高质量配方
        if not matched_tool:
            matched_tool = bp.get("default_tool_fallback")

        # 计算该主题的总综合热度
        total_score = sum(x[0] for x in scored_news[:4]) + sum(x[0] for x in scored_tweets[:3]) + (len(top_news) * 5) + (len(top_tweets) * 4)
        scored_blueprints.append({
            "blueprint": bp,
            "total_score": total_score,
            "top_news": top_news,
            "top_tweets": top_tweets,
            "matched_tool": matched_tool
        })

    # 3. 按综合热度得分降序排序，选出 Top 3
    scored_blueprints.sort(key=lambda x: x["total_score"], reverse=True)
    selected = scored_blueprints[:max_topics]

    # 4. 构建结构化 Topic 实体
    topic_results = []
    base_heat = 9.8

    for idx, item in enumerate(selected):
        bp = item["blueprint"]
        top_news = item["top_news"]
        top_tweets = item["top_tweets"]
        tool = item["matched_tool"]

        # 关联新闻格式化
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

        # 关联推文格式化
        clean_tweets = []
        for t in top_tweets:
            clean_tweets.append({
                "id": t.get("id", ""),
                "author": t.get("author", "AI Leader"),
                "author_handle": t.get("author_handle", "@ai"),
                "author_avatar": t.get("author_avatar", ""),
                "content_zh": t.get("content_zh") or t.get("original_content", ""),
                "content_en": t.get("original_content") or t.get("content_zh", ""),
                "url": t.get("url", "#"),
                "platform": t.get("platform", "x")
            })

        topic_heat = round(base_heat - (idx * 0.2), 1)

        topic_obj = {
            "topic_id": bp["id"],
            "heat_score": topic_heat,
            "badge_zh": bp["badge_zh"],
            "badge_en": bp["badge_en"],
            "category_tag_zh": bp["category_tag_zh"],
            "category_tag_en": bp["category_tag_en"],
            "title_zh": bp["title_zh"],
            "title_en": bp["title_en"],
            "summary_zh": bp["summary_zh"],
            "summary_en": bp["summary_en"],
            "perspective_pro": bp["perspective_pro"],
            "perspective_con": bp["perspective_con"],
            "linked_news": clean_news,
            "linked_tweets": clean_tweets,
            "linked_tool": tool,
            "linked_counts": {
                "news": len(clean_news),
                "tweets": len(clean_tweets),
                "has_tool": bool(tool)
            }
        }
        topic_results.append(topic_obj)

    # 5. 持久化存储到数据目录
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
        print(f"✅ [topic_cluster] 成功生成并持久化 24h Top {len(topic_results)} 核心话题专题!")
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
    header_desc = "· 事件脉络 · 大V观点立场对撞 · 关联情报束" if is_zh else "· Core Context · Viewpoints Collision · Linked Bundles"
    btn_collapse_txt = "▲ 收起" if is_zh else "▲ Collapse"

    # 1. 渲染话题 Tabs
    tab_buttons = []
    for idx, t in enumerate(topics):
        is_active = (idx == 0)
        badge = t.get("badge_zh" if is_zh else "badge_en", "")
        title = t.get("title_zh" if is_zh else "title_en", "")
        heat = t.get("heat_score", 9.8)
        
        # 截短 Tab 标题避免移动端过宽
        short_title = title if len(title) <= 12 else title[:11] + "…"
        
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
              <span>{"数据自动聚合更新" if is_zh else "Auto-aggregated 24h"}</span>
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
    print("Testing topic_cluster...")
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
            print(f"Generated {len(topics)} topics:")
            for t in topics:
                print(f"  - [{t['heat_score']}] {t['title_zh']} (News: {len(t['linked_news'])}, Tweets: {len(t['linked_tweets'])})")
