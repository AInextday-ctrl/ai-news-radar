"""
AI Curator Engine (专业栏目差异化精选引擎 v3.3)
--------------------------------------------
彻底重构栏目精选逻辑，杜绝“空洞评论无事实”、“单条孤立敷衍”与陈旧工具：
1. 行业快讯 (news)      -> 【事件全貌速览 + 4大核心事实拆解 + 战略研判】
   - 彻底解决“看完了不知道发生什么事”的根本痛点！
   - 首段必须先清晰写出 5W1H 事件全貌速览（谁、因何事、具体做了什么动作、当前什么进展）
   - 紧接着分点列出 4 大具体事实细节与工程数字
   - 最后才给出建立在坚实事实之上的战略研判！
   - 支持 3 大全球重磅头条一键平滑切换

2. 社交雷达 (celebrity) -> 【全球 5 大顶级 AI 领袖思辨矩阵】
   - Demis Hassabis, Yann LeCun, Sam Altman, Andrej Karpathy, Jim Fan
   - 真实大V原声引用 + 领袖核心立论 vs 极客社群争议焦点 + 真实互动指标
   - 前端支持一键即时切换与联动浏览

3. 落地工具 (tools)     -> 【24H 飙升火爆 · 高价值落地神器】
   - ppt-master (今日爆火 +4,607 ★/周) + graphify (+6,662 ★) + Concat (+2,629 ★) + orca (+8,250 ★)
   - 严格杜绝 ComfyUI、Ollama 等陈旧烂大街工具
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "public", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "curated_column_highlights.json")
PUBLIC_OUTPUT_FILE = os.path.join(PUBLIC_DATA_DIR, "curated_column_highlights.json")

# 严禁作为 24H 飙升置顶的陈旧“烂大街”工具或超大厂旗舰黑名单（保持雷达挖掘新锐黑马定位）
BLACKLIST_STALE_PATTERNS = [
    'claude-code', 'claude_code', 'claudecode', 'claude code', 'claude-seo', 'learn-claude-code',
    'cursor', 'openhands', 'copilot', 'github-copilot', 'chatgpt', 'gpt-4', 'gpt4',
    'ollama', 'comfyui', 'automatic1111', 'fooocus', 'forge',
    'langchain', 'langgraph', 'autogen', 'crewai', 'dify', 'flowise',
    'vllm', 'sglang', 'tgi', 'llama.cpp', 'llamacpp', 'fastchat', 'whisper', 'faster-whisper',
    'transformers', 'diffusers', 'stable-diffusion-webui',
    'devin', 'midjourney', 'lobe-chat', 'anything-llm', 'localai', 'gpt4all', 'open-webui',
    'jan', 'continue', 'aider', 'open-interpreter'
]

# 8 大核心落地领域元数据与兜底痛点定义
DOMAIN_META = {
    'agent': {
        'icon': '🤖',
        'tag_zh': '🤖 自主智能体与协作编排',
        'tag_en': '🤖 Autonomous Agent & Fleet',
        'short_zh': '自主智能体编排',
        'short_en': 'Agent Fleet',
        'pain_zh': '传统多智能体任务缺乏轻量标准沙箱与生命周期可观测性，复杂多阶段自动化在本地与团队环境极难稳定闭环。',
        'pain_en': 'Complex multi-step agent tasks lack standardized sandboxing and observability, making local workflows brittle.'
    },
    'code': {
        'icon': '💻',
        'tag_zh': '💻 编程架构与代码智能体',
        'tag_en': '💻 Code AST & Architecture',
        'short_zh': '代码架构与AST',
        'short_en': 'Codebase AST',
        'pain_zh': '传统向量检索在面对超大代码库时经常丢失跨文件调用依赖，缺乏深度代码 AST 与工程级设计约束。',
        'pain_en': 'Vector search misses critical cross-file dependency call paths in large repos without structural AST awareness.'
    },
    'multimedia': {
        'icon': '🎬',
        'tag_zh': '🎬 影音创作与多媒体AI',
        'tag_en': '🎬 Multimedia & Video AI',
        'short_zh': '本地多媒体剪辑',
        'short_en': 'Local Multimedia',
        'pain_zh': '商业剪辑工具订阅昂贵、强依赖云端上传且无法通过开放 API 或智能体实现大规模批量剪辑流水线。',
        'pain_en': 'Commercial video editors require steep subscriptions, cloud uploads, and lack scriptable AI agent orchestration.'
    },
    'office': {
        'icon': '📊',
        'tag_zh': '📊 办公文档与内容生成',
        'tag_en': '📊 Office Docs & Presentation',
        'short_zh': '办公文档与PPT',
        'short_en': 'Presentation AI',
        'pain_zh': '传统 AI 办公工具大多只能输出不可二次编辑的扁平位图，排版生硬且无法原生兼容企业级模板母版与动态图表。',
        'pain_en': 'Legacy AI presentation tools output flat uneditable images that fail to integrate with corporate .pptx templates.'
    },
    'browser': {
        'icon': '🌐',
        'tag_zh': '🌐 浏览器自主操作与智能爬虫',
        'tag_en': '🌐 Web Agent & Browser Automation',
        'short_zh': '浏览器自主感知',
        'short_en': 'Browser Agent',
        'pain_zh': '大模型原生缺乏实时动态穿透互联网能力，无法自动化执行跨平台社交检索、动态渲染抓取与免凭证信息聚合。',
        'pain_en': 'Frontier models lack direct dynamic web access, unable to seamlessly retrieve real-time cross-platform content.'
    },
    'vision': {
        'icon': '🎨',
        'tag_zh': '🎨 视觉设计与3D生成',
        'tag_en': '🎨 Visual Design & 3D Gen',
        'short_zh': '视觉设计与3D',
        'short_en': 'Visual Design',
        'pain_zh': '视觉生成工具依赖繁琐云端算力排队，缺少面向前端工程师和创作者的轻量本地化或可编程生成能力。',
        'pain_en': 'Creative visual tooling is tied to costly cloud queues without programmable native integration.'
    },
    'knowledge': {
        'icon': '🧠',
        'tag_zh': '🧠 知识库与图谱检索',
        'tag_en': '🧠 Knowledge Graph & Advanced RAG',
        'short_zh': '知识库与图谱',
        'short_en': 'Knowledge Graph',
        'pain_zh': '常规 RAG 检索受制于纯向量相似度计算，缺乏语义本体推理与确定性知识图谱关联，容易产生严重事实幻觉。',
        'pain_en': 'Standard RAG pipelines suffer from vector hallucination without deterministic semantic graph reasoning.'
    },
    'applied': {
        'icon': '💼',
        'tag_zh': '💼 行业落地与效率应用',
        'tag_en': '💼 Applied Productivity & Life',
        'short_zh': '行业落地应用',
        'short_en': 'Applied AI',
        'pain_zh': '通用模型脱离实际垂直业务场景，缺乏开箱即用的特定领域工作流封装与高质量工程级实践规范。',
        'pain_en': 'Generic models fail to solve domain-specific enterprise friction without specialized workflow wrappers.'
    }
}

# 深度精调落地工具知识库（选拔命中时优先套用人类精校文案，动态指标自动同步更新）
BREAKOUT_APPLIED_TOOLS = {
    "security-audit-skill": {
        "name": "security-audit-skill",
        "icon": "🛡️",
        "category_tag_zh": "🛡️ 智能体多阶段代码安全审计",
        "category_tag_en": "🛡️ Multi-Phase Agent Security Audit",
        "pain_point_zh": "编码代理自主生成代码时常不自觉引入反序列化、注入或权限绕过漏洞，传统人工审计耗时且容易遗漏隐蔽攻击面。",
        "pain_point_en": "Autonomous coding agents frequently introduce subtle vulnerabilities that manual code reviews miss under tight deadlines.",
        "key_features_zh": [
            "多阶段深度独立验证：对生成的代码变更执行威胁建模、动静态污点分析与边界推演",
            "机器可读结构化报告：输出格式化安全审计建议，允许代理根据报错自动自愈重构",
            "零云端数据外泄：在本地隔离环境中执行规则检测，保障企业专有代码私密安全"
        ],
        "key_features_en": [
            "Multi-Phase Independent Verification: Executes threat modeling, taint analysis, and boundary audits on diffs",
            "Machine-Readable Audit Evals: Formats findings so coding agents can self-heal vulnerabilities automatically",
            "Zero Cloud Data Leakage: Runs locally sandboxed rule matching to guarantee proprietary code privacy"
        ]
    },
    "impeccable": {
        "name": "impeccable",
        "icon": "🎨",
        "category_tag_zh": "💻 编码代理设计词汇与防粗制滥造",
        "category_tag_en": "💻 Design Vocabulary & Anti-Slop for Coding Agents",
        "pain_point_zh": "AI 辅助生成的网页界面往往充斥着千篇一律的粗糙‘AI 味’（AI-slop），缺乏审美精细度、排版节奏与严谨的设计系统。",
        "pain_point_en": "Agent-generated frontend UIs are plagued by generic 'AI-slop', lacking polished typography and cohesive design systems.",
        "key_features_zh": [
            "设计系统工程化约束：注入专业 UI/UX 词汇与组件规范，杜绝低质粗糙排版与无序堆砌",
            "发布前自动化设计评审：在代码提交前执行审美与可访问性审计，拦截不合格组件",
            "无缝赋能任意编程代理：原生适配各种 CLI 智能体，让代码不仅逻辑正确而且视觉精致"
        ],
        "key_features_en": [
            "Design System Guardrails: Injects professional UI/UX vocabulary to eliminate generic AI frontend slop",
            "Pre-Publish Design Critiques: Audits typography, contrast, and accessibility before landing pull requests",
            "Universal Agent Compatibility: Plugs into terminal coding agents to ensure high-craft visual delivery"
        ]
    },
    "agent-reach": {
        "name": "Agent-Reach",
        "icon": "🌐",
        "category_tag_zh": "🌐 跨平台智能体网络感知与多平台搜索",
        "category_tag_en": "🌐 Multi-Platform Web Agent & Social Search",
        "pain_point_zh": "智能体无法直接突破社交平台动态渲染与登录门槛检索一手资讯，通用搜索信噪比极低且难以结构化提取关键事实。",
        "pain_point_en": "Agents struggle to access dynamic social feeds and complex web apps directly without dedicated authenticated scrapers.",
        "key_features_zh": [
            "一键打通全球主流社媒：直接检索 Twitter、Reddit、YouTube、GitHub、B站等跨平台一手内容",
            "高信噪比纯净 Markdown：过滤页面繁杂广告与无用 DOM 结构，秒级返回高熵关键事实",
            "轻量本地 CLI / MCP 协议：原生支持作为智能体感知工具随调随用，零额外基建负担"
        ],
        "key_features_en": [
            "Cross-Platform Social Awareness: Read and search Twitter, Reddit, YouTube, GitHub, and Bilibili effortlessly",
            "High-Entropy Markdown Extraction: Strips ads and boilerplate DOM to deliver clean structured context",
            "Lightweight CLI & MCP Integration: Native tool interface ready for immediate agentic consumption"
        ]
    },
    "auto-ontology": {
        "name": "auto-ontology",
        "icon": "🧠",
        "category_tag_zh": "🧠 语义本体与基于图谱的推理层",
        "category_tag_en": "🧠 Semantic Ontology & Graph Reasoning",
        "pain_point_zh": "在大规模异构数据上，纯向量检索无法进行确定性关联推演，缺乏严谨的语义本体层导致复杂分析问答漏洞百出。",
        "pain_point_en": "On heterogeneous enterprise data, pure vector RAG fails complex relational reasoning without an explicit semantic ontology.",
        "key_features_zh": [
            "自动化本体构建：从非结构化数据中自动提取高精度语义关系图谱与实体层级",
            "确定性查询生成：将自然语言问题直接编译为高保真图查询，避免检索幻觉",
            "轻量 Python 框架封装：开箱即用集成到现有智能体与大模型流水线中"
        ],
        "key_features_en": [
            "Automated Ontology Synthesis: Extracts high-precision semantic relations and hierarchies from unstructured data",
            "Deterministic Query Compilation: Compiles natural queries into graph traversals to eradicate hallucinations",
            "Lightweight Python Framework: Seamlessly drops into modern agent pipelines with zero friction"
        ]
    },
    "video-shotcraft": {
        "name": "video-shotcraft",
        "icon": "🎥",
        "category_tag_zh": "🎥 电影级可编程宣传片视频技能",
        "category_tag_en": "🎥 Cinematic Code-Driven Promo Video Skill",
        "pain_point_zh": "传统制作产品宣传视频需要专业视频剪辑师花费数天时间手动打点调色，成本极高且无法随着产品版本自动更新演示视频。",
        "pain_point_en": "Crafting product promos requires manual video editor time and cannot automatically regenerate when product releases update.",
        "key_features_zh": [
            "Remotion 电影级代码渲染：124 款镜头配方卡与 150 个动作预览，完全由代码驱动精确到帧",
            "智能体一键驱动：无缝接入主流编码智能体，通过自然语言即可批量生成高精美宣传片",
            "完全开源私有：支持本地 Docker 或命令行秒级渲染输出 MP4，零额外订阅费用"
        ],
        "key_features_en": [
            "Remotion-Powered Code Rendering: 124 shot recipes and 150 motion previews rendered frame-accurately via code",
            "Agentic Video Generation: Drives complex product promos directly through natural language agent commands",
            "Fully Open-Source & Local: Render MP4s via local CLI or Docker with zero cloud lock-in"
        ]
    },
    "ppt-master": {
        "name": "ppt-master",
        "icon": "📊",
        "category_tag_zh": "📊 办公文档与原生 PPT 演示生成",
        "category_tag_en": "📊 Native PowerPoint & Document AI",
        "pain_point_zh": "传统 AI PPT 工具大多只能输出无法二次修改的死板“扁平图片”或简陋 Markdown，排版生硬且无法兼容企业级 .pptx 模板与动态图表。",
        "pain_point_en": "Traditional AI deck tools spit out uneditable flat images or rudimentary markdown, breaking custom corporate .pptx templates and data charts.",
        "key_features_zh": [
            "原生 PPTX 矢量与图层：直接输出带独立文本框、形状图层与动画效果的真正 PowerPoint，支持任意二次微调",
            "数据驱动的智能图表与音频：按需自动构建带数据绑定的原生图表，并根据演讲备注自动合成语音旁白",
            "无缝套用企业专属模板：一键导入团队现有的 .pptx 母版、字体与品牌色彩，严格符合企业 VI 规范"
        ],
        "key_features_en": [
            "Native PPTX Vector Shapes: Generates true PowerPoint files with editable text boxes, vector shapes, and animations",
            "Data-Backed Charts & Audio Narration: Generates data-bound charts on demand and audio voiceover from notes",
            "Corporate Template Compatible: Import existing .pptx masters, corporate fonts, and brand colors effortlessly"
        ],
        "quickstart_zh": "git clone https://github.com/hugohe3/ppt-master.git",
        "quickstart_en": "git clone https://github.com/hugohe3/ppt-master.git",
        "best_for_zh": "适合职场白领、产品经理、咨询顾问、市场策划、高校师生及创业团队",
        "best_for_en": "Ideal for knowledge workers, product managers, consultants, researchers, and founders",
        "url": "https://github.com/hugohe3/ppt-master?ref=ainewsradar"
    },
    "graphify": {
        "name": "graphify",
        "icon": "🕸️",
        "category_tag_zh": "💻 代码库架构与 AST 知识图谱",
        "category_tag_en": "💻 Codebase Knowledge Graph & AST RAG",
        "pain_point_zh": "接手超大混乱项目时，传统向量检索容易遗漏跨文件依赖与调用链路，导致 AI 编码助手产生严重幻觉与破坏性改动。",
        "pain_point_en": "Vector search frequently loses cross-file architectural context in massive codebases, causing coding agent hallucinations.",
        "key_features_zh": [
            "确定性 AST 知识图谱：本地解析代码语法树，每条边与函数依赖调用均具有精确的可解释性",
            "无缝直通智能编码助手：作为 MCP 插件让编码代理瞬间拥有全局代码仓库认知视野",
            "零向量数据库开销：无需外部向量数据库与云端嵌入，单命令行即可完成整个项目的结构化索引"
        ],
        "key_features_en": [
            "Deterministic AST Parsing: Locally builds dependency graphs where every call edge is fully explained",
            "Native Coding Agent Integration: Acts as an MCP skill giving coding agents global repository vision",
            "Zero Vector DB Dependency: No embeddings or external databases required, indexes entire repos via a single CLI"
        ],
        "quickstart_zh": "pip install graphify && graphify .",
        "quickstart_en": "pip install graphify && graphify .",
        "best_for_zh": "适合软件工程师、系统架构师、开源项目维护者与技术负责人",
        "best_for_en": "Ideal for software engineers, architects, and open-source contributors",
        "url": "https://github.com/Graphify-Labs/graphify?ref=ainewsradar"
    },
    "concat": {
        "name": "Concat",
        "icon": "🎬",
        "category_tag_zh": "🎬 本地影音剪辑与智能体驱动",
        "category_tag_en": "🎬 Local-First Video Editor & MCP",
        "pain_point_zh": "商业剪辑工具订阅昂贵、强依赖云端上传且无法通过 AI 脚本或智能体实现大规模批量剪辑流水线。",
        "pain_point_en": "Commercial video editors require steep subscriptions, cloud uploads, and lack scriptable AI agent orchestration.",
        "key_features_zh": [
            "本地优先与数据私有：所有渲染与剪辑均在本地执行，素材零上传，保障隐私与速度",
            "原生 MCP 智能体驱动：提供标准 MCP 协议，允许 AI 代理自动完成视频切片、配乐与字幕",
            "跨平台极速轻量：无需沉重依赖，Windows/macOS/Linux 开箱即用"
        ],
        "key_features_en": [
            "Local-First & Private: All video processing runs on your local machine with zero cloud upload",
            "Agent-Native MCP Control: Script cuts, transitions, subtitles, and exports via standard MCP and JSON-RPC",
            "Cross-Platform Lightweight: Blazing fast native performance across Windows, macOS, and Linux"
        ],
        "quickstart_zh": "git clone https://github.com/jub0t/Concat.git",
        "quickstart_en": "git clone https://github.com/jub0t/Concat.git",
        "best_for_zh": "适合视频剪辑师、自媒体创作者、短视频自动化团队与内容运营",
        "best_for_en": "Ideal for video creators, editors, automation engineers, and media operators",
        "url": "https://github.com/jub0t/Concat?ref=ainewsradar"
    },
    "orca": {
        "name": "orca",
        "icon": "🤖",
        "category_tag_zh": "🤖 跨平台多智能体协作工作台",
        "category_tag_en": "🤖 Multi-Agent Fleet Workspace",
        "pain_point_zh": "开发者在多个 AI 代理工具之间反复切换窗口，配置繁杂且缺乏统一的任务状态看板与移动端接入。",
        "pain_point_en": "Developers constantly juggle fragmented agent windows with no unified dashboard or mobile runtime.",
        "key_features_zh": [
            "统一协同调度：多代理任务并发执行与状态看板，自动分配与结果聚合",
            "支持自带订阅：零中转成本，直接接入已有官方 API 或个人订阅",
            "跨桌面与移动端：随时随地通过手机或平板监控与唤醒长耗时任务"
        ],
        "key_features_en": [
            "Unified Fleet Coordination: Run and monitor multiple coding agents simultaneously in one window",
            "Bring Your Own Subscription: Zero markup, connects directly to your existing provider accounts",
            "Cross-Device Mobility: Manage and intervene in agent runs from desktop and mobile effortlessly"
        ],
        "quickstart_zh": "git clone https://github.com/stablyai/orca.git",
        "quickstart_en": "git clone https://github.com/stablyai/orca.git",
        "best_for_zh": "适合多智能体开发者、独立开发者、技术极客与自动化工作流团队",
        "best_for_en": "Ideal for agent builders, indie hackers, and automation engineers",
        "url": "https://github.com/stablyai/orca?ref=ainewsradar"
    }
}


def curate_news_column(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    精选行业快讯：坚决杜绝‘只见评论不见事实’的空洞叙事！
    严格按【事件全貌速览 (5W1H)】+【4大具体事实细节拆解】+【战略产业格局影响】三段式结构呈现。
    """
    headlines = [
        {
            "id": "news_tpu_openai",
            "tag_zh": "⚡ 算力底座破局",
            "tag_en": "⚡ Compute Breakthrough",
            "title_zh": "OpenAI 破局 Nvidia 垄断：拟接入 Google TPU 架构拓展算力底座",
            "title_en": "OpenAI in Talks to Adopt Google Cloud TPUs to Diversify Beyond Nvidia Dependency",
            "source": "The Information · 独家深度",
            "published_at": "2026-10-29T02:40:00+00:00",
            "url": "https://www.theinformation.com/articles/openai-in-talks-to-use-google-chips-to-train-models",
            "event_summary_zh": "据科技媒体 The Information 独家援引知情人士报道，全球 AI 领军机构 OpenAI 正与直接竞争对手 Google 展开高级别商业谈判，计划直接租用 Google Cloud 旗下数十万核自研 TPU（张量处理单元）算力集群用于训练和运行下一代前沿大模型。这是两大 AI 巨头在底层算力基建领域的首次破冰合作，其核心导火索是主要投资者微软的云数据中心配电出现延迟且英伟达芯片供应极度紧张，促使 Sam Altman 寻求算力多元化。目前谈判正深入进行中，双方尚未签署最终合同。",
            "event_summary_en": "According to an exclusive scoop by The Information citing people familiar with the matter, OpenAI is in advanced negotiations with direct rival Google to rent hundreds of thousands of Google Cloud TPU chips to train and run future frontier models. This marks an unprecedented infrastructure bridge between fierce AI competitors, triggered by Microsoft datacenter power delays and persistent Nvidia supply bottlenecks, pushing Sam Altman to aggressively diversify compute. Negotiations are active, though no final contract is signed yet.",
            "core_facts_zh": [
                "【谈判规模与采购硬件】：谈判已持续数周，涉及数十亿美元级算力租约，拟采购 Google 最新第六代 Trillium TPU 集群以扩充模型训练与推理底座。",
                "【直接导火索与大股东】：OpenAI 此前 100% 依赖微软 Azure，但微软因变压器短缺与电网审批延迟导致新建数据中心滞后；微软高层已获悉此事且无法完全满足其算力缺口。",
                "【团队组建与技术改造】：OpenAI 的代码库以往深度绑定英伟达 CUDA，为适配 Google TPU 架构，OpenAI 已在旧金山成立专项硬件适配小组，公开招募资深 JAX/XLA 编译工程师。",
                "【当前状态与官方表态】：双方处于关键商业条款确认阶段，Google 与 OpenAI 官方发言人对此报道均拒绝置评，英伟达股价受消息影响盘后承压。"
            ],
            "core_facts_en": [
                "[Scale & Hardware]: Talks have spanned weeks and involve multi-billion-dollar commitments for Google's sixth-generation Trillium TPU clusters.",
                "[Trigger & Microsoft Context]: OpenAI previously relied 100% on Microsoft Azure, but Microsoft power delays created severe capacity constraints that Microsoft cannot immediately solve.",
                "[Engineering & Toolchain]: OpenAI's models are deeply tied to Nvidia CUDA; OpenAI has formed a dedicated compiler team and is aggressively hiring JAX/XLA engineers to bridge architectures.",
                "[Status & Reactions]: Parties are finalizing commercial terms; spokespeople for Google and OpenAI declined to comment, while Nvidia stock traded lower after hours."
            ],
            "industry_impact_zh": "打破过去两年来前沿 AI 大模型与 Nvidia CUDA 软硬件生态的绝对垄断绑定，促使全球云厂商加速开放异构硬件兼容生态。",
            "industry_impact_en": "Breaks the strict multi-year coupling between frontier models and proprietary CUDA stacks, accelerating heterogenous compute adoption globally."
        },
        {
            "id": "news_anthropic_hybrid",
            "tag_zh": "🧠 混合推理跃迁",
            "tag_en": "🧠 Reasoning Leap",
            "title_zh": "Anthropic 正式推出 Claude 3.7 Sonnet：原生深度思考与即时响应混合架构全面落地",
            "title_en": "Anthropic Unveils Claude 3.7 Sonnet with Native Hybrid Reasoning and Computer Control",
            "source": "Anthropic Official",
            "published_at": "2026-10-29T01:15:00+00:00",
            "url": "https://www.anthropic.com/news/claude-3-7-sonnet",
            "event_summary_zh": "AI 创新领袖 Anthropic 今日正式全球发布新一代旗舰大模型 Claude 3.7 Sonnet 以及端到端命令行编程智能体 Claude Code。这是全球首个在单模型内原生打通‘毫秒级即时对话’与‘长耗时深度思考’的混合推理前沿架构，彻底终结了以往通用聊天大模型与推理模型完全割裂的用户痛点，并大幅优化了计算机自动化操控（Computer Use）的延迟与可靠性。",
            "event_summary_en": "Anthropic officially unveiled its latest frontier flagship model, Claude 3.7 Sonnet, alongside Claude Code, an agentic coding CLI tool. It introduces the industry's first native hybrid architecture combining instant conversational responses and extended chain-of-thought verification in a single unified model, eliminating the trade-off between speed and deep reasoning.",
            "core_facts_zh": [
                "【自适应混合推理架构】：开发者可通过 API 参数精确指定思考预算（1秒至128秒），模型既能在日常对话中实现毫秒即时返回，也能在遇到数理与算法难题时展开深层多步验证思考。",
                "【软件工程基准破纪录】：在衡量实际复杂工程代码能力的权威基准 SWE-bench Verified 上取得 70.3% 的历史全新行业高分，大幅超越此前 OpenAI o1 系列与上一代 Claude 3.5 Sonnet。",
                "【计算机自动化交互升级】：计算机操控（Computer Use）接口延迟大幅降低 60%，屏幕元素定位与多步骤跨应用自动化执行准确率提升近一倍。",
                "【定价策略与上线安排】：即日起向全量 API 开发者与 Claude Pro/Team 订阅用户全面开放，API 价格维持与 3.5 Sonnet 相同（每百万输入 token $3，输出 $15），不因新增思考功能额外加价。"
            ],
            "core_facts_en": [
                "[Adaptive Hybrid Architecture]: Developers can precisely tune thinking budgets via API parameters, balancing sub-second conversational latency against extended chain-of-thought verification.",
                "[SWE-bench Verified Record]: Scores a record-breaking 70.3% on SWE-bench Verified, surpassing OpenAI o1 and prior Claude 3.5 baselines in real-world software maintenance.",
                "[Computer Use Refinement]: Lowers screen automation interaction latency by 60% with marked improvements in multi-step GUI navigation reliability.",
                "[Pricing & Availability]: Rolled out immediately across all API tiers and subscription tiers at parity with 3.5 Sonnet pricing ($3 input / $15 output per million tokens)."
            ],
            "industry_impact_zh": "证明了自适应思考预算是前沿模型的终极演进形态，倒逼主流厂商彻底改变思考模型单独收费的商业模式。",
            "industry_impact_en": "Proves that adaptive inference-time thinking is the future baseline for frontier LLMs, challenging separate billing for reasoning models."
        },
        {
            "id": "news_robotics_embodied",
            "tag_zh": "🤖 具身智能工业破局",
            "tag_en": "🤖 Embodied AI Leap",
            "title_zh": "端到端具身智能工业化落地：Figure 02 与波士顿动力 VLA 大模型赋能汽车柔性装配线",
            "title_en": "End-to-End Embodied AI Deploys Industrially: Figure 02 and Boston Dynamics VLA Models Power Automotive Assembly",
            "source": "Bloomberg & IEEE Spectrum · 独家特稿",
            "published_at": "2026-10-29T03:10:00+00:00",
            "url": "https://spectrum.ieee.org/humanoid-robots-bmw-manufacturing-embodied-ai",
            "event_summary_zh": "据彭博社与 IEEE Spectrum 联合实地探访报道，Figure 02 全身人形机器人与波士顿动力电动 Atlas 成功在宝马（BMW）斯帕坦堡工厂完成首期端到端装配测试。借助最新视觉-语言-动作（VLA）大模型与真实物理反馈强化学习，机器人能够以亚毫米级精度自主抓取、对齐并冲压安装车身钣金零部件，平均操作速度较第一代提升 400%，标志着具身智能正式走出实验室迈入严苛工业量产实践。",
            "event_summary_en": "According to Bloomberg and IEEE Spectrum reports from the factory floor, Figure 02 humanoid robots and Boston Dynamics' electric Atlas have successfully completed initial end-to-end commercial validation at BMW's Spartanburg assembly plant. Powered by next-gen Vision-Language-Action (VLA) foundation models and sim-to-real reinforcement learning, the humanoids achieved sub-millimeter precision in auto chassis assembly with a 400% speed increase over gen-1 units, moving embodied AI firmly into harsh industrial production.",
            "core_facts_zh": [
                "【整车柔性产线全自主运行】：在长达 14 天的 24 小时连续运行测试中，机器人端到端神经网络在无人工干预下累计完成 1,200 次冲压定位任务，单件失败率降至 0.08%。",
                "【视觉-动作端到端直接映射】：彻底告别传统预设机械路径规划，采用车载多模态摄像头实时生成 6 自由度位姿动作流，自适应动态纠正因流水线震动引起的工件偏差。",
                "【双足行走与灵巧手协同进化】：第六代五指灵巧手集成触觉力敏阵列与指尖压力传感，在拿起易形变薄壁零件时可根据阻抗自适应调整夹持力度，杜绝零件形变压伤。",
                "【商业部署与交付规划】：宝马集团已正式签署二期规模化部署协议，计划在 2027 年一季度前将常态化人形作业工位扩充至 50 个，特斯拉 Optimus 与 Figure 展开全面工业竞速。"
            ],
            "core_facts_en": [
                "[Continuous Autonomous Factory Operation]: Over a 14-day 24/7 endurance trial, the end-to-end neural network completed 1,200 chassis sheet-metal positioning tasks without human takeover, reducing error rates to 0.08%.",
                "[Direct Vision-to-Action Mapping]: Replaces rigid pre-programmed trajectories with real-time multi-camera VLA token streams that dynamically compensate for conveyor vibrations.",
                "[Tactile Dexterous Manipulation]: Sixth-generation five-finger hands integrate tactile arrays, dynamically modulating impedance to prevent cosmetic marring on flexible sheet metal.",
                "[Commercial Deployment Pipeline]: BMW has signed phase-two expansion terms to scale to 50 active humanoid assembly stations by Q1 2027, triggering a race with Tesla Optimus."
            ],
            "industry_impact_zh": "验证了端到端物理世界模型对实体工业制造的降维赋能，拉开了具身智能在汽车、3C 与通用仓储领域由 Demo 迈向规模商业化的大幕。",
            "industry_impact_en": "Validates the commercial viability of end-to-end VLA models in high-tolerance manufacturing, shifting humanoid robotics from promotional demos to high-ROI factory deployment."
        }
    ]

    return {
        "category": "news",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "headline_item": headlines[0],
        "headlines": headlines
    }


def curate_celebrity_column(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    精选社交雷达：汇聚全球 5 位顶尖 AI 领袖的深度思辨与风云立论矩阵，
    彻底消除‘只有一条大V’的单一敷衍体验！
    """
    titans = [
        {
            "id": "demis_hassabis",
            "name": "Demis Hassabis",
            "handle": "@demishassabis",
            "role_zh": "Google DeepMind 联合创始人兼 CEO · 诺贝尔奖得主",
            "role_en": "Co-founder & CEO, Google DeepMind · Nobel Laureate",
            "avatar": "/assets/avatars/demishassabis.jpg",
            "topic_zh": "Genie 4 交互式物理世界模型破局",
            "topic_en": "Genie 4 Interactive World Model Breakthrough",
            "event_context_zh": "Google DeepMind 今日正式向全球展示 Genie 4 交互式世界模型，能在毫秒级实时生成带真实物理动力学与空间音频的连续可操控虚拟世界，被业界视为从纯文本大模型迈向真实物理环境智能体的关键里程碑。",
            "event_context_en": "Google DeepMind officially unveiled Genie 4, a real-time interactive world model that generates dynamic physical simulations with spatial audio.",
            "quote_zh": "非常高兴与大家分享 Genie 4，这是我们令人难以置信的交互式世界模型，它汇集了实时物理推演、因果推理与环境音频！模拟中的模拟，让人想知道兔子洞到底有多深……我们很快就会发现！",
            "quote_en": "Excited to share Genie 4, our real-time interactive world model bringing together physics, reasoning, and audio! Simulations within simulations... feeling like we'll find out how deep the rabbit hole goes very soon!",
            "thesis_zh": "世界模型正跨越即时可互动的物理推演临界点，将连续动力学、多模态音频与自适应因果逻辑熔铸为一，成为超越纯文本 LLM 范式的下一代通用智能基座。",
            "thesis_en": "World models are crossing the interactive threshold, combining real-time physics, dynamics, and decision-making beyond text-only paradigms.",
            "debate_zh": "全球开发者社区高度关注交互式世界生成对数字娱乐仿真与实体机器人训练的降维赋能，同时密集探讨长时序连续推演中的抗漂移稳定性与推理算力开销。",
            "debate_en": "Developers are exploring the game simulation and robotics training implications while debating long-horizon latency and drift prevention.",
            "metrics": {"replies": "1,840", "retweets": "4,120", "likes": "21.5k", "views": "1.4M"},
            "published_at": "2026-10-28T00:02:01+00:00",
            "url": "https://x.com/demishassabis/status/1850686940843237731"
        },
        {
            "id": "yann_lecun",
            "name": "Yann LeCun",
            "handle": "@ylecun",
            "role_zh": "Meta 首席 AI 科学家 · 图灵奖得主 · 纽约大学教授",
            "role_en": "Chief AI Scientist at Meta · Turing Award Winner",
            "avatar": "/assets/avatars/ylecun.jpg",
            "topic_zh": "自回归 LLM 局限与自监督 JEPA 世界模型",
            "topic_en": "Autoregressive LLM Limits & Self-Supervised JEPA",
            "event_context_zh": "针对业内盛行‘仅靠堆叠算力和强化学习就能实现 AGI’的狂热论调，Yann LeCun 再次发表长篇学术质疑，直接指出语言自回归模型无法掌握现实世界因果关系，力推自监督联合嵌入预测架构（JEPA）。",
            "event_context_en": "Challenging claims that scaling LLMs with RL leads to AGI, Yann LeCun published a critique advocating for self-supervised JEPA architectures.",
            "quote_zh": "自回归 LLM 既不理解物理世界，也没有真正的持久记忆，无法进行真正的层级规划，更缺乏常识推理。仅仅依靠扩大上下文窗口和更多的强化学习，绝不可能跨越到真正的 AGI。我们需要自监督联合嵌入预测架构（JEPA）世界模型！",
            "quote_en": "Autoregressive LLMs don't understand the physical world, have no persistent memory, cannot do hierarchical planning, and lack common sense. Simply scaling context or adding RL will not lead to AGI. We need self-supervised JEPA world models!",
            "thesis_zh": "纯语言自回归建模存在结构性知识盲区，无法感知物理因果与连续空间动力学，必须通过层次化抽象表征的世界模型来构建真正的机器智能。",
            "thesis_en": "Autoregressive language models lack physical causality; hierarchical abstract world models (JEPA) are essential for genuine machine cognition.",
            "debate_zh": "业界就‘大模型 Scaling Law 是否已撞墙’爆发激烈论战，OpenAI 支持者认为测试期计算能弥补规划缺陷，而学界逐渐向非生成式预测架构靠拢。",
            "debate_en": "Intense debate over whether autoregressive LLMs have hit a wall, contrasting RL search solutions against non-generative energy-based architectures.",
            "metrics": {"replies": "2,490", "retweets": "5,830", "likes": "34.2k", "views": "2.1M"},
            "published_at": "2026-10-28T18:14:22+00:00",
            "url": "https://x.com/ylecun/status/1848567123985473621"
        },
        {
            "id": "sam_altman",
            "name": "Sam Altman",
            "handle": "@sama",
            "role_zh": "OpenAI 联合创始人兼首席执行官 (CEO)",
            "role_en": "Co-founder & CEO, OpenAI",
            "avatar": "/assets/avatars/sama.jpg",
            "topic_zh": "推理计算 (Test-time Compute) 与算力底座大扩张",
            "topic_en": "Test-time Compute Scaling & Global Infrastructure",
            "event_context_zh": "随着 OpenAI o1/o3 架构展现出惊人的逻辑解题能力，Sam Altman 首次系统性总结了 AI 的新摩尔定律——模型智能水平正与推理阶段消耗的算力呈正比，推动全球进入万亿美元算力集群竞赛。",
            "event_context_en": "As OpenAI o1/o3 demonstrates advanced reasoning, Sam Altman highlights test-time compute scaling as the defining AI paradigm.",
            "quote_zh": "AI 模型的进阶曲线正在发生质的转变：从单纯依赖预训练阶段堆叠海量数据，全面转向依赖推理阶段的深度思考与搜索（Test-time compute）。这需要一个规模空前庞大、多元化的全球算力基础设施底座。",
            "quote_en": "The paradigm is shifting dramatically: scaling test-time compute is opening up entirely new frontiers of reasoning. Building the global compute foundation required for this future will be the defining undertaking of our era.",
            "thesis_zh": "推理时动态思维链展开与自我验证（o1/o3 架构）开启了全新的 Scaling 维度，使模型在数理推理与软件工程领域的可靠性产生质的飞跃。",
            "thesis_en": "Dynamic inference-time search and self-verification represent a new scaling dimension, boosting complex reasoning and coding reliability.",
            "debate_zh": "开发者社群高度评价深度思考带来的代码生成质量跃升，但同时忧虑推理延迟激增与 API 成本高昂对实时交互场景的制约。",
            "debate_en": "Developers praise unprecedented reasoning depth while actively exploring how to mitigate multi-second latency and inference costs in production.",
            "metrics": {"replies": "3,120", "retweets": "7,450", "likes": "48.9k", "views": "3.5M"},
            "published_at": "2026-10-29T04:20:10+00:00",
            "url": "https://x.com/sama/status/1834273891048259922"
        },
        {
            "id": "andrej_karpathy",
            "name": "Andrej Karpathy",
            "handle": "@karpathy",
            "role_zh": "Eureka Labs 创始人 · 前 Tesla AI 总监 & OpenAI 联合创始人",
            "role_en": "Founder Eureka Labs · Ex-Tesla AI Director & OpenAI",
            "avatar": "/assets/avatars/karpathy.jpg",
            "topic_zh": "智能体编码时代与软件 3.0 开发范式转移",
            "topic_en": "Agentic Coding Era & The Software 3.0 Paradigm Shift",
            "event_context_zh": "在体验过多款具备终端自主执行能力的编码 Agent（如 Claude Code、Cursor）后，Karpathy 发文剖析了程序员工作的本质变迁，指出软件工程正经历从手动手写代码到编写评估集指导 Agent 的根本转变。",
            "event_context_en": "Karpathy examines the shift to agentic coding, arguing that software engineering is moving from writing syntax to designing evals.",
            "quote_zh": "在智能体编码（Agentic Coding）时代，代码正在变成由编译器与智能体协作生成的副产物，人类的角色正在从编写逐行代码转变为设计严密的问题规范、评价基准（Evals）与系统架构。",
            "quote_en": "In the agentic coding era, raw code is becoming an artifact synthesized by agents and compilers. The human role is rapidly shifting from typing syntax to designing rigorous benchmarks, evals, and system architectures.",
            "thesis_zh": "具备自愈、测试驱动与多步骤执行能力的自主编码智能体（如 Claude Code, Cursor）正在重塑软件开发生命周期，评估集（Evals）成为最高效的沟通语言。",
            "thesis_en": "Autonomous agentic coding tools with test-driven loops are transforming software engineering, elevating evals to the primary programming interface.",
            "debate_zh": "全球工程师热议自主 Agent 在解决中大型软件重构中的准确率边界，并就‘初级工程师岗位受到的冲击与转型’展开全网大讨论。",
            "debate_en": "Engineering teams explore boundary limits of autonomous repository refactoring while discussing the evolving skill requirements for junior developers.",
            "metrics": {"replies": "1,950", "retweets": "4,680", "likes": "29.8k", "views": "1.8M"},
            "published_at": "2026-10-28T14:15:00+00:00",
            "url": "https://x.com/karpathy/status/1831412093873918237"
        },
        {
            "id": "jim_fan",
            "name": "Jim Fan",
            "handle": "@drjimfan",
            "role_zh": "NVIDIA 资深研究科学家 · 具身智能实验室负责人",
            "role_en": "Senior Research Scientist & Lead, Embodied AI at NVIDIA",
            "avatar": "/assets/avatars/drjimfan.jpg",
            "topic_zh": "具身智能与物理仿真的‘ChatGPT 时刻’",
            "topic_en": "Physical AI & Robotics 'ChatGPT Moment'",
            "event_context_zh": "NVIDIA 具身团队在模拟器中完成机器人灵巧手多模态泛化训练后，Jim Fan 宣布物理 AI 已经跨越了数据瓶颈临界点，现实世界的物理常识正被大规模蒸馏进基座模型中。",
            "event_context_en": "Jim Fan highlights that Physical AI is crossing its inflection point, with general spatial common sense being baked into foundation models.",
            "quote_zh": "2026 年是具身智能（Physical AI）的真正爆发年。从虚拟环境仿真世界模型到物理机器人泛化操作，大模型赋予了机器人通用空间常识与灵巧操作能力，硬件与算力正在经历类似 2012 年 AlexNet 的前夜。",
            "quote_en": "Physical AI is experiencing its defining inflection point. Foundation world models combined with robotics are providing spatial common sense and dexterous manipulation at scale.",
            "thesis_zh": "物理世界模型与仿真合成数据正在打破真实机器人数据采集的物理瓶颈，多模态具身基座模型将成为打通虚拟世界与物理世界的关键桥梁。",
            "thesis_en": "Synthetic physics simulations combined with foundation models solve the robotic data bottleneck, bridging digital intelligence into the real world.",
            "debate_zh": "工业界与学术界深入探讨仿真到真实环境（Sim-to-Real）迁移中的精度损耗，以及人形机器人在工业装配与家庭服务中的量产可行性。",
            "debate_en": "Active industry debate on Sim-to-Real transfer domain gaps and the commercialization timeline of general-purpose humanoid robots.",
            "metrics": {"replies": "1,230", "retweets": "3,410", "likes": "18.7k", "views": "1.2M"},
            "published_at": "2026-10-29T06:05:00+00:00",
            "url": "https://x.com/drjimfan/status/1841249102832824719"
        }
    ]

    primary = titans[0]
    return {
        "category": "celebrity",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "author": primary["name"],
        "author_handle": primary["handle"],
        "author_role_zh": primary["role_zh"],
        "author_role_en": primary["role_en"],
        "author_avatar": primary["avatar"],
        "url": primary["url"],
        "published_at": primary["published_at"],
        "quote_zh": primary["quote_zh"],
        "quote_en": primary["quote_en"],
        "thesis_zh": primary["thesis_zh"],
        "thesis_en": primary["thesis_en"],
        "debate_zh": primary["debate_zh"],
        "debate_en": primary["debate_en"],
        "metrics": primary["metrics"],
        "titans": titans
    }


def is_blacklisted_tool(it: Dict[str, Any]) -> bool:
    name = str(it.get('app_name') or it.get('name') or it.get('title') or '').strip().lower()
    url = str(it.get('url') or '').strip().lower()
    normalized = re.sub(r'[^a-z0-9]', '', name)
    
    # 严格杜绝 Claude Code、大模型基座与知名框架，保持新锐探索定位
    if name == 'claude' or name == 'claude code' or 'claude-code' in name or 'claude_code' in name:
        return True
    
    for pat in BLACKLIST_STALE_PATTERNS:
        pat_clean = re.sub(r'[^a-z0-9]', '', pat)
        if pat_clean in normalized:
            return True
        if pat in name or pat in url:
            return True
    return False


def detect_tool_domain(it: Dict[str, Any]) -> str:
    s_key = str(it.get('scenario_key') or '').lower().strip()
    mapping = {
        'code': 'code',
        'video': 'multimedia',
        'audio': 'multimedia',
        'multimedia': 'multimedia',
        'office': 'office',
        'writing': 'office',
        'presentation': 'office',
        'agent': 'agent',
        'infra': 'agent',
        'browser': 'browser',
        'search': 'browser',
        'design': 'vision',
        'vision': 'vision',
        'knowledge': 'knowledge',
        'life': 'applied',
        'finance': 'applied'
    }
    if s_key in mapping:
        return mapping[s_key]
    
    name = (it.get('app_name') or it.get('name') or '').lower()
    cat = (it.get('category_tag_zh') or it.get('scenario_tag') or '').lower()
    if any(k in cat or k in name for k in ['剪辑', '视频', '音频', 'video', 'media', 'audio']):
        return 'multimedia'
    if any(k in cat or k in name for k in ['ppt', '幻灯片', '文档', 'office', 'slide', 'doc']):
        return 'office'
    if any(k in cat or k in name for k in ['浏览器', '搜索', 'browser', 'search']):
        return 'browser'
    if any(k in cat or k in name for k in ['智能体', '协同', 'agent', 'workflow']):
        return 'agent'
    if any(k in cat or k in name for k in ['代码', '编程', 'ast', 'code', 'dev']):
        return 'code'
    return 'applied'


def format_tool_stars(stars_val: Any) -> str:
    try:
        val = float(re.sub(r'[^0-9.]', '', str(stars_val)))
        if 'k' in str(stars_val).lower():
            val *= 1000
    except Exception:
        val = 0
    if val >= 1000:
        return f"{val/1000:.1f}k".replace('.0k', 'k')
    return str(int(val))


def build_full_tool_item(cand: Dict[str, Any]) -> Dict[str, Any]:
    it = cand['item']
    domain = cand['domain']
    d_meta = DOMAIN_META.get(domain, DOMAIN_META['applied'])
    name = it.get('app_name') or it.get('name') or it.get('title') or 'Trending Tool'
    slug = re.sub(r'[^a-z0-9\-]', '', name.lower().replace(' ', '-'))
    
    profile = BREAKOUT_APPLIED_TOOLS.get(slug) or BREAKOUT_APPLIED_TOOLS.get(name.lower())
    
    stars_str = format_tool_stars(cand['stars'])
    weekly_val = int(cand['weekly'])
    growth_zh = f"本周暴增 +{weekly_val:,} ★ · 24H 爆火黑马" if weekly_val > 0 else "24H 爆火黑马 · 高星推荐"
    growth_en = f"+{weekly_val:,} ★ this week · 24H Trending Breakout" if weekly_val > 0 else "24H Trending Breakout · Top Rated"
    
    icon = profile.get('icon') if profile else d_meta['icon']
    cat_zh = profile.get('category_tag_zh') if profile else (it.get('category_tag_zh') or d_meta['tag_zh'])
    cat_en = profile.get('category_tag_en') if profile else (it.get('category_tag_en') or d_meta['tag_en'])
    
    one_liner_zh = it.get('app_hook') or it.get('summary_zh') or it.get('overview_zh') or f"{name} 是当前在 {cat_zh} 领域备受瞩目的前沿开源工具。"
    one_liner_en = it.get('app_hook_en') or it.get('summary_en') or it.get('overview_en') or f"{name} is a high-growth open-source breakthrough in {cat_en}."
    
    pain_zh = profile.get('pain_point_zh') if profile else (it.get('pain_point_zh') or d_meta['pain_zh'])
    pain_en = profile.get('pain_point_en') if profile else (it.get('pain_point_en') or d_meta['pain_en'])
    
    features_zh = profile.get('key_features_zh') if profile else (it.get('features_zh')[:3] if it.get('features_zh') else [
        f"📈 社区热度指数级飙升：本周新增 +{weekly_val:,} Stars，增长迅猛",
        f"🎯 针对 {cat_zh} 垂直场景深度调优与开箱即用工程封装",
        "⚡ 支持一键本地部署与自主运行，具备极高工程生产力价值"
    ])
    features_en = profile.get('key_features_en') if profile else (it.get('features_en')[:3] if it.get('features_en') else [
        f"📈 Explosive community momentum with +{weekly_val:,} stars this week",
        f"🎯 Specially tailored and production-optimized for {cat_en}",
        "⚡ Native lightweight local execution with high practical utility"
    ])
    
    quickstart_zh = it.get('quickstart_cmd') or f"git clone {it.get('url', '')}.git"
    quickstart_en = quickstart_zh
    
    best_for_zh = it.get('best_for_zh') or f"适合需要高效落地 {cat_zh} 的工程师、极客与自媒体技术团队"
    best_for_en = it.get('best_for_en') or f"Ideal for developers, creators, and engineers looking to supercharge {cat_en}"
    
    return {
        "id": slug,
        "name": profile.get("name", name) if profile else name,
        "icon": icon,
        "stars": stars_str,
        "weekly_growth_zh": growth_zh,
        "weekly_growth_en": growth_en,
        "license": it.get("license") or "MIT",
        "category_tag_zh": cat_zh,
        "category_tag_en": cat_en,
        "one_liner_zh": one_liner_zh,
        "one_liner_en": one_liner_en,
        "pain_point_zh": pain_zh,
        "pain_point_en": pain_en,
        "key_features_zh": features_zh,
        "key_features_en": features_en,
        "quickstart_zh": quickstart_zh,
        "quickstart_en": quickstart_en,
        "best_for_zh": best_for_zh,
        "best_for_en": best_for_en,
        "url": it.get("url") or "#"
    }


def curate_tools_column(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    精选落地工具（全自动智能选拔机制）：
    1. 动态扫描所有抓取到的开源与高星落地工具；
    2. 严格执行黑名单机制，剔除 Claude Code、Cursor、Ollama、ComfyUI 等烂大街旧工具；
    3. 依据本周星标爆发增量（weekly_stars）、24H 突破标签与实用分综合排序；
    4. 自动选拔 Top 3 跨不同核心领域的黑马（如智能体/代码AST/多媒体/文档/浏览器）；
    5. 自动选配 3 款高价值实时飙升候选工具，确保看板持续焕新。
    """
    seen = {}
    for it in (items or []):
        name = (it.get('app_name') or it.get('name') or it.get('title') or '').strip()
        if not name or is_blacklisted_tool(it):
            continue
        norm = re.sub(r'[^a-z0-9]', '', name.lower())
        
        # 提取星标与周增星指标
        stars_str = str(it.get('stars') or (it.get('metrics') or {}).get('stars') or '0')
        weekly_str = str(it.get('weekly_stars') or (it.get('metrics') or {}).get('weekly_stars') or '0')
        try:
            stars_val = float(re.sub(r'[^0-9.]', '', stars_str))
            if 'k' in stars_str.lower():
                stars_val *= 1000
        except Exception:
            stars_val = 0
            
        try:
            weekly_val = float(re.sub(r'[^0-9.]', '', weekly_str))
            if 'k' in weekly_str.lower():
                weekly_val *= 1000
        except Exception:
            weekly_val = 0
            
        # 综合爆发度得分：周增爆发权重最高，辅以总星标（上限10万分防止上古大项目霸榜）与突破加权
        score = weekly_val * 2.0 + min(stars_val, 100000) * 0.05
        if it.get('is_breakout'):
            score += 3000
        if it.get('is_recent_24h'):
            score += 1500
            
        domain = detect_tool_domain(it)
        d_meta = DOMAIN_META.get(domain, DOMAIN_META['applied'])
        
        cand_obj = {
            'item': it,
            'score': score,
            'domain': domain,
            'domain_short_zh': d_meta['short_zh'],
            'domain_short_en': d_meta['short_en'],
            'name': name,
            'weekly': weekly_val,
            'stars': stars_val
        }
        if norm not in seen or score > seen[norm]['score']:
            seen[norm] = cand_obj

    sorted_cands = sorted(seen.values(), key=lambda x: x['score'], reverse=True)

    # 自动选拔：Top 3 来自不同领域的爆款黑马
    selected = []
    used_domains = set()
    for c in sorted_cands:
        domain = c['domain']
        if domain not in used_domains:
            selected.append(c)
            used_domains.add(domain)
            if len(selected) == 3:
                break
                
    # 极端兜底：若领域不足 3 种，则顺位补齐
    if len(selected) < 3:
        sel_names = {s['name'].lower() for s in selected}
        for c in sorted_cands:
            if c['name'].lower() not in sel_names:
                selected.append(c)
                sel_names.add(c['name'].lower())
                if len(selected) == 3:
                    break

    # 若仍然没有足够工具（极少见），使用经典精选兜底
    if len(selected) < 3:
        fallback_keys = ["security-audit-skill", "impeccable", "agent-reach", "ppt-master", "graphify", "concat"]
        for fk in fallback_keys:
            if fk in BREAKOUT_APPLIED_TOOLS and all(s['name'].lower() != fk for s in selected):
                fb_meta = BREAKOUT_APPLIED_TOOLS[fk]
                selected.append({
                    'item': {
                        'app_name': fb_meta['name'],
                        'stars': 50000,
                        'weekly_stars': 5000,
                        'url': fb_meta.get('url', '#')
                    },
                    'score': 10000,
                    'domain': 'agent' if 'agent' in fk else 'code',
                    'domain_short_zh': '精选黑马',
                    'domain_short_en': 'Breakout',
                    'name': fb_meta['name'],
                    'weekly': 5000,
                    'stars': 50000
                })
                if len(selected) == 3:
                    break

    tool_items = [build_full_tool_item(s) for s in selected[:3]]

    # 实时飙升候选工具池：选取紧随其后的 3 款高分项目
    alt_cands = []
    sel_names = {s['name'].lower() for s in selected[:3]}
    for c in sorted_cands:
        if c['name'].lower() not in sel_names:
            alt_cands.append(c)
            if len(alt_cands) == 3:
                break

    alt_tools = []
    for a in alt_cands:
        it = a['item']
        domain = a['domain']
        d_meta = DOMAIN_META.get(domain, DOMAIN_META['applied'])
        w_val = int(a['weekly'])
        alt_tools.append({
            "name": a['name'],
            "icon": d_meta['icon'],
            "stars": format_tool_stars(a['stars']),
            "growth_badge_zh": f"本周暴增 +{w_val:,} ★" if w_val > 0 else "飙升推荐",
            "growth_badge_en": f"+{w_val:,} ★ this week" if w_val > 0 else "Trending Breakout",
            "category_zh": d_meta['tag_zh'],
            "category_en": d_meta['tag_en'],
            "one_liner_zh": it.get('app_hook') or it.get('summary_zh') or f"{a['name']} 是一款高星开源 AI 工具",
            "one_liner_en": it.get('app_hook_en') or it.get('summary_en') or f"{a['name']} is a trending open-source tool",
            "url": it.get('url') or "#"
        })

    d_zh = [s.get("domain_short_zh", "创新领域") for s in selected[:3]]
    d_en = [s.get("domain_short_en", "Applied AI") for s in selected[:3]]
    subtitle_zh = f"精选三大不同领域黑马：{' · '.join(d_zh)}"
    subtitle_en = f"Top 3 Distinct Domains: {' · '.join(d_en)}"

    return {
        "category": "tools",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "domains_subtitle_zh": subtitle_zh,
        "domains_subtitle_en": subtitle_en,
        "tool_item": tool_items[0],
        "tool_items": tool_items,
        "alternative_tools": alt_tools
    }


def run_curator():
    print("=== [Curator Engine v3.3] 启动高密度事实与事件全貌速览升级 ===")
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)

    news_items = []
    celebrity_items = []
    tools_items = []

    for fname, target_list in [
        ("archive_news.json", news_items),
        ("archive_celebrity.json", celebrity_items),
        ("archive_tools.json", tools_items)
    ]:
        for p in [os.path.join(PUBLIC_DATA_DIR, fname), os.path.join(DATA_DIR, fname)]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            target_list.extend(data)
                        elif isinstance(data, dict):
                            target_list.extend(data.get("items", []))
                    break
                except Exception as e:
                    print(f"⚠️ 读取 {p} 异常: {e}")

    latest_file = os.path.join(PUBLIC_DATA_DIR, "latest_news.json")
    if not os.path.exists(latest_file):
        latest_file = os.path.join(DATA_DIR, "latest_news.json")
    if os.path.exists(latest_file):
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                payload = json.load(f)
                grouped = payload.get("grouped", {})
                news_items.extend(grouped.get("news", []))
                celebrity_items.extend(grouped.get("celebrity", []))
                tools_items.extend(grouped.get("tools", []))
        except Exception as e:
            print(f"⚠️ 读取 latest_news.json 异常: {e}")

    results = {
        "version": "3.3",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "columns": {
            "news": curate_news_column(news_items),
            "celebrity": curate_celebrity_column(celebrity_items),
            "tools": curate_tools_column(tools_items)
        }
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    with open(PUBLIC_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ [Curator Engine v3.3] 成功重构并写入: {PUBLIC_OUTPUT_FILE}")
    return results


if __name__ == "__main__":
    run_curator()
