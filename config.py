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
    "image": "🎨 图像编辑",
    "video": "🎬 视频创作",
    "code": "💻 编程提效",
    "agent": "🤖 智能体",
    "office": "✍️ 写作办公",
    "audio": "🎙️ 声音克隆"
}

# 体验门槛标签
PRICING_TAGS = {
    "free_open": "🟢 开源免费",
    "freemium": "🟡 免费试玩",
    "paid": "🔴 商业软件"
}

# 名人识别库及头像映射
CELEBRITY_PROFILES = {
    "sam altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama"},
    "altman": {"name": "Sam Altman", "handle": "@sama", "role": "OpenAI CEO", "avatar": "https://unavatar.io/x/sama"},
    "elon musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk"},
    "musk": {"name": "Elon Musk", "handle": "@elonmusk", "role": "xAI / Tesla", "avatar": "https://unavatar.io/x/elonmusk"},
    "dario amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO", "avatar": "https://unavatar.io/anthropic"},
    "amodei": {"name": "Dario Amodei", "handle": "@AnthropicAI", "role": "Anthropic CEO", "avatar": "https://unavatar.io/anthropic"},
    "andrej karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者", "avatar": "https://unavatar.io/x/karpathy"},
    "karpathy": {"name": "Andrej Karpathy", "handle": "@karpathy", "role": "AI 领军学者", "avatar": "https://unavatar.io/x/karpathy"},
    "yann lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家", "avatar": "https://unavatar.io/x/ylecun"},
    "lecun": {"name": "Yann LeCun", "handle": "@ylecun", "role": "Meta 首席AI科学家", "avatar": "https://unavatar.io/x/ylecun"},
    "jensen huang": {"name": "黄仁勋", "handle": "@NVIDIA", "role": "NVIDIA CEO", "avatar": "https://unavatar.io/nvidia"},
    "huang": {"name": "黄仁勋", "handle": "@NVIDIA", "role": "NVIDIA CEO", "avatar": "https://unavatar.io/nvidia"},
    "tibo": {"name": "Tibo", "handle": "@tibo_maker", "role": "AI 独立开发者", "avatar": "https://unavatar.io/x/tibo_maker"},
    "ilya sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 联合创始人", "avatar": "https://unavatar.io/x/ilyasut"},
    "sutskever": {"name": "Ilya Sutskever", "handle": "@ilyasut", "role": "SSI 联合创始人", "avatar": "https://unavatar.io/x/ilyasut"}
}

# 抓取源清单
SOURCES = {
    # 1. 行业突发权威媒体
    "techcrunch_ai": {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "default_category": "news",
        "type": "rss"
    },
    "theverge_ai": {
        "name": "The Verge AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "default_category": "news",
        "type": "rss"
    },
    "hacker_news": {
        "name": "Hacker News",
        "url": "https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI+OR+LLM+OR+OpenAI+OR+Claude+OR+DeepSeek&hitsPerPage=15",
        "default_category": "news",
        "type": "hn_api"
    },

    # 2. 名人领袖与一手社区讨论
    "sam_altman_blog": {
        "name": "Sam Altman Blog",
        "url": "https://blog.samaltman.com/posts.atom",
        "default_category": "celebrity",
        "type": "rss"
    },
    "reddit_singularity": {
        "name": "Reddit AI热议",
        "url": "https://www.reddit.com/r/singularity/.rss",
        "default_category": "celebrity",
        "type": "rss"
    },

    # 3. 场景化实用工具 (拒绝单纯模型)
    "product_hunt": {
        "name": "Product Hunt AI",
        "url": "https://www.producthunt.com/feed",
        "default_category": "tools",
        "type": "ph_feed"
    },
    "github_tools": {
        "name": "GitHub AI Tools",
        "url": "https://api.github.com/search/repositories?q=topic:ai-tools+stars:>100&sort=updated&order=desc&per_page=12",
        "default_category": "tools",
        "type": "github_tools"
    },

    # 4. YouTube 顶级视频源
    "youtube_channels": [
        {"name": "Fireship", "id": "UCsBjURrPoezykLs9EqgamOA"},
        {"name": "Two Minute Papers", "id": "UCbfYPyITQ-7l4upoX8nvctg"},
        {"name": "AI Explained", "id": "UCNJ1Ymd5yFuUPtn21xtRbbw"}
    ]
}
