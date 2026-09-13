"""
AI Radar Config - Data Sources and Category Definitions
"""

# 分栏定义 (支持中英文)
CATEGORIES = {
    "news": {
        "zh": "⚡ 突发·行业快讯",
        "en": "⚡ Breaking News"
    },
    "celebrity": {
        "zh": "🐦 名人·大V热点",
        "en": "🐦 Leaders & Voices"
    },
    "tools": {
        "zh": "🛠️ 爆款·新AI工具",
        "en": "🛠️ Hot AI Tools"
    },
    "insights": {
        "zh": "💡 实操·前沿精选",
        "en": "💡 Insights & Guides"
    }
}

# 抓取源配置 (全部为 100% 官方免费、公开、高可用源)
SOURCES = {
    # 1. 行业突发权威媒体 RSS
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

    # 2. 全球黑客热榜 (Hacker News Algolia API: 实时无限制免Key)
    "hacker_news": {
        "name": "Hacker News",
        "url": "https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI+OR+LLM+OR+OpenAI+OR+Claude+OR+DeepSeek&hitsPerPage=12",
        "default_category": "news",
        "type": "hn_api"
    },

    # 3. 名人与领袖博客
    "sam_altman_blog": {
        "name": "Sam Altman Blog",
        "url": "https://blog.samaltman.com/posts.atom",
        "default_category": "celebrity",
        "type": "rss"
    },

    # 4. 极客开源经验社区 (Reddit LocalLLaMA RSS)
    "reddit_localllama": {
        "name": "Reddit LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
        "default_category": "insights",
        "type": "rss"
    },

    # 5. Hugging Face 热门趋势模型/应用
    "huggingface_trending": {
        "name": "Hugging Face",
        "url": "https://huggingface.co/api/trending?limit=10",
        "default_category": "tools",
        "type": "hf_trending"
    },

    # 6. GitHub 热门新星 AI 项目
    "github_trending": {
        "name": "GitHub",
        "url": "https://api.github.com/search/repositories?q=topic:artificial-intelligence+created:>2026-08-01&sort=stars&order=desc&per_page=10",
        "default_category": "tools",
        "type": "github_api"
    },

    # 7. 前沿实操与实践博客
    "huggingface_blog": {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "default_category": "insights",
        "type": "rss"
    },
    "simonw_ai": {
        "name": "Simon Willison AI",
        "url": "https://simonwillison.net/atom/everything/",
        "default_category": "insights",
        "type": "rss"
    },

    # 8. 前沿研究预印本 (ArXiv CS.AI)
    "arxiv_ai": {
        "name": "ArXiv AI",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "default_category": "insights",
        "type": "rss"
    }
}
