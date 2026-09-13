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
        "zh": "🎬 爆款演示·实操技巧",
        "en": "🎬 Videos & Prompts"
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

# 名人识别库及头像映射 (覆盖全球顶尖 AI 领袖)
CELEBRITY_PROFILES = {
    "sam altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama", "platform": "x"},
    "altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama", "platform": "x"},
    "elon musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk", "platform": "x"},
    "musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk", "platform": "x"},
    "dario amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO", "avatar": "https://unavatar.io/anthropic", "platform": "x"},
    "amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO", "avatar": "https://unavatar.io/anthropic", "platform": "x"},
    "andrej karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者 / Eureka Labs", "avatar": "https://unavatar.io/x/karpathy", "platform": "x"},
    "karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者 / Eureka Labs", "avatar": "https://unavatar.io/x/karpathy", "platform": "x"},
    "yann lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家", "avatar": "https://unavatar.io/x/ylecun", "platform": "x"},
    "lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家", "avatar": "https://unavatar.io/x/ylecun", "platform": "x"},
    "jim fan": {"name": "Jim Fan", "handle": "@DrJimFan", "role": "NVIDIA AI Agent 负责人", "avatar": "https://unavatar.io/x/DrJimFan", "platform": "x"},
    "drjimfan": {"name": "Jim Fan", "handle": "@DrJimFan", "role": "NVIDIA AI Agent 负责人", "avatar": "https://unavatar.io/x/DrJimFan", "platform": "x"},
    "jensen huang": {"name": "黄仁勋", "handle": "@NVIDIA", "role": "NVIDIA CEO", "avatar": "https://unavatar.io/nvidia", "platform": "x"},
    "huang": {"name": "黄仁勋", "handle": "@NVIDIA", "role": "NVIDIA CEO", "avatar": "https://unavatar.io/nvidia", "platform": "x"},
    "demis hassabis": {"name": "Demis Hassabis", "handle": "@demishassabis", "role": "Google DeepMind CEO", "avatar": "https://unavatar.io/x/demishassabis", "platform": "x"},
    "hassabis": {"name": "Demis Hassabis", "handle": "@demishassabis", "role": "Google DeepMind CEO", "avatar": "https://unavatar.io/x/demishassabis", "platform": "x"},
    "greg brockman": {"name": "Greg Brockman", "handle": "@gdb", "role": "OpenAI 总裁", "avatar": "https://unavatar.io/x/gdb", "platform": "x"},
    "brockman": {"name": "Greg Brockman", "handle": "@gdb", "role": "OpenAI 总裁", "avatar": "https://unavatar.io/x/gdb", "platform": "x"},
    "ilya sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 创始人", "avatar": "https://unavatar.io/x/ilyasut", "platform": "x"},
    "sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 创始人", "avatar": "https://unavatar.io/x/ilyasut", "platform": "x"},
    "francois chollet": {"name": "François Chollet", "handle": "@fchollet", "role": "ARC-AGI 创始人", "avatar": "https://unavatar.io/x/fchollet", "platform": "x"},
    "chollet": {"name": "François Chollet", "handle": "@fchollet", "role": "ARC-AGI 创始人", "avatar": "https://unavatar.io/x/fchollet", "platform": "x"}
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

    # 2. 社交平台专栏：X (Twitter) 与 Reddit 独立监测
    "reddit_singularity": {
        "name": "Reddit r/singularity",
        "url": "https://www.reddit.com/r/singularity/.rss",
        "default_category": "celebrity",
        "platform": "reddit",
        "type": "rss"
    },
    "reddit_chatgpt": {
        "name": "Reddit r/ChatGPT",
        "url": "https://www.reddit.com/r/ChatGPT/.rss",
        "default_category": "celebrity",
        "platform": "reddit",
        "type": "rss"
    },
    "reddit_localllama": {
        "name": "Reddit r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
        "default_category": "celebrity",
        "platform": "reddit",
        "type": "rss"
    },

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

    # 4. YouTube 高热度实战技巧、经验指南与工作流
    "youtube_channels": [
        {"name": "Fireship", "id": "UCsBjURrPoezykLs9EqgamOA"},
        {"name": "Two Minute Papers", "id": "UCbfYPyITQ-7l4upoX8nvctg"},
        {"name": "AI Explained", "id": "UCNJ1Ymd5yFuUPtn21xtRbbw"}
    ]
}
