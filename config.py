"""
AI Radar 2.0 Config - Data Sources and Category Definitions
"""

# 分栏定义 (中英双语)
CATEGORIES = {
    "news": {
        "zh": "⚡ 突发·行业快讯",
        "en": "⚡ Breaking News"
    },
    "celebrity": {
        "zh": "🐦 领袖观点·社交热议",
        "en": "🐦 Voices & Social X"
    },
    "tools": {
        "zh": "🛠️ 场景落地·实用神器",
        "en": "🛠️ Applied AI Tools"
    },
    "videos": {
        "zh": "🎬 实战视频·演示",
        "en": "🎬 Hands-on Videos"
    },
    "prompts": {
        "zh": "💡 提示词库·咒语",
        "en": "💡 Prompt Bank"
    }
}

# 场景分类标签
SCENARIO_TAGS = {
    "image": "🎨 图像修图/设计",
    "video": "🎬 视频创作合成",
    "code": "💻 编程开发提效",
    "agent": "🤖 智能体/工作流",
    "office": "✍️ 写作办公知识库",
    "audio": "🎙️ 声音克隆音频",
    "chatbot": "💬 AI 客户端应用"
}

# 体验门槛标签
PRICING_TAGS = {
    "free_open": "🟢 开源免费",
    "freemium": "🟡 免费试玩",
    "paid": "🔴 商业软件"
}

# 名人识别库及头像映射 (覆盖全球顶尖 AI 领袖、核心科学家与高频发声一线工程师)
CELEBRITY_PROFILES = {
    # 1. OpenAI 核心团队
    "sam altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama", "platform": "x"},
    "altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama", "platform": "x"},
    "sama": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama", "platform": "x"},
    "greg brockman": {"name": "Greg Brockman", "handle": "@gdb", "role": "OpenAI 总裁兼联合创始人", "avatar": "https://unavatar.io/x/gdb", "platform": "x"},
    "brockman": {"name": "Greg Brockman", "handle": "@gdb", "role": "OpenAI 总裁兼联合创始人", "avatar": "https://unavatar.io/x/gdb", "platform": "x"},
    "noam brown": {"name": "Noam Brown", "handle": "@polynoamial", "role": "OpenAI 推理与 o1/o3 研发负责人", "avatar": "https://unavatar.io/x/polynoamial", "platform": "x"},
    "polynoamial": {"name": "Noam Brown", "handle": "@polynoamial", "role": "OpenAI 推理与 o1/o3 研发负责人", "avatar": "https://unavatar.io/x/polynoamial", "platform": "x"},
    "mira murati": {"name": "Mira Murati", "handle": "@miramurati", "role": "前 OpenAI CTO / 前沿实验室创始人", "avatar": "https://unavatar.io/x/miramurati", "platform": "x"},
    "murati": {"name": "Mira Murati", "handle": "@miramurati", "role": "前 OpenAI CTO / 前沿实验室创始人", "avatar": "https://unavatar.io/x/miramurati", "platform": "x"},
    "mark chen": {"name": "Mark Chen", "handle": "@markchen90", "role": "OpenAI 研究高级副总裁", "avatar": "https://unavatar.io/x/markchen90", "platform": "x"},
    "wojciech zaremba": {"name": "Wojciech Zaremba", "handle": "@woj_zaremba", "role": "OpenAI 联合创始人", "avatar": "https://unavatar.io/x/woj_zaremba", "platform": "x"},
    "john schulman": {"name": "John Schulman", "handle": "@johnschulman2", "role": "PPO/RLHF 奠基人 / Anthropic 科学家", "avatar": "https://unavatar.io/x/johnschulman2", "platform": "x"},

    # 2. Anthropic 核心团队
    "dario amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO 兼联合创始人", "avatar": "https://unavatar.io/anthropic", "platform": "x"},
    "amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO 兼联合创始人", "avatar": "https://unavatar.io/anthropic", "platform": "x"},
    "amanda askell": {"name": "Amanda Askell", "handle": "@AmandaAskell", "role": "Anthropic 对齐与性格哲学负责人", "avatar": "https://unavatar.io/x/AmandaAskell", "platform": "x"},
    "askell": {"name": "Amanda Askell", "handle": "@AmandaAskell", "role": "Anthropic 对齐与性格哲学负责人", "avatar": "https://unavatar.io/x/AmandaAskell", "platform": "x"},
    "chris olah": {"name": "Chris Olah", "handle": "@ch402", "role": "Anthropic 联合创始人 / 可解释性先驱", "avatar": "https://unavatar.io/x/ch402", "platform": "x"},
    "jack clark": {"name": "Jack Clark", "handle": "@jackclarkSF", "role": "Anthropic 联合创始人 / AI Policy", "avatar": "https://unavatar.io/x/jackclarkSF", "platform": "x"},

    # 3. Google & DeepMind 核心团队
    "demis hassabis": {"name": "Demis Hassabis", "handle": "@demishassabis", "role": "Google DeepMind CEO / 诺奖得主", "avatar": "https://unavatar.io/x/demishassabis", "platform": "x"},
    "hassabis": {"name": "Demis Hassabis", "handle": "@demishassabis", "role": "Google DeepMind CEO / 诺奖得主", "avatar": "https://unavatar.io/x/demishassabis", "platform": "x"},
    "jeff dean": {"name": "Jeff Dean", "handle": "@JeffDean", "role": "Google 首席科学家 / 架构泰斗", "avatar": "https://unavatar.io/x/JeffDean", "platform": "x"},
    "oriol vinyals": {"name": "Oriol Vinyals", "handle": "@OriolVinyalsML", "role": "Google DeepMind 研究副总裁", "avatar": "https://unavatar.io/x/OriolVinyalsML", "platform": "x"},
    "logan kilpatrick": {"name": "Logan Kilpatrick", "handle": "@OfficialLoganK", "role": "Google AI Studio 负责人", "avatar": "https://unavatar.io/x/OfficialLoganK", "platform": "x"},
    "logank": {"name": "Logan Kilpatrick", "handle": "@OfficialLoganK", "role": "Google AI Studio 负责人", "avatar": "https://unavatar.io/x/OfficialLoganK", "platform": "x"},

    # 4. Meta & 开源巨头
    "yann lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家 / 图灵奖得主", "avatar": "https://unavatar.io/x/ylecun", "platform": "x"},
    "lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家 / 图灵奖得主", "avatar": "https://unavatar.io/x/ylecun", "platform": "x"},
    "ylecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家 / 图灵奖得主", "avatar": "https://unavatar.io/x/ylecun", "platform": "x"},
    "mark zuckerberg": {"name": "Mark Zuckerberg", "handle": "@finkd", "role": "Meta CEO / 开源模型推手", "avatar": "https://unavatar.io/x/finkd", "platform": "x"},
    "zuckerberg": {"name": "Mark Zuckerberg", "handle": "@finkd", "role": "Meta CEO / 开源模型推手", "avatar": "https://unavatar.io/x/finkd", "platform": "x"},
    "finkd": {"name": "Mark Zuckerberg", "handle": "@finkd", "role": "Meta CEO / 开源模型推手", "avatar": "https://unavatar.io/x/finkd", "platform": "x"},
    "soumith chintala": {"name": "Soumith Chintala", "handle": "@soumithchintala", "role": "PyTorch 创始人", "avatar": "https://unavatar.io/x/soumithchintala", "platform": "x"},
    "soumithchintala": {"name": "Soumith Chintala", "handle": "@soumithchintala", "role": "PyTorch 创始人", "avatar": "https://unavatar.io/x/soumithchintala", "platform": "x"},

    # 5. NVIDIA 核心团队
    "nvidia": {"name": "NVIDIA 官方团队", "handle": "@NVIDIA", "role": "NVIDIA 官方技术与算力前沿", "avatar": "https://unavatar.io/nvidia", "platform": "x"},
    "jim fan": {"name": "Jim Fan", "handle": "@DrJimFan", "role": "NVIDIA AI Agent 负责人", "avatar": "https://unavatar.io/x/DrJimFan", "platform": "x"},
    "drjimfan": {"name": "Jim Fan", "handle": "@DrJimFan", "role": "NVIDIA AI Agent 负责人", "avatar": "https://unavatar.io/x/DrJimFan", "platform": "x"},
    "openaidevs": {"name": "OpenAI Developers", "handle": "@OpenAIDevs", "role": "OpenAI 开发者官方平台", "avatar": "https://unavatar.io/openai", "platform": "x"},
    "googleai": {"name": "Google AI", "handle": "@GoogleAI", "role": "Google AI 研发官方团队", "avatar": "https://unavatar.io/google", "platform": "x"},
    "anthropicai": {"name": "Anthropic 官方团队", "handle": "@AnthropicAI", "role": "Claude 研发官方团队", "avatar": "https://unavatar.io/anthropic", "platform": "x"},

    # 6. xAI / 独立前沿机构
    "elon musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk", "platform": "x"},
    "musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk", "platform": "x"},
    "ilya sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 联合创始人 / 深度学习泰斗", "avatar": "https://unavatar.io/x/ilyasut", "platform": "x"},
    "sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 联合创始人 / 深度学习泰斗", "avatar": "https://unavatar.io/x/ilyasut", "platform": "x"},
    "andrej karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者 / Eureka Labs", "avatar": "https://unavatar.io/x/karpathy", "platform": "x"},
    "karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者 / Eureka Labs", "avatar": "https://unavatar.io/x/karpathy", "platform": "x"},
    "francois chollet": {"name": "François Chollet", "handle": "@fchollet", "role": "ARC-AGI 创始人 / Keras 作者", "avatar": "https://unavatar.io/x/fchollet", "platform": "x"},
    "chollet": {"name": "François Chollet", "handle": "@fchollet", "role": "ARC-AGI 创始人 / Keras 作者", "avatar": "https://unavatar.io/x/fchollet", "platform": "x"},

    # 7. 一线热门 AI 工程师、明星创始人与布道师
    "arthur mensch": {"name": "Arthur Mensch", "handle": "@arthurmensch", "role": "Mistral AI CEO 兼联合创始人", "avatar": "https://unavatar.io/x/arthurmensch", "platform": "x"},
    "aravind srinivas": {"name": "Aravind Srinivas", "handle": "@AravSrinivas", "role": "Perplexity AI CEO", "avatar": "https://unavatar.io/x/AravSrinivas", "platform": "x"},
    "simon willison": {"name": "Simon Willison", "handle": "@simonw", "role": "独立 AI 工程师 / Prompt Injection 提出者", "avatar": "https://unavatar.io/x/simonw", "platform": "x"},
    "harrison chase": {"name": "Harrison Chase", "handle": "@hwchase17", "role": "LangChain 创始人兼 CEO", "avatar": "https://unavatar.io/x/hwchase17", "platform": "x"},
    "swyx": {"name": "Swyx (Shawn Wang)", "handle": "@swyx", "role": "AI Engineer Foundation / Latent Space", "avatar": "https://unavatar.io/x/swyx", "platform": "x"},
    "george hotz": {"name": "George Hotz (geohot)", "handle": "@realgeohot", "role": "tinygrad 创始人 / 极客黑客", "avatar": "https://unavatar.io/x/realgeohot", "platform": "x"},
    "geohot": {"name": "George Hotz (geohot)", "handle": "@realgeohot", "role": "tinygrad 创始人 / 极客黑客", "avatar": "https://unavatar.io/x/realgeohot", "platform": "x"},
    "bindu reddy": {"name": "Bindu Reddy", "handle": "@bindureddy", "role": "Abacus.ai CEO", "avatar": "https://unavatar.io/x/bindureddy", "platform": "x"},
    "pieter abbeel": {"name": "Pieter Abbeel", "handle": "@pabbeel", "role": "UC 伯克利机器人实验室教授", "avatar": "https://unavatar.io/x/pabbeel", "platform": "x"},
    "deepseek": {"name": "DeepSeek 核心研发团队", "handle": "@deepseek_ai", "role": "DeepSeek 官方研发团队", "avatar": "https://unavatar.io/github/deepseek-ai", "platform": "x"},
    
    # 8. 业界顶尖 AI 公司掌门人、前沿研究员与独立极客观察家 (含大家高度关注的 Tibo)
    "tibo": {"name": "Tibo", "handle": "@tibo_maker", "role": "独立 AI 创作者 / 极客架构观察家", "avatar": "https://unavatar.io/x/tibo_maker", "platform": "x"},
    "tibo_maker": {"name": "Tibo", "handle": "@tibo_maker", "role": "独立 AI 创作者 / 极客架构观察家", "avatar": "https://unavatar.io/x/tibo_maker", "platform": "x"},
    "satya nadella": {"name": "Satya Nadella", "handle": "@satyanadella", "role": "微软董事长兼 CEO", "avatar": "https://unavatar.io/x/satyanadella", "platform": "x"},
    "nadella": {"name": "Satya Nadella", "handle": "@satyanadella", "role": "微软董事长兼 CEO", "avatar": "https://unavatar.io/x/satyanadella", "platform": "x"},
    "jason wei": {"name": "Jason Wei", "handle": "@_jasonwei", "role": "OpenAI 研究员 / 思维链 CoT 奠基人", "avatar": "https://unavatar.io/x/_jasonwei", "platform": "x"},
    "_jasonwei": {"name": "Jason Wei", "handle": "@_jasonwei", "role": "OpenAI 研究员 / 思维链 CoT 奠基人", "avatar": "https://unavatar.io/x/_jasonwei", "platform": "x"},
    "rowan cheung": {"name": "Rowan Cheung", "handle": "@rowancheung", "role": "The Rundown AI 创始人", "avatar": "https://unavatar.io/x/rowancheung", "platform": "x"},
    "guillermo rauch": {"name": "Guillermo Rauch", "handle": "@rauchg", "role": "Vercel CEO / 前端生成式 AI 先驱", "avatar": "https://unavatar.io/x/rauchg", "platform": "x"},
    "rauchg": {"name": "Guillermo Rauch", "handle": "@rauchg", "role": "Vercel CEO / 前端生成式 AI 先驱", "avatar": "https://unavatar.io/x/rauchg", "platform": "x"},
    "amjad masad": {"name": "Amjad Masad", "handle": "@amasad", "role": "Replit CEO / AI Agent 原生环境开创者", "avatar": "https://unavatar.io/x/amasad", "platform": "x"},
    "nat friedman": {"name": "Nat Friedman", "handle": "@natfriedman", "role": "AI 领军投资人 / 前 GitHub CEO", "avatar": "https://unavatar.io/x/natfriedman", "platform": "x"},
    "daniel gross": {"name": "Daniel Gross", "handle": "@danielgross", "role": "SSI 联合创始人 / 前 Apple AI 负责人", "avatar": "https://unavatar.io/x/danielgross", "platform": "x"}
}

# 抓取源清单：严格剔除地方政务/会议水文，仅聚合全球顶尖 AI 突破与极客一线动态
SOURCES = {
    # 1. 全球一线顶级科技媒体突发 (24小时超高频全球榜 + 深度突破)
    "google_news_ai": {
        "name": "Google AI 实时快讯",
        "url": "https://news.google.com/rss/search?q=AI+OR+OpenAI+OR+Anthropic+OR+ChatGPT+when:1d&hl=en-US&gl=US&ceid=US:en",
        "default_category": "news",
        "type": "rss"
    },
    "x_trending_ai": {
        "name": "𝕏 实时爆款热议",
        "url": "https://news.google.com/rss/search?q=site:x.com+AI+OR+LLM+when:1d&hl=en-US&gl=US&ceid=US:en",
        "default_category": "celebrity",
        "platform": "x",
        "type": "x_trending"
    },
    "techmeme_ai": {
        "name": "Techmeme 硅谷风向",
        "url": "https://www.techmeme.com/feed.xml",
        "default_category": "news",
        "type": "rss"
    },
    "wired_ai": {
        "name": "Wired AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss",
        "default_category": "news",
        "type": "rss"
    },
    "venturebeat_ai": {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "default_category": "news",
        "type": "rss"
    },
    "theverge_ai": {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "default_category": "news",
        "type": "rss"
    },
    "arstechnica_ai": {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "default_category": "news",
        "type": "rss"
    },
    "mit_tech_review": {
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
        "default_category": "news",
        "type": "rss"
    },
    "the_decoder": {
        "name": "THE DECODER",
        "url": "https://the-decoder.com/feed/",
        "default_category": "news",
        "type": "rss"
    },
    "hacker_news": {
        "name": "Hacker News",
        "url": "https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI+OR+LLM+OR+OpenAI+OR+Claude+OR+DeepSeek&hitsPerPage=15",
        "default_category": "news",
        "type": "hn_api"
    },

    # 2. 社交平台专栏：全面聚焦 𝕏 (Twitter) 顶尖领袖与科学家独家发声，严禁匿名论坛水帖


    # 3. 场景化落地实用工具 (每日最新免安装可玩应用与高频更新开源神器)
    "github_tools": {
        "name": "GitHub AI 应用",
        "url": "https://api.github.com/search/repositories?q=topic:ai-app+OR+topic:ai-tool+OR+topic:llm-tool+stars:>30&sort=updated&order=desc&per_page=16",
        "default_category": "tools",
        "type": "github_tools"
    },
    "huggingface_spaces": {
        "name": "Hugging Face 体验应用",
        "url": "https://huggingface.co/api/spaces?sort=likes&direction=-1&limit=25",
        "default_category": "tools",
        "type": "hf_spaces"
    },
    "product_hunt": {
        "name": "Product Hunt 新品",
        "url": "https://www.producthunt.com/feed",
        "default_category": "tools",
        "type": "ph_feed"
    },

    # 4. YouTube 高热度实战技巧、经验指南与工作流（接入全球顶级 AI 极客技术源）
    "youtube_channels": [
        {"name": "Fireship", "id": "UCsBjURrPoezykLs9EqgamOA"},
        {"name": "Theo - t3.gg", "id": "UCbRP3c757lWg9M-U7TyEkXA"},
        {"name": "AI Explained", "id": "UCNJ1Ymd5yFuUPtn21xtRbbw"},
        {"name": "Two Minute Papers", "id": "UCbfYPyITQ-7l4upoX8nvctg"},
        {"name": "Matthew Berman", "id": "UCawZsQWqfGSbCI5yjkdVkTA"},
        {"name": "Andrej Karpathy", "id": "UCXUPKJO5MZQN11PqgIvyuvQ"},
        {"name": "3Blue1Brown", "id": "UCYO_jab_esuFRV4b17AJtAw"},
        {"name": "Matt Wolfe", "id": "UChpleBmo18P08aKCIgti38g"},
        {"name": "Yannic Kilcher", "id": "UCZHmQk67mN31gbHey6BVyNw"},
        {"name": "NetworkChuck", "id": "UCOuGATIAbd2DvzJmUgXn2IQ"}
    ]
}

# 顶流 AI 创作者矩阵元数据（前端博主直达栏与多样性展示使用）
AI_CREATORS = [
    {
        "id": "fireship",
        "name": "Fireship",
        "channel_id": "UCsBjURrPoezykLs9EqgamOA",
        "handle": "@fireship",
        "avatar": "https://unavatar.io/youtube/UCsBjURrPoezykLs9EqgamOA",
        "category": "⚡ 极速全栈实战",
        "subscribers": "3.4M+",
        "desc": "极速技术拆解与前沿模型实操"
    },
    {
        "id": "theo",
        "name": "Theo - t3.gg",
        "channel_id": "UCbRP3c757lWg9M-U7TyEkXA",
        "handle": "@t3dotgg",
        "avatar": "https://unavatar.io/x/t3dotgg",
        "category": "🛠️ 全栈工程与架构辩论",
        "subscribers": "360K+",
        "desc": "一线技术选型与模型落地深度评测"
    },
    {
        "id": "aiexplained",
        "name": "AI Explained",
        "channel_id": "UCNJ1Ymd5yFuUPtn21xtRbbw",
        "handle": "@aiexplained-official",
        "avatar": "https://unavatar.io/youtube/UCNJ1Ymd5yFuUPtn21xtRbbw",
        "category": "🔥 深度评测与基准盲测",
        "subscribers": "450K+",
        "desc": "严谨的大模型思考链与测试期计算极限盲测"
    },
    {
        "id": "twominutepapers",
        "name": "Two Minute Papers",
        "channel_id": "UCbfYPyITQ-7l4upoX8nvctg",
        "handle": "@TwoMinutePapers",
        "avatar": "https://unavatar.io/youtube/UCbfYPyITQ-7l4upoX8nvctg",
        "category": "🎓 论文精讲与学术突破",
        "subscribers": "1.7M+",
        "desc": "通俗震撼的前沿 AI 论文与图形学突破精讲"
    },
    {
        "id": "karpathy",
        "name": "Andrej Karpathy",
        "channel_id": "UCXUPKJO5MZQN11PqgIvyuvQ",
        "handle": "@karpathy",
        "avatar": "https://unavatar.io/x/karpathy",
        "category": "🎓 泰斗从零手写原理",
        "subscribers": "1.1M+",
        "desc": "OpenAI 联创手写微积分链式法则与神经网络"
    },
    {
        "id": "3blue1brown",
        "name": "3Blue1Brown",
        "channel_id": "UCYO_jab_esuFRV4b17AJtAw",
        "handle": "@3blue1brown",
        "avatar": "https://unavatar.io/youtube/UCYO_jab_esuFRV4b17AJtAw",
        "category": "🎓 几何直觉与可视化",
        "subscribers": "6.8M+",
        "desc": "Transformer 几何空间与注意力权重无死角拆解"
    },
    {
        "id": "matthew_berman",
        "name": "Matthew Berman",
        "channel_id": "UCawZsQWqfGSbCI5yjkdVkTA",
        "handle": "@matthew_berman",
        "avatar": "https://unavatar.io/youtube/UCawZsQWqfGSbCI5yjkdVkTA",
        "category": "🤖 开源模型与本地实测",
        "subscribers": "680K+",
        "desc": "开源模型微调、极速推理与私有化实测"
    },
    {
        "id": "matt_wolfe",
        "name": "Matt Wolfe",
        "channel_id": "UChpleBmo18P08aKCIgti38g",
        "handle": "@mreflow",
        "avatar": "https://unavatar.io/x/mreflow",
        "category": "🎨 AI 工具与多模态",
        "subscribers": "620K+",
        "desc": "最新 AI 实用工具盘点与多模态工作流"
    },
    {
        "id": "yannic_kilcher",
        "name": "Yannic Kilcher",
        "channel_id": "UCZHmQk67mN31gbHey6BVyNw",
        "handle": "@YannicKilcher",
        "avatar": "https://unavatar.io/youtube/UCZHmQk67mN31gbHey6BVyNw",
        "category": "🎓 硬核论文逐行细读",
        "subscribers": "260K+",
        "desc": "强化学习与大模型底层数学架构精读"
    },
    {
        "id": "networkchuck",
        "name": "NetworkChuck",
        "channel_id": "UCOuGATIAbd2DvzJmUgXn2IQ",
        "handle": "@NetworkChuck",
        "avatar": "https://unavatar.io/youtube/UCOuGATIAbd2DvzJmUgXn2IQ",
        "category": "⚡ 极客网络与硬件本地化",
        "subscribers": "4.2M+",
        "desc": "5分钟在普通笔记本部署本地私密 AI"
    }
]

# 创作者防霸屏与多样性门禁规则 (Author Diversity Gate)
YOUTUBE_DIVERSITY_RULES = {
    "max_viral_per_author": 1,  # 近期爆点专栏中，单个作者最多出现 1 条
    "max_total_per_author": 2,  # 全站视频库中，单个作者最多出现 2 条
}

