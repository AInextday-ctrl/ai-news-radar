#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Radar 2.0 - 统一动态知识图谱与自适应标签学习引擎 (Unified AI Knowledge Base & Dynamic Tag Engine)
=================================================================================================
核心职责：
1. 单一事实源 (SSOT): 全局共享 `data/knowledge_graph.json`，服务于爬虫(Apify/X)、评分质检(微信引擎)、分析过滤。
2. 全生命周期状态机: 自动追踪模型与实体演进 (ACTIVE_SOTA vs DEPRECATED)，自动挂载上位替代，坚决淘汰旧版本 (如 Claude 3.7/GPT-4)。
3. 自主动态学习 (Self-Learning): 从全网最新快讯、天梯榜 (LMSYS Arena) 与社交爆帖中自动发现新版本与飙升标签。
4. 动态检索生成器 (Query Generator): 根据当前活跃 SOTA 实体与飙升标签，自适应生成 𝕏 / Apify 深度搜索式，彻底取代死板的静态字符串。
"""

import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "public", "data")
KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge_graph.json")
PUBLIC_KNOWLEDGE_FILE = os.path.join(PUBLIC_DATA_DIR, "knowledge_graph.json")


class DynamicKnowledgeStore:
    _data = None

    @classmethod
    def load(cls) -> Dict[str, Any]:
        if cls._data is not None:
            return cls._data
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    cls._data = json.load(f)
                    return cls._data
            except Exception as e:
                print(f"⚠️ [Knowledge Base] 加载异常: {e}")
        cls._data = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "system_description": "开放式实体动态知识图谱与全生命周期状态机 (Open Entity Knowledge Graph & Lifecycle State Machine)",
            "entities": {},
            "trending_tags": {}
        }
        return cls._data

    @classmethod
    def save(cls):
        if not cls._data:
            return
        cls._data["updated_at"] = datetime.now(timezone.utc).isoformat()
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
        try:
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._data, f, ensure_ascii=False, indent=2)
            with open(PUBLIC_KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ [Knowledge Base] 保存异常: {e}")

    @classmethod
    def get_active_sota_models(cls) -> List[str]:
        """提取全量处于 ACTIVE_SOTA 活跃生命周期的前沿大模型与关键代际"""
        data = cls.load()
        active_list = []
        for e_id, e_info in data.get("entities", {}).items():
            for v_obj in e_info.get("versions", []):
                if v_obj.get("lifecycle_status") == "ACTIVE_SOTA":
                    v_str = str(v_obj.get("version", "")).strip()
                    clean_id = e_id.replace("_", " ").title()
                    if re.match(r'^\d+(\.\d+)?$', v_str):
                        active_list.append(f"{clean_id} {v_str}")

        # 结合当前天梯榜最新顶尖代表 (SOTA 系列，严格过滤过时废弃版本如 Claude 3.7)
        sota_presets = [
            "Claude Fable 5.1", "Claude Opus 5.5", "Claude Sonnet 5.5",
            "GPT 6 Astra", "GPT 6 Sol", "GPT 5.6 Sol", "GPT 6 Luna",
            "DeepSeek-V4.1", "DeepSeek-V4", "GLM 5.3 Flash", "Step 5",
            "Gemini 2.5", "Grok 3.5", "FLUX.2", "Kling 3.0", "Wan 2.5"
        ]
        combined = list(dict.fromkeys(active_list + sota_presets))
        # 严格过滤掉已废弃的历史旧代模型 (如 Claude 3.7, Claude 3.5, GPT-4 等)
        deprecated_tokens = ["3.7", "3.5", "gpt-4", "gpt 4", "midjourney v5"]
        final_models = [m for m in combined if not any(dep in m.lower() for dep in deprecated_tokens)]
        return [m for m in final_models if m and len(m) >= 3]

    @classmethod
    def get_dynamic_trending_queries(cls) -> List[str]:
        """
        自适应生成 𝕏 / Apify 检索式。
        完全依托知识库中的 ACTIVE_SOTA 状态动态拼装，绝不硬编码过时模型 (如 Claude 3.7 已被自动废弃淘汰)。
        """
        data = cls.load()
        active_tags = data.setdefault("trending_tags", {})

        # 1. 核心高热前沿技术标签池 (支持根据真实频次动态更新)
        default_tags = ["AI", "LLM", "GenerativeAI", "GenAI", "ClaudeCode", "Cursor", "DeepSeek", "VibeCoding", "AIAgent", "PromptEngineering", "ComfyUI", "FLUX"]
        top_tags = sorted(active_tags.keys(), key=lambda t: active_tags[t].get("count", 0), reverse=True)[:10]
        merged_tags = list(dict.fromkeys(top_tags + default_tags))[:12]

        tag_query_1 = " OR ".join([f"%23{t}" if not t.startswith("#") else t.replace("#", "%23") for t in merged_tags[:6]])
        tag_query_2 = " OR ".join([f"%23{t}" if not t.startswith("#") else t.replace("#", "%23") for t in merged_tags[6:12]])

        # 2. 从知识图谱动态提取最新 SOTA 模型通配
        sota_models = cls.get_active_sota_models()
        clean_model_terms = []
        for m in sota_models[:10]:
            clean = m.replace('"', '').strip()
            if " " in clean:
                clean_model_terms.append(f'"{clean}"')
            else:
                clean_model_terms.append(clean)
        models_subquery = " OR ".join(clean_model_terms[:8]) if clean_model_terms else '"Claude Opus 5.5" OR "GPT 6" OR "DeepSeek-V4"'

        # 3. 架构突破与工程范式
        breakthrough_subquery = '"Claude Code" OR "Cursor reset" OR "Codex reset" OR "vibe coding" OR "AI agent" OR "test-time compute"'

        return [
            f"({tag_query_1}) (min_faves:50 OR min_retweets:10)",
            f"({tag_query_2}) (min_faves:30 OR min_retweets:5)",
            f"({models_subquery}) (min_faves:30)",
            f"({breakthrough_subquery}) (min_faves:25)"
        ]

    @classmethod
    def get_or_learn_entity(cls, entity_id: str, display_name: str, context_text: str, detected_version: Optional[str] = None) -> Dict[str, Any]:
        """JIT 实体冷启动与即时自学入库"""
        data = cls.load()
        entities = data.setdefault("entities", {})
        clean_id = entity_id.lower().strip().replace(" ", "_").replace("-", "_")

        now_str = datetime.now(timezone.utc).isoformat()
        today_date = datetime.now().strftime("%Y-%m-%d")

        if clean_id not in entities:
            lower_ctx = context_text.lower()
            if any(k in lower_ctx for k in ["video", "sora", "kling", "wan", "视频生成", "帧率"]):
                domain = "video_generation"
                half_life = 120
            elif any(k in lower_ctx for k in ["code", "coding", "cursor", "claude code", "编程", "重构"]):
                domain = "ai_coding_developer_tools"
                half_life = 120
            elif any(k in lower_ctx for k in ["robot", "embodied", "具身", "机械臂", "人形"]):
                domain = "embodied_robotics"
                half_life = 180
            elif any(k in lower_ctx for k in ["audio", "voice", "speech", "语音", "全双工"]):
                domain = "voice_speech"
                half_life = 150
            elif any(k in lower_ctx for k in ["protein", "bio", "alphafold", "分子", "生物"]):
                domain = "bio_computing"
                half_life = 240
            elif any(k in lower_ctx for k in ["chip", "gpu", "lpu", "算力", "芯片", "硬件"]):
                domain = "ai_hardware"
                half_life = 200
            else:
                domain = "llm_reasoning"
                half_life = 180

            v = detected_version or "1.0"
            new_entity = {
                "id": clean_id,
                "display_name": display_name,
                "domain_tag": domain,
                "half_life_days": half_life,
                "first_learned_at": now_str,
                "last_updated_at": now_str,
                "active_version": v,
                "versions": [
                    {
                        "version": v,
                        "release_date": today_date,
                        "lifecycle_status": "ACTIVE_SOTA",
                        "superseded_by": None,
                        "benchmark_highlights": f"最新一代 {display_name} 前沿架构与落地实践"
                    }
                ]
            }
            entities[clean_id] = new_entity
            cls.save()
            print(f"🌱 [Knowledge Base 自主学习] 发现新实体: {display_name} (v{v} · {domain}) 已入库！")
            return new_entity
        else:
            entity = entities[clean_id]
            if detected_version:
                cls.ingest_version_update(clean_id, detected_version, context_text)
            return entity

    @classmethod
    def ingest_version_update(cls, entity_id: str, new_version: str, context_text: str = ""):
        """版本跃迁：自动将历史版本标记为 DEPRECATED 废弃并挂载上位替代"""
        data = cls.load()
        entities = data.setdefault("entities", {})
        clean_id = entity_id.lower().strip().replace(" ", "_").replace("-", "_")
        if clean_id not in entities:
            return

        entity = entities[clean_id]
        cur_v_str = str(entity.get("active_version", "1.0"))

        def parse_v(s):
            m = re.findall(r'\d+(?:\.\d+)?', str(s))
            return float(m[0]) if m else 0.0

        if parse_v(new_version) > parse_v(cur_v_str):
            today_date = datetime.now().strftime("%Y-%m-%d")
            for ver_obj in entity.get("versions", []):
                if ver_obj.get("lifecycle_status") == "ACTIVE_SOTA":
                    ver_obj["lifecycle_status"] = "DEPRECATED"
                    ver_obj["superseded_by"] = new_version
                    ver_obj["deprecation_warning"] = f"存在上位替代: {new_version} 已上线，旧版 {ver_obj.get('version')} 严禁作为当前主流横评标杆"

            entity.setdefault("versions", []).append({
                "version": new_version,
                "release_date": today_date,
                "lifecycle_status": "ACTIVE_SOTA",
                "superseded_by": None,
                "benchmark_highlights": f"新晋跃迁版本 {new_version}，性能与时效处于当前黄金期"
            })
            entity["active_version"] = new_version
            entity["last_updated_at"] = datetime.now(timezone.utc).isoformat()
            cls.save()
            print(f"🚀 [Knowledge Base 版本跃升] {entity.get('display_name')} 跃升至 v{new_version} (历史版 v{cur_v_str} 已自动标记为 DEPRECATED 淘汰！)")

    @classmethod
    def learn_from_feed_items(cls, items: List[Dict[str, Any]], arena_models: Optional[List[Dict[str, Any]]] = None):
        """
        从最新资讯流、天梯榜与热推中自主学习前沿标签与模型演进。
        每一次定时流水线运行均自动调用本方法，确保知识库永久鲜活。
        """
        data = cls.load()
        tags_store = data.setdefault("trending_tags", {})
        entities = data.setdefault("entities", {})
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. 扫描 LMSYS Chatbot Arena 权威榜单，自动更新 SOTA 模型版本
        if arena_models and isinstance(arena_models, list):
            for model_info in arena_models:
                m_name = model_info.get("model", "")
                m_score = model_info.get("arena_score", 0)
                if not m_name:
                    continue
                # 解析品牌与版本号
                if "claude" in m_name.lower():
                    v_match = re.search(r'(\d+(?:\.\d+)?)', m_name)
                    if v_match:
                        cls.get_or_learn_entity("claude", "Anthropic Claude 系列模型", m_name, detected_version=v_match.group(1))
                elif "gpt" in m_name.lower():
                    v_match = re.search(r'gpt[- ]?(\d+(?:\.\d+)?)', m_name, re.I)
                    if v_match:
                        cls.get_or_learn_entity("gpt", "OpenAI GPT 系列模型", m_name, detected_version=v_match.group(1))
                elif "deepseek" in m_name.lower():
                    v_match = re.search(r'(?:v|r)?(\d+(?:\.\d+)?)', m_name, re.I)
                    if v_match:
                        cls.get_or_learn_entity("deepseek", "DeepSeek 系列开源模型", m_name, detected_version=v_match.group(1))

        # 2. 扫描快讯与推文标题提取高频热门标签与新型实体
        for it in items:
            title = f"{it.get('title', '')} {it.get('title_zh', '')} {it.get('title_en', '')}".strip()
            if not title:
                continue

            # 提取 #Hashtag 标签
            hashtags = re.findall(r'#([a-zA-Z0-9_\u4e00-\u9fa5]{2,20})', title)
            for raw_tag in hashtags:
                clean_tag = raw_tag.strip()
                if clean_tag.lower() in ["ai", "news", "today", "update", "breaking"]:
                    continue
                if clean_tag not in tags_store:
                    tags_store[clean_tag] = {"count": 1, "first_seen": now_iso, "last_seen": now_iso}
                else:
                    tags_store[clean_tag]["count"] = tags_store[clean_tag].get("count", 0) + 1
                    tags_store[clean_tag]["last_seen"] = now_iso

            # 探测模型跃迁版本
            for brand, brand_name in [("claude", "Anthropic Claude"), ("gpt", "OpenAI GPT"), ("deepseek", "DeepSeek"), ("kling", "快手可灵 Kling"), ("wan", "通义 Wan")]:
                m_ver = re.search(rf'\b{brand}\b[ -]?(?:v)?(\d+(?:\.\d+)?)', title, re.I)
                if m_ver:
                    v_str = m_ver.group(1)
                    cls.ingest_version_update(brand, v_str, title)

        cls.save()
        print(f"🧠 [Knowledge Base 持续学习] 学习完毕: 当前掌握 {len(entities)} 类核心前沿实体，追踪 {len(tags_store)} 组全网动态标签。")

    @classmethod
    def scan_and_learn_from_text(cls, text: str):
        if not text:
            return
        lower = text.lower()
        data = cls.load()
        for e_id, e_info in data.get("entities", {}).items():
            kw = e_id.replace("_", " ")
            m = re.findall(rf'{kw}\s*(?:v)?(\d+(?:\.\d+)?)', lower)
            for v_str in m:
                cls.ingest_version_update(e_id, v_str, text)

        potential_entities = [
            ("seadance", "SeaDance 动作视频生成模型", [r'\b(seadance|sea\s*dance)\b']),
            ("figure", "Figure 具身智能机器人", [r'\b(figure\s*0[1-9]|figure\s*robot)\b']),
            ("alphafold", "AlphaFold 蛋白质结构大模型", [r'\b(alphafold\s*[1-9]?)\b']),
            ("animateanyone", "AnimateAnyone 人物动作驱动模型", [r'\b(animateanyone)\b']),
            ("groq_lpu", "Groq LPU 极速推理芯片", [r'\b(groq\s*lpu|groq)\b']),
        ]
        for ent_id, ent_name, patterns in potential_entities:
            for pat in patterns:
                m_match = re.search(pat, lower)
                if m_match:
                    m_v = re.findall(rf'{pat}\s*(?:v)?(\d+(?:\.\d+)?)', lower)
                    v = m_v[0] if m_v else "1.0"
                    cls.get_or_learn_entity(ent_id, ent_name, text, detected_version=v)

    @classmethod
    def audit_text_freshness(cls, text: str) -> Dict[str, Any]:
        """全量知识生命周期与时效审计门禁"""
        data = cls.load()
        entities = data.get("entities", {})
        lower_text = text.lower()

        deprecated_violations = []
        active_confirmations = []

        historical_qualifiers = ["历史", "回顾", "早年", "昔日", "初代", "溯源", "历程", "过去", "发展史", "淘汰", "早已过时"]
        has_historical_context = any(q in lower_text for q in historical_qualifiers)

        for e_id, e_info in entities.items():
            name_kw = e_info.get("display_name", "").lower()
            e_kw = e_id.replace("_", " ")

            for ver_obj in e_info.get("versions", []):
                v_str = ver_obj.get("version", "")
                status = ver_obj.get("lifecycle_status", "")

                patterns = [
                    f"{e_kw} {v_str}",
                    f"{e_kw} v{v_str}",
                    f"{e_kw}-{v_str}",
                    f"{e_kw}v{v_str}"
                ]
                hit = any(p in lower_text for p in patterns)

                if hit:
                    if status in ["DEPRECATED", "HISTORICAL_BENCHMARK"]:
                        if not has_historical_context:
                            deprecated_violations.append({
                                "entity": e_info.get("display_name"),
                                "version": v_str,
                                "status": status,
                                "superseded_by": ver_obj.get("superseded_by"),
                                "warning": ver_obj.get("deprecation_warning")
                            })
                    elif status == "ACTIVE_SOTA":
                        active_confirmations.append({
                            "entity": e_info.get("display_name"),
                            "version": v_str,
                            "status": status
                        })

        if deprecated_violations:
            penalty = 15
            passed = False
            reasons = [f"使用了已废弃版本【{v['entity']} v{v['version']}】，上位替代为【v{v['superseded_by']}】" for v in deprecated_violations]
            summary = "❌ 触发时效性断代违规：" + "；".join(reasons)
        else:
            penalty = 0
            passed = True
            if active_confirmations:
                actives = [f"{a['entity']} v{a['version']}" for a in active_confirmations]
                summary = f"✅ 通过时效性生命周期审计：所引用的前沿实体（{', '.join(actives[:3])}）均处于 ACTIVE_SOTA 活跃生命周期！"
            else:
                summary = "✅ 通过时效性生命周期审计：无过期废弃版本干扰。"

        return {
            "passed": passed,
            "deprecated_violations": deprecated_violations,
            "active_confirmations": active_confirmations,
            "penalty": penalty,
            "summary": summary
        }


# 便捷导出单例方法
get_dynamic_trending_queries = DynamicKnowledgeStore.get_dynamic_trending_queries
get_active_sota_models = DynamicKnowledgeStore.get_active_sota_models
learn_from_feed_items = DynamicKnowledgeStore.learn_from_feed_items
load_knowledge_graph = DynamicKnowledgeStore.load
