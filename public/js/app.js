
    // Global Edge Image Optimizer via wsrv.nl CDN (WebP, auto-compress, edge cache)
    function optimizeImageUrl(url, width = 480) {
      if (!url || typeof url !== 'string') return '';
      const u = url.trim();
      if (!u || u === 'null' || u === 'undefined' || u === 'none') return '';
      if (u.startsWith('/') || u.startsWith('./')) {
        if (u.includes('/assets/tool-previews/') && !u.includes('?v=')) {
          return u + '?v=4';
        }
        return u;
      }
      if (u.startsWith('data:') || u.startsWith('blob:')) return u;
      if (u.includes('images.openai.com/blob') || u.includes('574ebad3-c5b7-4147')) return '';
      if (u.includes('s0.wp.com') || u.includes('wp.com') || u.includes('youtube.com') || u.includes('ytimg.com') || u.includes('raw.githubusercontent.com') || u.includes('github.com')) {
        return u;
      }
      if (u.includes('images.unsplash.com')) {
        return u.replace(/w=\d+/, `w=${width}`).replace(/q=\d+/, 'q=80') + (u.includes('auto=format') ? '' : '&auto=format');
      }
      return `https://wsrv.nl/?url=${encodeURIComponent(u)}&w=${width}&output=webp&q=80`;
    }

    function optimizeAvatarUrl(url, size = 80) {
      if (!url || typeof url !== 'string') return 'https://api.dicebear.com/7.x/bottts/svg?seed=VIP';
      const u = url.trim();
      if (!u || u === 'null' || u === 'undefined' || u === 'none') return 'https://api.dicebear.com/7.x/bottts/svg?seed=VIP';
      if (u.startsWith('data:') || u.startsWith('blob:')) return u;
      if (u.includes('unavatar.io') || u.includes('twimg.com') || u.includes('pbs.twimg.com')) {
        return `https://wsrv.nl/?url=${encodeURIComponent(u)}&w=${size}&h=${size}&fit=cover&output=webp&q=80`;
      }
      return u;
    }
    const urlParams = new URLSearchParams(window.location.search);
    const paramLang = urlParams.get('lang');
    // 英文为主站 (English-First)：优先尊重 URL 参数与用户主动设定的语言，默认一律为 'en'
    let currentLang = 'en';
    document.documentElement.lang = (currentLang === 'zh') ? 'zh-CN' : 'en';
    let currentTheme = localStorage.getItem('theme') || 'auto';
    let selectedCreator = null;
    let currentTab = 'all';
    let cachedData = null;
    let refreshCountdown = 180;
    let searchQuery = '';
    let toolScenarioFilter = 'all';
    let sideSocialFilter = 'all';
    let socialPlatformFilter = 'all';
    let socialViewMode = 'leader'; // 'leader' (行业大V领袖) | 'viral' (24h全网平台爆帖)
    let viralPlatformFilter = 'all'; // 'all' | 'x' | 'threads'
    let videoTypeFilter = 'all';
    let videoSubFilter = 'all';
    let promptCategoryFilter = 'all';
    let categoryCurrentPage = 1;
    let categoryPageSize = 100;
    try {
      const savedCatSize = Number(localStorage.getItem('ainews_cat_page_size'));
      if ([30, 50, 100].includes(savedCatSize)) {
        categoryPageSize = savedCatSize;
      }
    } catch(e) {}

    const I18N = {
      zh: {
        pageTitle: "AI 资讯雷达 | 全景 AI 动态与场景落地工具站",
        headerTitle: "AI 资讯雷达",
        subtitle: "全网热点 · 社交雷达 · 视频实战 · 落地工具 · 提示词库",
        refreshBtn: "刷新",
        autoRefresh: "自动刷新",
        searchPlaceholder: "搜索关键词...",
        digestTitle: "今日 AI 风向标 (60秒必读 Top 3)",
        digestSubtitle: "· 帮你在最短时间内抓住今日行业核心脉搏",
        digestUpdateTag: "当日实时更新",
        digestLoading: "正在提炼今日重磅...",
        viralTickerTitle: "24h 领袖爆款推文 · 实时走马灯",
        viralTickerSubtitle: "· 汇聚全球 AI 领袖洞见、底层架构拆解、前沿模型动态与极客实战演示",
        viralTickerMore: "全网社交雷达 →",
        newsTitle: "⚡ 突发·行业快讯",
        newsSubCount: "实时追踪",
        newsNoMatch: "暂无符合条件的快讯",
        newsBreakingTag: "⚡ 突发快讯 · 全球追踪",
        sourceLabel: "信源:",
        readMore: "阅读原文 ↗",
        celebTitle: "🐦 社交雷达 · 𝕏 与前沿社区",
        celebSideAll: "全部",
        celebSideX: "𝕏 动态",
        celebSideReddit: "Reddit",
        celebBadgeX: "𝕏 社交动态",
        celebBadgeReddit: "Reddit 深度热议",
        celebVerifiedTitle: "已认证官方/开发者",
        celebOriginalTweet: "${isZh ? '直达原推' : 'Original'} ↗",
        celebViewPost: "查看热帖 ↗",
        celebNoMatch: "暂无该平台动态",
        redditCommunity: "Reddit 极客社群",
        toolsTitle: "🛠️ 场景落地·实用工具",
        allToolsLink: "全部工具 →",
        toolsNoMatch: "暂无落地工具",
        tryTool: "立即体验 ↗",
        toolToday: "今日",
        videosTitle: "🎬 实战视频·演示",
        allVideosLink: "全部视频 →",
        videosNoMatch: "暂无实战视频",
        promptsTitle: "💡 提示词库·实战模版",
        allPromptsLink: "全部提示词 →",
        promptsNoMatch: "暂无符合条件的提示词",
        promptBadge: "💡 核心提示词模版",
        promptModelPrefix: "🎯 推荐: ",
        promptTempPrefix: "⚙️ ",
        copyPrompt: "一键复制提示词 📋",
        copySuccess: "Prompt 提示词已复制到剪贴板！",
        promptGenSota: "当前最新 SOTA 旗舰 (版本优先)",
        promptGenLegacy: "历史模型归档库 (Legacy Archive)",
        promptScenarioAll: "全部场景 / All",
        promptScenarioCode: "💻 编程开发",
        promptScenarioNovel: "✍️ 短剧小说",
        promptScenarioAnalysis: "📊 数据分析",
        promptScenarioReport: "📑 商业报告",
        promptScenarioTravel: "✈️ 生活旅行",
        promptScenarioImage: "🎨 灵感生图",
        promptScenarioVideo: "🎬 动态视效",
        viewSampleOutput: "👀 查看实测生成效果样例 (Sample Output)",
        hideSampleOutput: "收起效果样例 ↑",
        copySampleCodeBtn: "复制代码 📋",
        playVideo: "站内播放 ▶",
        todayTag: "🔥 今日首发",
        readPaper: "精读 →",
        arenaTitle: "🏆 LMSYS 天梯榜",
        arenaSubTag: "Top 25 盲测",
        arenaNoMatch: "暂无评测数据",
        arxivTitle: "📄 ArXiv 每日突破论文",
        arxivSubTag: "极客前沿研读",
        arxivNoMatch: "暂无论文推荐",
        catViewTitle: "专栏全景浏览",
        catViewDesc: "查看该分类下的全部深度收录情报",
        celebFilterAll: "全部动态",
        celebFilterCompany: "🏢 官方机构",
        celebFilterPerson: "👤 大V与研发者",
        socialModeLeader: "🐦 前沿发声",
        socialModeViral: "🔥 24h 热门讨论",
        viralFilterAll: "🔥 全部热门",
        viralFilterX: "𝕏 (Twitter) 热门",
        viralFilterThreads: "🧵 Threads 热议",
        viralNoMatch: "暂无符合条件的 24 小时平台爆帖",
        viralSectionTitle: "🔥 24小时全网平台爆帖 (𝕏 & Threads)",
        viralSectionDesc: "实时感知过去 24 小时内阅读量破万、点赞飙升的全球 AI 极客、开发者与前沿实验原生热帖",
        viralSurgeTag: "⚡ 24h 飙升",
        viewOnThreads: "直达 Threads 原帖 / 互动",
        toolFilterAll: "全部工具",
        toolFilterWeb: "🟢 免部署在线玩",
        toolFilterDesign: "🎨 修图设计",
        toolFilterCode: "💻 编程提效",
        toolFilterClient: "💬 AI客户端",
        toolFilterAgent: "🤖 Agent工作流",
        adLeftTitle: "AI 品牌展示",
        adLeftDesc: "高价值极客定向",
        adRightTitle: "生态精选赞助",
        adRightDesc: "前沿生产力触达",
        videoPlatAll: "全部精选",
        videoPlatYtLong: "YouTube 横屏长视频",
        videoPlatYtShorts: "YouTube Shorts 短视频",
        videoPlatTikTok: "TikTok 爆款短视频",
        promptCatTibo: "🌟 Tibo GPT重置",
        promptCatDeepSeek: "🧠 DeepSeek R4",
        promptCatClaude: "⚡ Claude 5.5",
        promptCatOpenAI: "🎯 OpenAI GPT-6/o3",
        promptCatSora: "🎬 Wan 2.1 / Sora 2",
        videoSubAll: "全部视频",
        videoSubViral: "🔥 近期爆点",
        videoSubTutorial: "🎓 系统教学",
        videoSubInsight: "💡 独家经验",
        videoSubTips: "⚡ 实操技巧",
        videoSubMastery: "🤖 模型技巧",
        promptCatAll: "全部提示词",
        promptCatCoding: "💻 编码架构",
        promptCatImage: "🎨 图像生成",
        promptCatVideo: "🎥 视频生成",
        promptCatReasoning: "🧠 深度推理",
        promptCatResearch: "🔬 学术科研",
        promptCatAgent: "🤖 智能体与MCP",
        promptCatGame3D: "🎮 游戏与3D",
        promptCatWriting: "✍️ 生产力写作",
        promptDirectives: "提示词指令",
        promptUsageGuide: "💡 使用指南: ",
        footerBrand: "🤖 AI 资讯雷达 4.0",
        footerDesc: "高频追踪全球顶级大模型突发、社交前沿动态、落地应用神器与 YouTube 实战实操演示。",
        modalVideoTitle: "AI 视频演示",
        hotTagsLabel: "热门标签:",
        searchResultsHeading: "全站智能检索",
        clearSearch: "清除搜索",
        searchHitsNews: "行业快讯",
        searchHitsCeleb: "社交雷达 · 𝕏 动态",
        searchHitsTools: "场景落地神器",
        searchHitsVideos: "实战视频",
        searchHitsPrompts: "提示词库",
        archiveNews: "查看快讯历史归档",
        archiveCeleb: "查看历史社交动态",
        archiveTools: "查看历史落地神器",
        archiveVideos: "查看历史视频",
        archivePrompts: "查看历史提示词",
        archiveCollapse: "收起历史归档 ↑",
        noRecentNews: "⚡ 今日暂无新增快讯，历史最新收录见下方归档",
        noRecentCeleb: "🐦 暂无新增社交动态，历史最新收录见下方归档",
        noRecentTools: "🛠️ 今日暂无新增神器，历史最新收录见下方归档",
        noRecentVideos: "🎬 今日暂无新增视频，历史最新收录见下方归档",
        noRecentPrompts: "💡 今日暂无新增提示词，历史最新收录见下方归档",
        viralBadge: "🔥 近期爆款",
        viralChip: "🔥 近期爆点",
        aiModalBadge: "资讯概要",
        aiModalBriefingTitle: "事件脉络速览",
        aiModalInsightTitle: "AI 点评",
        aiModalSourceBtn: "阅读原文 / 直达报道",
        aiModalImageHint: "点击查看高清原图",
        aiAnalysisBtn: "资讯概要",
        expandCatNewsArchive: "点击展开历史资讯库",
        collapseCatNewsArchive: "收起历史资讯库 ↑",
        archiveViewTitle: "历史资讯全量归档库",
        archiveViewDesc: "全量沉淀超出24小时的历史快讯、社交前沿动态与落地工具，支持即时分类检索与跨页回溯",
        archiveSearchPlaceholder: "在历史归档中检索...",
        tabs: {
          all: "综合全景",
          news: "行业快讯",
          celebrity: "社交雷达",
          tools: "落地工具",
          videos: "实战视频",
          prompts: "提示词库",
          archive: "全量归档"
        }
      },
      en: {
        pageTitle: "AI Radar | Real-Time Global AI Intel & Applied Tools",
        headerTitle: "AI News Radar",
        subtitle: "Breaking AI · Social Radar · Video Guides · Applied Tools · Prompt Bank",
        refreshBtn: "Refresh",
        autoRefresh: "Auto Refresh",
        searchPlaceholder: "Site-wide search (enter keyword or click hot tags)...",
        digestTitle: "Today's Top 3 Highlights (60s Read)",
        digestSubtitle: "· Grasp the pulse of AI breakthroughs in 60 seconds",
        digestUpdateTag: "Updated Daily in Real-Time",
        digestLoading: "Extracting today's top stories...",
        viralTickerTitle: "Viral AI Titan Tweets",
        viralTickerSubtitle: "· Curated AI titan insights, architecture deep dives, frontier models & builder showcases",
        viralTickerMore: "View All Radar →",
        newsTitle: "⚡ Breaking News & Industry",
        newsSubCount: "Live Radar",
        newsNoMatch: "No matching news found",
        newsBreakingTag: "⚡ Breaking · Global Intel",
        sourceLabel: "Source:",
        readMore: "Read More ↗",
        celebTitle: "🐦 Social Radar · 𝕏 & Community",
        celebSideAll: "All",
        celebSideX: "𝕏 Feed",
        celebSideReddit: "Reddit",
        celebBadgeX: "𝕏 Social Post",
        celebBadgeReddit: "Reddit Discussion",
        celebVerifiedTitle: "Verified Official / Creator",
        celebOriginalTweet: "Original Tweet ↗",
        celebViewPost: "View Post ↗",
        celebNoMatch: "No social posts found",
        redditCommunity: "Reddit Tech Community",
        toolsTitle: "🛠️ Applied AI Tools",
        allToolsLink: "All Tools →",
        toolsNoMatch: "No tools found",
        tryTool: "Try It Out ↗",
        toolToday: "Today",
        videosTitle: "🎬 Hands-on Videos",
        allVideosLink: "All Videos →",
        videosNoMatch: "No hands-on videos found",
        promptsTitle: "💡 Prompt Bank",
        allPromptsLink: "All Prompts →",
        promptsNoMatch: "No prompt templates found",
        promptBadge: "💡 Advanced Prompt Master",
        promptModelPrefix: "🎯 Model: ",
        promptTempPrefix: "⚙️ ",
        copyPrompt: "Copy Prompt 📋",
        copySuccess: "Prompt copied to clipboard!",
        promptGenSota: "Current SOTA Flagships (Version Priority)",
        promptGenLegacy: "Historical Archive (Legacy Models)",
        promptScenarioAll: "All Scenarios",
        promptScenarioCode: "💻 Coding & Dev",
        promptScenarioNovel: "✍️ Fiction & Novel",
        promptScenarioAnalysis: "📊 Data Analysis",
        promptScenarioReport: "📑 Executive Reports",
        promptScenarioTravel: "✈️ Travel & Living",
        promptScenarioImage: "🎨 Visual Generation",
        promptScenarioVideo: "🎬 Dynamic VFX & Video",
        viewSampleOutput: "👀 View Tangible Sample Output",
        hideSampleOutput: "Collapse Sample Output ↑",
        copySampleCodeBtn: "Copy Code 📋",
        playVideo: "Watch Video ▶",
        todayTag: "🔥 TODAY",
        readPaper: "Read Paper →",
        arenaTitle: "🏆 LMSYS Leaderboard",
        arenaSubTag: "Top 25 Live",
        arenaNoMatch: "No benchmark data available",
        arxivTitle: "📄 ArXiv Daily Breakthroughs",
        arxivSubTag: "Geek Research Highlights",
        arxivNoMatch: "No papers available",
        catViewTitle: "Category Panoramic View",
        catViewDesc: "Explore all curated intelligence and tools in this category",
        celebFilterAll: "All Feed",
        celebFilterCompany: "🏢 Official Labs",
        celebFilterPerson: "👤 Researchers & Creators",
        socialModeLeader: "🐦 Frontier Feed",
        socialModeViral: "🔥 Trending Buzz",
        viralFilterAll: "🔥 All Viral",
        viralFilterX: "𝕏 (Twitter) Hits",
        viralFilterThreads: "🧵 Threads Buzz",
        viralNoMatch: "No 24h viral posts matching the criteria",
        viralSectionTitle: "🔥 24h Viral Social Radar (𝕏 & Threads)",
        viralSectionDesc: "Real-time radar tracking 10k+ views & surging AI threads across 𝕏 and Threads in the last 24h",
        viralSurgeTag: "⚡ 24h Surge",
        viewOnThreads: "View on Threads / Join Conversation",
        toolFilterAll: "All Tools",
        toolFilterWeb: "🟢 Online Web App",
        toolFilterDesign: "🎨 Image & Design",
        toolFilterCode: "💻 Coding Dev",
        toolFilterClient: "💬 AI Client",
        toolFilterAgent: "🤖 Agent Workflow",
        adLeftTitle: "AI Brand Space",
        adLeftDesc: "High-Value Tech Reach",
        adRightTitle: "Ecosystem Sponsor",
        adRightDesc: "Next-Gen Productivity",
        videoPlatAll: "All Curated",
        videoPlatYtLong: "YouTube Landscape",
        videoPlatYtShorts: "YouTube Shorts",
        videoPlatTikTok: "TikTok Viral",
        promptCatTibo: "🌟 Tibo GPT Reset",
        promptCatDeepSeek: "🧠 DeepSeek R4",
        promptCatClaude: "⚡ Claude 5.5",
        promptCatOpenAI: "🎯 OpenAI GPT-6/o3",
        promptCatSora: "🎬 Wan 2.1 / Sora 2",
        videoSubAll: "All Videos",
        videoSubViral: "🔥 Trending Viral",
        videoSubTutorial: "🎓 Tutorials",
        videoSubInsight: "💡 Insights",
        videoSubTips: "⚡ Practical Tips",
        videoSubMastery: "🤖 Model Mastery",
        promptCatAll: "All Prompts",
        promptCatCoding: "💻 Coding & Arch",
        promptCatImage: "🎨 Image Gen",
        promptCatVideo: "🎥 Video Gen",
        promptCatReasoning: "🧠 Deep Reasoning",
        promptCatResearch: "🔬 Research",
        promptCatAgent: "🤖 Agents & MCP",
        promptCatGame3D: "🎮 Game & 3D",
        promptCatWriting: "✍️ Writing",
        promptDirectives: "Prompt Directives",
        promptUsageGuide: "💡 Usage Guide: ",
        footerBrand: "🤖 AI Radar 4.0",
        footerDesc: "Tracking global LLM breakthroughs, official lab announcements on 𝕏 & Reddit, applied tools, and hands-on YouTube tutorials in real time.",
        modalVideoTitle: "AI Video Demo",
        hotTagsLabel: "Hot Tags:",
        searchResultsHeading: "Site-wide Intelligence Search",
        clearSearch: "Clear Search",
        searchHitsNews: "Breaking News",
        searchHitsCeleb: "Social Radar · 𝕏 Feed",
        searchHitsTools: "Applied Tools",
        searchHitsVideos: "Hands-on Videos",
        searchHitsPrompts: "Prompt Bank",
        archiveNews: "View Historical News Archive",
        archiveCeleb: "View Historical Social Feed",
        archiveTools: "View Historical Tools Archive",
        archiveVideos: "View Historical Videos",
        archivePrompts: "View Historical Prompts",
        archiveCollapse: "Collapse Archive ↑",
        noRecentNews: "⚡ No new updates today, see historical archive below",
        noRecentCeleb: "🐦 No new social posts today, see historical archive below",
        noRecentTools: "🛠️ No new tools today, see historical archive below",
        noRecentVideos: "🎬 No new videos today, see historical archive below",
        noRecentPrompts: "💡 No new prompts today, see historical archive below",
        viralBadge: "🔥 Viral Hit",
        viralChip: "🔥 Trending Viral",
        aiModalBadge: "News Briefing",
        aiModalBriefingTitle: "Executive News Briefing",
        aiModalInsightTitle: "AI Hot Take",
        aiModalSourceBtn: "Read Full Story",
        aiModalImageHint: "Click to view HD original image",
        aiAnalysisBtn: "Briefing",
        expandCatNewsArchive: "Expand Historical News Archive",
        collapseCatNewsArchive: "Collapse Historical Archive ↑",
        archiveViewTitle: "Historical Intelligence Archive",
        archiveViewDesc: "Comprehensive repository of past AI news, social intel, and practical tools with search and pagination",
        archiveSearchPlaceholder: "Search within archives...",
        tabs: {
          all: "Overview",
          news: "News",
          celebrity: "Social Radar",
          tools: "Tools",
          videos: "Videos",
          prompts: "Prompts",
          archive: "Archive"
        }
      }
    };

    // 技术规格标签翻译助手
    function translateSpecTag(tag, lang) {
      if (lang === 'zh') return tag;
      const dict = {
        "10万卡液冷集群": "100k Liquid Cooled GPUs",
        "物理具身AI": "Physical Embodied AI",
        "后训练推理": "Post-training Reasoning",
        "算力经济学": "Compute Economics",
        "LLM作为CPU内核": "LLM as CPU Kernel",
        "自主Agent": "Autonomous Agents",
        "JEPA架构": "JEPA Architecture",
        "分层世界模型": "World Models",
        "具身智能爆发": "Embodied AI Boom",
        "物理仿真基座": "Physics Simulation Base",
        "安全超级智能": "Safe Superintelligence",
        "可扩展对齐": "Scalable Alignment",
        "混合推理机制": "Hybrid Reasoning",
        "透明思考链": "Transparent Thinking Chain",
        "ARC-AGI评测": "ARC-AGI Benchmark",
        "新技能泛化效率": "Skill Acquisition Speed",
        "科学发现范式": "Scientific Paradigm",
        "加速计算范式": "Accelerated Computing",
        "万亿代工制造": "AI Factory",
        "开源权重": "Open Weights",
        "视觉生成": "Vision Gen",
        "推理模型": "Reasoning Model",
        "长上下文": "Long Context",
        "基准评测": "Benchmark",
        "企业落地": "Enterprise",
        "智能体": "Agent",
        "具身智能": "Embodied AI",
        "算力集群": "Compute Cluster",
        "系统演进": "Systems",
        "世界模型": "World Models",
        "科学发现": "AI for Science",
        "代码生成": "Code Gen",
        "多模态": "Multimodal",
        "声音克隆": "Voice Clone",
        "极低延迟": "Ultra-low Latency",
        "本地部署": "Local Deploy",
        "显存优化": "VRAM Optimization",
        "算力基础设施": "Compute Infrastructure",
        "GPT重置法则": "GPT Reset Rules",
        "上下文净化与深度推导": "Context Purge & Reasoning",
        "GPT重置秘技": "GPT Reset Trick",
        "上下文净化": "Context Purge",
        "思维链CoT奠基": "CoT Reasoning Pioneer",
        "推理模型指引": "Reasoning Model Guidance",
        "前沿模型Scaling": "Frontier Scaling",
        "经验安全对齐": "Empirical Safety",
        "实时多模态": "Real-time Multimodal",
        "亚秒级交互": "Sub-second Interaction",
        "超级智能原则": "Superintelligence Principles",
        "微软MAI准则": "MAI Code of Conduct",
        "防止权力垄断": "Preventing Monopoly",
        "开源前沿模型": "Open Source Frontier",
        "擎天柱价值": "Optimus Value",
        "GPT-6实测": "GPT-6 Testing",
        "Agent地图综合": "Agent Map Synthesis",
        "前沿节奏自律": "Pacing the Frontier",
        "独立安全评估": "Independent Evaluation",
        "全行业团结": "Industry Unity",
        "超级智能向善": "Safe Superintelligence",
        "前沿标准组织": "Standards Body",
        "行业共识": "Industry Consensus",
        "硅谷监管激辩": "SV Regulation Debate",
        "前沿自律": "Frontier Restraint",
        "测试期算力成本暴跌": "Test-time Compute Drops",
        "ARC-AGI基准": "ARC-AGI Benchmark",
        "行业澄清": "Clarification",
        "科研诚信争论": "Research Integrity",
        "算力云网络安全": "Cloud Security",
        "自主Agent防失控": "Rogue Agent Containment",
        "671B MoE 架构": "671B MoE Architecture",
        "128K 上下文": "128K Context",
        "1M 原生上下文": "1M Native Context",
        "2M 极限上下文": "2M Ultra Context",
        "SWE-bench 高分": "SWE-bench Top Score",
        "AIME/数学竞赛级": "AIME / Math Olympiad",
        "开源权重可商用": "Open Weights / Commercial",
        "支持本地/端侧部署": "Local / On-Device Deploy",
        "原生多模态理解": "Native Multimodal",
        "SOTA 深度推理链": "SOTA Reasoning Chain",
        "自主智能体工作流": "Autonomous Agent Workflow",
        "分层世界模型架构": "Hierarchical World Model",
        "FP8/INT4 极限制化": "FP8 / INT4 Quantized",
        "零样本泛化": "Zero-shot Generalization",
        "商业级高清生图": "Commercial HD Gen",
        "SOTA 性能突破": "SOTA Breakthrough",
        "权威测评认证": "Benchmark Verified",
        "Sora2物理世界": "Sora 2 Physics",
        "Wan2.1实测": "Wan 2.1 Demo",
        "离线端侧推理": "Offline Edge AI",
        "DeepSeek R1": "DeepSeek R1",
        "Claude 4.6混合推理": "Claude 4.6 Hybrid",
        "One-Prompt游戏": "One-Prompt Game",
        "Computer Use": "Computer Use",
        "智能体自主操作": "Autonomous Agent OS",
        "具身视觉世界模型": "Embodied World Model",
        "机器人灵巧手": "Dexterous Hands"
      };
      for (const [zhKey, enVal] of Object.entries(dict)) {
        if (tag.includes(zhKey)) {
          return tag.replace(zhKey, enVal);
        }
      }
      return tag;
    }

    // 纯净双语信源名翻译格式化 (Strict Bilingual Isolation)
    function formatSource(source, lang) {
      if (!source) return '';
      if (lang === 'zh') return source;
      const dict = {
        'Techmeme 硅谷风向': 'Techmeme · Silicon Valley',
        'Google AI 实时快讯': 'Google News · AI Alerts',
        '𝕏 实时爆款热议': '𝕏 · Viral Trending',
        '深度落地工具': 'Applied Tools',
        '场景落地应用': 'Practical Apps',
        'Hugging Face 在线应用': 'Hugging Face Spaces',
        '机器之心 产业突破': 'Synced AI',
        '量子位 突破洞察': 'QbitAI',
        '知乎 AI 深度讨论': 'Zhihu AI Column',
        'V2EX 极客实战': 'V2EX AI Nodes',
        '实战技巧 · Prompt': 'Practical Prompts',
        '架构实操': 'Systems Lab',
        '工程实战': 'Engineering',
        'DBA极客': 'DBA Geek',
        '全栈开发': 'Full-Stack',
        '设计前沿': 'Design Studio',
        '智能体实验室': 'Agent Lab',
        '深度学习先锋': 'Deep Learning',
        '学术极客': 'Academic Geek',
        'VC投资人': 'VC Investor',
        '提示词大师': 'Prompt Master',
        '极客实验室': 'Tech Lab',
        'AI编码': 'AI Coding',
        '自动化极客': 'Auto Geek',
        '机器人视界': 'Robotics Lab',
        '视觉先锋': 'Visual Lab'
      };
      let s = source;
      for (const [zhKey, enVal] of Object.entries(dict)) {
        if (s.includes(zhKey)) {
          s = s.replace(zhKey, enVal);
        }
      }
      s = s.replace(/YouTube\s*·\s*[\u4e00-\u9fa5]+/g, 'YouTube AI');
      s = s.replace(/TikTok\s*·\s*[\u4e00-\u9fa5]+/g, 'TikTok AI');
      s = s.replace(/𝕏\s*\(Twitter\)\s*·\s*/g, '𝕏 · ');
      return s;
    }

    // 通用标签双语翻译助手
    function translateTag(tag, lang) {
      if (!tag) return '';
      if (lang === 'zh') return tag;
      const dict = {
        '24h飙升': '24h Viral',
        '近期爆款': 'Viral Hit',
        '近期爆点': 'Viral Hit',
        '爆款生成': 'Viral Video',
        '极客绝技': 'Pro Tip',
        '系统教学': 'System Tutorial',
        '避坑实操': 'Hands-on',
        '视频生成': 'Video Gen',
        '实战技巧': 'Practical Tips',
        '端侧AI': 'Edge AI',
        '智能编程': 'AI Coding',
        '电脑接管': 'Computer Use',
        '具身智能': 'Embodied AI',
        '人形机器人': 'Humanoid Robot',
        '置顶爆款': 'Pinned Viral',
        '𝕏置顶爆款': '𝕏 Pinned',
        '𝕏推特大V': '𝕏 Leader',
        '极客实战': 'Geek Practice',
        '思维链': 'Chain of Thought',
        '反垄断': 'Anti-monopoly',
        '开源生态': 'Open Source',
        '安全自律': 'Frontier Safety',
        '行业协作': 'Industry Collab',
        '标准协议': 'Standards',
        '硅谷风向': 'Silicon Valley',
        '监管辩论': 'Regulation Debate',
        '推理算力': 'Inference Compute',
        '科研诚信': 'Research Integrity',
        '安全对齐': 'Safety Alignment',
        '免部署': 'Zero-Setup Web',
        '客户端': 'Desktop Client',
        '智能体': 'Agent',
        '图像': 'Image Gen',
        '编程': 'Coding',
        '声音': 'Audio',
        '写作': 'Writing',
        '开源': 'Open Source',
        '商业级': 'Enterprise',
        '免费商用': 'Free Commercial',
        '免费': 'Free',
        '离线': 'Offline',
        '本地': 'Local'
      };
      for (const [k, v] of Object.entries(dict)) {
        if (tag.includes(k)) return tag.replace(k, v);
      }
      return tag;
    }

    function hasChineseText(str) {
      return typeof str === 'string' && /[\u4e00-\u9fa5]/.test(str);
    }

    function formatVideoTitle(item, lang) {
      if (!item) return '';
      const rawTitle = item.title || '';
      const rawTitleZh = item.title_zh || '';
      if (lang !== 'zh') {
        return item.title_en || rawTitle;
      }
      // 中文模式：处理类似 "【🔥 近期爆点】The Billion Dollar AI Advantage..."
      const prefixMatch = rawTitleZh.match(/^([【\[].*?[】\]]\s*)/) || rawTitle.match(/^([【\[].*?[】\]]\s*)/);
      const prefix = prefixMatch ? prefixMatch[1] : '';
      const bodyZh = rawTitleZh ? rawTitleZh.replace(/^([【\[].*?[】\]]\s*)/, '').trim() : '';
      
      // 如果 bodyZh 已经有实质中文
      if (hasChineseText(bodyZh)) {
        return prefix + bodyZh;
      }
      
      // 检查摘要 summary_zh 是否包含高质量中文提取
      const summaryZh = item.summary_zh || '';
      if (hasChineseText(summaryZh)) {
        // 滤除常见链接和赞赏前缀
        const cleanSum = summaryZh
          .replace(/^[❤️\s\d+赞·个赞]+\s*/g, '')
          .replace(/https?:\/\/\S+/g, '')
          .replace(/📝.*?https?:\/\/\S+/g, '')
          .replace(/🙏.*?/g, '')
          .trim();
        const firstSentence = cleanSum.split(/[。！？\n]/)[0].trim();
        if (firstSentence && firstSentence.length >= 6 && firstSentence.length <= 45 && hasChineseText(firstSentence)) {
          return prefix + firstSentence;
        }
      }

      // 如果有 bodyZh 则返回，否则返回 rawTitleZh 或 rawTitle
      return rawTitleZh || rawTitle;
    }
    function translateScenarioTag(scenario, lang = 'en') {
      if (!scenario) return lang === 'zh' ? '💻 AI 编程与开发' : '💻 AI Coding & Dev';
      const s = String(scenario);
      if (lang === 'zh') {
        if (/办公|文档|表格|ppt|slide|spreadsheet|excel|pdf|office/i.test(s)) return '📊 办公文档与 PPT';
        if (/视频|剪辑|动漫|短剧|字幕|video|film|subtitle/i.test(s)) return '🎬 视频剪辑与生成';
        if (/语音|声音|音频|音乐|配音|播客|voice|audio|speech|tts|asr/i.test(s)) return '🎙️ 语音对话与音频';
        if (/图像|设计|修图|绘画|3d|建模|画板|image|design|photo|canvas/i.test(s)) return '🎨 图像设计与 3D';
        if (/联网|搜索|浏览器|网页|爬虫|search|browser|crawl|scrape/i.test(s)) return '🌐 联网搜索与浏览器';
        if (/知识库|记忆|笔记|论文|学术|文献|翻译|knowledge|memory|research|rag/i.test(s)) return '🧠 知识库与学术研究';
        if (/金融|量化|交易|股票|求职|简历|面试|健康|医疗|看盘|finance|trading|career|life/i.test(s)) return '💼 金融看盘·求职与生活';
        if (/写作|小说|文案|剧本|社媒|营销|内容创作|writing|copy|marketing|growth/i.test(s)) return '✍️ 写作创作与营销';
        if (/编程|代码|开发|终端|调试|测试|coding|dev|code/i.test(s)) return '💻 AI 编程与开发';
        if (/桌面助手|客户端|聊天|工作台|client|assistant|desktop/i.test(s)) return '💬 AI 桌面助手与客户端';
        if (/网关|路由|推理|算力|沙箱|微调|模型|本地部署|model|api|sandbox|gateway/i.test(s)) return '🔌 模型 API 与本地部署';
        if (/智能体|工作流|多智能体|编排|自动化|agent|workflow/i.test(s)) return '🤖 智能体工作流编排';
        if (hasChineseText(s)) return s;
        return '💻 AI 编程与开发';
      } else {
        if (/办公|文档|表格|ppt|slide|spreadsheet|excel|pdf|office/i.test(s)) return '📊 Office, Docs & PPT';
        if (/视频|剪辑|动漫|短剧|字幕|video|film|subtitle/i.test(s)) return '🎬 Video Editing & Gen';
        if (/语音|声音|音频|音乐|配音|播客|voice|audio|speech|tts|asr/i.test(s)) return '🎙️ Voice, Speech & Audio';
        if (/图像|设计|修图|绘画|3d|建模|画板|image|design|photo|canvas/i.test(s)) return '🎨 Image, Design & 3D';
        if (/联网|搜索|浏览器|网页|爬虫|search|browser|crawl|scrape/i.test(s)) return '🌐 Web Search & Browser';
        if (/知识库|记忆|笔记|论文|学术|文献|翻译|knowledge|memory|research|rag/i.test(s)) return '🧠 Knowledge & Research';
        if (/金融|量化|交易|股票|求职|简历|面试|健康|医疗|看盘|finance|trading|career|life/i.test(s)) return '💼 Finance, Career & Life';
        if (/写作|小说|文案|剧本|社媒|营销|内容创作|writing|copy|marketing|growth/i.test(s)) return '✍️ Writing, Copy & Growth';
        if (/编程|代码|开发|终端|调试|测试|coding|dev|code/i.test(s)) return '💻 AI Coding & Dev';
        if (/桌面助手|客户端|聊天|工作台|client|assistant|desktop/i.test(s)) return '💬 AI Clients & Assistants';
        if (/网关|路由|推理|算力|沙箱|微调|模型|本地部署|model|api|sandbox|gateway/i.test(s)) return '🔌 Model API & Sandbox';
        if (/智能体|工作流|多智能体|编排|自动化|agent|workflow/i.test(s)) return '🤖 Multi-Agent Workflow';
        return '💻 AI Coding & Dev';
      }
    }

    // 运行方式/部署形态标签翻译助手
    function translateRuntimeBadge(badge, lang = 'en') {
      if (!badge) return lang === 'zh' ? '🟢 免部署在线玩' : '🟢 Cloud / Web';
      const b = String(badge);
      if (lang === 'zh') {
        if (/命令行|cli|terminal/i.test(b)) return '⚡ 命令行执行';
        if (/完全开源免费|开源免装|开源免费|开源|open\s*source/i.test(b)) return '🟢 完全开源免费';
        if (/webgpu|免装即用|免部署|在线|web|cloud|online/i.test(b)) return '🟢 免部署在线玩';
        if (/免费试玩|免费试用|试玩|trial|freemium/i.test(b)) return '🟡 免费试玩';
        if (/docker/i.test(b)) return '🐳 Docker 一键部署';
        if (/本地\s*gpu|local\s*gpu/i.test(b)) return '🟢 本地 GPU 运行';
        if (/桌面端|客户端|desktop|native/i.test(b)) return '💻 跨平台桌面端';
        if (/插件|扩展|extension|plugin/i.test(b)) return '💻 浏览器插件';
        if (/api\s*key/i.test(b)) return '🔑 自备 API Key';
        if (hasChineseText(b)) return b;
        return '🟢 免部署在线玩';
      } else {
        if (/命令行|一键执行|cli/i.test(b)) return '⚡ CLI / 1-Click Run';
        if (/开源|open\s*source/i.test(b)) return '🟢 Open Source';
        if (/webgpu|免装即用|免部署|在线|web|cloud|online/i.test(b)) return '🟢 Web Online / Zero-Install';
        if (/免费试玩|免费试用|试玩|trial|freemium/i.test(b)) return '🟡 Free Trial';
        if (/docker/i.test(b)) return '🐳 Docker 1-Click Deploy';
        if (/本地\s*gpu|local\s*gpu/i.test(b)) return '🟢 Local GPU Run';
        if (/桌面端|客户端|desktop/i.test(b)) return '💻 Cross-Platform App';
        if (/插件|工具|extension/i.test(b)) return '💻 Browser Extension';
        if (/api\s*key/i.test(b)) return '🔑 Bring API Key';
        return '🟢 Web App';
      }
    }

    // 计费/收费模式标签翻译助手
    function translatePricingTag(pricing, lang = 'en') {
      if (!pricing) return lang === 'zh' ? '🟢 完全开源免费' : '🟢 Free / Open Source';
      const p = String(pricing);
      if (lang === 'zh') {
        if (/完全开源免费|开源免费|开源|open\s*source/i.test(p)) return '🟢 完全开源免费';
        if (/免费试玩|免费试用|试玩|freemium|trial/i.test(p)) return '🟡 免费试玩 / Freemium';
        if (/免部署在线|在线试玩|web\s*demo/i.test(p)) return '🟢 在线免费体验';
        if (/付费|商业|paid|commercial/i.test(p)) return '💳 商业付费';
        if (/免费|free/i.test(p)) return '🟢 免费使用';
        if (hasChineseText(p)) return p;
        return '🟢 免费使用';
      } else {
        if (/完全开源免费|开源免费|开源|open\s*source/i.test(p)) return '🟢 Open Source & Free';
        if (/免费试玩|免费试用|试玩|freemium|trial/i.test(p)) return '🟡 Free Trial / Freemium';
        if (/免部署在线|在线试玩|web\s*demo/i.test(p)) return '🟢 Free Web Demo';
        if (/付费|商业|paid|commercial/i.test(p)) return '💳 Paid / Commercial';
        if (/免费|free/i.test(p)) return '🟢 Free';
        return '🟢 Freemium';
      }
    }

    // 实操难度标签翻译助手
    function translateDifficultyTag(tag, lang = 'en') {
      if (!tag) return lang === 'zh' ? '🔥 热门实操' : '🔥 Trending Tutorial';
      const t = String(tag);
      if (lang === 'zh') {
        if (/避坑|guide/i.test(t)) return '🛠️ 实战避坑指南';
        if (/工作流|workflow/i.test(t)) return '⚡ 生产级工作流';
        if (/大师课|出图|masterclass/i.test(t)) return '🎨 进阶大师课';
        if (/智能体|agent/i.test(t)) return '🤖 智能体实战';
        if (/语音|voice/i.test(t)) return '🎙️ 语音 Agent 教程';
        if (hasChineseText(t)) return t;
        return '🔥 热门实操';
      } else {
        if (/避坑|guide/i.test(t)) return '🛠️ Hands-on Guide';
        if (/工作流|workflow/i.test(t)) return '⚡ Production Workflow';
        if (/大师课|出图|masterclass/i.test(t)) return '🎨 Studio Masterclass';
        if (/智能体|agent/i.test(t)) return '🤖 Agent Tutorial';
        if (/语音|voice/i.test(t)) return '🎙️ Voice Agent';
        return '🔥 Trending Tutorial';
      }
    }

    // 精确时间解析与相对时间
    function formatTime(rawTime, lang = 'zh') {
      if (!rawTime) return { display: (lang === 'zh' ? '经典收录' : 'Curated'), exactTime: (lang === 'zh' ? '经典收录' : 'Curated'), isToday: false, relative: (lang === 'zh' ? '经典' : 'Curated') };
      try {
        const date = new Date(rawTime);
        if (isNaN(date.getTime())) return { display: rawTime, exactTime: rawTime, isToday: false, relative: rawTime };

        const now = new Date();
        const diffSec = Math.max(0, Math.floor((now - date) / 1000));
        const isToday = diffSec < 86400;

        const Y = date.getFullYear();
        const M = String(date.getMonth() + 1).padStart(2, '0');
        const D = String(date.getDate()).padStart(2, '0');
        const h = String(date.getHours()).padStart(2, '0');
        const m = String(date.getMinutes()).padStart(2, '0');
        const exactTime = `${Y}-${M}-${D} ${h}:${m}`;

        let relative = '';
        if (diffSec < 60) {
          relative = lang === 'zh' ? '刚刚' : 'Just now';
        } else if (diffSec < 3600) {
          const mins = Math.floor(diffSec / 60);
          relative = lang === 'zh' ? `${mins}分钟前` : `${mins}m ago`;
        } else if (diffSec < 86400) {
          const hours = Math.floor(diffSec / 3600);
          relative = lang === 'zh' ? `${hours}小时前` : `${hours}h ago`;
        } else if (diffSec < 86400 * 2) {
          relative = lang === 'zh' ? `昨天 ${h}:${m}` : `Yesterday ${h}:${m}`;
        } else if (diffSec < 86400 * 30) {
          const days = Math.floor(diffSec / 86400);
          relative = lang === 'zh' ? `${days}天前` : `${days}d ago`;
        } else {
          relative = `${Y}-${M}-${D}`;
        }

        return { display: `${exactTime} · ${relative}`, exactTime, relative, isToday };
      } catch (e) {
        return { display: rawTime || '', exactTime: rawTime || '', relative: '', isToday: false };
      }
    }

    // 主题切换控制 (浅色 / 深色 / 系统自适应)
    function setTheme(mode) {
      currentTheme = mode;
      localStorage.setItem('theme', mode);
      applyTheme();
    }

    function applyTheme() {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const isDark = currentTheme === 'dark' || (currentTheme === 'auto' && prefersDark);
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      const btnLight = document.getElementById('theme-btn-light');
      const btnDark = document.getElementById('theme-btn-dark');
      const btnAuto = document.getElementById('theme-btn-auto');

      const activeClass = "px-2 py-1 text-xs rounded-lg transition-all bg-indigo-600 text-white font-bold shadow-sm flex items-center space-x-1";
      const inactiveClass = "px-2 py-1 text-xs rounded-lg transition-all text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white font-medium flex items-center space-x-1";

      if (btnLight) btnLight.className = (currentTheme === 'light') ? activeClass : inactiveClass;
      if (btnDark) btnDark.className = (currentTheme === 'dark') ? activeClass : inactiveClass;
      if (btnAuto) btnAuto.className = (currentTheme === 'auto') ? activeClass : inactiveClass;
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (currentTheme === 'auto') applyTheme();
    });

    // ==========================================
    // 国际化整站自适应翻译引擎配置 (Translate.js - 支持 70+ 全球语种)
    // ==========================================
    const BROWSER_LANG_MAP = {
      'zh-tw': 'chinese_traditional',
      'zh-hk': 'chinese_traditional',
      'zh-mo': 'chinese_traditional',
      'zh-hant': 'chinese_traditional',
      'zh': 'chinese_simplified',
      'zh-cn': 'chinese_simplified',
      'zh-sg': 'chinese_simplified',
      'en': 'english',
      'ja': 'japanese',
      'ko': 'korean',
      'de': 'deutsch', // 德语对应 translate.js 标识为 deutsch (de)
      'fr': 'french',
      'es': 'spanish',
      'ru': 'russian',
      'pt': 'portuguese',
      'it': 'italian',
      'nl': 'dutch',
      'ar': 'arabic',
      'hi': 'hindi',
      'vi': 'vietnamese',
      'th': 'thai',
      'id': 'indonesian',
      'tr': 'turkish',
      'pl': 'polish',
      'uk': 'ukrainian',
      'sv': 'swedish',
      'no': 'norwegian',
      'nb': 'norwegian',
      'nn': 'norwegian',
      'da': 'danish',
      'fi': 'finnish',
      'cs': 'czech',
      'el': 'greek',
      'he': 'hebrew',
      'iw': 'hebrew',
      'ms': 'malay',
      'fil': 'filipino',
      'tl': 'filipino',
      'hu': 'hungarian',
      'ro': 'romanian'
    };

    let currentSiteLang = 'english';

    // 自动探测访客系统/浏览器语言 (仅用于智能提供切换建议，不主动替用户强制修改)
    function detectVisitorLanguage() {
      const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
      if (BROWSER_LANG_MAP[navLang]) {
        return BROWSER_LANG_MAP[navLang];
      }
      const prefix = navLang.split('-')[0];
      if (BROWSER_LANG_MAP[prefix]) {
        return BROWSER_LANG_MAP[prefix];
      }
      return 'english';
    }

    // 默认主站语言为英文 (English-First)，若用户未手动设置过偏好，保持为 'english'
    if (!currentSiteLang) {
      currentSiteLang = (currentLang === 'zh') ? 'chinese_simplified' : 'english';
    }

    // 🌐 全局6大核心专栏官方规范术语字典 (严格单行、固定等比、不受第三方机翻破坏)
    const NAV_TABS_I18N = {
      chinese_simplified: { all: "综合全景", news: "行业快讯", celebrity: "社交雷达", tools: "落地工具", videos: "实战视频", prompts: "提示词库" },
      chinese_traditional: { all: "綜合全景", news: "行業快訊", celebrity: "社交雷達", tools: "落地工具", videos: "實戰影片", prompts: "提示詞庫" },
      english: { all: "Overview", news: "News", celebrity: "Social Radar", tools: "Tools", videos: "Videos", prompts: "Prompts" },
      russian: { all: "Обзор", news: "Новости", celebrity: "Соцсети", tools: "Инструменты", videos: "Видео", prompts: "Промпты" },
      arabic: { all: "نظرة عامة", news: "أخبار", celebrity: "رادار التواصل", tools: "أدوات", videos: "فيديوهات", prompts: "موجهات" },
      japanese: { all: "総合", news: "ニュース", celebrity: "ソーシャル", tools: "AIツール", videos: "動画", prompts: "プロンプト" },
      korean: { all: "종합", news: "뉴스", celebrity: "소셜 레이더", tools: "AI 툴", videos: "실전 영상", prompts: "프롬프트" },
      french: { all: "Vue globale", news: "Actualités", celebrity: "Radar Social", tools: "Outils AI", videos: "Vidéos", prompts: "Prompts" },
      deutsch: { all: "Übersicht", news: "News", celebrity: "Social Radar", tools: "AI-Tools", videos: "Videos", prompts: "Prompts" },
      spanish: { all: "Panorama", news: "Noticias", celebrity: "Radar Social", tools: "Herramientas", videos: "Videos", prompts: "Prompts" },
      italian: { all: "Panoramica", news: "Notizie", celebrity: "Radar Sociale", tools: "Strumenti", videos: "Video", prompts: "Prompt" },
      portuguese: { all: "Visão Geral", news: "Notícias", celebrity: "Radar Social", tools: "Ferramentas", videos: "Vídeos", prompts: "Prompts" },
      dutch: { all: "Overzicht", news: "Nieuws", celebrity: "Sociaal Radar", tools: "AI-Tools", videos: "Video's", prompts: "Prompts" },
      polish: { all: "Przegląd", news: "Wiadomości", celebrity: "Radar Społeczny", tools: "Narzędzia", videos: "Wideo", prompts: "Prompty" },
      ukrainian: { all: "Огляд", news: "Новини", celebrity: "Соцмережі", tools: "Інструменти", videos: "Відео", prompts: "Промпти" },
      turkish: { all: "Genel Bakış", news: "Haberler", celebrity: "Sosyal Radar", tools: "AI Araçları", videos: "Videolar", prompts: "Promptlar" },
      vietnamese: { all: "Tổng quan", news: "Tin vắn", celebrity: "Radar MXH", tools: "Công cụ", videos: "Video", prompts: "Prompt" },
      thai: { all: "ภาพรวม", news: "ข่าวสาร", celebrity: "โซเชียลเรดาร์", tools: "เครื่องมือ AI", videos: "วิดีโอ", prompts: "พรอมต์" },
      indonesian: { all: "Ikhtisar", news: "Berita", celebrity: "Radar Sosial", tools: "Alat AI", videos: "Video", prompts: "Prompt" },
      hindi: { all: "समग्र", news: "समाचार", celebrity: "सोशल रडार", tools: "टूल्स", videos: "वीडियो", prompts: "प्रॉम्प्ट्स" },
      hebrew: { all: "סקירה", news: "חדשות", celebrity: "רדאר חברתי", tools: "כלי AI", videos: "סרטונים", prompts: "פרומפטים" },
      greek: { all: "Επισκόπηση", news: "Ειδήσεις", celebrity: "Κοινωνικά", tools: "Εργαλεία AI", videos: "Βίντεο", prompts: "Prompts" }
    };

    function updateNavTabsLanguage(lang) {
      if (!lang) lang = currentSiteLang || 'chinese_simplified';
      const dict = NAV_TABS_I18N[lang] || (lang === 'zh' ? NAV_TABS_I18N['chinese_simplified'] : NAV_TABS_I18N['english']);
      const keys = ['all', 'news', 'celebrity', 'tools', 'videos', 'prompts'];
      keys.forEach(k => {
        const el = document.getElementById(`nav-text-${k}`);
        if (el && dict[k]) {
          el.textContent = dict[k];
        }
      });
    }

    function initTranslateEngine() {
      if (typeof translate === 'undefined') return;

      translate.selectLanguageTag.show = false;
      translate.service.use('client.edge');
      translate.language.setLocal(window.location.pathname.startsWith('/zh') ? 'chinese_simplified' : 'english');
      if (translate.listener) {
        translate.listener.use = true;
      }

      translate.ignore.class.push('notranslate');
      translate.ignore.id.push('nav-tabs');
      translate.ignore.class.push('code-box');
      translate.ignore.tag.push('code');
      translate.ignore.tag.push('pre');

      // 🌐 注册全局专业术语字典：杜绝“Floor tools”、“All files are archived”等低劣机翻，确保紧凑单行自适应
      if (translate.nomenclature && translate.nomenclature.append) {
        // 英语专业精简术语表
        translate.nomenclature.append('chinese_simplified', 'english', `
综合全景=Overview
行业快讯=News
社交雷达=Social Radar
落地工具=Tools
实战视频=Videos
提示词库=Prompts
全量归档=Archive
全网热点=Trending
前沿发声=Frontier Feed
24h 热门讨论=Trending Buzz
官方机构=Official Labs
大V与研发者=Creators
AI资讯雷达=AI News Radar
全球顶尖 AI 动态高频追踪体系=Global AI Pulse Radar
今日 AI 风向标=Today AI Highlights
自动刷新=Auto Refresh
刷新=Refresh
今日更新=Today Updates
活跃源=Active Sources
监控标签=Tracked Tags
深度研报=Deep Reports
论文专区=Papers
快捷筛选=Quick Filter
全部=All
收藏=Bookmarks
历史资讯全量归档库=Historical Intelligence Archive
全站智能搜索 (模型/动态/工具/论文)...=Global Smart Search...
全站智能搜索...=Search...
        `.trim());

        // 阿拉伯语简明精炼术语表 (防止多词冗余换行)
        translate.nomenclature.append('chinese_simplified', 'arabic', `
综合全景=نظرة عامة
行业快讯=أخبار
社交雷达=رادار التواصل
落地工具=أدوات
实战视频=فيديوهات
提示词库=موجهات
全量归档=الأرشيف
全网热点=شائع
前沿发声=أصوات رائدة
24h 热门讨论=نقاشات 24س
官方机构=جهات رسمية
大V与研发者=مطورون
AI资讯雷达=رادار الذكاء الاصطناعي
        `.trim());

        // 日语
        translate.nomenclature.append('chinese_simplified', 'japanese', `
综合全景=総合
行业快讯=ニュース
社交雷达=ソーシャル
落地工具=AIツール
实战视频=動画
提示词库=プロンプト
全量归档=アーカイブ
全网热点=トレンド
        `.trim());

        // 韩语
        translate.nomenclature.append('chinese_simplified', 'korean', `
综合全景=종합
行业快讯=뉴스
社交雷达=소셜 레이더
落地工具=AI 툴
实战视频=실전 영상
提示词库=프롬프트
全量归档=아카이브
        `.trim());

        // 法语
        translate.nomenclature.append('chinese_simplified', 'french', `
综合全景=Vue globale
行业快讯=Actualités
社交雷达=Radar Social
落地工具=Outils
实战视频=Vidéos
提示词库=Prompts
全量归档=Archives
        `.trim());

        // 德语
        translate.nomenclature.append('chinese_simplified', 'german', `
综合全景=Übersicht
行业快讯=News
社交雷达=Social Radar
落地工具=Tools
实战视频=Videos
提示词库=Prompts
全量归档=Archiv
        `.trim());

        // 西班牙语
        translate.nomenclature.append('chinese_simplified', 'spanish', `
综合全景=Panorama
行业快讯=Noticias
社交雷达=Radar Social
落地工具=Herramientas
实战视频=Videos
提示词库=Prompts
全量归档=Archivo
        `.trim());

        // 俄语
        translate.nomenclature.append('chinese_simplified', 'russian', `
综合全景=Обзор
行业快讯=Новости
社交雷达=Соцсети
落地工具=Инструменты
实战视频=Видео
提示词库=Промпты
全量归档=Архив
        `.trim());
      }

      const selectEl = document.getElementById('site-lang-select');
      if (selectEl && currentSiteLang) {
        // 如果当前语言不在预设的常用选项里，动态添加一个选项显示
        let opt = selectEl.querySelector(`option[value="${currentSiteLang}"]`);
        if (!opt && currentSiteLang !== 'chinese_simplified') {
          opt = document.createElement('option');
          opt.value = currentSiteLang;
          opt.textContent = `🌐 ${currentSiteLang}`;
          selectEl.appendChild(opt);
        }
        selectEl.value = currentSiteLang;
      }

      if (currentSiteLang === 'english') {
        setLanguage('en');
        try {
          if (translate.reset) translate.reset();
        } catch (e) {}
      } else {
        updateNavTabsLanguage(currentSiteLang);
        translate.execute();
        if (currentSiteLang !== 'chinese_simplified') {
          translate.changeLanguage(currentSiteLang);
        }
      }
    }

    function changeSiteLanguage(targetLang, persist = true) {
      currentSiteLang = targetLang;
      if (persist) {
        localStorage.setItem('ai_radar_user_site_lang', targetLang);
      }
      const selectEl = document.getElementById('site-lang-select');
      if (selectEl && selectEl.value !== targetLang) {
        selectEl.value = targetLang;
      }

      // 1. 如果选择中文，直接跳转精美无瑕的中文版 /zh
      if (targetLang === 'chinese_simplified' || targetLang === 'chinese_traditional') {
        localStorage.setItem('ai_radar_user_lang', 'zh');
        if (!window.location.pathname.startsWith('/zh')) {
          window.location.href = '/zh';
          return;
        }
        setLanguage('zh', persist);
        return;
      }

      // 2. 如果选择英文，保持在主站 /
      if (targetLang === 'english') {
        localStorage.setItem('ai_radar_user_lang', 'en');
        if (window.location.pathname.startsWith('/zh')) {
          window.location.href = '/';
          return;
        }
        setLanguage('en', persist);
        if (typeof translate !== 'undefined' && translate.reset) {
          try { translate.reset(); } catch (e) {}
        }
        updateNavTabsLanguage('english');
        return;
      }

      // 3. 其它小语种（日、韩、法、德、西等）：按需动态加载 Translate.js，绝不拖累首屏性能
      loadAndExecuteTranslatePlugin(targetLang);
      updateNavTabsLanguage(targetLang);
    }

    // 动态按需加载翻译插件引擎
    function loadAndExecuteTranslatePlugin(targetLang) {
      const exec = () => {
        try {
          if (typeof translate !== 'undefined') {
            translate.selectLanguageTag.show = false;
            translate.service.use('client.edge');
            translate.language.setLocal(window.location.pathname.startsWith('/zh') ? 'chinese_simplified' : 'english');
            translate.ignore.class.push('notranslate');
            translate.ignore.id.push('nav-tabs');
            translate.ignore.class.push('code-box');
            translate.ignore.tag.push('code');
            translate.ignore.tag.push('pre');
            translate.execute();
            translate.changeLanguage(targetLang);
          }
        } catch (err) {
          console.warn('Translate execution failed:', err);
        }
      };

      if (typeof translate === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://res.zvo.cn/translate/translate.js';
        script.async = true;
        script.onload = exec;
        document.body.appendChild(script);
      } else {
        exec();
      }
    }

    function applyCurrentTranslation() {
      if (typeof translate !== 'undefined' && translate.execute) {
        const lang = localStorage.getItem('ai_radar_user_site_lang') || currentSiteLang;
        if (lang && lang !== 'chinese_simplified' && lang !== 'english') {
          setTimeout(() => {
            try {
              translate.execute();
            } catch (e) {}
          }, 60);
        }
      }
    }

    // 💡 智能系统语言检测与多语言系统本地化提示 (根据访客系统母语自适应呈现提示语，绝不主动强行替用户切换)
    const LANG_SUGGESTION_I18N = {
      'zh-cn': {
        name: '简体中文',
        flag: '🇨🇳',
        target: 'chinese_simplified',
        title: '网页语言切换与翻译',
        desc: '网页语言可在此切换，或使用翻译插件浏览。',
        btn: '切换为中文',
        keep: '保持英文'
      },
      'zh-tw': {
        name: '繁體中文',
        flag: '🇭🇰',
        target: 'chinese_traditional',
        title: '網頁語言切換與翻譯',
        desc: '網頁語言可在此切換，或使用翻譯外掛閱讀。',
        btn: '切換為繁體中文',
        keep: '保持英文'
      },
      'ja': {
        name: '日本語',
        flag: '🇯🇵',
        target: 'japanese',
        title: '言語の切り替えと翻訳',
        desc: 'ウェブページの言語はここで切り替えるか、翻訳プラグインをご利用いただけます。',
        btn: '日本語に切り替え',
        keep: '英語のまま'
      },
      'ko': {
        name: '한국어',
        flag: '🇰🇷',
        target: 'korean',
        title: '언어 전환 및 번역',
        desc: '웹페이지 언어를 여기서 전환하거나 번역 기능을 사용할 수 있습니다.',
        btn: '한국어로 전환',
        keep: '영어 유지'
      },
      'de': {
        name: 'Deutsch',
        flag: '🇩🇪',
        target: 'deutsch',
        title: 'Sprachwechsel & Übersetzung',
        desc: 'Die Website-Sprache kann hier gewechselt oder per Übersetzungs-Plugin gelesen werden.',
        btn: 'Auf Deutsch wechseln',
        keep: 'Englisch behalten'
      },
      'fr': {
        name: 'Français',
        flag: '🇫🇷',
        target: 'french',
        title: 'Changement de langue & Traduction',
        desc: 'La langue de la page peut être modifiée ici, ou vous pouvez utiliser le plugin de traduction.',
        btn: 'Passer en français',
        keep: 'Garder l’anglais'
      },
      'es': {
        name: 'Español',
        flag: '🇪🇸',
        target: 'spanish',
        title: 'Cambio de idioma y traducción',
        desc: 'Puede cambiar el idioma de la página aquí o usar el complemento de traducción.',
        btn: 'Cambiar a español',
        keep: 'Mantener inglés'
      },
      'ru': {
        name: 'Русский',
        flag: '🇷🇺',
        target: 'russian',
        title: 'Смена языка и перевод',
        desc: 'Язык веб-страницы можно переключить здесь или использовать плагин перевода.',
        btn: 'Переключить на русский',
        keep: 'Оставить английский'
      },
      'ar': {
        name: 'العربية',
        flag: '🇸🇦',
        target: 'arabic',
        title: 'تغيير اللغة والترجمة',
        desc: 'يمكنك تغيير لغة الصفحة هنا أو استخدام أداة الترجمة.',
        btn: 'التبديل إلى العربية',
        keep: 'الإبقاء على الإنجليزية'
      },
      'pt': {
        name: 'Português',
        flag: '🇧🇷',
        target: 'portuguese',
        title: 'Mudança de idioma e tradução',
        desc: 'O idioma da página pode ser alterado aqui ou use o recurso de tradução.',
        btn: 'Mudar para português',
        keep: 'Manter em inglês'
      },
      'it': {
        name: 'Italiano',
        flag: '🇮🇹',
        target: 'italian',
        title: 'Cambio lingua e traduzione',
        desc: 'La lingua della pagina può essere modificata qui o usa lo strumento di traduzione.',
        btn: 'Passa all’italiano',
        keep: 'Mantieni l’inglese'
      },
      'vi': {
        name: 'Tiếng Việt',
        flag: '🇻🇳',
        target: 'vietnamese',
        title: 'Chuyển đổi ngôn ngữ & dịch thuật',
        desc: 'Bạn có thể chuyển đổi ngôn ngữ trang web tại đây hoặc sử dụng tiện ích dịch.',
        btn: 'Chuyển sang Tiếng Việt',
        keep: 'Giữ tiếng Anh'
      },
      'id': {
        name: 'Bahasa Indonesia',
        flag: '🇮🇩',
        target: 'indonesian',
        title: 'Ubah Bahasa & Terjemahan',
        desc: 'Bahasa halaman dapat diubah di sini, atau gunakan fitur terjemahan.',
        btn: 'Ubah ke Bahasa Indonesia',
        keep: 'Tetap Bahasa Inggris'
      },
      'th': {
        name: 'ไทย',
        flag: '🇹🇭',
        target: 'thai',
        title: 'เปลี่ยนภาษาและการแปล',
        desc: 'คุณสามารถเปลี่ยนภาษาของหน้าเว็บได้ที่นี่ หรือใช้ปลั๊กอินแปลภาษา',
        btn: 'เปลี่ยนเป็นภาษาไทย',
        keep: 'ใช้ภาษาอังกฤษต่อไป'
      },
      'en': {
        name: 'English',
        flag: '🇬🇧',
        target: 'english',
        title: 'Language Switcher & Translation',
        desc: 'Webpage language can be switched here, or use the translation widget.',
        btn: 'Switch to English',
        keep: 'Dismiss'
      }
    };

    function checkAndShowLangSuggestion() {
      // 若用户在当前页面会话中已主动点击关闭或保持，不再重复弹窗打扰
      if (sessionStorage.getItem('ai_radar_lang_suggest_dismissed')) return;

      // 综合检测浏览器与系统语言列表 (支持 navigator.languages 数组与无痕模式 fallback)
      const langCandidates = [];
      if (Array.isArray(navigator.languages) && navigator.languages.length > 0) {
        navigator.languages.forEach(l => {
          if (l && typeof l === 'string') langCandidates.push(l.toLowerCase());
        });
      }
      const singleLang = (navigator.language || navigator.userLanguage || navigator.browserLanguage || '').toLowerCase();
      if (singleLang && !langCandidates.includes(singleLang)) {
        langCandidates.push(singleLang);
      }

      // 识别访客首选非英语语言（优先匹配系统实际母语）
      let detectedKey = null;
      for (const raw of langCandidates) {
        if (!raw) continue;
        if (raw.startsWith('zh')) {
          if (raw.includes('tw') || raw.includes('hk') || raw.includes('hant') || raw.includes('mo')) {
            detectedKey = 'zh-tw';
          } else {
            detectedKey = 'zh-cn';
          }
          break;
        }
        const prefix = raw.split('-')[0];
        if (LANG_SUGGESTION_I18N[prefix]) {
          detectedKey = prefix;
          break;
        }
      }

      // 如果完全没匹配到具体小语种，但含有英文以外的 BROWSER_LANG_MAP
      if (!detectedKey) {
        for (const raw of langCandidates) {
          const prefix = raw.split('-')[0];
          if (BROWSER_LANG_MAP[raw] || BROWSER_LANG_MAP[prefix]) {
            const mapped = BROWSER_LANG_MAP[raw] || BROWSER_LANG_MAP[prefix];
            if (mapped !== 'english') {
              // 匹配对应配置或回退简中
              detectedKey = (LANG_SUGGESTION_I18N[prefix]) ? prefix : 'zh-cn';
              break;
            }
          }
        }
      }

      // 网站当前实际激活语言 ('english' | 'chinese_simplified' | 'chinese_traditional' | ...)
      const siteLang = currentSiteLang || (currentLang === 'zh' ? 'chinese_simplified' : 'english');

      // 如果用户系统全部都是 pure en，且网站已经是 english，则无需打扰
      if (!detectedKey) {
        // 如果是英文系统且主站也是英文，不弹窗
        if (siteLang === 'english') return;
        // 如果网站不是英文但系统是英文，则提示切换回英文
        detectedKey = 'en';
      }

      const config = LANG_SUGGESTION_I18N[detectedKey] || LANG_SUGGESTION_I18N['zh-cn'];
      
      // 判断是否与网站当前语言冲突（如果网站已经切换为该目标语言，不重复提示）
      if (siteLang === config.target) return;

      const bubble = document.getElementById('lang-suggest-bubble');
      if (!bubble) return;

      const titleEl = document.getElementById('lang-suggest-title');
      const descEl = document.getElementById('lang-suggest-desc');
      const btnEl = document.getElementById('lang-suggest-switch-btn');
      const btnTextEl = document.getElementById('lang-suggest-btn-text');
      const keepBtnEl = document.getElementById('lang-suggest-keep-btn');

      if (titleEl) {
        titleEl.innerHTML = `<span>🌐 ${config.title}</span>`;
      }
      if (descEl) {
        descEl.textContent = config.desc;
      }
      if (btnEl) {
        const flagSpan = btnEl.querySelector('span:first-child');
        if (flagSpan) flagSpan.textContent = config.flag;
        if (btnTextEl) btnTextEl.textContent = config.btn;
        btnEl.onclick = () => {
          changeSiteLanguage(config.target, true);
          dismissLangSuggestion(true);
        };
      }
      if (keepBtnEl) {
        keepBtnEl.textContent = config.keep;
      }

      // 展开提示框 (保证高层级与优雅平滑淡入)
      bubble.classList.remove('hidden', 'pointer-events-none');
      bubble.style.display = 'block';
      setTimeout(() => {
        bubble.style.opacity = '1';
        bubble.style.transform = 'translateY(0)';
      }, 50);

      // 8 秒后自动平滑淡出消失 (严格不主动替用户强制修改语言)
      if (window.langSuggestDismissTimer) clearTimeout(window.langSuggestDismissTimer);
      window.langSuggestDismissTimer = setTimeout(() => {
        dismissLangSuggestion(false);
      }, 8000);
    }

    function dismissLangSuggestion(userDismissed = true) {
      if (window.langSuggestDismissTimer) {
        clearTimeout(window.langSuggestDismissTimer);
        window.langSuggestDismissTimer = null;
      }
      const bubble = document.getElementById('lang-suggest-bubble');
      if (bubble) {
        bubble.style.opacity = '0';
        bubble.style.transform = 'translateY(-8px)';
        setTimeout(() => {
          bubble.style.display = 'none';
          bubble.classList.add('hidden', 'pointer-events-none');
        }, 400);
      }
      if (userDismissed) {
        sessionStorage.setItem('ai_radar_lang_suggest_dismissed', '1');
      }
    }

    // 挂载到全局方便测试与调试
    window.checkAndShowLangSuggestion = checkAndShowLangSuggestion;
    window.dismissLangSuggestion = dismissLangSuggestion;

    // 切换语言基底
    function setLanguage(lang, persist = true) {
      currentLang = lang;
      if (persist) {
        localStorage.setItem('ai_radar_user_lang', lang);
      }
      document.documentElement.lang = (lang === 'zh') ? 'zh-CN' : 'en';
      try {
        const u = new URL(window.location.href);
        if (lang === 'en') {
          u.searchParams.set('lang', 'en');
        } else {
          u.searchParams.delete('lang');
        }
        window.history.replaceState(null, '', u.toString());
      } catch (e) {}

      const btnZh = document.getElementById('lang-zh');
      const btnEn = document.getElementById('lang-en');
      if (btnZh && btnEn) {
        if (lang === 'zh') {
          btnZh.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 bg-indigo-600 text-white shadow-sm";
          btnEn.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white";
        } else {
          btnEn.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 bg-indigo-600 text-white shadow-sm";
          btnZh.className = "px-2.5 py-1 text-xs font-semibold rounded-lg transition-all duration-200 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white";
        }
      }
      const selectEl = document.getElementById('site-lang-select');
      if (selectEl && currentSiteLang) {
        selectEl.value = currentSiteLang;
      }

      const txtLight = document.getElementById('theme-txt-light');
      if (txtLight) txtLight.textContent = (lang === 'zh') ? '浅色' : 'Light';
      const txtDark = document.getElementById('theme-txt-dark');
      if (txtDark) txtDark.textContent = (lang === 'zh') ? '深色' : 'Dark';
      if (typeof currentSocialModalItem !== 'undefined' && currentSocialModalItem) {
        currentSocialModalLang = (lang === 'zh') ? 'zh' : 'en';
        if (typeof renderSocialModalData === 'function') renderSocialModalData();
      }
      const txtAuto = document.getElementById('theme-txt-auto');
      if (txtAuto) txtAuto.textContent = (lang === 'zh') ? '自动' : 'Auto';

      const t = I18N[lang];
      document.title = t.pageTitle;
      const headerTitle = document.getElementById('header-title');
      if (headerTitle) headerTitle.textContent = t.headerTitle;
      const subEl = document.getElementById('header-subtitle');
      if (subEl) subEl.textContent = t.subtitle;
      const refBtn = document.getElementById('refresh-btn-text');
      if (refBtn) refBtn.textContent = t.refreshBtn;
      
      const refreshIndicator = document.getElementById('refresh-indicator');
      if (refreshIndicator) {
        refreshIndicator.innerHTML = `${t.autoRefresh} (<span id="timer">${refreshCountdown}</span>s)`;
      }

      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.placeholder = t.searchPlaceholder;

      const htText = document.getElementById('hot-tags-text');
      if (htText) htText.textContent = t.hotTagsLabel;
      const bClearSearch = document.getElementById('btn-clear-search-text');
      if (bClearSearch) bClearSearch.textContent = t.clearSearch;
      const sLabelNews = document.getElementById('search-label-news');
      if (sLabelNews) sLabelNews.textContent = t.searchHitsNews;
      const sLabelCeleb = document.getElementById('search-label-celeb');
      if (sLabelCeleb) sLabelCeleb.textContent = t.searchHitsCeleb;
      const sLabelTools = document.getElementById('search-label-tools');
      if (sLabelTools) sLabelTools.textContent = t.searchHitsTools;
      const sLabelVideos = document.getElementById('search-label-videos');
      if (sLabelVideos) sLabelVideos.textContent = t.searchHitsVideos;
      renderHotTags();

      const dTitle = document.getElementById('digest-title');
      if (dTitle) dTitle.textContent = t.digestTitle;
      const digestSub = document.getElementById('digest-subtitle');
      if (digestSub) digestSub.textContent = t.digestSubtitle;
      const digestTag = document.getElementById('digest-update-tag');
      if (digestTag) digestTag.textContent = t.digestUpdateTag;

      const vtTitle = document.getElementById('viral-ticker-title');
      if (vtTitle) vtTitle.textContent = t.viralTickerTitle;
      const vtSub = document.getElementById('viral-ticker-subtitle');
      if (vtSub) vtSub.textContent = t.viralTickerSubtitle;
      const vtMore = document.getElementById('viral-ticker-more');
      if (vtMore) vtMore.textContent = t.viralTickerMore;

      const topThreeLoading = document.getElementById('top-three-loading');
      if (topThreeLoading) topThreeLoading.textContent = t.digestLoading;

      const secNews = document.getElementById('section-title-news');
      if (secNews) secNews.textContent = t.newsTitle;
      const newsSub = document.getElementById('news-sub-count');
      if (newsSub) newsSub.textContent = t.newsSubCount;

      const secCeleb = document.getElementById('section-title-celebrity');
      if (secCeleb) secCeleb.textContent = t.celebTitle;
      const sideAll = document.getElementById('side-social-all');
      if (sideAll) sideAll.textContent = t.celebSideAll;
      const sideX = document.getElementById('side-social-x');
      if (sideX) sideX.textContent = t.celebSideX;
      const sideReddit = document.getElementById('side-social-reddit');
      if (sideReddit) sideReddit.textContent = t.celebSideReddit;

      const secTools = document.getElementById('section-title-tools');
      if (secTools) secTools.textContent = t.toolsTitle;
      const linkTools = document.getElementById('link-all-tools');
      if (linkTools) linkTools.textContent = t.allToolsLink;

      const secVideos = document.getElementById('section-title-videos');
      if (secVideos) secVideos.textContent = t.videosTitle;
      const linkVideos = document.getElementById('link-all-videos');
      if (linkVideos) linkVideos.textContent = t.allVideosLink;

      const secArena = document.getElementById('section-title-arena');
      if (secArena) secArena.innerHTML = `<span>${t.arenaTitle}</span>`;
      const arenaTag = document.getElementById('arena-sub-tag');
      if (arenaTag) arenaTag.textContent = t.arenaSubTag;

      const secArxiv = document.getElementById('section-title-arxiv');
      if (secArxiv) secArxiv.innerHTML = `<span>${t.arxivTitle}</span>`;
      const arxivTag = document.getElementById('arxiv-sub-tag');
      if (arxivTag) arxivTag.textContent = t.arxivSubTag;

      if (currentSiteLang && currentSiteLang !== 'chinese_simplified') {
        updateNavTabsLanguage(currentSiteLang);
      } else {
        updateNavTabsLanguage(lang === 'zh' ? 'chinese_simplified' : 'english');
      }

      const catTitle = document.getElementById('cat-view-title');
      if (catTitle) catTitle.textContent = t.tabs[currentTab] || t.catViewTitle;
      const catDesc = document.getElementById('cat-view-desc');
      if (catDesc) catDesc.textContent = t.catViewDesc;

      // 更新专栏子筛选按钮文本
      const cfAll = document.getElementById('celeb-filter-all');
      if (cfAll) cfAll.textContent = t.celebFilterAll;
      const cfCompany = document.getElementById('celeb-filter-company');
      if (cfCompany) cfCompany.textContent = t.celebFilterCompany;
      const cfPerson = document.getElementById('celeb-filter-person');
      if (cfPerson) cfPerson.textContent = t.celebFilterPerson;

      const txtLeader = document.getElementById('txt-social-mode-leader');
      if (txtLeader) txtLeader.textContent = t.socialModeLeader;
      const txtViral = document.getElementById('txt-social-mode-viral');
      if (txtViral) txtViral.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>${t.socialModeViral}`;
      const vfAll = document.getElementById('viral-filter-all');
      if (vfAll) vfAll.textContent = t.viralFilterAll;
      const vfX = document.getElementById('viral-filter-x');
      if (vfX) vfX.textContent = t.viralFilterX;
      const vfThreads = document.getElementById('viral-filter-threads');
      if (vfThreads) vfThreads.textContent = t.viralFilterThreads;

      const toLabel = document.getElementById('tool-origin-label');
      if (toLabel) toLabel.textContent = (lang === 'zh') ? '🧭 价值维度:' : '🧭 Dimension:';
      const tsLabel = document.getElementById('tool-scenario-label');
      if (tsLabel) tsLabel.textContent = (lang === 'zh') ? '🛠️ 日常场景:' : '🛠️ Daily Scenarios:';
      const toAll = document.getElementById('tool-origin-all');
      if (toAll) toAll.textContent = (lang === 'zh') ? '⚡ 综合多源精选' : '⚡ All Curated';
      const toGh = document.getElementById('tool-origin-github');
      if (toGh) toGh.textContent = (lang === 'zh') ? '📈 本周指数飙升 (GitHub)' : '📈 Weekly Star Surge (GitHub)';
      const toWeb = document.getElementById('tool-origin-web');
      if (toWeb) toWeb.textContent = (lang === 'zh') ? '🌐 免装 Web 应用' : '🌐 Web Apps (Zero-Install)';
      const toHf = document.getElementById('tool-origin-huggingface');
      if (toHf) toHf.textContent = (lang === 'zh') ? '🤗 在线试玩 Space' : '🤗 Live Spaces';

      const scenLabels = {
        'tool-lbl-all': (lang === 'zh') ? '全部场景' : 'All Scenarios',
        'tool-lbl-code': (lang === 'zh') ? '💻 AI 编程与开发' : '💻 AI Coding & Dev',
        'tool-lbl-client': (lang === 'zh') ? '💬 桌面助手与客户端' : '💬 AI Clients & Assistants',
        'tool-lbl-agent': (lang === 'zh') ? '🤖 智能体工作流' : '🤖 Multi-Agent Workflow',
        'tool-lbl-knowledge': (lang === 'zh') ? '🧠 知识库与学术研究' : '🧠 Knowledge & Research',
        'tool-lbl-browser': (lang === 'zh') ? '🌐 联网搜索与浏览器' : '🌐 Web Search & Browser',
        'tool-lbl-writing': (lang === 'zh') ? '✍️ 写作创作与营销' : '✍️ Writing, Copy & Growth',
        'tool-lbl-life': (lang === 'zh') ? '💼 金融·求职与生活' : '💼 Finance, Career & Life',
        'tool-lbl-design': (lang === 'zh') ? '🎨 图像设计与 3D' : '🎨 Image, Design & 3D',
        'tool-lbl-office': (lang === 'zh') ? '📊 办公文档与 PPT' : '📊 Office, Docs & PPT',
        'tool-lbl-video': (lang === 'zh') ? '🎬 视频剪辑与生成' : '🎬 Video Editing & Gen',
        'tool-lbl-infra': (lang === 'zh') ? '🔌 模型 API 与部署' : '🔌 Model API & Sandbox',
        'tool-lbl-audio': (lang === 'zh') ? '🎙️ 语音对话与音频' : '🎙️ Voice, Speech & Audio'
      };
      Object.entries(scenLabels).forEach(([id, txt]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = txt;
      });

      // 广告位双语占位文本更新
      const elAlt = document.getElementById('ad-left-title');
      if (elAlt) elAlt.textContent = t.adLeftTitle || (lang === 'zh' ? 'AI 品牌展示' : 'AI Brand Space');
      const elAld = document.getElementById('ad-left-desc');
      if (elAld) elAld.textContent = t.adLeftDesc || (lang === 'zh' ? '高价值极客定向' : 'High-Value Tech Reach');
      const elArt = document.getElementById('ad-right-title');
      if (elArt) elArt.textContent = t.adRightTitle || (lang === 'zh' ? '生态精选赞助' : 'Ecosystem Sponsor');
      const elArd = document.getElementById('ad-right-desc');
      if (elArd) elArd.textContent = t.adRightDesc || (lang === 'zh' ? '前沿生产力触达' : 'Next-Gen Productivity');

      // 视频平台分栏与子分类按钮文本更新
      const vpAll = document.getElementById('video-plat-all');
      if (vpAll) vpAll.innerHTML = `<span>🎬</span><span>${t.videoPlatAll || '全部精选'}</span>`;
      const vpYtLong = document.getElementById('video-plat-yt-long');
      if (vpYtLong) vpYtLong.innerHTML = `<span>🖥️</span><span>${t.videoPlatYtLong || 'YouTube 横屏长视频'}</span>`;
      const vpYtShorts = document.getElementById('video-plat-yt-shorts');
      if (vpYtShorts) vpYtShorts.innerHTML = `<span>📱</span><span>${t.videoPlatYtShorts || 'YouTube Shorts 短视频'}</span>`;
      const vpTk = document.getElementById('video-plat-tiktok');
      if (vpTk) vpTk.innerHTML = `<span>🎵</span><span>${t.videoPlatTikTok || 'TikTok 爆款短视频'}</span>`;

      const vsAll = document.getElementById('video-sub-all');
      if (vsAll) vsAll.textContent = t.videoSubAll;
      const vsViral = document.getElementById('video-sub-viral');
      if (vsViral) vsViral.textContent = t.videoSubViral;
      const vsTut = document.getElementById('video-sub-tutorial');
      if (vsTut) vsTut.textContent = t.videoSubTutorial;
      const vsIns = document.getElementById('video-sub-insight');
      if (vsIns) vsIns.textContent = t.videoSubInsight;
      const vsTips = document.getElementById('video-sub-tips');
      if (vsTips) vsTips.textContent = t.videoSubTips;
      const vsMast = document.getElementById('video-sub-mastery');
      if (vsMast) vsMast.textContent = t.videoSubMastery;

      // 提示词代际模式与场景分类筛选按钮更新
      const pgSota = document.getElementById('txt-prompt-gen-sota');
      if (pgSota) pgSota.textContent = t.promptGenSota;
      const pgLegacy = document.getElementById('txt-prompt-gen-legacy');
      if (pgLegacy) pgLegacy.textContent = t.promptGenLegacy;

      const pcAll = document.getElementById('prompt-cat-all');
      if (pcAll) pcAll.textContent = t.promptScenarioAll || '全部场景 / All';
      const pcCode = document.getElementById('prompt-cat-code');
      if (pcCode) pcCode.textContent = t.promptScenarioCode || '💻 编程开发';
      const pcNovel = document.getElementById('prompt-cat-novel');
      if (pcNovel) pcNovel.textContent = t.promptScenarioNovel || '✍️ 短剧小说';
      const pcAnalysis = document.getElementById('prompt-cat-analysis');
      if (pcAnalysis) pcAnalysis.textContent = t.promptScenarioAnalysis || '📊 数据分析';
      const pcReport = document.getElementById('prompt-cat-report');
      if (pcReport) pcReport.textContent = t.promptScenarioReport || '📑 商业报告';
      const pcTravel = document.getElementById('prompt-cat-travel');
      if (pcTravel) pcTravel.textContent = t.promptScenarioTravel || '✈️ 生活旅行';
      const pcImage = document.getElementById('prompt-cat-image');
      if (pcImage) pcImage.textContent = t.promptScenarioImage || '🎨 灵感生图';
      const pcVideo = document.getElementById('prompt-cat-video');
      if (pcVideo) pcVideo.textContent = t.promptScenarioVideo || '🎬 动态视效';

      const secPrompts = document.getElementById('section-title-prompts');
      if (secPrompts) secPrompts.textContent = t.promptsTitle;
      const linkPrompts = document.getElementById('link-all-prompts');
      if (linkPrompts) linkPrompts.textContent = t.allPromptsLink;
      const sLabelPrompts = document.getElementById('search-label-prompts');
      if (sLabelPrompts) sLabelPrompts.textContent = t.searchHitsPrompts;

      // 更新页脚与弹窗
      const fBrand = document.getElementById('footer-brand');
      if (fBrand) fBrand.textContent = t.footerBrand;
      const fArch = document.getElementById('footer-arch');
      if (fArch) fArch.textContent = t.footerArch;
      const fGit = document.getElementById('footer-github');
      if (fGit) fGit.textContent = t.footerGithub;
      const fDesc = document.getElementById('footer-desc');
      if (fDesc) fDesc.textContent = t.footerDesc;

      const modalTitle = document.getElementById('modal-video-title');
      if (modalTitle) modalTitle.textContent = t.modalVideoTitle;
      const arcTitle = document.getElementById('archive-view-title');
      if (arcTitle) arcTitle.textContent = t.archiveViewTitle || '历史资讯全量归档库';
      const arcDesc = document.getElementById('archive-view-desc');
      if (arcDesc) arcDesc.textContent = t.archiveViewDesc || '全量沉淀超出24小时的历史快讯...';
      const arcInput = document.getElementById('archive-search-input');
      if (arcInput) arcInput.placeholder = t.archiveSearchPlaceholder || '在历史归档中检索...';

      if (cachedData) {
        renderUI(cachedData);
      }
    }

    const VALID_TABS = ['all', 'news', 'celebrity', 'tools', 'videos', 'prompts'];

    function getTabFromHash() {
      const hash = (window.location.hash || '').replace('#', '').trim().toLowerCase();
      return VALID_TABS.includes(hash) ? hash : null;
    }

    function handleHashNavigation() {
      const targetTab = getTabFromHash() || 'all';
      if (targetTab !== currentTab) {
        switchTab(targetTab, false);
      }
    }

    // 切换 Tab 分类
    function switchTab(tab, updateHash = true) {
      if (!VALID_TABS.includes(tab)) tab = 'all';
      currentTab = tab;

      if (updateHash) {
        try {
          const currentUrl = new URL(window.location.href);
          if (tab === 'all') {
            currentUrl.hash = '';
            const cleanUrl = currentUrl.pathname + currentUrl.search;
            window.history.replaceState(null, '', cleanUrl);
          } else {
            currentUrl.hash = `#${tab}`;
            window.history.replaceState(null, '', currentUrl.toString());
          }
        } catch (e) {
          if (tab === 'all') {
            window.location.hash = '';
          } else {
            window.location.hash = `#${tab}`;
          }
        }
      }

      if (searchQuery) {
        searchQuery = '';
        const input = document.getElementById('search-input');
        if (input) input.value = '';
        const clearBtn = document.getElementById('btn-clear-search');
        if (clearBtn) clearBtn.classList.add('hidden');
      }
      
      const tabKeys = ['all', 'news', 'celebrity', 'tools', 'videos', 'prompts'];
      tabKeys.forEach(k => {
        const btn = document.getElementById(`tab-btn-${k}`);
        const badge = document.getElementById(`badge-count-${k}`);
        if (btn) {
          const isActive = (k === tab);
          if (isActive) {
            if (k === 'prompts') {
              btn.className = "tab-btn active w-full h-9 sm:h-9.5 rounded-xl text-xs xl:text-sm font-bold transition-all flex items-center justify-center space-x-1 sm:space-x-1.5 px-1 bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/30 overflow-hidden whitespace-nowrap";
            } else {
              btn.className = "tab-btn active w-full h-9 sm:h-9.5 rounded-xl text-xs xl:text-sm font-bold transition-all flex items-center justify-center space-x-1 sm:space-x-1.5 px-1 bg-indigo-600 text-white shadow-md shadow-indigo-600/30 overflow-hidden whitespace-nowrap";
            }
            if (badge) {
              badge.className = "text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-white/20 text-white font-bold font-mono shrink-0 ml-0.5 border border-white/40 shadow-xs backdrop-blur-xs";
            }
          } else {
            if (k === 'prompts') {
              btn.className = "tab-btn w-full h-9 sm:h-9.5 rounded-xl text-xs xl:text-sm font-bold text-purple-800 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/50 border border-purple-300 dark:border-purple-700/70 hover:bg-purple-100 dark:hover:bg-purple-900/60 shadow-sm transition-all flex items-center justify-center space-x-1 sm:space-x-1.5 px-1 overflow-hidden whitespace-nowrap";
              if (badge) badge.className = "text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-900 dark:text-purple-200 border border-purple-300 dark:border-purple-700/70 font-mono font-bold shrink-0 ml-0.5";
            } else {
              btn.className = "tab-btn w-full h-9 sm:h-9.5 rounded-xl text-xs xl:text-sm font-semibold text-slate-800 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/80 transition-all flex items-center justify-center space-x-1 sm:space-x-1.5 px-1 overflow-hidden whitespace-nowrap";
              if (badge) badge.className = "text-[10px] sm:text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-300 dark:border-slate-700 font-mono font-bold shrink-0 ml-0.5";
            }
          }
        }
      });

      const viewAll = document.getElementById('view-all');
      const viewCat = document.getElementById('view-category');
      const viewSearch = document.getElementById('view-search');
      if (viewSearch) viewSearch.classList.add('hidden');
      const celebSubfilter = document.getElementById('celebrity-subfilter');
      const toolsSubfilter = document.getElementById('tools-subfilter');
      const videosSubfilter = document.getElementById('videos-subfilter');
      const promptsSubfilter = document.getElementById('prompts-subfilter');

      const topThreeSection = document.getElementById('top-three-section');
      if (topThreeSection) {
        topThreeSection.classList.toggle('hidden', tab !== 'all');
      }

      if (tab === 'all') {
        if (viewAll) viewAll.classList.remove('hidden');
        if (viewCat) viewCat.classList.add('hidden');
        if (typeof syncThreeColumnsHeight === 'function') setTimeout(syncThreeColumnsHeight, 50);
      } else {
        if (viewAll) viewAll.classList.add('hidden');
        if (viewCat) viewCat.classList.remove('hidden');

        const socialSwitcherWrap = document.getElementById('social-mode-switcher-wrap');
        if (socialSwitcherWrap) {
          socialSwitcherWrap.classList.toggle('hidden', tab !== 'celebrity');
        }
        if (celebSubfilter) {
          celebSubfilter.classList.toggle('hidden', tab !== 'celebrity' || socialViewMode !== 'leader');
        }
        const viralSubfilter = document.getElementById('viral-platform-subfilter');
        if (viralSubfilter) {
          viralSubfilter.classList.toggle('hidden', tab !== 'celebrity' || socialViewMode !== 'viral');
        }
        if (toolsSubfilter) toolsSubfilter.classList.toggle('hidden', tab !== 'tools');
        if (videosSubfilter) videosSubfilter.classList.toggle('hidden', tab !== 'videos');
        if (promptsSubfilter) promptsSubfilter.classList.toggle('hidden', tab !== 'prompts');

        const creatorsRail = document.getElementById('creators-rail-container');
        if (creatorsRail) {
          creatorsRail.classList.toggle('hidden', tab !== 'videos');
          if (tab === 'videos') {
            renderCreatorsRail();
          }
        }

        const t = I18N[currentLang];
        const titleEl = document.getElementById('cat-view-title');
        const catTitles = {
          news: currentLang === 'zh' ? '⚡ 行业突发快讯专栏' : '⚡ Breaking AI News',
          celebrity: currentLang === 'zh' ? '🐦 社交雷达 · 𝕏 与前沿社区动态' : '🐦 Social Radar · 𝕏 & Community Pulse',
          tools: currentLang === 'zh' ? '🛠️ 场景落地·实用工具专栏' : '🛠️ Applied AI Tools Directory',
          videos: currentLang === 'zh' ? '🎬 实战视频·深度演示专栏' : '🎬 Hands-on Video Tutorials',
          prompts: currentLang === 'zh' ? '💡 提示词库·前沿模型实战模版' : '💡 Prompt Bank · SOTA AI System Prompts'
        };
        if (titleEl) titleEl.textContent = catTitles[tab] || t.tabs[tab] || tab;
        const catDesc = document.getElementById('cat-view-desc');
        if (catDesc) catDesc.textContent = t.catViewDesc;
        renderCategoryView(tab);
      }

      // 平滑回滚到内容顶部
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // 热门标签库定义 (支持双语与一键直达检索)
    const HOT_TAGS = [
      { id: 'viral', zh: '🔥 近期爆点', en: '🔥 Trending Viral', query: '爆点' },
      { id: 'fable', zh: '#Fable5.1', en: '#Fable5.1', query: 'fable' },
      { id: 'astra', zh: '#GPT-6Astra', en: '#GPT-6Astra', query: 'astra' },
      { id: 'deepseek', zh: '#DeepSeek', en: '#DeepSeek', query: 'deepseek' },
      { id: 'cursor', zh: '#Cursor', en: '#Cursor', query: 'cursor' },
      { id: 'tutorial', zh: '#🎓 系统教学', en: '#🎓 Tutorials', query: '教学' },
      { id: 'tips', zh: '#⚡ 实操技巧', en: '#⚡ Practical Tips', query: '实操技巧' },
      { id: 'mastery', zh: '#🤖 模型技巧', en: '#🤖 Model Mastery', query: '模型技巧' },
      { id: 'mcp', zh: '#MCP智能体', en: '#MCP Agents', query: 'mcp' },
      { id: 'local', zh: '#本地部署', en: '#Local Deploy', query: '本地部署' },
      { id: 'opensource', zh: '#开源神器', en: '#Open Source', query: '开源' },
      { id: 'web', zh: '#免部署在线玩', en: '#Web Tools', query: '免部署' }
    ];

    // 渲染热门标签栏
    function renderHotTags() {
      const container = document.getElementById('hot-tags-container');
      if (!container) return;
      const isZh = currentLang === 'zh';
      container.innerHTML = HOT_TAGS.map(t => {
        const label = isZh ? t.zh : t.en;
        const isActive = searchQuery === t.query.toLowerCase() || (searchQuery && label.toLowerCase().includes(searchQuery));
        return `<button type="button" onclick="executeTagSearch('${t.query}')" class="px-2.5 py-1 rounded-full text-xs font-medium shrink-0 transition-all ${
          isActive
            ? 'bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/40 border border-indigo-400 scale-105'
            : 'bg-slate-900/80 text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-800/90'
        }">${label}</button>`;
      }).join('');
    }

    // 点击标签直达全站检索
    function executeTagSearch(query) {
      const cleanQ = query.replace(/^#/, '').trim().toLowerCase();
      const searchInput = document.getElementById('search-input');
      if (searchQuery === cleanQ) {
        clearSearch();
      } else {
        searchQuery = cleanQ;
        if (searchInput) searchInput.value = query.replace(/^#/, '');
        updateClearButtonVisibility();
        renderHotTags();
        if (cachedData) renderUI(cachedData);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }

    // 清空全站搜索
    function clearSearch() {
      searchQuery = '';
      const searchInput = document.getElementById('search-input');
      if (searchInput) searchInput.value = '';
      updateClearButtonVisibility();
      renderHotTags();
      if (cachedData) renderUI(cachedData);
    }

    // 更新搜索框内清除图标的显隐
    function updateClearButtonVisibility() {
      const btn = document.getElementById('btn-clear-search');
      if (btn) {
        btn.classList.toggle('hidden', !searchQuery);
      }
    }

    // 历史归档折叠状态管理
    const historyArchiveOpen = {
      news: false,
      celebrity: false,
      tools: false,
      videos: false,
      prompts: false
    };

    function toggleHistoryArchive(sectionKey) {
      historyArchiveOpen[sectionKey] = !historyArchiveOpen[sectionKey];
      const container = document.getElementById(`container-archive-${sectionKey}`);
      const txt = document.getElementById(`txt-archive-${sectionKey}`);
      const arrow = document.getElementById(`arrow-archive-${sectionKey}`);
      const count = container ? (container.dataset.count || '0') : '0';
      const isZh = currentLang === 'zh';

      if (container) {
        if (historyArchiveOpen[sectionKey]) {
          container.classList.remove('hidden');
          if (arrow) arrow.textContent = '▲';
          if (txt) txt.textContent = isZh ? '收起历史归档 ↑' : 'Collapse Archive ↑';
        } else {
          container.classList.add('hidden');
          if (arrow) arrow.textContent = '▼';
          const defaultLabel = sectionKey === 'news' ? (isZh ? `查看历史归档 (已收录 ${count} 条)` : `View Historical News (${count} items)`)
            : sectionKey === 'celebrity' ? (isZh ? `查看历史大V发言 (已收录 ${count} 条)` : `View Historical Voices (${count} items)`)
            : sectionKey === 'tools' ? (isZh ? `查看历史落地工具 (已收录 ${count} 条)` : `View Historical Tools (${count} items)`)
            : sectionKey === 'videos' ? (isZh ? `查看历史实战视频 (已收录 ${count} 条)` : `View Historical Videos (${count} items)`)
            : (isZh ? `查看历史提示词 (已收录 ${count} 条)` : `View Historical Prompts (${count} items)`);
          if (txt) txt.textContent = defaultLabel + ' ↓';
        }
      }
    }

    // 专栏快讯历史归档折叠状态与切换
    let catNewsArchiveOpen = false;
    function toggleCatNewsArchive() {
      catNewsArchiveOpen = !catNewsArchiveOpen;
      const container = document.getElementById('container-cat-news-archive');
      const txt = document.getElementById('txt-cat-news-archive');
      const t = I18N[currentLang];
      const count = container ? (container.dataset.count || '0') : '0';
      if (container) {
        if (catNewsArchiveOpen) {
          container.classList.remove('hidden');
          if (txt) txt.textContent = t.collapseCatNewsArchive || '收起历史资讯库 ↑';
        } else {
          container.classList.add('hidden');
          if (txt) txt.textContent = `${t.expandCatNewsArchive || '点击展开历史资讯库'} (${count} 条) ↓`;
        }
      }
    }

    // 判断条目是否严格在 24 小时有效时效期之内 (首页严格 24 小时门禁，过期坚决清退，一个不留)
    function isWithin24Hours(rawTime) {
      if (!rawTime) return false;
      try {
        const date = new Date(rawTime);
        if (isNaN(date.getTime())) return false;
        const now = new Date();
        const diffSec = Math.floor((now - date) / 1000);
        return diffSec >= -300 && diffSec <= 86400;
      } catch (e) {
        return false;
      }
    }

    // 严格判定是否为 OpenAI Codex 负责人 Thibault Sottiaux (@thsottiaux) 关于 Codex reset 的核心推文 (自发布时间起算维持 24 小时)
    function isTiboResetTweet(item) {
      if (!item || typeof item !== 'object') return false;
      // 严格排除提示词 (prompts) 等非推特分类
      if (item.is_prompt || item.category === 'prompts' || item.sub_type === 'reasoning') return false;

      const handle = (item.author_handle || item.handle || '').toLowerCase().trim();
      const author = (item.author || '').toLowerCase().trim();
      const url = (item.url || '').toLowerCase();

      // 坚决排除 @tibo_maker 等其他博主
      if (handle.includes('tibo_maker') || author.includes('tibo_maker') || url.includes('tibo_maker')) {
        return false;
      }

      // 必须是 OpenAI Codex 负责人 Thibault Sottiaux (@thsottiaux)
      const isThsottiaux = handle.includes('thsottiaux') || url.includes('thsottiaux') || 
                           (author.includes('sottiaux') && (author.includes('tibo') || author.includes('thibault') || author.includes('codex') || author.includes('openai')));
      if (!isThsottiaux) return false;

      const text = ((item.full_text_en || '') + ' ' + (item.full_text_zh || '') + ' ' + (item.title || '') + ' ' + (item.title_en || '') + ' ' + (item.title_zh || '') + ' ' + (item.summary_en || '') + ' ' + (item.summary_zh || '') + ' ' + (item.content_snippet || '')).toLowerCase();
      const isReset = text.includes('reset') || text.includes('重置');
      if (!isReset) return false;

      // 维持24小时 (自推文发布时间起算)
      const rawTime = item.raw_published_at || item.pubDate || item.date || item.created_at || item.time;
      if (!rawTime) return false;
      const pubTs = new Date(rawTime).getTime();
      if (isNaN(pubTs) || pubTs <= 0) return false;
      const diffHours = (Date.now() - pubTs) / (1000 * 3600);
      return diffHours >= -1 && diffHours <= 24;
    }

    // 严格过滤无意义单句推文、脱离语境闲聊回复与空短链接
    function isMeaningfulTweet(it) {
      if (!it || typeof it !== 'object') return false;
      // 凡是出现 Tibo 的 reset 相关推文，在 24 小时内享有最高豁免权，100% 视为有价值推文
      if (isTiboResetTweet(it)) return true;
      const itemId = String(it.id || '');
      if (itemId.startsWith('mock_')) return false;
      const text = (it.full_text_en || it.content_snippet || it.title || '').trim();
      if (!text) return false;
      if (/^https?:\/\/\S+$/i.test(text)) return false;
      const substantive = text.replace(/https?:\/\/\S+|@\w+/g, '').trim();
      const lowValue = /^(?:gm|gn|great|cool|awesome|congrats|congratulations|agreed|same|yes|no|thanks|thank you|lol|lmao|nice|wow|true|facts|word|check this out|excited for this|eyes on this|👀|🔥|🚀|💯|happy to help|appreciate it|welcome|good plans are simple.*|what would you like.*|grok.*|tesla self-driving.*|you can’t possibly.*|legit how i look.*)$/i;
      if (lowValue.test(substantive)) return false;
      const hasMedia = !!(it.image_url || it.video_url || it.has_video || (it.media_urls && it.media_urls.length));
      const isReply = !!(it.isReply || it.is_reply || text.startsWith('@'));
      if (isReply) {
        if (!hasMedia && substantive.length < 120) return false;
      }
      if (!hasMedia) {
        if (substantive.length < 60) return false;
        const sentences = substantive.split(/[.!?。！？\n]+/).map(s => s.trim()).filter(Boolean);
        if (sentences.length <= 1 && substantive.length < 80) return false;
      }
      return true;
    }

    // 搜索输入过滤
    function handleSearch(val) {
      searchQuery = (val || '').trim().toLowerCase();
      updateClearButtonVisibility();
      renderHotTags();
      if (cachedData) {
        renderUI(cachedData);
      }
    }

    // 官方企业、前沿实验室与技术品牌官方推特白名单与判定引擎 (124+ 全景知名品牌矩阵)
    const COMPANY_HANDLES = new Set([
      'aider_ai', 'alibaba_qwen', 'amd', 'anthropic', 'anthropicai', 'anyscalecompute',
      'apple', 'arm', 'artificialanlys', 'augmentcode', 'awscloud', 'baichuanai',
      'baidu_inc', 'baseten', 'bfl_ml', 'businessbarista', 'bytedancetalk', 'cartesia_ai',
      'cerebras', 'cerebrassystems', 'character_ai', 'civitai', 'claudeai', 'clayrun',
      'codeiumdev', 'cognition_labs', 'cohere', 'continuedev', 'coreweave', 'crewaiinc',
      'cursor_ai', 'decagon_ai', 'deepseek', 'deepseek_ai', 'dify_ai', 'elevenlabsio',
      'factoryai', 'fireworksai', 'foxnews', 'ft', 'genspark_ai', 'github',
      'gleansearch', 'googleai', 'googleaistudio', 'googledeepmind', 'groq', 'groqinc',
      'hailuo_ai', 'harvey_ai', 'hedra_labs', 'heptabase', 'heygen_official', 'huggingface',
      'ibmresearch', 'ideogram_ai', 'intelai', 'jandotai', 'kling_ai', 'kobeissiletter',
      'krea_ai', 'lambdaapi', 'langchainai', 'leonardoai_', 'llama_index', 'lmstudioai',
      'lmsysorg', 'lovable_dev', 'luma_ai', 'magic_dev', 'magnific_ai', 'meshyai',
      'meta', 'metaai', 'microsoft', 'midjourney', 'milvusio', 'minimax_ai',
      'mistral', 'mistralai', 'modal_labs', 'moonshotai', 'msftresearch', 'mtslive',
      'notionhq', 'nvidia', 'nvidiaai', 'nvidiaomniverse', 'ollama', 'openai',
      'openaidevs', 'openinterpreter', 'openrouter', 'orbitionnetwork', 'perplexity', 'perplexity_ai',
      'pika_labs', 'pinecone', 'play_ht', 'poe_platform', 'pyautogen', 'qdrant_engine',
      'qualcomm', 'recraftai', 'replicate', 'replit', 'runpod_io', 'runwayml',
      'sambanovaai', 'scale_ai', 'sensetime_tech', 'sgl_project', 'sierra_ai', 'sourcegraph',
      'stabilityai', 'stackblitz', 'stepfun_ai', 'suno_ai_', 'supermaven_ai', 'synthesiaio',
      'tabnine', 'tencentglobal', 'tenstorrent', 'together', 'togethercompute', 'tripoai',
      'trychroma', 'udio', 'unslothai', 'unusual_whales', 'v0', 'vercel',
      'vllm_project', 'warpdotdev', 'weaviate_io', 'weights_biases', 'xai', 'yousearchengine',
      'zhipuai'
    ]);

    function isCompanyOrBrand(it) {
      if (!it) return false;
      if (it.entity_type === 'company') return true;
      if (it.entity_type === 'person') return false;
      const h = (it.author_handle || '').replace(/^@/, '').toLowerCase().trim();
      const a = (it.author || '').toLowerCase().trim();
      // 排除虽然含 official 但实际为个人大V的账号 (如 Logan Kilpatrick)
      if (h === 'officiallogank' || h === 'logank') return false;
      if (COMPANY_HANDLES.has(h)) return true;
      if (/(?:team|devs|studio|labs|corp|inc|media|news|network|letter)/i.test(h)) return true;
      if (a.includes('官方') || a.includes('团队') || a.includes('平台') || a.includes('机构') || a.includes('developers') || a.includes('research team')) return true;
      return false;
    }


    // ==========================================
    // 历史全量归档库管理引擎 (带分类筛选、实时搜索与优雅多页翻查)
    // ==========================================
    let cachedArchiveData = null;
    let archiveLoading = false;
    let archiveCurrentCategory = 'all';
    let archiveSearchQuery = '';
    let archiveCurrentPage = 1;
    const ARCHIVE_PAGE_SIZE = 12;

    async function loadArchiveData() {
      if (cachedArchiveData) return cachedArchiveData;
      if (archiveLoading) return null;
      archiveLoading = true;
      try {
        const res = await fetch('/data/archive_news.json?t=' + Date.now());
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        cachedArchiveData = data;
        updateArchiveBadges();
        return data;
      } catch (e) {
        console.warn('Load archive error:', e);
        return null;
      } finally {
        archiveLoading = false;
      }
    }

    function updateArchiveBadges() {
      const items = cachedArchiveData?.items || [];
      const total = items.length;
      const counts = {
        all: total,
        news: items.filter(it => it.category === 'news').length,
        celebrity: items.filter(it => it.category === 'celebrity').length,
        tools: items.filter(it => it.category === 'tools').length,
        videos: items.filter(it => it.category === 'videos').length
      };

      const setTxt = (id, txt) => {
        const el = document.getElementById(id);
        if (el) el.textContent = txt;
      };

      setTxt('badge-count-archive', total);
      setTxt('arch-count-all', counts.all);
      setTxt('arch-count-news', counts.news);
      setTxt('arch-count-celeb', counts.celebrity);
      setTxt('arch-count-tools', counts.tools);
      setTxt('arch-count-videos', counts.videos);

      const totalBadge = document.getElementById('archive-total-badge');
      if (totalBadge) {
        const isZh = currentLang === 'zh';
        totalBadge.textContent = isZh ? `已收录 ${total} 篇` : `${total} items archived`;
      }
    }

    function filterArchiveCategory(cat) {
      archiveCurrentCategory = cat;
      archiveCurrentPage = 1;
      
      const cats = ['all', 'news', 'celebrity', 'tools', 'videos'];
      cats.forEach(c => {
        const btn = document.getElementById(`arch-cat-${c}`);
        if (!btn) return;
        if (c === cat) {
          btn.className = "arch-filter-btn active px-3 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 text-white shadow-sm shadow-indigo-600/30";
        } else {
          btn.className = "arch-filter-btn px-3 py-1.5 rounded-xl text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700";
        }
      });

      renderArchiveView();
    }

    function handleArchiveSearch(val) {
      archiveSearchQuery = (val || '').trim().toLowerCase();
      archiveCurrentPage = 1;
      const btnClear = document.getElementById('btn-clear-archive-search');
      if (btnClear) btnClear.classList.toggle('hidden', !archiveSearchQuery);
      renderArchiveView();
    }

    function clearArchiveSearch() {
      const input = document.getElementById('archive-search-input');
      if (input) input.value = '';
      archiveSearchQuery = '';
      const btnClear = document.getElementById('btn-clear-archive-search');
      if (btnClear) btnClear.classList.add('hidden');
      archiveCurrentPage = 1;
      renderArchiveView();
    }

    function renderArchiveCard(item) {
      const cat = item.category || 'news';
      if (cat === 'celebrity' || cat === 'leader_opinions') {
        if (item.sub_category === 'viral_post' || item.is_viral) {
          return renderViralPostCard(item);
        }
        return renderCelebrityCard(item);
      }
      if (cat === 'tools' || cat === 'applied_tools') return renderToolCard(item);
      if (cat === 'videos' || cat === 'video_prompts') return renderVideoCard(item);
      if (cat === 'prompts') return renderPromptCard(item);
      return renderNewsCard(item);
    }

    async function renderArchiveView() {
      const container = document.getElementById('archive-grid-container');
      const pageSummary = document.getElementById('archive-page-summary');
      const pagination = document.getElementById('archive-pagination-container');
      if (!container) return;

      const isZh = currentLang === 'zh';

      if (!cachedArchiveData) {
        container.innerHTML = `
          <div class="col-span-1 md:col-span-2 lg:col-span-3 py-16 flex flex-col items-center justify-center space-y-3">
            <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-xs text-slate-400 font-mono">${isZh ? '正在从云端调取全量历史资讯归档库...' : 'Loading full historical archive from cloud...'}</p>
          </div>
        `;
        const data = await loadArchiveData();
        if (!data || !data.items) {
          container.innerHTML = `<div class="col-span-1 md:col-span-2 lg:col-span-3 py-12 text-center text-xs text-slate-400">${isZh ? '暂未加载到归档数据或网络波动，请稍后刷新重试' : 'No archive data available or network error.'}</div>`;
          return;
        }
      }

      let items = cachedArchiveData.items || [];

      // 1. 分类过滤
      if (archiveCurrentCategory !== 'all') {
        items = items.filter(it => it.category === archiveCurrentCategory);
      }

      // 2. 搜索过滤
      if (archiveSearchQuery) {
        items = items.filter(it => {
          const t = (it.title || '').toLowerCase();
          const s = (it.summary || '').toLowerCase();
          const a = (it.author || '').toLowerCase();
          const h = (it.author_handle || '').toLowerCase();
          const tags = Array.isArray(it.tags) ? it.tags.join(' ').toLowerCase() : '';
          return t.includes(archiveSearchQuery) || s.includes(archiveSearchQuery) || a.includes(archiveSearchQuery) || h.includes(archiveSearchQuery) || tags.includes(archiveSearchQuery);
        });
      }

      const totalItems = items.length;
      const totalPages = Math.max(1, Math.ceil(totalItems / ARCHIVE_PAGE_SIZE));

      if (archiveCurrentPage > totalPages) archiveCurrentPage = totalPages;
      if (archiveCurrentPage < 1) archiveCurrentPage = 1;

      // 摘要文本
      if (pageSummary) {
        pageSummary.textContent = isZh
          ? `第 ${archiveCurrentPage} / ${totalPages} 页 · 共 ${totalItems} 条`
          : `Page ${archiveCurrentPage} / ${totalPages} · Total ${totalItems} items`;
      }

      if (totalItems === 0) {
        container.innerHTML = `
          <div class="col-span-1 md:col-span-2 lg:col-span-3 py-16 text-center text-slate-400">
            <span class="text-3xl block mb-2">🔍</span>
            <p class="text-xs">${isZh ? '未找到符合条件的归档情报，请尝试切换分类或搜索关键词' : 'No matching archived items found.'}</p>
          </div>
        `;
        if (pagination) pagination.innerHTML = '';
        return;
      }

      // 3. 切片分页
      const startIndex = (archiveCurrentPage - 1) * ARCHIVE_PAGE_SIZE;
      const pageItems = items.slice(startIndex, startIndex + ARCHIVE_PAGE_SIZE);

      container.innerHTML = pageItems.map(renderArchiveCard).join('');

      // 4. 渲染分页控制器
      renderArchivePagination(totalPages, totalItems);
    }

    function renderArchivePagination(totalPages, totalItems) {
      const pagination = document.getElementById('archive-pagination-container');
      if (!pagination) return;
      if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
      }

      const isZh = currentLang === 'zh';
      const cur = archiveCurrentPage;

      // 生成页码序列 (智能省略算法)
      const pageNumbers = [];
      if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);
      } else {
        pageNumbers.push(1);
        if (cur > 3) pageNumbers.push('...');
        const start = Math.max(2, cur - 1);
        const end = Math.min(totalPages - 1, cur + 1);
        for (let i = start; i <= end; i++) pageNumbers.push(i);
        if (cur < totalPages - 2) pageNumbers.push('...');
        pageNumbers.push(totalPages);
      }

      let html = `
        <div class="text-xs text-slate-500 dark:text-slate-400 font-mono">
          ${isZh ? `显示第 ${(cur-1)*ARCHIVE_PAGE_SIZE + 1} - ${Math.min(cur*ARCHIVE_PAGE_SIZE, totalItems)} 条 · 共 ${totalItems} 条` : `Showing ${(cur-1)*ARCHIVE_PAGE_SIZE + 1}-${Math.min(cur*ARCHIVE_PAGE_SIZE, totalItems)} of ${totalItems}`}
        </div>
        <div class="flex items-center space-x-1.5">
          <button type="button" onclick="changeArchivePage(${cur - 1})" ${cur === 1 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg text-xs font-semibold ${cur === 1 ? 'opacity-40 cursor-not-allowed bg-slate-100 dark:bg-slate-800/40 text-slate-400' : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-indigo-600 hover:text-white border border-slate-300 dark:border-slate-700 cursor-pointer'} transition-all flex items-center space-x-1">
            <span>◀</span>
            <span class="hidden sm:inline">${isZh ? '上一页' : 'Prev'}</span>
          </button>
      `;

      pageNumbers.forEach(p => {
        if (p === '...') {
          html += `<span class="px-2 py-1 text-slate-400 font-mono text-xs">...</span>`;
        } else if (p === cur) {
          html += `<button type="button" class="w-8 h-8 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-sm shadow-indigo-600/30 flex items-center justify-center">${p}</button>`;
        } else {
          html += `<button type="button" onclick="changeArchivePage(${p})" class="w-8 h-8 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 flex items-center justify-center transition-all cursor-pointer">${p}</button>`;
        }
      });

      html += `
          <button type="button" onclick="changeArchivePage(${cur + 1})" ${cur === totalPages ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg text-xs font-semibold ${cur === totalPages ? 'opacity-40 cursor-not-allowed bg-slate-100 dark:bg-slate-800/40 text-slate-400' : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-indigo-600 hover:text-white border border-slate-300 dark:border-slate-700 cursor-pointer'} transition-all flex items-center space-x-1">
            <span class="hidden sm:inline">${isZh ? '下一页' : 'Next'}</span>
            <span>▶</span>
          </button>
        </div>
      `;

      pagination.innerHTML = html;
    }

    function changeArchivePage(p) {
      archiveCurrentPage = p;
      renderArchiveView();
      const el = document.getElementById('view-archive');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }

    // 侧边栏社交平台过滤
    function setSidebarSocialFilter(platform) {
      sideSocialFilter = platform;
      if (cachedData) renderUI(cachedData);
    }

    // 专栏广场：领袖与品牌分类过滤 (全部动态 / 官方企业与品牌 / 行业领袖与大V)
    function filterSocialPlatform(filterType) {
      socialPlatformFilter = filterType;
      categoryCurrentPage = 1;
      celebritySpotlightPage = 0; // 筛选切换时重置爆款头条翻页至第一页
      const btnMap = {
        'all': 'celeb-filter-all',
        'company': 'celeb-filter-company',
        'person': 'celeb-filter-person'
      };
      Object.keys(btnMap).forEach(k => {
        const b = document.getElementById(btnMap[k]);
        if (b) {
          b.className = (k === filterType)
            ? "celeb-filter-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-sky-600 text-white shadow-sm shadow-sky-600/30"
            : "celeb-filter-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700";
        }
      });
      if (currentTab === 'celebrity') {
        renderCategoryView('celebrity');
      } else {
        renderCelebritySpotlightBanner();
      }
    }

    let toolOriginFilter = 'all';

    // 工具多维价值与来源筛选 (今日最新入库 / 本周飙升黑马 / 商业Web与闭源应用 / 免装开箱秒玩 / 开源极客 / HF在线试玩)
    function filterToolOrigin(origin) {
      toolOriginFilter = origin || 'all';
      categoryCurrentPage = 1;
      const originBtns = {
        'all': 'tool-origin-all',
        'surge': 'tool-origin-surge',
        'web': 'tool-origin-web',
        'demo': 'tool-origin-demo',
        'github': 'tool-origin-github',
        'huggingface': 'tool-origin-huggingface'
      };
      Object.entries(originBtns).forEach(([k, btnId]) => {
        const b = document.getElementById(btnId);
        if (b) {
          b.className = (k === toolOriginFilter)
            ? "tool-origin-btn active px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-bold bg-emerald-600 text-white shadow-sm shadow-emerald-600/30 whitespace-nowrap shrink-0 flex items-center space-x-1.5 transition-all"
            : "tool-origin-btn px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 whitespace-nowrap shrink-0 flex items-center space-x-1.5 transition-all";
        }
      });
      if (currentTab === 'tools') {
        renderCategoryView('tools');
      }
    }

    function normalizeToolScenarioKey(raw) {
      if (!raw || raw === 'all') return 'all';
      const s = String(raw).toLowerCase();
      if (/办公|文档|表格|ppt|slide|spreadsheet|excel|pdf|office/.test(s)) return 'office';
      if (/视频|剪辑|动漫|短剧|字幕|video|film|subtitle/.test(s)) return 'video';
      if (/语音|声音|音频|音乐|配音|播客|voice|audio|speech|tts|asr/.test(s)) return 'audio';
      if (/图像|设计|修图|绘画|3d|建模|画板|image|design|photo|canvas/.test(s)) return 'design';
      if (/联网|搜索|浏览器|网页|爬虫|search|browser|crawl|scrape/.test(s)) return 'browser';
      if (/知识库|记忆|笔记|论文|学术|文献|翻译|knowledge|memory|research|rag/.test(s)) return 'knowledge';
      if (/金融|量化|交易|股票|求职|简历|面试|健康|医疗|看盘|finance|trading|career|life/.test(s)) return 'life';
      if (/写作|小说|文案|剧本|社媒|营销|内容创作|writing|copy|marketing|growth/.test(s)) return 'writing';
      if (/编程|代码|开发|终端|调试|测试|coding|dev|code/.test(s)) return 'code';
      if (/桌面助手|客户端|聊天|工作台|client|assistant|desktop/.test(s)) return 'client';
      if (/网关|路由|推理|算力|沙箱|微调|模型|本地部署|model|api|sandbox|gateway|infra/.test(s)) return 'infra';
      if (/智能体|工作流|多智能体|编排|自动化|agent|workflow/.test(s)) return 'agent';
      return 'code';
    }

    function updateToolScenarioCounts(baseList) {
      if (!Array.isArray(baseList)) return;
      const counts = {
        'all': baseList.length,
        'code': 0,
        'client': 0,
        'agent': 0,
        'knowledge': 0,
        'browser': 0,
        'writing': 0,
        'life': 0,
        'design': 0,
        'office': 0,
        'video': 0,
        'infra': 0,
        'audio': 0
      };
      baseList.forEach(it => {
        const k = normalizeToolScenarioKey(it.scenario_key || it.scenario_tag || '');
        if (counts[k] !== undefined) counts[k]++;
      });
      const cntMap = {
        'all': 'tool-cnt-all',
        'code': 'tool-cnt-code',
        'client': 'tool-cnt-client',
        'agent': 'tool-cnt-agent',
        'knowledge': 'tool-cnt-knowledge',
        'browser': 'tool-cnt-browser',
        'writing': 'tool-cnt-writing',
        'life': 'tool-cnt-life',
        'design': 'tool-cnt-design',
        'office': 'tool-cnt-office',
        'video': 'tool-cnt-video',
        'infra': 'tool-cnt-infra',
        'audio': 'tool-cnt-audio'
      };
      Object.entries(cntMap).forEach(([k, elId]) => {
        const el = document.getElementById(elId);
        if (el) {
          el.textContent = counts[k] || 0;
        }
      });
    }

    // 工具场景筛选 (覆盖12大真实日常场景)
    function filterToolScenario(scenario) {
      toolScenarioFilter = normalizeToolScenarioKey(scenario);
      categoryCurrentPage = 1;
      const btnMap = {
        'all': 'tool-filter-all',
        'code': 'tool-filter-code',
        'client': 'tool-filter-client',
        'agent': 'tool-filter-agent',
        'knowledge': 'tool-filter-knowledge',
        'browser': 'tool-filter-browser',
        'writing': 'tool-filter-writing',
        'life': 'tool-filter-life',
        'design': 'tool-filter-design',
        'office': 'tool-filter-office',
        'video': 'tool-filter-video',
        'infra': 'tool-filter-infra',
        'audio': 'tool-filter-audio'
      };
      Object.entries(btnMap).forEach(([scenKey, btnId]) => {
        const b = document.getElementById(btnId);
        if (b) {
          const isActive = (scenKey === toolScenarioFilter);
          b.className = isActive
            ? "tool-filter-btn active px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-600 text-white shadow-sm whitespace-nowrap shrink-0 flex items-center gap-1 transition-all"
            : "tool-filter-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 whitespace-nowrap shrink-0 flex items-center gap-1 transition-all";
        }
      });
      if (currentTab === 'tools') {
        renderCategoryView('tools');
      }
    }

    let videoPlatformFilter = 'all';

    // 专栏广场：实战视频平台分栏筛选 (全部精选 / YouTube横屏 / YouTube Shorts / TikTok)
    function filterVideoPlatform(plat) {
      videoPlatformFilter = plat;
      categoryCurrentPage = 1;
      const bAll = document.getElementById('video-plat-all');
      const bYtLong = document.getElementById('video-plat-yt-long');
      const bYtShorts = document.getElementById('video-plat-yt-shorts');
      const bTt = document.getElementById('video-plat-tiktok');

      const normalClass = "video-plat-btn px-3.5 py-1.5 rounded-xl text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 shrink-0 transition-all flex items-center space-x-1.5";

      if (bAll) bAll.className = normalClass;
      if (bYtLong) bYtLong.className = normalClass;
      if (bYtShorts) bYtShorts.className = normalClass;
      if (bTt) bTt.className = normalClass;

      // 激活态赋能
      if (plat === 'all' && bAll) {
        bAll.className = "video-plat-btn active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-rose-600 text-white shrink-0 shadow-sm shadow-rose-600/30 transition-all flex items-center space-x-1.5";
      } else if (plat === 'youtube-long' && bYtLong) {
        bYtLong.className = "video-plat-btn active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white shadow-sm shadow-red-600/30 transition-all flex items-center space-x-1.5";
      } else if (plat === 'youtube-shorts' && bYtShorts) {
        bYtShorts.className = "video-plat-btn active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-red-600 text-white shadow-sm shadow-red-600/30 transition-all flex items-center space-x-1.5";
      } else if (plat === 'tiktok' && bTt) {
        bTt.className = "video-plat-btn active px-3.5 py-1.5 rounded-xl text-xs font-bold bg-gradient-to-r from-slate-900 to-black text-rose-300 border border-rose-500/60 shadow-sm shadow-rose-500/30 shrink-0 transition-all flex items-center space-x-1.5";
      }

      if (currentTab === 'videos') {
        renderCategoryView('videos');
      }
    }

    // 切换短视频静音 / 取消静音
    function toggleVideoCardMute(btnEl) {
      if (!btnEl) return;
      const card = btnEl.closest('.vertical-video-card');
      if (!card) return;
      const playerSlot = card.querySelector('.vertical-player-slot');
      const iframe = playerSlot ? playerSlot.querySelector('iframe') : null;

      // 如果尚未挂载播放器，点击取消静音按钮自动触发原位播放并解开静音
      if (!iframe) {
        const playTarget = card.querySelector('[data-embed-src]');
        if (playTarget) {
          const embedSrc = playTarget.getAttribute('data-embed-src');
          const platform = playTarget.getAttribute('data-platform');
          mountInPlaceVerticalVideo(card, embedSrc, platform);
        }
        return;
      }

      const isMuted = btnEl.getAttribute('data-muted') !== 'false';
      if (isMuted) {
        btnEl.setAttribute('data-muted', 'false');
        btnEl.innerHTML = '<span>🔊</span><span>Sound On</span>';
        btnEl.className = 'pointer-events-auto video-mute-btn px-2.5 py-1 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-emerald-400/40 backdrop-blur-md';
        if (iframe && iframe.contentWindow) {
          iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'unMute', args: [] }), '*');
          iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'setVolume', args: [100] }), '*');
        }
      } else {
        btnEl.setAttribute('data-muted', 'true');
        btnEl.innerHTML = '<span>🔇</span><span>Unmute</span>';
        btnEl.className = 'pointer-events-auto video-mute-btn px-2.5 py-1 rounded-full bg-black/80 hover:bg-rose-600 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-white/20 backdrop-blur-md';
        if (iframe && iframe.contentWindow) {
          iframe.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'mute', args: [] }), '*');
        }
      }
    }

    // 专栏广场：实战视频场景子分类筛选
    function filterVideoSub(sub) {
      videoSubFilter = sub;
      categoryCurrentPage = 1;
      const subKeys = ['all', 'viral', 'tutorial', 'insight', 'tips'];
      subKeys.forEach(k => {
        const b = document.getElementById(`video-sub-${k}`);
        if (b) {
          b.className = (k === sub)
            ? "video-sub-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-600 text-white shrink-0 shadow-sm shadow-rose-600/30 transition-all"
            : "video-sub-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 shrink-0 transition-all";
        }
      });
      if (currentTab === 'videos') {
        renderCategoryView('videos');
      }
    }

    // ==========================================
    // 视频鼠标悬停静音自动预览引擎 (Hover Silent Preview)
    // ==========================================
    let hoverVideoTimer = null;
    let activePreviewSlot = null;

    function startVideoHoverPreview(cardEl, videoId, platform) {
      clearTimeout(hoverVideoTimer);
      if (!videoId || platform === 'tiktok') return; // YouTube 提供原生无感低延迟静音微预览

      hoverVideoTimer = setTimeout(() => {
        const slot = cardEl.querySelector('.video-preview-slot');
        if (!slot) return;

        // 如果之前有运行的预览层，先安全注销
        if (activePreviewSlot && activePreviewSlot !== slot) {
          activePreviewSlot.innerHTML = '';
        }

        const iframe = document.createElement('iframe');
        iframe.className = "w-full h-full absolute inset-0 object-cover pointer-events-none transition-opacity duration-300 opacity-0 z-10";
        iframe.src = `https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&mute=1&controls=0&loop=1&playlist=${videoId}&playsinline=1&modestbranding=1&rel=0&iv_load_policy=3`;
        iframe.setAttribute('frameborder', '0');
        iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');

        iframe.onload = () => {
          iframe.classList.remove('opacity-0');
          iframe.classList.add('opacity-100');
        };

        slot.innerHTML = '';
        slot.appendChild(iframe);
        activePreviewSlot = slot;

        const badge = cardEl.querySelector('.preview-indicator');
        if (badge) badge.classList.remove('hidden');
      }, 240); // 240ms 防抖，避免快速滚动页面时触发多余请求
    }

    function stopVideoHoverPreview(cardEl) {
      clearTimeout(hoverVideoTimer);
      const slot = cardEl.querySelector('.video-preview-slot');
      if (slot) {
        slot.innerHTML = '';
      }
      const badge = cardEl.querySelector('.preview-indicator');
      if (badge) badge.classList.add('hidden');
      if (activePreviewSlot === slot) {
        activePreviewSlot = null;
      }
    }

    // ==========================================
    // 9:16 竖屏短视频通用原位即开即播引擎 (In-Place Video Playback Engine)
    // 彻底解决多 iframe 并发加载导致的风控卡顿、黑屏转圈与内存消耗
    // ==========================================
    let activeInPlaceVideoCard = null;

    function mountInPlaceVerticalVideo(cardEl, embedUrl, platform) {
      if (!cardEl) return;
      const playerSlot = cardEl.querySelector('.vertical-player-slot');
      if (!playerSlot) return;

      // 如果当前卡片已在播放，则不重复挂载
      if (playerSlot.querySelector('iframe')) return;

      // 如果有其他正在播放的短视频卡片，先优雅注销，保证同一时刻全站仅播放单个音频流
      if (activeInPlaceVideoCard && activeInPlaceVideoCard !== cardEl) {
        unmountInPlaceVerticalVideo(activeInPlaceVideoCard);
      }

      // 创建内嵌原生播放器
      const iframe = document.createElement('iframe');
      iframe.className = "w-full h-full absolute inset-0 z-10 bg-black border-0 rounded-xl";
      
      const isTikTok = platform === 'tiktok' || embedUrl.includes('tiktok.com');
      let finalSrc = embedUrl;
      if (isTikTok) {
        finalSrc = embedUrl + (embedUrl.includes('?') ? '&autoplay=1' : '?autoplay=1');
      } else {
        finalSrc = embedUrl + (embedUrl.includes('?') ? '&autoplay=1&mute=0' : '?autoplay=1&mute=0');
      }
      
      iframe.src = finalSrc;
      iframe.setAttribute('frameborder', '0');
      iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
      iframe.setAttribute('allowfullscreen', 'true');

      playerSlot.innerHTML = '';
      playerSlot.appendChild(iframe);
      playerSlot.classList.remove('hidden');

      // 隐藏封面引导层，让 iframe 接收直接点击交互
      const overlay = cardEl.querySelector('.vertical-cover-overlay');
      if (overlay) {
        overlay.classList.add('opacity-0', 'pointer-events-none');
      }

      // 自动更新左上角静音按钮为“声音已开”高亮状态
      const muteBtn = cardEl.querySelector('.video-mute-btn');
      if (muteBtn) {
        muteBtn.setAttribute('data-muted', 'false');
        muteBtn.innerHTML = '<span>🔊</span><span>Sound On</span>';
        muteBtn.className = 'pointer-events-auto video-mute-btn px-2.5 py-1 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-emerald-400/40 backdrop-blur-md';
      }

      activeInPlaceVideoCard = cardEl;
    }

    function unmountInPlaceVerticalVideo(cardEl) {
      if (!cardEl) return;
      const playerSlot = cardEl.querySelector('.vertical-player-slot');
      if (playerSlot) {
        playerSlot.innerHTML = '';
        playerSlot.classList.add('hidden');
      }
      const overlay = cardEl.querySelector('.vertical-cover-overlay');
      if (overlay) {
        overlay.classList.remove('opacity-0', 'pointer-events-none');
      }
      const muteBtn = cardEl.querySelector('.video-mute-btn');
      if (muteBtn) {
        muteBtn.setAttribute('data-muted', 'true');
        muteBtn.innerHTML = '<span>🔇</span><span>Unmute</span>';
        muteBtn.className = 'pointer-events-auto video-mute-btn px-2.5 py-1 rounded-full bg-black/80 hover:bg-rose-600 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-white/20 backdrop-blur-md';
      }
      if (activeInPlaceVideoCard === cardEl) {
        activeInPlaceVideoCard = null;
      }
    }

    // 专栏广场：提示词场景分类筛选 (按最新前沿大模型与高阶核心应用场景)
    let promptGenerationFilter = 'sota'; // 'sota' (当前旗舰优先) | 'legacy' (历史模型归档)

    let promptSubmodeFilter = 'all'; // 'all' | 'workflow' | 'prompt'

    function switchPromptSubmode(mode) {
      promptSubmodeFilter = mode || 'all';
      const submodeBtns = {
        'all': 'prompt-submode-all',
        'workflow': 'prompt-submode-workflow',
        'prompt': 'prompt-submode-prompt'
      };
      Object.entries(submodeBtns).forEach(([k, btnId]) => {
        const b = document.getElementById(btnId);
        if (b) {
          b.className = (k === promptSubmodeFilter)
            ? "prompt-submode-btn active px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-bold bg-purple-600 text-white shadow-sm flex items-center gap-1.5 shrink-0 whitespace-nowrap transition-all"
            : "prompt-submode-btn px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1.5 shrink-0 whitespace-nowrap transition-all";
        }
      });
      if (currentTab === 'prompts') {
        renderCategoryView('prompts');
      }
    }

    function switchPromptGeneration(gen) {
      promptGenerationFilter = gen;
      categoryCurrentPage = 1;
      const btnSota = document.getElementById('prompt-gen-sota');
      const btnLegacy = document.getElementById('prompt-gen-legacy');
      if (btnSota && btnLegacy) {
        if (gen === 'sota') {
          btnSota.className = "prompt-gen-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-sm shadow-purple-600/30 flex items-center gap-1 shrink-0";
          btnLegacy.className = "prompt-gen-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1 shrink-0";
        } else {
          btnLegacy.className = "prompt-gen-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-sm shadow-amber-600/30 flex items-center gap-1 shrink-0";
          btnSota.className = "prompt-gen-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1 shrink-0";
        }
      }
      if (currentTab === 'prompts') {
        renderCategoryView('prompts');
      }
    }

    function filterPromptCategory(cat) {
      promptCategoryFilter = cat;
      categoryCurrentPage = 1;
      const catBtns = [
        { id: 'prompt-cat-all', key: 'all' },
        { id: 'prompt-cat-code', key: 'code' },
        { id: 'prompt-cat-novel', key: 'novel' },
        { id: 'prompt-cat-analysis', key: 'analysis' },
        { id: 'prompt-cat-report', key: 'report' },
        { id: 'prompt-cat-travel', key: 'travel' },
        { id: 'prompt-cat-image', key: 'image' },
        { id: 'prompt-cat-video', key: 'video' },
        { id: 'prompt-cat-tibo', key: 'tibo_reset' },
        { id: 'prompt-cat-deepseek', key: 'deepseek_r4' },
        { id: 'prompt-cat-claude', key: 'claude_55' },
        { id: 'prompt-cat-openai', key: 'openai_o3' },
        { id: 'prompt-cat-sora', key: 'sora2_wan21' },
        { id: 'prompt-cat-agent', key: 'agent' },
        { id: 'prompt-cat-coding', key: 'coding' },
        { id: 'prompt-cat-reasoning', key: 'reasoning' }
      ];

      catBtns.forEach(item => {
        const b = document.getElementById(item.id);
        if (b) {
          const isActive = (item.key === cat);
          b.className = isActive
            ? "prompt-cat-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-purple-600 text-white shrink-0 shadow-sm shadow-purple-600/30"
            : "prompt-cat-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 shrink-0";
        }
      });

      if (currentTab === 'prompts') {
        renderCategoryView('prompts');
      }
    }

    function toggleSampleDrawer(id) {
      const drawer = document.getElementById(`sample-drawer-${id}`);
      const arrow = document.getElementById(`sample-arrow-${id}`);
      const btnTxt = document.getElementById(`sample-btn-txt-${id}`);
      const t = I18N[currentLang];
      if (drawer) {
        const isHidden = drawer.classList.contains('hidden');
        drawer.classList.toggle('hidden');
        if (arrow) {
          arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
        }
        if (btnTxt) {
          btnTxt.textContent = isHidden ? (t.hideSampleOutput || '收起效果样例 ↑') : (t.viewSampleOutput || '👀 查看实测生成效果样例 (Sample Output)');
        }
      }
    }

    function copySampleCode(id) {
      const codeEl = document.getElementById(`sample-code-${id}`);
      if (codeEl) {
        copyToClipboard(codeEl.textContent || codeEl.innerText);
      }
    }

    function renderSampleOutputContent(id, sample) {
      if (!sample) return '';
      const t = I18N[currentLang];
      const isZh = currentLang === 'zh';
      const sampleTitle = isZh
        ? (sample.title || '生成效果大图')
        : (sample.title_en || (!/[\u4e00-\u9fa5]/.test(sample.title || '') && sample.title) || 'Verified Sample Output');
      const sampleText = isZh
        ? (sample.content || '')
        : (sample.content_en || (!/[\u4e00-\u9fa5]/.test(sample.content || '') ? (sample.content || '') : '// Verified sample output preview. Copy prompt above to execute.'));
      if (sample.type === 'image') {
        return `
          <div class="space-y-2">
            <div class="rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800 bg-black max-h-72 relative group/img cursor-pointer" onclick="window.open('${sample.media_url}', '_blank')">
              <img src="${sample.media_url}" class="w-full h-full object-contain group-hover/img:scale-105 transition-transform duration-300" loading="lazy" alt="${escapeHtml(sampleTitle)}">
              <span class="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/80 text-white text-[9px] font-mono backdrop-blur-md">${isZh ? '🔍 点击看超清原图' : '🔍 View Full Resolution'}</span>
            </div>
            ${sampleText ? `<p class="text-[10px] text-slate-600 dark:text-slate-400 font-mono leading-relaxed bg-white/60 dark:bg-slate-900/60 p-2 rounded border border-slate-200/60 dark:border-slate-800/60">${escapeHtml(sampleText)}</p>` : ''}
          </div>
        `;
      } else if (sample.type === 'video') {
        return `
          <div class="space-y-2">
            <div class="rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800 bg-black aspect-video relative group/vid">
              <video src="${sample.media_url}" class="w-full h-full object-cover" autoplay loop muted playsinline></video>
              <span class="absolute top-2 right-2 px-2 py-0.5 rounded bg-black/80 text-white text-[9px] font-mono backdrop-blur-md flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>${isZh ? 'MP4 实测动效' : 'MP4 Demo Video'}</span>
              </span>
            </div>
            ${sampleText ? `<p class="text-[10px] text-slate-600 dark:text-slate-400 font-mono leading-relaxed bg-white/60 dark:bg-slate-900/60 p-2 rounded border border-slate-200/60 dark:border-slate-800/60">${escapeHtml(sampleText)}</p>` : ''}
          </div>
        `;
      } else if (sample.type === 'code') {
        return `
          <div class="space-y-1.5">
            <div class="relative group/code">
              <pre class="p-2.5 rounded-lg bg-slate-900 text-emerald-400 font-mono text-[10px] overflow-x-auto leading-relaxed max-h-60 whitespace-pre"><code id="sample-code-${id}">${escapeHtml(sampleText)}</code></pre>
              <button type="button" onclick="copySampleCode('${id}')" class="absolute top-1.5 right-1.5 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-[9px] font-mono border border-slate-700 shadow-sm transition-colors cursor-pointer">
                ${t.copySampleCodeBtn || (isZh ? '复制代码 📋' : 'Copy Code 📋')}
              </button>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="p-2.5 rounded-lg bg-white/80 dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-[11px] leading-relaxed max-h-60 overflow-y-auto whitespace-pre-wrap border border-slate-200 dark:border-slate-800 font-sans shadow-inner select-all">${escapeHtml(sampleText)}</div>
        `;
      }
    }

    
    // ==========================================
    // 渲染当日火爆的名人推文横向滚动栏 (Viral Leader Tweets Ticker)
    // ==========================================
    let viralTickerInterval = null;
        window.viralTickerInterval = null;
        window.viralTickerInterval = null;
    window.viralTickerPaused = false;
    window.viralTickerHovered = false;
    window.viralTickerCurrentPage = 0;
    window.viralTickerTotalPages = 1;

    function resolveViralTweetTag(item, isZh) {
      const author = ((item.author || '') + ' ' + (item.author_handle || '')).toLowerCase();
      const title = ((item.title || '') + ' ' + (item.title_zh || '') + ' ' + (item.title_en || '')).toLowerCase();
      const text = ((item.full_text_zh || '') + ' ' + (item.full_text_en || '') + ' ' + (item.summary_zh || '') + ' ' + (item.summary_en || '')).toLowerCase();
      const combo = author + ' ' + title + ' ' + text;

      // 1. 架构深度解析 (Architecture Deep Dive)
      const archKeys = [
        "reset architecture", "gpt reset", "context reset", "attention drift", 
        "context purge", "attention buffer", "prior bias", "first-principles reasoning",
        "transformer architecture", "kv cache", "inference engine", "架构重构", "重置架构",
        "重置机制", "注意力死锁", "注意力漂移", "底层架构", "注意力机制"
      ];
      if (archKeys.some(k => combo.includes(k))) {
        return { badge: isZh ? '⚡ 架构深度解析' : '⚡ ARCHITECTURE INSIGHT', isHl: true, theme: 'amber' };
      }

      // 2. 极客实战演示 / 落地案例 / Agent 工作流 (Builder Showcase & Workflow)
      const demoKeys = [
        "blender", "mcp agent", "mcp agents", "3d website", "meshes", "triangles",
        "scene: ", "scene :", "wilderness hotel", "created the video with", "i've built an internal",
        "i used", "built an internal", "concept for a", "workflow demo", "made using seedance",
        "prompt :", "frame io", "极客制作", "实战演示", "实战案例", "落地案例", "工作流演示",
        "打造了", "制作了", "克隆了"
      ];
      if (demoKeys.some(k => combo.includes(k))) {
        return { badge: isZh ? '🛠️ 极客实战演示' : '🛠️ BUILDER SHOWCASE', isHl: true, theme: 'cyan' };
      }

      // 3. 官方重磅发布 / 产品与订阅上线 (Official Release & Product Drop)
      const releaseKeys = [
        "officially introduced", "just introduced", "is live!", "is live 🔴",
        "officially launched", "we shipped", "we are launching", "announces the",
        "new subscription", "subscribers can", "官宣上线", "正式推出", "官方发布",
        "重磅上线", "全新订阅"
      ];
      if (releaseKeys.some(k => combo.includes(k))) {
        return { badge: isZh ? '🌟 官方重磅发布' : '🌟 OFFICIAL RELEASE', isHl: true, theme: 'emerald' };
      }

      // 4. 前沿技术突破 / SOTA 指标跃升 (Frontier Breakthrough & SOTA)
      const breakKeys = [
        "breakthrough for v", "major breakthrough", "breakthrough in", "sota record", 
        "state-of-the-art", "record-breaking", "重大突破", "核心突破", "技术跃升"
      ];
      if (breakKeys.some(k => combo.includes(k))) {
        return { badge: isZh ? '⚡ 核心技术突破' : '⚡ FRONTIER BREAKTHROUGH', isHl: true, theme: 'rose' };
      }

      // 5. 领袖前沿观点 / 行业观察 (Titan Insight & Commentary)
      const leaderKeys = ["musk", "elon", "sama", "altman", "karpathy", "zuck", "zuckerberg", "lecun", "hassabis"];
      if (leaderKeys.some(k => author.includes(k))) {
        return { badge: isZh ? '💡 领袖前沿观点' : '💡 TITAN INSIGHT', isHl: false, theme: 'indigo' };
      }

      // 6. 全网极客热推 (24h Trending)
      const customBadge = (isZh ? item.badge_zh : item.badge_en) || item.badge;
      if (customBadge && !customBadge.toLowerCase().includes('breakthrough') && !customBadge.toLowerCase().includes('reset')) {
        return { badge: customBadge, isHl: false, theme: 'slate' };
      }
      return { badge: isZh ? '🔥 24h 极客热推' : '🔥 24H TRENDING', isHl: false, theme: 'slate' };
    }

    function isValidTweetImageUrl(url) {
      if (!url || typeof url !== 'string') return false;
      const u = url.trim().toLowerCase();
      if (u.includes('t.co/') || u.includes('bit.ly/') || u.includes('tinyurl.com/')) return false;
      if (['pbs.twimg.com', 'twimg.com', 'unsplash.com', 'ytimg.com', 'cloudinary.com', 'githubusercontent.com'].some(h => u.includes(h))) return true;
      return ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg'].some(ext => u.includes(ext));
    }

    function renderViralTickerCard(item, isZh, cardIdx = 0) {
      const tagInfo = resolveViralTweetTag(item, isZh);
      const isHl = tagInfo.isHl;
      const badgeText = escapeHtml(tagInfo.badge);
      const theme = tagInfo.theme;
      const author = escapeHtml(item.author || (isZh ? 'AI 领袖' : 'AI Pioneer'));
      const handle = escapeHtml(item.author_handle || `@${(item.author || 'vip').replace(/\s+/g, '')}`);
      const role = escapeHtml(isZh ? (item.author_role || 'AI 先锋观察者') : (item.author_role_en || 'AI Pioneer & Builder'));

      const text = escapeHtml(isZh ? (item.full_text_zh || item.quote_zh || item.title_zh || item.title || item.summary_zh || '') : (item.full_text_en || item.quote_en || item.title_en || item.title || item.summary_en || ''));
      const avatar = optimizeAvatarUrl(item.author_avatar || `https://unavatar.io/x/${handle.replace('@', '')}`, 80);
      const timeStr = isZh ? '24h 实时' : '24h Live';
      const btnText = isZh ? '查看原帖 ↗' : 'View Post ↗';
      const url = item.url || '#';
      const visCls = cardIdx === 0 ? "flex" : "hidden md:flex";

      const twImg = item.image_url || item.media || '';
      let thumbHtml = '';
      if (isValidTweetImageUrl(twImg)) {
        const optImg = `https://wsrv.nl/?url=${encodeURIComponent(twImg)}&w=240&output=webp&q=80`;
        thumbHtml = `
          <div class="tweet-thumb-box shrink-0 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 cursor-pointer group/img shadow-sm" style="width: 72px; height: 54px; max-width: 72px; max-height: 54px;" onclick="openImageLightbox('${escapeHtml(twImg)}', event)" title="${isZh ? '点击放大高清原图' : 'Click to view full image'}">
            <img src="${optImg}" alt="Tweet media" style="width: 72px; height: 54px; object-fit: cover;" class="group-hover/img:scale-105 transition-transform duration-300" loading="lazy" onerror="this.closest('.tweet-thumb-box')?.remove();">
          </div>`;
      } else if (item.has_video || item.video_url) {
        thumbHtml = `
          <div class="tweet-thumb-box shrink-0 flex items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400" style="width: 72px; height: 54px; max-width: 72px; max-height: 54px;">
            <span class="text-base">🎥</span>
          </div>`;
      }

      if (isHl) {
        let pillStyle = "bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 shadow-amber-500/30";
        let borderStyle = "border-2 border-amber-400 dark:border-amber-400/90 shadow-[0_0_20px_rgba(251,191,36,0.22)] dark:shadow-[0_0_25px_rgba(251,191,36,0.28)]";
        let topLine = "bg-gradient-to-r from-amber-400 via-orange-500 to-sky-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]";
        let cardBg = "bg-gradient-to-br from-amber-500/10 via-white to-sky-500/10 dark:from-amber-950/40 dark:via-slate-900/90 dark:to-indigo-950/40";
        if (theme === 'cyan') {
          pillStyle = "bg-gradient-to-r from-cyan-500 via-sky-500 to-indigo-500 shadow-cyan-500/30";
          borderStyle = "border-2 border-sky-400 dark:border-sky-400/90 shadow-[0_0_20px_rgba(56,189,248,0.22)] dark:shadow-[0_0_25px_rgba(56,189,248,0.28)]";
          topLine = "bg-gradient-to-r from-cyan-400 via-sky-500 to-indigo-500 shadow-[0_0_8px_rgba(56,189,248,0.8)]";
          cardBg = "bg-gradient-to-br from-sky-500/10 via-white to-indigo-500/10 dark:from-sky-950/40 dark:via-slate-900/90 dark:to-indigo-950/40";
        } else if (theme === 'emerald') {
          pillStyle = "bg-gradient-to-r from-emerald-500 via-teal-500 to-sky-500 shadow-emerald-500/30";
          borderStyle = "border-2 border-emerald-400 dark:border-emerald-400/90 shadow-[0_0_20px_rgba(52,211,153,0.22)] dark:shadow-[0_0_25px_rgba(52,211,153,0.28)]";
          topLine = "bg-gradient-to-r from-emerald-400 via-teal-500 to-sky-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]";
          cardBg = "bg-gradient-to-br from-emerald-500/10 via-white to-sky-500/10 dark:from-emerald-950/40 dark:via-slate-900/90 dark:to-indigo-950/40";
        } else if (theme === 'rose') {
          pillStyle = "bg-gradient-to-r from-rose-500 via-pink-500 to-purple-500 shadow-rose-500/30";
          borderStyle = "border-2 border-rose-400 dark:border-rose-400/90 shadow-[0_0_20px_rgba(244,63,94,0.22)] dark:shadow-[0_0_25px_rgba(244,63,94,0.28)]";
          topLine = "bg-gradient-to-r from-rose-400 via-pink-500 to-purple-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]";
          cardBg = "bg-gradient-to-br from-rose-500/10 via-white to-purple-500/10 dark:from-rose-950/40 dark:via-slate-900/90 dark:to-indigo-950/40";
        }

        return `
          <article class="relative rounded-2xl p-3.5 ${visCls} flex-col justify-between space-y-2 transition-all duration-300 group cursor-pointer h-full ${cardBg} ${borderStyle} hover:shadow-xl hover:-translate-y-0.5" style="height: 180px; max-height: 180px; overflow: hidden;">
            <div class="absolute -top-[2px] left-4 right-4 h-[3px] ${topLine} rounded-full"></div>
            <div class="space-y-1.5 pt-0.5 flex-1 min-h-0 overflow-hidden flex flex-col justify-between">
              <div class="flex items-center justify-between text-[10px] gap-2 shrink-0">
                <div class="flex items-center space-x-2 min-w-0">
                  <div class="relative shrink-0">
                    <img src="${avatar}" alt="${author}" width="28" height="28" class="w-7 h-7 rounded-full object-cover bg-slate-900 ring-2 ring-sky-400/80 shadow-sm" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=VIP'">
                    <span class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-sky-500 text-slate-950 flex items-center justify-center text-[8px] font-black ring-1 ring-white dark:ring-slate-900 shadow">⚡</span>
                  </div>
                  <div class="min-w-0 truncate">
                    <div class="flex items-center space-x-1">
                      <span class="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">${author}</span>
                      <span class="text-sky-500 text-[10px] font-black">✓</span>
                    </div>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate block">${handle} · ${role}</span>
                  </div>
                </div>
                <span class="relative inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wide ${pillStyle} text-white shadow-sm shrink-0">
                  <span class="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_#fff]"></span>
                  <span>${badgeText}</span>
                </span>
              </div>
              <div class="flex gap-2 items-start my-0.5 flex-1 min-h-0 overflow-hidden">
                <p class="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed line-clamp-3 flex-1 min-w-0 m-0 group-hover:text-sky-600 dark:group-hover:text-sky-300 transition-colors">
                  ${text}
                </p>
                ${thumbHtml}
              </div>
            </div>
            <div class="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1.5 border-t border-slate-200/60 dark:border-slate-800/60 shrink-0">
              <span class="font-mono flex items-center gap-1 text-slate-700 dark:text-slate-300 font-semibold">
                <span>⚡</span>
                <span>${timeStr}</span>
              </span>
              <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-sky-700 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300 font-bold hover:underline flex items-center gap-0.5">
                <span>${btnText}</span>
              </a>
            </div>
          </article>
        `;
      } else {
        const pillCls = theme === 'indigo'
          ? "bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/25"
          : "bg-sky-50 dark:bg-sky-500/15 text-sky-700 dark:text-sky-400 border border-sky-200 dark:border-sky-500/25";
        return `
          <article class="relative rounded-2xl p-3.5 ${visCls} flex-col justify-between space-y-2 transition-all duration-300 group cursor-pointer h-full bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/90 border border-slate-200 dark:border-slate-800 hover:border-sky-500/50 shadow-sm hover:shadow-md hover:-translate-y-0.5" style="height: 180px; max-height: 180px; overflow: hidden;">
            <div class="space-y-1.5 flex-1 min-h-0 overflow-hidden flex flex-col justify-between">
              <div class="flex items-center justify-between text-[10px] gap-2 shrink-0">
                <div class="flex items-center space-x-2 min-w-0">
                  <img src="${avatar}" alt="${author}" width="28" height="28" class="w-7 h-7 rounded-full object-cover bg-slate-900 ring-1 ring-slate-200 dark:ring-slate-800 shrink-0" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=VIP'">
                  <div class="min-w-0 truncate">
                    <div class="flex items-center space-x-1">
                      <span class="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">${author}</span>
                      <span class="text-sky-500 text-[10px] font-black">✓</span>
                    </div>
                    <span class="text-[10px] text-slate-500 dark:text-slate-400 font-mono truncate block">${handle} · ${role}</span>
                  </div>
                </div>
                <span class="font-semibold px-2 py-0.5 rounded-full ${pillCls} shrink-0 text-[10px]">${badgeText}</span>
              </div>
              <div class="flex gap-2 items-start my-0.5 flex-1 min-h-0 overflow-hidden">
                <p class="text-xs text-slate-600 dark:text-slate-300 leading-relaxed line-clamp-3 flex-1 min-w-0 m-0 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">
                  ${text}
                </p>
                ${thumbHtml}
              </div>
            </div>
            <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-slate-100 dark:border-slate-800/60 shrink-0">
              <span class="font-mono text-slate-400">🕒 ${timeStr}</span>
              <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-sky-700 dark:text-sky-400 hover:text-sky-800 dark:hover:text-sky-300 font-semibold hover:underline">
                ${btnText}
              </a>
            </div>
          </article>
        `;
      }
    }

    // 渲染 Tibo 的 Reset 核心专属置顶卡片 (第一行第一个位置，重磅突出高亮框设计)
    function renderTiboPinnedCard(item, isZh) {
      const author = 'Thibault Sottiaux (Tibo)';
      const handle = '@thsottiaux';
      const role = escapeHtml(isZh ? (item.author_role || 'OpenAI Codex 负责人 / 前沿模型产品主管') : (item.author_role_en || 'OpenAI Codex Lead / Frontier Models Product'));
      let text = escapeHtml(isZh ? (item.full_text_zh || item.quote_zh || item.title_zh || item.title || item.summary_zh || '') : (item.full_text_en || item.quote_en || item.title_en || item.title || item.summary_en || ''));
      
      // 重点高亮 Reset / 重置
      const hlText = text.replace(/\b(reset)\b/gi, '<span class="text-amber-600 dark:text-amber-400 font-black underline decoration-amber-400/70">$1</span>')
                         .replace(/(重置)/g, '<span class="text-amber-600 dark:text-amber-400 font-black underline decoration-amber-400/70">$1</span>');
      
      const avatar = optimizeAvatarUrl('https://unavatar.io/x/thsottiaux', 80);
      const badgeText = isZh ? '🔥 24H RESET 置顶' : '🔥 24H RESET PINNED';
      const spotlightTag = isZh ? '24h 独家聚焦 · 锁定首位' : '24h Spotlight · Pinned #1';
      const btnText = isZh ? '查看原帖 ↗' : 'View Post ↗';
      const statusId = item.status_id || (item.url && item.url.match(/status\/(\d+)/) ? item.url.match(/status\/(\d+)/)[1] : '');
      const url = statusId ? `https://x.com/thsottiaux/status/${statusId}` : ((item.url && item.url.includes('thsottiaux') && item.url.includes('/status/')) ? item.url : 'https://x.com/thsottiaux/status/2110595484180214059');

      const twImg = item.image_url || item.media || '';
      let thumbHtml = '';
      if (isValidTweetImageUrl(twImg)) {
        const optImg = `https://wsrv.nl/?url=${encodeURIComponent(twImg)}&w=240&output=webp&q=80`;
        thumbHtml = `
          <div class="tweet-thumb-box shrink-0 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 cursor-pointer group/img shadow-sm" style="width: 72px; height: 54px; max-width: 72px; max-height: 54px;" onclick="openImageLightbox('${escapeHtml(twImg)}', event)" title="${isZh ? '点击放大高清原图' : 'Click to view full image'}">
            <img src="${optImg}" alt="Tweet media" style="width: 72px; height: 54px; object-fit: cover;" class="group-hover/img:scale-105 transition-transform duration-300" loading="lazy" onerror="this.closest('.tweet-thumb-box')?.remove();">
          </div>`;
      } else if (item.has_video || item.video_url) {
        thumbHtml = `
          <div class="tweet-thumb-box shrink-0 flex items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400" style="width: 72px; height: 54px; max-width: 72px; max-height: 54px;">
            <span class="text-base">🎥</span>
          </div>`;
      }

      return `
        <article class="relative rounded-2xl p-3.5 flex flex-col justify-between space-y-2 transition-all duration-300 group cursor-pointer h-full
          bg-gradient-to-br from-amber-500/15 via-white to-rose-500/10 dark:from-amber-950/70 dark:via-slate-900/95 dark:to-orange-950/60
          border-2 border-amber-400 dark:border-amber-300/90
          shadow-[0_0_25px_rgba(251,191,36,0.35),inset_0_0_15px_rgba(251,191,36,0.12)] dark:shadow-[0_0_35px_rgba(251,191,36,0.45),inset_0_0_20px_rgba(251,191,36,0.2)]
          hover:shadow-[0_0_35px_rgba(251,191,36,0.55)] hover:-translate-y-0.5" style="height: 180px; max-height: 180px; overflow: hidden;" onclick="window.open('${url}','_blank')">
          <div class="absolute -top-[2px] left-3 right-3 h-[3.5px] bg-gradient-to-r from-amber-400 via-rose-500 to-amber-300 rounded-full shadow-[0_0_12px_rgba(251,191,36,0.9)] animate-pulse"></div>
          <div class="space-y-1.5 pt-0.5 flex-1 min-h-0 overflow-hidden flex flex-col justify-between">
            <div class="flex items-center justify-between text-[10px] gap-2 shrink-0">
              <div class="flex items-center space-x-2 min-w-0">
                <div class="relative shrink-0">
                  <img src="${avatar}" alt="${author}" width="28" height="28" class="w-7 h-7 rounded-full object-cover bg-slate-900 ring-2 ring-amber-400 dark:ring-amber-300 shadow-[0_0_10px_rgba(251,191,36,0.5)]" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=VIP'">
                  <span class="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-gradient-to-br from-amber-400 to-rose-500 text-white flex items-center justify-center text-[8px] font-black shadow ring-1 ring-white dark:ring-slate-900">📌</span>
                </div>
                <div class="min-w-0 truncate">
                  <div class="flex items-center space-x-1">
                    <span class="font-bold text-xs text-slate-900 dark:text-slate-100 truncate">${author}</span>
                    <span class="text-sky-500 text-[10px] font-black">✓</span>
                  </div>
                  <span class="text-[10px] text-amber-700/80 dark:text-amber-400/90 font-mono truncate block font-medium">${handle} · ${role}</span>
                </div>
              </div>
              <span class="relative inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-wide bg-gradient-to-r from-amber-500 via-rose-500 to-pink-500 text-white shadow-md shadow-amber-500/30 shrink-0 border border-amber-300/40">
                <span class="relative flex h-2 w-2">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                </span>
                <span>${badgeText}</span>
              </span>
            </div>
            <div class="flex gap-2 items-start my-0.5 flex-1 min-h-0 overflow-hidden">
              <p class="text-xs text-slate-900 dark:text-slate-100 font-medium leading-relaxed line-clamp-3 flex-1 min-w-0 m-0 group-hover:text-amber-600 dark:group-hover:text-amber-300 transition-colors">
                ${hlText}
              </p>
              ${thumbHtml}
            </div>
          </div>
          <div class="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-1.5 border-t border-amber-200/50 dark:border-amber-900/50 shrink-0">
            <span class="font-mono flex items-center gap-1.5 text-amber-700 dark:text-amber-300 font-bold">
              <span class="animate-pulse text-amber-500">⚡</span>
              <span>${spotlightTag}</span>
            </span>
            <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-amber-600 dark:text-amber-400 hover:text-amber-700 dark:hover:text-amber-300 font-bold hover:underline flex items-center gap-0.5" onclick="event.stopPropagation()">
              <span>${btnText}</span>
            </a>
          </div>
        </article>
      `;
    }

    function renderLeadVideoCard(leadMedia, isZh) {
      if (!leadMedia || typeof leadMedia !== 'object') return '';
      let videoId = leadMedia.video_id || '';
      if (!videoId && leadMedia.url) {
        const m = String(leadMedia.url).match(/(?:v=|youtu\.be\/|embed\/)([0-9A-Za-z_-]{11})/);
        if (m) videoId = m[1];
      }
      const title = escapeHtml((isZh ? leadMedia.title_zh : leadMedia.title_en) || leadMedia.title || '');
      const titleEsc = title.replace(/'/g, "\'").replace(/"/g, '&quot;');
      let author = escapeHtml(leadMedia.source || leadMedia.author || 'AI Engineer').replace(/^YouTube\s*·\s*/, '').trim();
      const url = escapeHtml(leadMedia.url || '#');
      const diffH = leadMedia.diff_hours || 12.0;
      const timeBadge = isZh ? `${diffH}h 前` : `${diffH}h ago`;
      const tags = leadMedia.tags || ['#HandsOn', '#Benchmark', '#AI'];
      const tagsHtml = tags.slice(0, 2).map(t => `<span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 border border-indigo-500/20">${escapeHtml(t)}</span>`).join(' ');

      const leadBadge = isZh ? '🎬 48h 极客实测' : '🎬 48h Lab Review';
      const leadSourceText = isZh ? '原片 ↗' : 'Source ↗';
      const leadPlayText = isZh ? '影院播放 ▶' : 'Theater Play ▶';
      const embedUrl = videoId ? `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&rel=0` : url;

      let posterUrl = '';
      let fallbackPoster = '';
      if (videoId) {
        posterUrl = `https://wsrv.nl/?url=https%3A//i.ytimg.com/vi/${encodeURIComponent(videoId)}/maxresdefault.jpg&w=400&output=webp&q=85`;
        fallbackPoster = `https://wsrv.nl/?url=https%3A//i.ytimg.com/vi/${encodeURIComponent(videoId)}/hqdefault.jpg&w=400&output=webp&q=85`;
      } else if (leadMedia.image_url && isValidTweetImageUrl(leadMedia.image_url)) {
        posterUrl = `https://wsrv.nl/?url=${encodeURIComponent(leadMedia.image_url)}&w=400&output=webp&q=85`;
        fallbackPoster = posterUrl;
      } else {
        posterUrl = 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=400&q=80';
        fallbackPoster = posterUrl;
      }

      return `
        <div class="flex flex-col justify-between bg-slate-900/95 dark:bg-slate-950/95 rounded-xl border border-indigo-500/30 p-3 shadow-md relative overflow-hidden group/vcard text-white h-full" style="height: 180px; max-height: 180px; overflow: hidden;">
          <div class="flex items-center justify-between text-xs mb-1.5 shrink-0">
            <div class="flex items-center space-x-1.5 min-w-0">
              <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black bg-gradient-to-r from-rose-500 to-red-600 text-white shadow-sm shrink-0">
                <span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                <span>${leadBadge}</span>
              </span>
              <span class="text-slate-200 font-bold text-xs truncate max-w-[130px]">📺 ${author}</span>
            </div>
            <span class="text-slate-300 font-mono text-[10px] bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-700/60 shrink-0">⚡ ${timeBadge}</span>
          </div>

          <div class="flex items-center gap-2.5 my-1 flex-1 min-h-0 overflow-hidden">
            <div class="relative shrink-0 rounded-lg overflow-hidden bg-black cursor-pointer group/thumb border border-slate-800 shadow-inner" style="width: 104px; height: 62px; max-width: 104px; max-height: 62px;" onclick="openVideoModal('${embedUrl}', '${titleEsc}', 'youtube', '${url}')" title="${isZh ? '点击就地影院播放' : 'Click to play in theater mode'}">
              <img src="${posterUrl}" alt="${title}" style="width: 104px; height: 62px; object-fit: cover;" onerror="this.onerror=null; this.src='${fallbackPoster}'" loading="eager">
              <div class="absolute inset-0 bg-black/25 group-hover/thumb:bg-black/5 transition-colors flex items-center justify-center">
                <div class="w-6 h-6 rounded-full bg-red-600/95 text-white flex items-center justify-center text-[10px] shadow-lg group-hover/thumb:scale-110 transition-transform">▶</div>
              </div>
            </div>
            <div class="min-w-0 flex-1 flex flex-col justify-between h-full py-0.5">
              <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-xs font-bold text-slate-100 hover:text-sky-300 transition-colors line-clamp-2 leading-snug" title="${title}">
                ${title}
              </a>
              <div class="flex items-center gap-1 overflow-hidden mt-1">
                ${tagsHtml}
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between pt-1.5 border-t border-slate-800/80 text-[10px] text-slate-400 shrink-0">
            <span class="font-mono">16:9 ${isZh ? '实测跑分' : 'Lab Benchmark'}</span>
            <div class="flex items-center gap-2">
              <button type="button" onclick="openVideoModal('${embedUrl}', '${titleEsc}', 'youtube', '${url}')" class="text-rose-400 hover:text-rose-300 font-bold flex items-center gap-0.5 cursor-pointer">
                <span>${leadPlayText}</span>
              </button>
              <a href="${url}" target="_blank" rel="noopener noreferrer" class="text-slate-400 hover:text-slate-200">
                <span>${leadSourceText}</span>
              </a>
            </div>
          </div>
        </div>
      `;
    }

    function updateTickerPageUI(cur, total) {
      const ind = document.getElementById('viral-ticker-page-indicator');
      if (ind) ind.textContent = `${cur} / ${Math.max(1, total)}`;
    }

    function playHeroLeadVideo(videoId, fallbackUrl) {
      if (window.event) window.event.stopPropagation();
      const box = document.getElementById('hero-lead-video-box');
      if (!box) {
        if (fallbackUrl && fallbackUrl !== '#') {
          window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
        }
        return;
      }
      if (!videoId) {
        if (fallbackUrl && fallbackUrl !== '#') {
          window.open(fallbackUrl, '_blank', 'noopener,noreferrer');
        }
        return;
      }
      box.removeAttribute('onclick');
      box.classList.remove('cursor-pointer');
      box.innerHTML = `
        <iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&rel=0&modestbranding=1" 
          title="AI Hands-on Demo" 
          class="w-full h-full border-0 rounded-xl" 
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
          allowfullscreen>
        </iframe>
      `;
    }

    function openImageLightbox(imageUrl, e) {
      if (e && e.stopPropagation) e.stopPropagation();
      if (!imageUrl) return;
      let modal = document.getElementById('image-lightbox-modal');
      if (!modal) {
        modal = document.createElement('div');
        modal.id = 'image-lightbox-modal';
        modal.className = 'fixed inset-0 z-[9999] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 cursor-zoom-out transition-opacity duration-300';
        modal.onclick = closeImageLightbox;
        modal.innerHTML = `
          <div class="relative max-w-5xl max-h-[92vh] flex flex-col items-center" onclick="event.stopPropagation()">
            <button type="button" onclick="closeImageLightbox()" class="absolute -top-11 right-0 text-white/80 hover:text-white text-2xl font-bold p-2 cursor-pointer transition-colors" aria-label="Close">✕</button>
            <img id="image-lightbox-img" src="" alt="Enlarged view" class="max-w-full max-h-[85vh] object-contain rounded-xl shadow-2xl border border-white/10">
          </div>
        `;
        document.body.appendChild(modal);
        window.addEventListener('keydown', (evt) => {
          if (evt.key === 'Escape') closeImageLightbox();
        });
      }
      const img = document.getElementById('image-lightbox-img');
      if (img) img.src = imageUrl;
      modal.classList.remove('hidden');
      modal.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    }

    function closeImageLightbox() {
      const modal = document.getElementById('image-lightbox-modal');
      if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
      }
      document.body.style.overflow = '';
    }

    function renderHeroMediaShowcase(heroShowcase) {
      if (!heroShowcase) return false;
      const leadMedia = heroShowcase.lead_media || heroShowcase.video;
      const viralTweets = heroShowcase.viral_tweets || heroShowcase.tweets || [];
      renderViralTicker(viralTweets, leadMedia);
      return true;
    }

    function renderViralTicker(tweets, leadMedia = null) {
      const isZh = currentLang === 'zh';
      let container = document.getElementById('viral-ticker-container');
      if (!container) {
        const vp = document.getElementById('viral-ticker-viewport');
        if (vp && vp.parentNode) {
          container = document.createElement('div');
          container.id = 'viral-ticker-container';
          container.className = 'relative w-full';
          vp.parentNode.insertBefore(container, vp);
          container.appendChild(vp);
        }
      }
      if (!container) return;

      const tiboResetTweet = (tweets || []).find(it => isTiboResetTweet(it));
      const titleEl = document.getElementById('viral-ticker-title');
      const subtitleEl = document.getElementById('viral-ticker-subtitle');
      if (leadMedia || tiboResetTweet) {
        if (titleEl) titleEl.textContent = isZh ? '🎬 极客实测展厅 · 48h 独家前沿与领袖精粹' : '🎬 48h Hands-on Lab & Leader Radar';
        if (subtitleEl) subtitleEl.textContent = isZh ? '· 拒绝同质化：汇聚 48h 内最具实操价值的极客上手评测与领袖视效动态' : '· Zero Redundancy: 48h Battle-Tested AI Workflows, Model Reviews & Leader Visuals';
      } else {
        if (titleEl) titleEl.textContent = isZh ? '当日 AI 领袖与核心火爆推文 · 垂直走马灯' : '24h Viral AI Leader Tweets · Live Ticker';
        if (subtitleEl) subtitleEl.textContent = isZh ? '· 汇聚全球 AI 顶流导师、核心架构师与创始团队的 24h 最新研判与实录' : '· Curated AI titan insights, architecture deep dives, frontier models & builder showcases';
      }

      if ((!tweets || tweets.length === 0) && !leadMedia) {
        container.innerHTML = `
          <div id="viral-ticker-viewport" class="w-full relative overflow-hidden h-[145px] md:h-[180px]">
            <div id="viral-ticker-slider" class="flex flex-col space-y-4">
              <div class="text-xs text-slate-400 p-3">${isZh ? '暂无当日火爆推文' : 'No viral leader tweets available for today'}</div>
            </div>
          </div>`;
        updateTickerPageUI(1, 1);
        return;
      }

      if (tiboResetTweet) {
        // Priority 1: Tibo reset tweet pinned in Column 1 (User's Absolute Rule)
        const pinnedCardHtml = renderTiboPinnedCard(tiboResetTweet, isZh);
        const otherTweets = (tweets || []).filter(it => !isTiboResetTweet(it));
        const sliderCards = [];
        if (leadMedia) {
          sliderCards.push(renderLeadVideoCard(leadMedia, isZh));
        }
        otherTweets.forEach((it, cIdx) => {
          sliderCards.push(renderViralTickerCard(it, isZh, cIdx));
        });

        const pages = [];
        for (let i = 0; i < sliderCards.length; i += 2) {
          const slice = sliderCards.slice(i, i + 2);
          pages.push(`
            <div class="viral-ticker-page grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full shrink-0 items-stretch h-[145px] md:h-[180px]">
              ${slice.join('')}
            </div>
          `);
        }

        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 items-stretch">
            <div id="viral-ticker-pinned" class="w-full h-full min-h-[145px] md:min-h-[180px]">
              ${pinnedCardHtml}
            </div>
            <div id="viral-ticker-viewport" class="col-span-1 md:col-span-2 relative overflow-hidden h-[145px] md:h-[180px]">
              <div id="viral-ticker-slider" class="flex flex-col space-y-4 transition-transform duration-700 ease-out" style="transform: translateY(0px);">
                ${pages.join('')}
              </div>
            </div>
          </div>
        `;
        window.viralTickerCurrentPage = 0;
        window.viralTickerTotalPages = Math.max(1, pages.length);
        updateTickerPageUI(1, pages.length);
      } else if (leadMedia) {
        // Priority 2: Lead Video pinned in Column 1; Columns 2 & 3 scroll down through tweets (2 per page)
        const pinnedCardHtml = renderLeadVideoCard(leadMedia, isZh);
        const pages = [];
        for (let i = 0; i < (tweets || []).length; i += 2) {
          const slice = (tweets || []).slice(i, i + 2);
          const cards = slice.map((it, cIdx) => renderViralTickerCard(it, isZh, cIdx)).join('');
          pages.push(`
            <div class="viral-ticker-page grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full shrink-0 items-stretch h-[145px] md:h-[180px]">
              ${cards}
            </div>
          `);
        }

        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3.5 items-stretch">
            <div id="viral-ticker-pinned" class="w-full h-full min-h-[145px] md:min-h-[180px]">
              ${pinnedCardHtml}
            </div>
            <div id="viral-ticker-viewport" class="col-span-1 md:col-span-2 relative overflow-hidden h-[145px] md:h-[180px]">
              <div id="viral-ticker-slider" class="flex flex-col space-y-4 transition-transform duration-700 ease-out" style="transform: translateY(0px);">
                ${pages.join('')}
              </div>
            </div>
          </div>
        `;
        window.viralTickerCurrentPage = 0;
        window.viralTickerTotalPages = Math.max(1, pages.length);
        updateTickerPageUI(1, pages.length);
      } else {
        // Priority 3: Full 3-card sliding ticker
        const pages = [];
        for (let i = 0; i < (tweets || []).length; i += 3) {
          const slice = (tweets || []).slice(i, i + 3);
          const cards = slice.map((it, cIdx) => renderViralTickerCard(it, isZh, cIdx)).join('');
          pages.push(`
            <div class="viral-ticker-page grid grid-cols-1 md:grid-cols-3 gap-3.5 w-full shrink-0 items-stretch h-[145px] md:h-[180px]">
              ${cards}
            </div>
          `);
        }

        container.innerHTML = `
          <div id="viral-ticker-viewport" class="w-full relative overflow-hidden h-[145px] md:h-[180px]">
            <div id="viral-ticker-slider" class="flex flex-col space-y-4 transition-transform duration-700 ease-out" style="transform: translateY(0px);">
              ${pages.join('')}
            </div>
          </div>
        `;
        window.viralTickerCurrentPage = 0;
        window.viralTickerTotalPages = Math.max(1, pages.length);
        updateTickerPageUI(1, pages.length);
      }

      initViralTickerAutoScroll();
    }

    function fitViralTickerHeight() {
      // Pure CSS h-[145px] md:h-[180px] handles height with zero forced reflow and zero CLS
    }

    function flipViralTicker(direction) {
      const slider = document.getElementById('viral-ticker-slider');
      if (!slider) return;
      const pages = slider.querySelectorAll('.viral-ticker-page');
      if (pages.length <= 1) return;

      window.viralTickerCurrentPage = (window.viralTickerCurrentPage + direction + pages.length) % pages.length;
      
      const pageEl = pages[0];
      const step = pageEl ? (pageEl.offsetHeight + 16) : ((window.innerWidth >= 768 ? 180 : 145) + 16);
      const offset = window.viralTickerCurrentPage * step;
      slider.style.transform = `translateY(-${offset}px)`;
      updateTickerPageUI(window.viralTickerCurrentPage + 1, pages.length);
    }

    function toggleViralTickerPause() {
      window.viralTickerPaused = !window.viralTickerPaused;
      const btn = document.getElementById('viral-ticker-pause');
      if (btn) {
        btn.textContent = window.viralTickerPaused ? '▶' : '⏸';
        btn.title = window.viralTickerPaused ? (currentLang === 'zh' ? '播放' : 'Play') : (currentLang === 'zh' ? '暂停' : 'Pause');
      }
    }

    function initViralTickerAutoScroll() {
      const section = document.getElementById('viral-ticker-section');
      if (!section) return;

      if (!section._hoverInit) {
        section._hoverInit = true;
        section.addEventListener('mouseenter', () => { window.viralTickerHovered = true; }, { passive: true });
        section.addEventListener('mouseleave', () => { window.viralTickerHovered = false; }, { passive: true });
      }

      if (window.viralTickerInterval) clearInterval(window.viralTickerInterval);
      window.viralTickerInterval = setInterval(() => {
        if (document.hidden || window.viralTickerPaused || window.viralTickerHovered) return;
        flipViralTicker(1);
      }, 7000);
    }

    window.flipViralTicker = flipViralTicker;
    window.toggleViralTickerPause = toggleViralTickerPause;

    // =========================================================================
    // 🔥 24h 核心话题全景透视 · 智库专题 (Topic Focus: 脉络 + 立场对撞 + 情报束)
    // =========================================================================
    let currentTopicFocusIdx = 0;

    function switchTopicFocus(idx) {
      currentTopicFocusIdx = idx;
      const tabs = document.querySelectorAll('.topic-tab-btn');
      tabs.forEach((btn, i) => {
        const isActive = (i === idx);
        btn.classList.toggle('active', isActive);
        if (isActive) {
          btn.className = "topic-tab-btn active px-3 py-1.5 rounded-xl font-bold text-xs bg-indigo-600 text-white shadow-md border border-indigo-400/40 transition-all cursor-pointer flex items-center gap-1.5";
        } else {
          btn.className = "topic-tab-btn px-3 py-1.5 rounded-xl font-semibold text-xs bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-all cursor-pointer flex items-center gap-1.5";
        }
      });
      const cards = document.querySelectorAll('.topic-focus-card');
      cards.forEach((card, i) => {
        card.classList.toggle('hidden', i !== idx);
      });
    }

    function toggleTopicFocusCollapse() {
      const content = document.getElementById('topic-focus-content');
      const btn = document.getElementById('topic-focus-toggle-btn');
      if (!content) return;
      const isCollapsed = content.classList.contains('hidden');
      const isZh = (currentLang === 'zh');
      if (isCollapsed) {
        content.classList.remove('hidden');
        if (btn) btn.textContent = isZh ? '▲ 收起' : '▲ Collapse';
        try { localStorage.setItem('topic_focus_collapsed', 'false'); } catch(e) {}
      } else {
        content.classList.add('hidden');
        if (btn) btn.textContent = isZh ? '▼ 展开' : '▼ Expand';
        try { localStorage.setItem('topic_focus_collapsed', 'true'); } catch(e) {}
      }
    }

    function renderTopicFocus(topics) {
      if (!topics || !Array.isArray(topics) || topics.length === 0) return;
      const section = document.getElementById('topic-focus-section');
      if (!section) return;

      const isZh = (currentLang === 'zh');
      const tabsBar = document.getElementById('topic-tabs-bar');
      const contentEl = document.getElementById('topic-focus-content');
      const headerTitle = document.getElementById('topic-focus-header-title');
      const headerDesc = document.getElementById('topic-focus-header-desc');
      const toggleBtn = document.getElementById('topic-focus-toggle-btn');

      if (headerTitle) {
        const titleText = isZh ? "🔥 24h 核心话题全景透视" : "🔥 24h Topic Focus & Perspectives";
        const badgeText = isZh ? "TOP 3 智库专题" : "TOP 3 DOSSIERS";
        headerTitle.innerHTML = `<span>${titleText}</span><span class="text-[10px] px-2 py-0.5 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono font-bold tracking-wider">${badgeText}</span>`;
      }
      if (headerDesc) {
        headerDesc.textContent = isZh ? "· 事件脉络 · 大V观点立场对撞 · 关联情报束" : "· Core Context · Viewpoints Collision · Linked Bundles";
      }

      try {
        const wasCollapsed = localStorage.getItem('topic_focus_collapsed') === 'true';
        if (contentEl) {
          contentEl.classList.toggle('hidden', wasCollapsed);
        }
        if (toggleBtn) {
          toggleBtn.textContent = wasCollapsed ? (isZh ? '▼ 展开' : '▼ Expand') : (isZh ? '▲ 收起' : '▲ Collapse');
        }
      } catch(e) {}

      if (tabsBar && contentEl) {
        tabsBar.innerHTML = topics.map((t, idx) => {
          const isAct = (idx === currentTopicFocusIdx);
          const badge = (isZh ? t.badge_zh : t.badge_en) || "";
          const title = (isZh ? t.title_zh : t.title_en) || "";
          const heat = t.heat_score || 9.8;
          const shortTitle = title.length > 12 ? title.slice(0, 11) + "…" : title;
          const cls = isAct
            ? "topic-tab-btn active px-3 py-1.5 rounded-xl font-bold text-xs bg-indigo-600 text-white shadow-md border border-indigo-400/40 transition-all cursor-pointer flex items-center gap-1.5"
            : "topic-tab-btn px-3 py-1.5 rounded-xl font-semibold text-xs bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 hover:text-white border border-slate-700/60 transition-all cursor-pointer flex items-center gap-1.5";
          return `
            <button type="button" id="topic-tab-${idx}" onclick="switchTopicFocus(${idx})" class="${cls}" data-idx="${idx}">
              <span class="text-[11px] font-mono opacity-90">${badge.slice(0, 2)}</span>
              <span class="truncate">${escapeHtml(shortTitle)}</span>
              <span class="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/20 text-white font-bold ml-0.5">${heat}</span>
            </button>`;
        }).join('');

        contentEl.innerHTML = topics.map((t, idx) => {
          const isAct = (idx === currentTopicFocusIdx);
          const cardCls = "topic-focus-card grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch" + (isAct ? "" : " hidden");
          const catTag = isZh ? (t.category_tag_zh || "") : (t.category_tag_en || "");
          const heat = t.heat_score || 9.8;
          const title = isZh ? (t.title_zh || "") : (t.title_en || "");
          const summary = isZh ? (t.summary_zh || "") : (t.summary_en || "");
          
          const pro = t.perspective_pro || {};
          const con = t.perspective_con || {};
          const proRole = isZh ? (pro.role_zh || "") : (pro.role_en || "");
          const proSpeaker = isZh ? (pro.speaker_zh || "") : (pro.speaker_en || "");
          const proPoint = isZh ? (pro.point_zh || "") : (pro.point_en || "");
          const conRole = isZh ? (con.role_zh || "") : (con.role_en || "");
          const conSpeaker = isZh ? (con.speaker_zh || "") : (con.speaker_en || "");
          const conPoint = isZh ? (con.point_zh || "") : (con.point_en || "");

          const newsList = t.linked_news || [];
          const newsHtml = newsList.map(n => {
            const nTitle = isZh ? (n.title_zh || n.title) : (n.title_en || n.title);
            const nSrc = n.source || "Global AI";
            const nId = n.id || "";
            const nUrl = n.url || "#";
            const clickAttr = nId ? `onclick="if(!event.target.closest('a')) openAiNewsModal('${nId}')"` : '';
            return `
              <div class="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-indigo-500/40 transition-colors cursor-pointer group" ${clickAttr}>
                <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30 shrink-0 font-mono mt-0.5">${escapeHtml(nSrc.slice(0, 10))}</span>
                <div class="min-w-0 flex-1">
                  <a href="${nUrl}" target="_blank" rel="noopener noreferrer" class="text-xs text-slate-200 group-hover:text-indigo-300 transition-colors line-clamp-2 leading-snug font-medium block">
                    ${escapeHtml(nTitle)}
                  </a>
                </div>
              </div>`;
          }).join('') || `<p class="text-xs text-slate-400">${isZh ? "暂无关联快讯" : "No linked news"}</p>`;

          const tweetList = t.linked_tweets || [];
          const tweetHtml = tweetList.map(tw => {
            const author = tw.author || "AI Leader";
            const handle = tw.author_handle || "@ai";
            const content = isZh ? (tw.content_zh || tw.content_en) : (tw.content_en || tw.content_zh);
            const avatar = tw.author_avatar || "https://api.dicebear.com/7.x/bottts/svg?seed=VIP";
            return `
              <div class="flex items-start gap-2.5 p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-sky-500/40 transition-colors">
                <img src="${avatar}" alt="${escapeHtml(author)}" width="24" height="24" class="w-6 h-6 rounded-full object-cover shrink-0 ring-1 ring-slate-700 mt-0.5" loading="lazy" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=VIP'">
                <div class="min-w-0 flex-1">
                  <div class="flex items-center justify-between text-[11px] gap-1 mb-0.5">
                    <span class="font-bold text-slate-200 truncate">${escapeHtml(author)}</span>
                    <a href="${tw.url || '#'}" target="_blank" rel="noopener noreferrer" class="text-[10px] text-sky-400 hover:underline shrink-0">${isZh ? "原帖 ↗" : "Post ↗"}</a>
                  </div>
                  <p class="text-[11px] text-slate-300 line-clamp-2 leading-relaxed">${escapeHtml(content || '')}</p>
                </div>
              </div>`;
          }).join('');

          const tool = t.linked_tool;
          let toolHtml = "";
          if (tool) {
            const toolName = isZh ? (tool.title_zh || tool.name) : (tool.title_en || tool.name);
            const toolDesc = isZh ? (tool.desc_zh || tool.takeaway_zh || "") : (tool.desc_en || tool.takeaway_en || "");
            const isWf = !!tool.is_workflow;
            const tagLabel = isWf ? (isZh ? "🛠️ 实战落地配方" : "🛠️ Production Playbook") : (isZh ? "🚀 场景落地工具" : "🚀 Applied AI Tool");
            const actionBtn = isWf ? (isZh ? "📋 一键直达工作流" : "📋 View Playbook") : (isZh ? "立即体验 ↗" : "Try Tool ↗");
            const toolClick = isWf ? `onclick="switchTab('prompts')"` : '';
            toolHtml = `
              <div class="mt-2.5 p-2.5 rounded-xl bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-slate-900/60 border border-purple-500/30 hover:border-purple-400/50 transition-all">
                <div class="flex items-center justify-between gap-1 mb-1">
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">${tagLabel}</span>
                  <span class="text-[10px] text-emerald-400 font-mono font-semibold">${tool.weekly_stars || '+3,000★'}</span>
                </div>
                <h4 class="text-xs font-bold text-slate-100 truncate mt-1">${escapeHtml(toolName)}</h4>
                <p class="text-[11px] text-slate-300 line-clamp-2 leading-relaxed mt-1">${escapeHtml(toolDesc)}</p>
                <div class="flex items-center justify-end mt-2 pt-1.5 border-t border-purple-500/20">
                  <a href="${tool.url || tool.github_url || '#'}" target="_blank" rel="noopener noreferrer" ${toolClick} class="text-xs font-semibold text-purple-300 hover:text-purple-200 hover:underline inline-flex items-center gap-1">
                    <span>${actionBtn}</span>
                  </a>
                </div>
              </div>`;
          }

          return `
            <article id="topic-focus-card-${idx}" class="${cardCls}" data-idx="${idx}">
              <div class="lg:col-span-4 flex flex-col justify-between space-y-3 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 font-mono">
                      ${escapeHtml(catTag)}
                    </span>
                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30 font-mono">
                      🔥 ${isZh ? "爆度" : "HEAT"} ${heat}
                    </span>
                  </div>
                  <h3 class="text-base sm:text-lg font-black text-white leading-snug tracking-tight">
                    ${escapeHtml(title)}
                  </h3>
                  <div class="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-200 text-xs sm:text-sm leading-relaxed">
                    ${escapeHtml(summary)}
                  </div>
                </div>
                <div class="flex items-center gap-2 pt-2 border-t border-slate-800/80 flex-wrap text-[10px] text-indigo-300 font-mono">
                  <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">🎯 ${isZh ? "核心爆发点" : "Core Milestone"}</span>
                  <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">💡 ${isZh ? "行业范式影响" : "Industry Impact"}</span>
                  <span class="px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-500/30">⚡ ${isZh ? "24h 追踪" : "24h Live"}</span>
                </div>
              </div>

              <div class="lg:col-span-4 flex flex-col justify-between space-y-3 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between pb-1.5 border-b border-slate-800">
                    <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5 uppercase tracking-wider">
                      <span>⚔️</span>
                      <span>${isZh ? "大V观点立场对撞" : "Perspectives Collision"}</span>
                    </h4>
                    <span class="text-[10px] text-slate-400 font-mono">${isZh ? "双面对照" : "Dual Perspectives"}</span>
                  </div>

                  <div class="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 text-emerald-100 space-y-1.5 shadow-sm">
                    <div class="flex items-center justify-between gap-1 text-[11px]">
                      <span class="font-bold text-emerald-300">${escapeHtml(proRole)}</span>
                      <span class="text-[10px] text-emerald-400 font-mono truncate max-w-[140px]">${escapeHtml(proSpeaker)}</span>
                    </div>
                    <p class="text-xs text-emerald-100/90 leading-relaxed font-normal">
                      “${escapeHtml(proPoint)}”
                    </p>
                  </div>

                  <div class="p-3 rounded-xl bg-rose-950/30 border border-rose-500/30 text-rose-100 space-y-1.5 shadow-sm">
                    <div class="flex items-center justify-between gap-1 text-[11px]">
                      <span class="font-bold text-rose-300">${escapeHtml(conRole)}</span>
                      <span class="text-[10px] text-rose-400 font-mono truncate max-w-[140px]">${escapeHtml(conSpeaker)}</span>
                    </div>
                    <p class="text-xs text-rose-100/90 leading-relaxed font-normal">
                      “${escapeHtml(conPoint)}”
                    </p>
                  </div>
                </div>

                <div class="text-[10px] text-slate-400 text-right pt-1 font-mono">
                  ${isZh ? "智库核心研判 · 拒绝盲目跟风" : "Independent Analysis · Beyond the Hype"}
                </div>
              </div>

              <div class="lg:col-span-4 flex flex-col justify-between space-y-2.5 p-4 rounded-xl bg-slate-950/70 border border-indigo-500/20 shadow-md">
                <div>
                  <div class="flex items-center justify-between pb-1.5 border-b border-slate-800 mb-2">
                    <h4 class="text-xs font-bold text-slate-200 flex items-center gap-1.5 uppercase tracking-wider">
                      <span>🔗</span>
                      <span>${isZh ? "关联情报束" : "Linked Intelligence Bundle"}</span>
                    </h4>
                    <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      ${newsList.length} ${isZh ? "快讯" : "News"} · ${tweetList.length} ${isZh ? "推文" : "Tweets"}
                    </span>
                  </div>

                  <div class="space-y-1.5 mb-2">
                    ${newsHtml}
                  </div>

                  <div class="space-y-1.5">
                    ${tweetHtml}
                  </div>

                  ${toolHtml}
                </div>

                <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                  <span>${isZh ? "数据自动聚合更新" : "Auto-aggregated 24h"}</span>
                  <button type="button" onclick="switchTab('all')" class="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline cursor-pointer">
                    ${isZh ? "查看完整信息流 →" : "Explore Full Stream →"}
                  </button>
                </div>
              </div>
            </article>`;
        }).join('');
      }
    }

    window.switchTopicFocus = switchTopicFocus;
    window.toggleTopicFocusCollapse = toggleTopicFocusCollapse;

    // 渲染今日 60s Top 3 走马灯 (支持 AI 资讯概要弹窗与直达原文)
    function renderTopThree(topItems) {
      const container = document.getElementById('top-three-container');
      const t = I18N[currentLang];
      if (!topItems || topItems.length === 0) {
        container.innerHTML = `<div class="text-xs text-slate-400 col-span-3">${t.digestLoading}</div>`;
        return;
      }

      const isZh = currentLang === 'zh';
      container.innerHTML = topItems.map((item, idx) => {
        const isCrowned = idx === 0;
        const badge = (isZh ? (item.badge_zh || item.badge) : (item.badge_en || item.badge)) || (isZh ? "⚡ 今日头条" : "⚡ Top Story");
        const crownBadge = isCrowned ? (isZh ? "👑 24h 重大破圈头条" : "👑 24h Headline") : badge;
        const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
        const summary = (isZh ? (item.summary_zh || item.summary || item.content_snippet) : (item.summary_en || item.summary || item.content_snippet)) || "";
        const timeObj = formatTime(item.raw_published_at, currentLang);
        const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30 text-[9px] font-bold">${t.todayTag}</span>` : '';
        const cleanSource = item.source || "";
        const itemId = item.id || `top_${idx}`;

        const articleClass = isCrowned
          ? "group border-2 border-amber-500/60 dark:border-amber-400/50 shadow-md ring-1 ring-amber-500/20 bg-gradient-to-br from-amber-50/40 via-white to-amber-100/20 dark:from-slate-900 dark:via-slate-900/90 dark:to-amber-950/20 p-3.5 rounded-xl transition-all flex flex-col justify-between space-y-2.5 cursor-pointer relative"
          : "group bg-white/90 dark:bg-slate-900/80 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 p-3.5 rounded-xl transition-all flex flex-col justify-between space-y-2.5 shadow-sm cursor-pointer";

        const badgeHtml = isCrowned
          ? `<span class="font-extrabold px-2 py-0.5 rounded-md bg-gradient-to-r from-amber-500 to-rose-500 text-white shadow-sm shrink-0 flex items-center gap-1">${crownBadge}</span>`
          : `<span class="font-bold px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/25 shrink-0">${badge}</span>`;

        return `
          <article class="${articleClass}" onclick="if(!event.target.closest('a, button')) openAiNewsModal('${itemId}')">
            <div class="space-y-1.5">
              <div class="flex items-center justify-between text-[10px] gap-2">
                <div class="flex items-center space-x-1.5 min-w-0">
                  ${badgeHtml}
                  ${todayBadge}
                </div>
                <span class="text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap shrink-0 ml-auto" title="${timeObj.display}">🕒 ${timeObj.relative || timeObj.display}</span>
              </div>
              <h3 class="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors line-clamp-2 leading-snug cursor-pointer" onclick="event.stopPropagation(); openAiNewsModal('${itemId}')">
                ${title}
              </h3>
              <p class="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                ${summary}
              </p>
            </div>
            <div class="flex items-center justify-between text-[10px] text-slate-500 pt-2 border-t border-slate-200 dark:border-slate-800/60 gap-2">
              <span class="truncate max-w-[110px] sm:max-w-[130px]">${t.sourceLabel || '信源:'} ${cleanSource}</span>
              <div class="flex items-center space-x-1.5 shrink-0">
                <button type="button" onclick="event.stopPropagation(); openAiNewsModal('${itemId}')" class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 hover:from-indigo-500/20 hover:to-purple-500/20 text-indigo-600 dark:text-indigo-300 border border-indigo-200/80 dark:border-indigo-800/80 text-[10px] font-semibold transition-all shadow-sm cursor-pointer">
                  <span>📋</span>
                  <span>${t.aiAnalysisBtn || '资讯概要'}</span>
                </button>
                <a href="${item.url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" class="text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline font-medium shrink-0">
                  ${t.readMore || '阅读原文 ↗'}
                </a>
              </div>
            </div>
          </article>
        `;
      }).join('');
    }

    // 辅助函数：根据工具类型提供现代化矢量微图标
    function getToolSvgIcon(iconType) {
      if (iconType === 'vision') {
        return `<svg class="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>`;
      } else if (iconType === 'code') {
        return `<svg class="w-4 h-4 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>`;
      } else if (iconType === 'audio') {
        return `<svg class="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>`;
      } else if (iconType === 'chat') {
        return `<svg class="w-4 h-4 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>`;
      } else {
        return `<svg class="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>`;
      }
    }

    // ==========================================
    // 专门卡片渲染：新闻快讯卡片 (支持 Gemini AI 深度解读交互)
    // ==========================================
    function renderNewsCard(item, cardIndex = -1) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
      const summary = (isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || "";
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold">${t.todayTag}</span>` : '';

      const specList = item.spec_tags || [];
      const specBadges = (specList && specList.length)
        ? `<div class="flex items-center gap-1.5 flex-wrap pt-0.5">${specList.map(s => `<span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/70 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">⚡ ${escapeHtml(translateSpecTag(s, currentLang))}</span>`).join('')}</div>`
        : '';

      const isFakeOrGenericCover = (url) => {
        if (!url || typeof url !== 'string') return true;
        const u = url.toLowerCase().trim();
        if (!u || u === 'null' || u === 'undefined' || u === 'none') return true;
        const badPatterns = [
          'photo-1618005182384-a83a8bd57fbe',
          'photo-1620712943543',
          'photo-1558494949-ef010cbdcc31',
          'photo-1526374965328',
          'photo-1485827404703',
          'lh3.googleusercontent.com/j6_cofbog',
          'lh3.googleusercontent.com',
          'techmeme.com/img',
          'techmeme.com/pml',
          'techmeme_sq',
          'pml.png',
          'pixel',
          'spacer',
          'tracking',
          'icon.',
          'avatar.',
          '260915_thespark_climateinnovators.jpg',
          '6b72d2fb-fbfe-41f2-ba26-d64817454f73_1200x675.jpeg'
        ];
        return badPatterns.some(p => u.includes(p));
      };
      const hasRealImage = !!(item.image_url && !isFakeOrGenericCover(item.image_url));
      const cleanSource = item.source || "";
      const hasVideo = !!(item.has_video || (item.media_assets && item.media_assets.has_video) || (item.video_url && item.video_url.length > 5));
      const videoBadge = hasVideo ? `<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/25 text-[9px] font-bold flex items-center gap-0.5">${isZh ? '📹 现场视频' : '📹 Video Report'}</span>` : '';
      const imgLoading = cardIndex === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy" decoding="async"';

      const isMajorBreaking = (cardIndex === 0 && (item.hot_score >= 5 || item.is_major_breaking));
      if (isMajorBreaking) {
        return `
        <article class="glass-card rounded-2xl p-4 sm:p-5 flex flex-col md:flex-row gap-4 justify-between group border-2 border-amber-500/60 dark:border-amber-400/50 hover:border-amber-500 transition-all cursor-pointer shadow-lg hover:shadow-xl bg-gradient-to-br from-amber-50/50 via-white to-orange-50/30 dark:from-slate-900 dark:via-slate-900/90 dark:to-amber-950/20 col-span-full relative" onclick="if(!event.target.closest('a')) openAiNewsModal('${item.id}')">
          <div class="absolute -top-3 left-4 px-3 py-0.5 rounded-full bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 text-white text-[10px] sm:text-xs font-black shadow-md flex items-center gap-1.5">
            <span>👑</span>
            <span>${isZh ? '24h 重大破圈头条 · 全网焦点' : '24h Major Breakthrough Headline'}</span>
          </div>
          ${hasRealImage ? `
            <div class="w-full md:w-5/12 aspect-video rounded-xl overflow-hidden bg-slate-950 border border-amber-500/30 relative shrink-0">
              <img src="${optimizeImageUrl(item.image_url, 720)}" data-orig="${escapeHtml(item.image_url)}" alt="${escapeHtml(title)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="eager" fetchpriority="high" onerror="this.onerror=null; if(this.parentElement) this.parentElement.style.display='none';">
              ${hasVideo ? `<span class="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md text-amber-400 border border-amber-500/40 text-[10px] font-bold flex items-center gap-1 shadow-md">▶ ${isZh ? '现场视频' : 'Video Report'}</span>` : ''}
            </div>` : ''}
          <div class="flex-1 flex flex-col justify-between space-y-2.5 min-w-0">
            <div>
              <div class="flex items-center justify-between text-xs mb-1.5">
                <div class="flex items-center space-x-2">
                  <span class="font-extrabold text-[11px] px-2.5 py-0.5 rounded-full bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30">⚡ ${cleanSource}</span>
                  ${todayBadge}
                  <span class="px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-700 dark:text-rose-300 border border-rose-500/30 text-[10px] font-bold">🔥 Hot 5.0</span>
                </div>
                <span class="text-xs text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap">🕒 ${timeObj.relative || timeObj.display}</span>
              </div>
              <h3 class="font-black text-base sm:text-lg text-slate-900 dark:text-slate-50 group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors leading-snug">
                ${title}
              </h3>
              ${specBadges}
              <p class="text-xs sm:text-sm text-slate-600 dark:text-slate-300 line-clamp-3 mt-1.5 leading-relaxed">
                ${summary}
              </p>
            </div>
            <div class="flex items-center justify-between text-xs pt-2.5 border-t border-amber-200/50 dark:border-amber-900/40 text-slate-500 dark:text-slate-400">
              <span class="text-xs font-mono text-amber-600 dark:text-amber-400 font-bold group-hover:underline flex items-center gap-1">
                ⚡ ${isZh ? '点击查看 5W1H 深度研判与速读' : 'Click for In-depth 5W1H Briefing'}
              </span>
              <a href="${item.url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" class="text-xs text-amber-700 dark:text-amber-400 hover:text-amber-600 hover:underline font-bold">
                ${isZh ? '官方公报 / 原文报道' : 'Official Report'} ↗
              </a>
            </div>
          </div>
        </article>
        `;
      }

      return `
        <article class="glass-card rounded-2xl p-3.5 sm:p-4 flex flex-row gap-3 sm:gap-4 justify-between group border border-slate-200/80 dark:border-slate-800/80 hover:border-indigo-500/60 transition-all cursor-pointer shadow-sm hover:shadow-lg hover:-translate-y-0.5 bg-white/95 dark:bg-slate-900/90" onclick="if(!event.target.closest('a')) openAiNewsModal('${item.id}')">
          ${hasRealImage ? `
            <div class="w-20 h-20 sm:w-36 sm:h-24 rounded-lg overflow-hidden bg-slate-950 border border-slate-200/80 dark:border-slate-800/80 relative shrink-0">
              <img src="${optimizeImageUrl(item.image_url, 480)}" data-orig="${escapeHtml(item.image_url)}" alt="${escapeHtml(title)}" width="480" height="270" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" ${imgLoading} onerror="this.onerror=null; if(this.parentElement) this.parentElement.style.display='none'; else this.style.display='none';">
              ${hasVideo ? `<span class="absolute bottom-1 right-1 px-1 py-0.5 rounded bg-black/75 backdrop-blur-md text-amber-400 border border-amber-500/30 text-[8px] font-bold flex items-center gap-0.5 shadow-sm">${isZh ? '▶' : '▶'}</span>` : ''}
            </div>` : ''}
          <div class="flex-1 flex flex-col justify-between space-y-2 min-w-0">
            <div>
              <div class="flex items-center justify-between text-xs mb-1">
                <div class="flex items-center space-x-1.5">
                  <span class="font-bold text-[10px] px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/25">${cleanSource}</span>
                  ${todayBadge}
                  ${videoBadge}
                </div>
                <span class="text-[11px] text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap" title="${timeObj.display}">🕒 ${timeObj.relative || timeObj.display}</span>
              </div>
              <h3 class="font-bold text-sm sm:text-base text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors leading-snug line-clamp-2">
                ${title}
              </h3>
              ${specBadges}
              <p class="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mt-1 leading-relaxed">
                ${summary}
              </p>
            </div>
            <div class="flex items-center justify-between text-xs pt-2 mt-2 border-t border-slate-100 dark:border-slate-800/60 text-slate-500 dark:text-slate-400">
              <span class="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 font-medium group-hover:underline flex items-center gap-1">
                ⚡ ${isZh ? '点击查看速读' : 'Click for Briefing'}
              </span>
              <a href="${item.url}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" class="text-[11px] text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline font-medium">
                ${isZh ? '源站' : 'Source'} ↗
              </a>
            </div>
          </div>
        </article>
      `;
    }

    // ==========================================
    // 专门卡片渲染：领袖观点·社交卡片 (𝕏 / Reddit 独立排版)
    // ==========================================
    // 严苛的 24 小时动态置顶判定 (仅限 24h 内且包含重置相关突破内容的资讯，超 24h 自动注销置顶特权)
    function isItemPinnedActive(item) {
      if (!item || !item.is_pinned) return false;
      if (!item.raw_published_at) return false;
      try {
        const pubTime = new Date(item.raw_published_at).getTime();
        const now = Date.now();
        const diffSec = (now - pubTime) / 1000;
        // 超过 24 小时 (86400秒) 严格取消置顶特权
        if (diffSec < 0 || diffSec > 86400) return false;
      } catch (e) {
        return false;
      }
      const text = `${item.title || ''} ${item.title_zh || ''} ${item.content_snippet || ''} ${(item.tags || []).join(' ')}`.toLowerCase();
      return text.includes('重置') || text.includes('reset') || text.includes('思维链重启');
    }

    function formatTweetText(text) {
      if (!text) return '';
      // 1. 先反转义 HTML entities，防止双重转义 (如 &#039; &quot; &amp; &lt; &gt;)
      let str = String(text)
        .replace(/&amp;/g, '&')
        .replace(/&#039;/g, "'")
        .replace(/&apos;/g, "'")
        .replace(/&quot;/g, '"')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>');

      // 清洗推文尾部 Twitter 自动附带的原生富媒体/引用锚点裸短链 (https://t.co/...)
      str = str.replace(/\s*https:\/\/t\.co\/[a-zA-Z0-9_-]+$/g, '');

      // 2. 安全转义 HTML 尖括号与与号，防止 XSS，保留纯单引号与双引号
      str = str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // 3. 高亮 #标签 (英中数字及下划线)
      str = str.replace(/#([\w\u4e00-\u9fa5]+)/g, '<span class="text-sky-500 dark:text-sky-400 font-medium hover:underline cursor-pointer">#$1</span>');
      // 4. 高亮 @提及 (Twitter Handle)
      str = str.replace(/@([a-zA-Z0-9_]+)/g, '<span class="text-sky-500 dark:text-sky-400 font-medium hover:underline cursor-pointer">@$1</span>');
      // 5. 高亮 http/https 链接
      str = str.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="text-sky-500 dark:text-sky-400 hover:underline break-all">$1</a>');
      return str;
    }

    function toggleTweetExpand(btn) {
      if (window.event) window.event.stopPropagation();
      const parent = btn.parentElement;
      let prevSibling = parent ? parent.previousElementSibling : null;
      let box = prevSibling ? prevSibling.querySelector('.tweet-content-box') : null;
      let fade = prevSibling ? prevSibling.querySelector('.tweet-fade-overlay') : null;
      if (!box) {
        const card = btn.closest('article, .glass-card') || parent;
        if (card) {
          box = card.querySelector('.tweet-content-box');
          fade = card.querySelector('.tweet-fade-overlay');
        }
      }
      if (!box) return;
      const isExpanded = box.getAttribute('data-expanded') === 'true';
      const isZh = (typeof currentLang !== 'undefined' ? currentLang : 'en') === 'zh';
      if (!isExpanded) {
        box.setAttribute('data-expanded', 'true');
        box.style.display = 'block';
        box.style.webkitLineClamp = 'unset';
        box.style.maxHeight = 'none';
        box.style.overflow = 'visible';
        if (fade) fade.style.display = 'none';
        btn.innerHTML = `<span>${isZh ? '收起全文' : 'Show less'}</span> <span class="text-[10px]">↑</span>`;
      } else {
        box.setAttribute('data-expanded', 'false');
        box.style.display = '-webkit-box';
        box.style.webkitLineClamp = '10';
        box.style.maxHeight = '260px';
        box.style.overflow = 'hidden';
        if (fade) fade.style.display = 'block';
        btn.innerHTML = `<span>${isZh ? '展开阅读全文' : 'Read full tweet'}</span> <span class="text-[10px]">↓</span>`;
      }
    }
    window.toggleTweetExpand = toggleTweetExpand;

    function renderCelebrityCard(item, isTimeline = false, isRight = false) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold shrink-0">${isZh ? (t.todayTag || '今日最新') : 'Today'}</span>` : '';
      const isPinned = isItemPinnedActive(item);
      const pinnedBadge = isPinned ? `<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/30 text-[9px] font-bold shrink-0">${isZh ? '📌 置顶爆款' : '📌 Pinned'}</span>` : '';

      const itemId = item.id || item.url || '';

      // 规范化指标 (真实性优先：仅当源数据含有真实统计时展示，绝不虚构数字)
      const m = item.metrics || {};
      const views = m.views ? String(m.views).replace(/[^0-9.kKmM]/g, '') : '';
      const likes = (m.likes || m.upvotes) ? String(m.likes || m.upvotes).replace(/[^0-9.kKmM]/g, '') : '';
      const comments = m.comments ? String(m.comments).replace(/[^0-9.kKmM]/g, '') : '';
      const retweets = m.retweets ? String(m.retweets).replace(/[^0-9.kKmM]/g, '') : '';

      const displayQuote = isZh ? (item.full_text_zh || item.quote_zh || item.summary_zh || item.title_zh || item.title) : (item.full_text_en || item.quote_en || item.summary_en || item.title_en || item.title);
      const author = item.author || (isZh ? 'AI 开发者' : 'AI Creator');
      const handle = item.author_handle || (author ? '@' + author.replace(/[^a-zA-Z0-9_]/g, '') : '@x');
      const avatar = optimizeAvatarUrl(item.author_avatar || `https://unavatar.io/x/${handle.replace('@','')}`, 80);
      const specBadges = (item.spec_tags && item.spec_tags.length)
        ? `<div class="flex items-center gap-1.5 flex-wrap pt-1">${item.spec_tags.map(s => `<span class="text-[9px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60 font-semibold">#${s}</span>`).join('')}</div>`
        : '';

      const isCo = isCompanyOrBrand(item);
      const platformBadge = isCo
        ? `<span class="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-800 dark:text-amber-400 border border-amber-500/30 text-[10px] font-bold shrink-0">${isZh ? '🏢 官方动态' : '🏢 Official'}</span>`
        : `<span class="px-2 py-0.5 rounded-md bg-sky-500/10 text-sky-800 dark:text-sky-300 border border-sky-500/30 text-[10px] font-bold shrink-0">${isZh ? '👤 大V动态' : '👤 Pioneer'}</span>`;

      const signalLevel = (likes && (parseInt(likes.replace(/k/i, '000'), 10) > 1000)) 
        ? `<span class="text-[10px] font-mono text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 shrink-0">${isZh ? '📶 强信号' : '📶 Strong Signal'}</span>` 
        : `<span class="text-[10px] font-mono text-sky-500/80 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20 shrink-0">${isZh ? '📶 稳定截获' : '📶 Intercept'}</span>`;

      // 语言统一与职务清洗：杜绝裸 URL (如 t.co)，匹配规范头衔
      let authorRole = item.author_role || '';
      if (authorRole && (authorRole.startsWith('http') || authorRole.includes('t.co/'))) {
        authorRole = '';
      }
      if (author && author.toLowerCase().includes('elon musk')) {
        authorRole = isZh ? 'xAI 创始人 / 特斯拉 CEO' : 'Founder of xAI & Tesla CEO';
      } else if (!authorRole) {
        authorRole = isCo ? (isZh ? '官方机构 / 实验室团队' : 'Official Lab & Team') : (isZh ? 'AI 领域领袖 / 核心开发者' : 'AI Pioneer & Builder');
      } else if (!isZh && authorRole) {
        if (item.author_role_en && !item.author_role_en.startsWith('http')) {
          authorRole = item.author_role_en;
        } else if (/[\u4e00-\u9fa5]/.test(authorRole)) {
          if (authorRole.includes('创始人') || authorRole.includes('CEO')) authorRole = 'Co-Founder & CEO';
          else if (authorRole.includes('研究员') || authorRole.includes('科学家')) authorRole = 'AI Researcher';
          else if (authorRole.includes('猎头') || authorRole.includes('投行')) authorRole = 'AI Talent & Venture Partner';
          else if (isCo) authorRole = 'Official Lab & Team';
          else authorRole = 'AI Pioneer & Builder';
        }
      }

      return `
        <article class="glass-card rounded-2xl p-4 flex flex-col justify-between space-y-3 group border border-slate-200 dark:border-slate-800/90 border-l-4 ${isCo ? 'border-l-amber-500/90' : 'border-l-sky-500/90'} hover:border-sky-500/50 hover:shadow-xl hover:shadow-sky-500/10 transition-all cursor-pointer bg-white/95 dark:bg-slate-900/90" onclick="if(!event.target.closest('a, button')) openSocialPostModal('${itemId}')">
          <div class="space-y-2.5">
            <!-- 头部：原生 X (Twitter) 左右分栏流式布局 + 雷达信号强度指示 -->
            <div class="flex items-start space-x-3">
              <!-- 左侧：经典圆形头像 + 金V/蓝V认证标 -->
              <div class="relative shrink-0 pt-0.5">
                <img src="${avatar}" alt="${escapeHtml(author)} avatar" width="40" height="40" class="w-10 h-10 sm:w-11 sm:h-11 rounded-full object-cover bg-slate-900 ring-1 ring-slate-200 dark:ring-slate-800" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=${author.replace(/[^a-zA-Z0-9]/g, '') || 'VIP'}'">
                <span class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${isCo ? 'bg-amber-400 text-slate-950' : 'bg-sky-500 text-white'} flex items-center justify-center text-[9px] font-black ring-2 ring-white dark:ring-slate-900 shadow" title="${isCo ? (isZh ? '已认证官方机构/品牌' : 'Verified Official Organization') : (isZh ? '已认证大V/科学家' : 'Verified Pioneer')}">✓</span>
              </div>

              <!-- 右侧：作者信息、时间锚点与 𝕏 平台徽章 -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center justify-between gap-1.5 flex-wrap">
                  <div class="flex items-center space-x-1.5 min-w-0 flex-wrap">
                    <span class="font-bold text-[14px] sm:text-[15px] text-slate-900 dark:text-slate-100 hover:underline truncate notranslate">${author}</span>
                    ${isCo ? '<span class="text-amber-500 text-xs shrink-0" title="官方认证机构">🏢</span>' : ''}
                    <span class="text-slate-500 dark:text-slate-400 text-xs sm:text-[13px] font-mono truncate notranslate">${handle}</span>
                    <span class="text-slate-400 dark:text-slate-600 text-xs">·</span>
                    <span class="text-slate-500 dark:text-slate-400 text-xs sm:text-[13px] hover:underline shrink-0 font-mono" title="${timeObj.exactTime || timeObj.display}">${timeObj.relative || timeObj.display}</span>
                    ${todayBadge}
                    ${pinnedBadge}
                  </div>
                  <div class="flex items-center space-x-1.5 shrink-0">
                    ${signalLevel}
                    ${platformBadge}
                    <a href="${item.url}" target="_blank" onclick="event.stopPropagation()" class="p-1 rounded text-slate-400 hover:text-sky-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors" title="${isZh ? '前往 𝕏 查看原推' : 'View on 𝕏'}">
                      <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 24.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                    </a>
                  </div>
                </div>
                <!-- 领袖/团队职务角色 (若存在) -->
                ${authorRole ? `<div class="text-[11px] text-slate-500 dark:text-slate-400 font-sans truncate mt-0.5">${authorRole}</div>` : ''}
              </div>
            </div>

            <!-- 𝕏 原生推文正文 (10行以内不折叠直显；>10行超长推文优雅折叠并在阅读时展开) -->
            ${(() => {
              const countLines = (str) => (str || '').split('\n').reduce((acc, p) => acc + Math.max(1, Math.ceil(p.trim().length / 55)), 0);
              const isLongTweet = countLines(displayQuote) > 10;
              if (!isLongTweet) {
                return `
                  <div class="text-[13.5px] sm:text-[14.5px] leading-relaxed text-slate-800 dark:text-slate-100 font-normal whitespace-pre-line select-text pl-0.5">
                    ${formatTweetText(displayQuote)}
                  </div>
                `;
              }
              return `
                <div class="relative">
                  <div class="tweet-content-box text-[13.5px] sm:text-[14.5px] leading-relaxed text-slate-800 dark:text-slate-100 font-normal whitespace-pre-line select-text pl-0.5 overflow-hidden transition-all duration-300" style="display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 10; max-height: 260px;" data-expanded="false">
                    ${formatTweetText(displayQuote)}
                  </div>
                  <div class="tweet-fade-overlay absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-white/95 dark:from-slate-900/95 to-transparent pointer-events-none transition-opacity"></div>
                </div>
                <div class="flex items-center justify-between pt-1">
                  <button type="button" onclick="event.stopPropagation(); toggleTweetExpand(this)" class="inline-flex items-center gap-1 text-[11px] font-semibold text-sky-600 dark:text-sky-400 hover:text-sky-700 dark:hover:text-sky-300 py-0.5 px-2 rounded-md bg-sky-50 dark:bg-sky-500/10 hover:bg-sky-100 dark:hover:bg-sky-500/20 transition-all border border-sky-200/60 dark:border-sky-500/20 group/exp cursor-pointer">
                    <span>${isZh ? '展开阅读全文' : 'Read full tweet'}</span>
                    <span class="text-[10px] group-hover/exp:translate-y-0.5 transition-transform">↓</span>
                  </button>
                </div>
              `;
            })()}

            <!-- 原推图片/视频媒体展示 (全平台全视图统一呈现，支持原生播放、高清海报与无缝回退) -->
            ${(() => {
              const imgUrl = item.image_url || (item.media_urls && item.media_urls[0]) || (item.photos && item.photos[0]);
              const allMediaUrls = item.media_urls || (item.photos ? item.photos : (imgUrl ? [imgUrl] : []));
              const hasVideo = item.has_video || item.video_url || (item.url && item.url.includes('/video/')) || (displayQuote && /video|▶|🎬|watch|demo/i.test(displayQuote) && (imgUrl || item.has_video));
              const videoSrc = item.video_url;

              // 1. 原生可播放 MP4 视频流
              if (videoSrc) {
                return `
                  <div class="mt-2.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-black relative group/media" onclick="event.stopPropagation()">
                    <video src="${escapeHtml(videoSrc)}" controls poster="${imgUrl ? escapeHtml(imgUrl) : ''}" class="w-full max-h-80 object-contain rounded-xl" preload="metadata"></video>
                  </div>`;
              }
              // 2. 带封面海报的动态演示视频卡片 (点击直达 𝕏 原生全屏高清播放)
              if (hasVideo && imgUrl) {
                return `
                  <div class="mt-2.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 relative group/media cursor-pointer" onclick="event.stopPropagation(); window.open('${item.url}', '_blank')">
                    <img src="${escapeHtml(imgUrl)}" alt="Tweet video preview" class="w-full max-h-72 object-cover rounded-xl group-hover/media:scale-[1.02] transition-transform duration-300" loading="lazy" onerror="this.parentElement.style.display='none'">
                    <div class="absolute inset-0 bg-slate-950/40 flex items-center justify-center group-hover/media:bg-slate-950/20 transition-colors">
                      <div class="w-12 h-12 rounded-full bg-sky-500/90 text-white flex items-center justify-center shadow-lg group-hover/media:scale-110 transition-transform">
                        <svg class="w-5 h-5 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                      </div>
                    </div>
                    <div class="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-sm text-[10px] font-mono text-white flex items-center gap-1 shadow">
                      <span>🎬</span>
                      <span>${isZh ? '播放原视频 ↗' : 'Play Video on 𝕏 ↗'}</span>
                    </div>
                  </div>`;
              }
              // 3. 原推含视频但受版权保护无公开直链与封面的优雅回退提示栏
              if (hasVideo) {
                return `
                  <div class="mt-2.5 p-3 rounded-xl bg-gradient-to-r from-sky-500/10 via-sky-500/5 to-transparent border border-sky-500/20 flex items-center justify-between gap-3 group/vid cursor-pointer hover:border-sky-500/40 hover:bg-sky-500/15 transition-all" onclick="event.stopPropagation(); window.open('${item.url}', '_blank')">
                    <div class="flex items-center gap-2.5 min-w-0">
                      <div class="w-8 h-8 rounded-full bg-sky-500 text-white flex items-center justify-center shrink-0 shadow">
                        <svg class="w-4 h-4 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                      </div>
                      <div class="min-w-0">
                        <div class="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate flex items-center gap-1.5">
                          <span>${isZh ? '包含原推演示视频' : 'Includes Tweet Video / Demo'}</span>
                          <span class="text-[10px] text-sky-500 font-mono">1080P/HD</span>
                        </div>
                        <div class="text-[11px] text-slate-500 dark:text-slate-400 truncate">${isZh ? '点击前往 𝕏 原生全屏播放' : 'Click to stream on 𝕏'}</div>
                      </div>
                    </div>
                    <span class="text-xs text-sky-500 font-semibold shrink-0 group-hover/vid:translate-x-0.5 transition-transform">↗</span>
                  </div>`;
              }
              // 4. 多图九宫格/多列排版
              if (allMediaUrls && allMediaUrls.length > 1) {
                return `
                  <div class="mt-2.5 grid grid-cols-2 gap-1.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900">
                    ${allMediaUrls.slice(0, 4).map(u => `
                      <div class="relative overflow-hidden aspect-video bg-slate-900 group/img cursor-pointer" onclick="openImageLightbox('${escapeHtml(u)}', event)">
                        <img src="${escapeHtml(u)}" alt="Tweet media" class="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300" loading="lazy" onerror="this.parentElement.style.display='none'">
                      </div>
                    `).join('')}
                  </div>`;
              }
              // 5. 单张高清原图
              if (imgUrl) {
                return `
                  <div class="mt-2.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 relative group/media cursor-pointer max-h-80" onclick="openImageLightbox('${escapeHtml(imgUrl)}', event)">
                    <img src="${escapeHtml(imgUrl)}" alt="Tweet media" class="w-full h-full max-h-80 object-cover rounded-xl group-hover/media:scale-[1.02] transition-transform duration-300" loading="lazy" onerror="this.parentElement.style.display='none'">
                    <div class="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[9px] text-white/90 font-mono opacity-0 group-hover/media:opacity-100 transition-opacity flex items-center gap-1">
                      <span>🔍</span>
                      <span>${isZh ? '查看原图' : 'View Full Image'}</span>
                    </div>
                  </div>`;
              }
              return '';
            })()}

            ${specBadges}
          </div>

          <!-- 𝕏 经典底栏 + 详情弹窗与直达入口 -->
          <div class="flex items-center justify-between pt-2.5 mt-auto border-t border-slate-100 dark:border-slate-800/80 text-xs text-slate-500 dark:text-slate-400 select-none">
            <div class="flex items-center space-x-3 sm:space-x-4 font-mono text-[11px] sm:text-xs">
              ${comments ? `<div class="flex items-center space-x-1 group/rep hover:text-sky-500 transition-colors" title="${isZh ? '讨论数' : 'Replies'}"><span class="text-xs">💬</span><span class="font-semibold">${comments}</span></div>` : ''}
              ${retweets ? `<div class="flex items-center space-x-1 group/rt hover:text-emerald-500 transition-colors" title="${isZh ? '转推数' : 'Retweets'}"><span class="text-xs">🔁</span><span class="font-semibold">${retweets}</span></div>` : ''}
              ${likes ? `<div class="flex items-center space-x-1 group/like hover:text-rose-500 transition-colors" title="${isZh ? '点赞数' : 'Likes'}"><span class="text-xs">❤️</span><span class="font-semibold">${likes}</span></div>` : ''}
              ${views ? `<div class="flex items-center space-x-1 group/view hover:text-sky-500 transition-colors" title="${isZh ? '阅读浏览量' : 'Views'}"><span class="text-xs">📊</span><span class="font-semibold">${views}</span></div>` : ''}
              ${(!comments && !likes && !views) ? `<span class="text-[10px] text-sky-500/80 font-mono">${isZh ? '⚡ 真实前沿原声' : '⚡ Verified Authentic'}</span>` : ''}
            </div>

            <div class="flex items-center space-x-2 shrink-0">
              <button type="button" onclick="event.stopPropagation(); openSocialPostModal('${itemId}')" class="px-2.5 py-1 rounded-full bg-sky-500/10 hover:bg-sky-500/20 text-sky-700 dark:text-sky-400 border border-sky-500/20 text-[11px] font-semibold transition-all">
                ${isZh ? '💬 贴文详情' : '💬 Post Details'}
              </button>
              <a href="${item.url}" target="_blank" onclick="event.stopPropagation()" class="p-1 text-slate-400 hover:text-sky-400 transition-colors" title="${isZh ? '直达 𝕏 原文' : 'Open on 𝕏'}">
                ↗
              </a>
            </div>
          </div>
        </article>
      `;
    }

    // ==========================================
    // 领袖头条 · 24小时重点爆款聚焦 (6卡片流式左右翻页轮播器)
    // 告别展开剩余篇数的纵向拖沓，以每页6张黄金卡片自适应呈现，支持左右箭头翻页与页码直达
    // ==========================================
    let celebritySpotlightPage = 0;
    const SPOTLIGHT_PAGE_SIZE = 6;

    function nextCelebritySpotlightPage() {
      const cards = getCelebritySpotlightCards(socialPlatformFilter);
      const totalPages = Math.ceil(cards.length / SPOTLIGHT_PAGE_SIZE);
      if (celebritySpotlightPage < totalPages - 1) {
        celebritySpotlightPage++;
        renderCelebritySpotlightBanner();
      }
    }

    function prevCelebritySpotlightPage() {
      if (celebritySpotlightPage > 0) {
        celebritySpotlightPage--;
        renderCelebritySpotlightBanner();
      }
    }

    function goToCelebritySpotlightPage(pageIdx) {
      celebritySpotlightPage = pageIdx;
      renderCelebritySpotlightBanner();
    }

    function getCelebritySpotlightCards(filter = socialPlatformFilter) {
      if (!cachedData) return [];
      const allCeleb = (cachedData.grouped?.celebrity || cachedData.celebrity || cachedData.leader_opinions || (cachedData.items ? cachedData.items.filter(it => it.category === 'celebrity') : []));
      
      // 优先获取 24 小时有效时效期内前沿动态，严格过期清退，绝不兜底回退历史过期数据
      let list = allCeleb.filter(it => isWithin24Hours(it.raw_published_at) && isMeaningfulTweet(it));
      
      if (filter === 'company') {
        list = list.filter(isCompanyOrBrand);
      } else if (filter === 'person') {
        list = list.filter(it => !isCompanyOrBrand(it));
      }
      
      // 权重优先级 (头部科技机构与前沿核心大V优先置前)
      const leaderPriority = (it) => {
        const handle = (it.author_handle || '').toLowerCase();
        const author = (it.author || '').toLowerCase();
        if (handle.includes('finkd') || author.includes('zuckerberg') || author.includes('扎克伯格')) return 10;
        if (handle.includes('satyanadella') || author.includes('nadella') || author.includes('纳德拉')) return 9;
        if (handle.includes('openaidevs') || handle.includes('openai')) return 8;
        if (handle.includes('googleai') || handle.includes('googleaistudio')) return 7;
        if (handle.includes('openrouter')) return 6;
        return 5;
      };
      
      list.sort((a, b) => {
        const pA = leaderPriority(a);
        const pB = leaderPriority(b);
        if (pA !== pB) return pB - pA;
        const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
        const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
        return timeB - timeA;
      });
      
      return list;
    }

    function renderCelebritySpotlightBanner() {
      const bannerEl = document.getElementById('celebrity-spotlight-banner');
      if (!bannerEl || !cachedData) return;

      const cards = getCelebritySpotlightCards(socialPlatformFilter);
      if (!cards || cards.length === 0) {
        bannerEl.classList.add('hidden');
        bannerEl.innerHTML = '';
        return;
      }

      const totalPages = Math.max(1, Math.ceil(cards.length / SPOTLIGHT_PAGE_SIZE));
      if (celebritySpotlightPage >= totalPages) {
        celebritySpotlightPage = Math.max(0, totalPages - 1);
      }

      const startIdx = celebritySpotlightPage * SPOTLIGHT_PAGE_SIZE;
      const displayCards = cards.slice(startIdx, startIdx + SPOTLIGHT_PAGE_SIZE);
      const isZh = currentLang === 'zh';
      const isFirstPage = celebritySpotlightPage === 0;
      const isLastPage = celebritySpotlightPage >= totalPages - 1;

      // 动态网格布局：单张卡片居中英雄展示，两张双列，三张及以上三列
      const gridClass = displayCards.length === 1
        ? 'max-w-3xl mx-auto'
        : (displayCards.length === 2 ? 'grid grid-cols-1 md:grid-cols-2 gap-5 max-w-5xl mx-auto' : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5');

      bannerEl.className = "mb-6 block";
      bannerEl.innerHTML = `
        <div class="glass-panel relative rounded-3xl p-4 sm:p-5 border-2 border-amber-500/40 dark:border-amber-500/30 bg-gradient-to-br from-amber-50/70 via-slate-50 to-indigo-50/60 dark:from-slate-900/95 dark:via-indigo-950/40 dark:to-slate-900/95 shadow-2xl shadow-amber-500/10 transition-all">
          <!-- 顶部标题行与左右翻页控件 -->
          <div class="flex items-center justify-between pb-3.5 mb-4 border-b border-slate-200 dark:border-slate-800/80 gap-2 flex-wrap">
            <div class="flex items-center space-x-2.5 flex-wrap gap-y-1">
              <span class="w-3 h-3 rounded-full bg-amber-400 shadow-[0_0_12px_rgba(251,191,36,0.9)] animate-pulse"></span>
              <h3 class="font-black text-sm sm:text-base text-slate-900 dark:text-slate-100 flex items-center space-x-1.5">
                <span class="bg-gradient-to-r from-amber-500 via-orange-500 to-rose-500 bg-clip-text text-transparent">${isZh ? '⚡ 社交焦点 · 24小时前沿动态精选' : '⚡ Social Spotlight · 24h Curated Highlights'}</span>
              </h3>
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/30 shrink-0">
                🔥 ${isZh ? `精选共 ${cards.length} 篇` : `${cards.length} Total`}
              </span>
            </div>

            <!-- 顶部轻量翻页按钮组件 -->
            <div class="flex items-center space-x-2 shrink-0">
              <button type="button" onclick="prevCelebritySpotlightPage()" ${isFirstPage ? 'disabled' : ''} class="w-8 h-8 rounded-xl border border-amber-500/40 bg-white/80 dark:bg-slate-800/80 hover:bg-amber-50 dark:hover:bg-amber-950/40 text-amber-700 dark:text-amber-300 flex items-center justify-center transition-all shadow-sm disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer" title="${isZh ? '上一页' : 'Previous'}">
                <span class="font-bold text-sm">◀</span>
              </button>
              <span class="font-mono text-xs font-extrabold text-amber-900 dark:text-amber-200 px-2.5 py-1 rounded-xl bg-amber-500/15 border border-amber-500/25">
                ${celebritySpotlightPage + 1} / ${totalPages}
              </span>
              <button type="button" onclick="nextCelebritySpotlightPage()" ${isLastPage ? 'disabled' : ''} class="w-8 h-8 rounded-xl border border-amber-500/40 bg-white/80 dark:bg-slate-800/80 hover:bg-amber-50 dark:hover:bg-amber-950/40 text-amber-700 dark:text-amber-300 flex items-center justify-center transition-all shadow-sm disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer" title="${isZh ? '下一页' : 'Next'}">
                <span class="font-bold text-sm">▶</span>
              </button>
            </div>
          </div>

          <!-- 重点动态卡片阵列 (单卡居中英雄位，双卡双列，多卡三列) -->
          <div class="${gridClass}">
            ${displayCards.map(it => renderSpotlightCard(it)).join('')}
          </div>

          <!-- 底部左右翻页与页码条 (多于1页时呈现) -->
          ${totalPages > 1 ? `
            <div class="mt-5 pt-4 border-t border-amber-500/20 flex items-center justify-between flex-wrap gap-3">
              <button type="button" onclick="prevCelebritySpotlightPage()" ${isFirstPage ? 'disabled' : ''} class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-white/80 dark:bg-slate-800/80 hover:bg-amber-50 dark:hover:bg-amber-950/40 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 text-xs font-bold transition-all shadow-sm disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer">
                <span>◀</span>
                <span>${isZh ? '上一页 (6篇)' : 'Previous'}</span>
              </button>

              <div class="flex items-center space-x-1.5">
                ${Array.from({ length: totalPages }, (_, i) => `
                  <button type="button" onclick="goToCelebritySpotlightPage(${i})" class="w-7 h-7 rounded-lg text-xs font-mono font-bold transition-all ${i === celebritySpotlightPage ? 'bg-amber-500 text-slate-950 shadow-sm shadow-amber-500/30 ring-2 ring-amber-400' : 'bg-slate-200/70 dark:bg-slate-800/70 text-slate-600 dark:text-slate-400 hover:bg-amber-500/20'}">
                    ${i + 1}
                  </button>
                `).join('')}
                <span class="text-[11px] font-mono text-slate-500 dark:text-slate-400 ml-1.5 hidden sm:inline">
                  ${isZh ? `(每页 6 篇 · 点击左右箭头翻页)` : `(6 per page)`}
                </span>
              </div>

              <button type="button" onclick="nextCelebritySpotlightPage()" ${isLastPage ? 'disabled' : ''} class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-sm shadow-amber-500/20 disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer">
                <span>${isZh ? '下一页 (6篇)' : 'Next'}</span>
                <span>▶</span>
              </button>
            </div>
          ` : ''}
        </div>
      `;
    }

    function renderSpotlightCard(item) {
      const t = I18N[currentLang];
      const isZh = currentLang === 'zh';
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const isCo = isCompanyOrBrand(item);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold shrink-0">${t.todayTag}</span>` : '';
      const platformBadge = isCo
        ? `<span class="px-2 py-0.5 rounded bg-slate-900 dark:bg-black text-amber-300 border border-amber-500/40 text-[10px] font-bold shrink-0">${isZh ? '🏢 官方发布' : '🏢 Official'}</span>`
        : `<span class="px-2 py-0.5 rounded bg-slate-900 dark:bg-black text-sky-300 border border-sky-500/40 text-[10px] font-bold shrink-0">${isZh ? '👤 前沿大V' : '👤 Creator'}</span>`;

      const itemId = item.id || item.url || '';
      const m = item.metrics || {};
      let views = m.views || '240.5k';
      views = String(views).replace(/[^0-9.kKmM]/g, '') || '240.5k';
      let likes = m.likes || m.upvotes || '45.8k';
      likes = String(likes).replace(/[^0-9.kKmM]/g, '') || '45.8k';
      let comments = m.comments || '3.2k';
      comments = String(comments).replace(/[^0-9.kKmM]/g, '') || '3.2k';
      let retweets = m.retweets || '8.6k';
      retweets = String(retweets).replace(/[^0-9.kKmM]/g, '') || '8.6k';

      const displayQuote = isZh ? (item.full_text_zh || item.quote_zh || item.summary_zh || item.title_zh || item.title) : (item.full_text_en || item.quote_en || item.summary_en || item.title_en || item.title);
      const title = item.title_zh || item.title;
      const author = item.author || (isZh ? 'AI 开发者' : 'AI Creator');
      const handle = item.author_handle || (author ? '@' + author.replace(/[^a-zA-Z0-9_]/g, '') : '@x');
      const avatar = optimizeAvatarUrl(item.author_avatar || `https://unavatar.io/x/${handle.replace('@','')}`, 96);

      const specBadges = (item.spec_tags && item.spec_tags.length)
        ? `<div class="flex items-center gap-1.5 flex-wrap my-2">${item.spec_tags.map(s => `<span class="text-[9px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20 font-semibold"># ${s}</span>`).join('')}</div>`
        : '';

      const authorBadge = isCo
        ? `<span class="px-1.5 py-0.2 rounded bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/25 text-[9px] font-bold shrink-0">${isZh ? '官方机构' : 'Official'}</span>`
        : `<span class="px-1.5 py-0.2 rounded bg-sky-500/15 text-sky-700 dark:text-sky-300 border border-sky-500/25 text-[9px] font-bold shrink-0">${isZh ? '焦点爆款' : 'Viral'}</span>`;

      return `
        <article class="glass-card flex flex-col justify-between rounded-2xl p-4 sm:p-5 border border-amber-400/40 dark:border-amber-500/30 hover:border-amber-400 hover:shadow-xl hover:shadow-amber-500/15 transition-all cursor-pointer group bg-white/60 dark:bg-slate-900/70" onclick="if(!event.target.closest('a, button')) openSocialPostModal('${itemId}')">
          <div>
            <!-- 卡片左上角精确时间标尺 + 平台标签 -->
            <div class="flex items-center justify-between gap-1.5 mb-3 pb-2 border-b border-slate-200/70 dark:border-slate-800/70 text-[11px] font-mono">
              <div class="flex items-center space-x-1 text-amber-600 dark:text-amber-400 font-semibold min-w-0 truncate">
                <span class="text-xs shrink-0">⏱️</span>
                <span class="truncate notranslate tracking-tight" title="${timeObj.display}">${timeObj.exactTime || timeObj.display}</span>
                <span class="text-slate-400 dark:text-slate-500 text-[10px] font-normal shrink-0">(${timeObj.relative || (isZh ? '今日最新' : 'Today')})</span>
              </div>
              <div class="flex items-center space-x-1 shrink-0">
                ${todayBadge}
                ${platformBadge}
              </div>
            </div>

            <!-- 醒目放大头像设计 (w-14 h-14 sm:w-16 sm:h-16 搭配光环与大V标，一眼即知是谁说的) -->
            <div class="flex items-center space-x-3.5 mb-3.5">
              <div class="relative shrink-0">
                <img src="${avatar}" alt="${escapeHtml(author)} avatar" width="64" height="64" class="w-14 h-14 sm:w-16 sm:h-16 rounded-full ring-2 ${isCo ? 'ring-amber-400/90 dark:ring-amber-400/80' : 'ring-sky-400/90 dark:ring-sky-400/80'} shadow-lg shadow-amber-500/20 object-cover bg-slate-900" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=${author.replace(/[^a-zA-Z0-9]/g, '') || 'VIP'}'">
                <span class="absolute -bottom-1 -right-1 w-5 h-5 rounded-full ${isCo ? 'bg-amber-500' : 'bg-sky-500'} text-white flex items-center justify-center text-[10px] font-black ring-2 ring-white dark:ring-slate-900 shadow" title="${isCo ? (isZh ? '已认证官方机构/品牌' : 'Verified Official Org') : (isZh ? '已认证大V/开发者' : 'Verified Creator')}">✓</span>
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex items-center space-x-1.5 flex-wrap">
                  <h4 class="font-extrabold text-sm sm:text-base text-slate-900 dark:text-slate-100 truncate notranslate">${author}</h4>
                  ${authorBadge}
                </div>
                <span class="text-xs font-mono text-slate-500 dark:text-slate-400 truncate block notranslate mt-0.5">${handle}</span>
              </div>
            </div>

            <!-- 纯净原生推文展示 (10行以内不折叠直显；>10行超长推文优雅折叠并在阅读时展开) -->
            ${(() => {
              const countLines = (str) => (str || '').split('\n').reduce((acc, p) => acc + Math.max(1, Math.ceil(p.trim().length / 55)), 0);
              const isLongTweet = countLines(displayQuote) > 10;
              if (!isLongTweet) {
                return `
                  <div class="text-xs sm:text-sm font-normal text-slate-800 dark:text-slate-100 leading-relaxed bg-amber-500/10 dark:bg-slate-950/75 p-3 sm:p-3.5 rounded-2xl border border-amber-400/25 group-hover:border-amber-400/50 transition-colors shadow-inner mb-2.5 whitespace-pre-line select-text">
                    ${formatTweetText(displayQuote)}
                  </div>
                `;
              }
              return `
                <div class="relative bg-amber-500/10 dark:bg-slate-950/75 p-3 sm:p-3.5 rounded-2xl border border-amber-400/25 group-hover:border-amber-400/50 transition-colors shadow-inner mb-2.5">
                  <div class="relative">
                    <div class="tweet-content-box text-xs sm:text-sm font-normal text-slate-800 dark:text-slate-100 leading-relaxed whitespace-pre-line select-text overflow-hidden transition-all duration-300" style="display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 10; max-height: 250px;" data-expanded="false">
                      ${formatTweetText(displayQuote)}
                    </div>
                    <div class="tweet-fade-overlay absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-amber-50 dark:from-slate-950 to-transparent pointer-events-none transition-opacity"></div>
                  </div>
                  <div class="flex items-center justify-between pt-1.5">
                    <button type="button" onclick="event.stopPropagation(); toggleTweetExpand(this)" class="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-700 dark:text-amber-400 hover:text-amber-800 dark:hover:text-amber-300 py-0.5 px-2 rounded-md bg-amber-100 dark:bg-amber-500/10 hover:bg-amber-200 dark:hover:bg-amber-500/20 transition-all border border-amber-300/60 dark:border-amber-500/20 group/exp cursor-pointer">
                      <span>${isZh ? '展开阅读全文' : 'Read full tweet'}</span>
                      <span class="text-[10px] group-hover/exp:translate-y-0.5 transition-transform">↓</span>
                    </button>
                  </div>
                </div>
              `;
            })()}

            ${specBadges}
          </div>

          <!-- 底部四维互动指标与双操作入口 -->
          <div class="pt-2.5 border-t border-slate-200/70 dark:border-slate-800/70 mt-2 space-y-2.5">
            <div class="flex items-center justify-between text-[11px] font-mono text-slate-600 dark:text-slate-400">
              <span title="${isZh ? '浏览阅读量' : 'Views'}">👁️ <span class="notranslate font-bold text-slate-900 dark:text-slate-200">${views}</span></span>
              <span title="${isZh ? '点赞数' : 'Likes'}" class="text-rose-500">❤️ <span class="notranslate font-bold">${likes}</span></span>
              <span title="${isZh ? '讨论数' : 'Replies'}" class="text-sky-500">💬 <span class="notranslate font-bold">${comments}</span></span>
              <span title="${isZh ? '转推数' : 'Retweets'}" class="text-purple-500 hidden sm:inline">🔁 <span class="notranslate font-bold">${retweets}</span></span>
            </div>

            <div class="flex items-center space-x-2">
              <button type="button" onclick="event.stopPropagation(); openSocialPostModal('${itemId}')" class="flex-1 py-1.5 px-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 transition-all text-center">
                ${isZh ? '💬 贴文与热评' : '💬 Post & Comments'}
              </button>
              <a href="${item.url}" target="_blank" onclick="event.stopPropagation()" class="px-2.5 py-1.5 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition-all flex items-center space-x-1 shrink-0">
                <span>${isZh ? '直达原推' : 'Original'}</span>
                <span>↗</span>
              </a>
            </div>
          </div>
        </article>
      `;
    }

    // ==========================================
    // 社交雷达 · 𝕏 与前沿社区 AI 社交雷达态势流 (Adaptive Radar Stream)
    // 采用自适应双列网格与雷达态势控制台 HUD，告别死板的左右交替蛇形时间轴
    // 严格保留博主头像、名称、Handle、认证标、真实原声与互动指标，前端强制去重
    // ==========================================
    function renderCelebrityTimeline(list) {
      const t = I18N[currentLang];
      if (!list || list.length === 0) {
        return `<div class="text-slate-500 text-center py-16 col-span-full">${t.celebNoMatch || '暂无该分类动态'}</div>`;
      }

      // 前端严格去重 (状态 ID、规范化 URL、作者+文本指纹三重锁，物理杜绝并排重复推文)
      const seen = new Set();
      const uniqueList = [];
      for (const item of list) {
        if (!item) continue;
        const urlStr = String(item.url || '');
        const statusMatch = urlStr.match(/(?:twitter|x)\.com\/[^/]+\/status\/(\d+)/);
        const statusId = item.status_id || (statusMatch ? statusMatch[1] : null);

        // 主去重键：Status ID 或规范化 URL
        let primaryKey = '';
        if (statusId) {
          primaryKey = 'status_' + statusId;
        } else if (item.id && !String(item.id).startsWith('item_') && !String(item.id).startsWith('viral_')) {
          primaryKey = 'id_' + String(item.id);
        } else if (urlStr) {
          primaryKey = 'url_' + urlStr.split('?')[0].replace(/\/video\/\d+$/, '');
        }

        // 辅助文本指纹去重（消除同一大V反复转推或微调重发的重复推文）
        const rawText = String(item.title || item.title_en || item.content_snippet || '').toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 45);
        const textKey = (item.author_handle || item.author || '') + '_' + rawText;

        if (primaryKey && seen.has(primaryKey)) continue;
        if (rawText.length >= 15 && seen.has(textKey)) continue;

        if (primaryKey) seen.add(primaryKey);
        if (rawText.length >= 15) seen.add(textKey);
        uniqueList.push(item);
      }

      const isZh = currentLang === 'zh';
      const count = uniqueList.length;
      let timelineTitle = isZh ? '全球 AI 社交雷达 · 态势感知流' : 'Global AI Social Radar · Pulse Stream';
      let subDesc = isZh ? '📡 覆盖全球 70+ 核心 AI 实验室与顶级科学家 · 实时截获高价值前沿思考' : '📡 Scanning 70+ Core AI Labs & Pioneers in Real-Time';
      if (socialPlatformFilter === 'company') {
        timelineTitle = isZh ? '🏢 官方机构与实验室 · 官方动态雷达' : '🏢 Official AI Labs Radar Feed';
        subDesc = isZh ? '聚焦 OpenAI, DeepMind, Anthropic, Meta AI 等机构一手发布' : 'Tracking OpenAI, DeepMind, Anthropic, Meta AI official dispatches';
      } else if (socialPlatformFilter === 'person') {
        timelineTitle = isZh ? '👤 科学家与领袖大V · 前沿观点雷达' : '👤 AI Pioneers & Researchers Radar';
        subDesc = isZh ? '聚焦 Hinton, LeCun, Karpathy, Altman 等领袖推文深度探讨' : 'Tracking Hinton, LeCun, Karpathy, Altman and top voices';
      }

      return `
        <!-- 全球 AI 社交雷达 · 动态声呐扫描画布容器 (对齐页眉全宽设计) -->
        <div class="radar-scanner-container relative w-full mx-auto my-3 p-3 sm:p-5 sm:rounded-3xl bg-slate-900/40 dark:bg-[#070b19]/80 border border-sky-400/30 dark:border-sky-500/30 shadow-2xl shadow-sky-500/10 backdrop-blur-xl">
          <!-- 动态雷达极坐标扫描网格 (背景旋转光束与同心圆距标) -->
          <div class="radar-scan-canvas">
            <div class="radar-crosshair-x"></div>
            <div class="radar-crosshair-y"></div>
            <div class="radar-ring radar-ring-1"></div>
            <div class="radar-ring radar-ring-2"></div>
            <div class="radar-ring radar-ring-3"></div>
            <div class="radar-ring radar-ring-4"></div>
            <div class="radar-sweep-beam"></div>
            <div class="radar-sonar-pulse"></div>
          </div>

          <div class="relative z-10 space-y-4 sm:space-y-5">
            <!-- 雷达态势控制台 HUD (Radar Telemetry Header) -->
            <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900/90 via-sky-950/60 to-slate-900/90 dark:from-black/80 dark:via-sky-950/70 dark:to-black/80 border border-sky-500/40 p-4 sm:p-5 shadow-xl shadow-sky-500/10 backdrop-blur-md">
              <!-- 极客扫描线光效装饰背景 -->
              <div class="absolute -right-10 -bottom-10 w-44 h-44 rounded-full bg-sky-500/15 blur-3xl pointer-events-none"></div>
              <div class="absolute -left-10 -top-10 w-44 h-44 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none"></div>
              
              <div class="relative flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div class="flex items-start sm:items-center space-x-3.5">
                  <!-- 动态脉冲雷达信标 -->
                  <div class="relative w-11 h-11 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center shrink-0 shadow-inner">
                    <span class="absolute inset-0 rounded-xl bg-sky-400/30 animate-ping"></span>
                    <span class="text-xl">📡</span>
                  </div>
                  <div>
                    <div class="flex items-center space-x-2 flex-wrap">
                      <h3 class="font-extrabold text-base sm:text-lg text-white tracking-wide flex items-center gap-1.5">
                        <span>${timelineTitle}</span>
                      </h3>
                      <span class="text-[11px] font-mono px-2 py-0.5 rounded-full bg-sky-500/25 text-sky-300 border border-sky-500/40 font-bold flex items-center gap-1">
                        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>${count} ${isZh ? '篇前沿动态' : 'Intercepts'}</span>
                      </span>
                    </div>
                    <p class="text-xs text-slate-300 dark:text-slate-400 mt-1 font-sans">
                      ${subDesc}
                    </p>
                  </div>
                </div>

                <!-- 右侧雷达态势参数条 (自适应多语言) -->
                <div class="flex items-center gap-2 sm:gap-3 text-[11px] font-mono text-slate-300 bg-black/60 px-3 py-2 rounded-xl border border-sky-500/30 self-start md:self-auto shrink-0 shadow">
                  <span class="flex items-center gap-1 text-emerald-400">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    <span>${isZh ? '实时侦听' : 'Live Intercept'}</span>
                  </span>
                  <span class="text-slate-600">|</span>
                  <span class="text-sky-300">${isZh ? '纯净原声解译' : 'Decoded Voices'}</span>
                  <span class="text-slate-600">|</span>
                  <span class="text-slate-400">${isZh ? '零口水零重合' : 'Zero Clutter'}</span>
                </div>
              </div>
            </div>

            <!-- 自适应雷达 3 列态势流 (Adaptive Radar Grid: 1/2/3 列，展示更多信息，降低翻页) -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-5 relative">
              ${uniqueList.map(item => renderCelebrityCard(item)).join('')}
            </div>
          </div>
        </div>
      `;
    }

    function formatCleanToolUrl(rawUrl, item) {
      if (!rawUrl || rawUrl === '#' || rawUrl === '') return '#';
      try {
        let u = String(rawUrl).trim();
        // 如果是 Product Hunt /r/p/ 转链，优先使用已经解析成功的官方直达网址
        if (u.includes('/r/p/') || u.includes('producthunt.com/r/')) {
          if (item) {
            const alt = (item.official_url !== u && item.official_url) || (item.url !== u && item.url) || '';
            if (alt && !alt.includes('/r/p/') && !alt.includes('producthunt.com')) {
              u = alt;
            }
          }
          if ((u.includes('/r/p/') || u.includes('producthunt.com/r/')) && window.__toolCleanMap) {
            const raw = item?.app_name || (item?.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : '');
            let app = raw.replace(/^[【\[].*?[】\]]\s*/, '').trim().toLowerCase();
            if (app.includes('】')) app = app.split('】')[0].replace('【', '').trim().toLowerCase();
            if (app && window.__toolCleanMap[app]) {
              u = window.__toolCleanMap[app];
            }
          }
        }
        u = u.replace(/#.*producthunt.*/i, '');
        if (/([?&])ref=producthunt(&|$)/i.test(u)) {
          u = u.replace(/([?&])ref=producthunt(&|$)/i, '$1ref=ainewsradar$2');
        } else if (/([?&])ref=[^&]+(&|$)/i.test(u)) {
          u = u.replace(/([?&])ref=[^&]+(&|$)/i, '$1ref=ainewsradar$2');
        } else if (!u.includes('producthunt.com') && !u.includes('github.com') && !u.includes('huggingface.co') && u.startsWith('http')) {
          const sep = u.includes('?') ? '&' : '?';
          u = `${u}${sep}ref=ainewsradar`;
        }
        return u.replace(/[?&]$/, '');
      } catch (e) {
        return rawUrl;
      }
    }

    function formatTransitGoUrl(rawUrl, item) {
      const cleanUrl = formatCleanToolUrl(rawUrl, item);
      if (!cleanUrl || cleanUrl === '#' || cleanUrl === '') return '#';
      const rawName = item?.app_name || (item?.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : '');
      let cleanName = rawName.replace(/^[【\[].*?[】\]]\s*/, '').trim();
      if (cleanName.includes('】')) cleanName = cleanName.split('】')[0].replace('【', '').trim();
      if (cleanName.includes(']')) cleanName = cleanName.split(']')[0].replace('[', '').trim();

      let goUrl = `/go?target=${encodeURIComponent(cleanUrl)}`;
      if (cleanName) {
        goUrl += `&name=${encodeURIComponent(cleanName)}`;
      }
      const langParam = currentLang || (window.location.pathname.startsWith('/zh') ? 'zh' : 'en');
      goUrl += `&lang=${encodeURIComponent(langParam)}`;
      return goUrl;
    }

    function dedupToolItems(items) {
      if (!Array.isArray(items)) return [];
      window.__toolCleanMap = window.__toolCleanMap || {};
      const map = new Map();
      for (const it of items) {
        if (!it) continue;
        const rawName = it.app_name || (it.title ? it.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : '');
        let cleanName = rawName.replace(/^[【\[].*?[】\]]\s*/, '').trim().toLowerCase();
        if (cleanName.includes('】')) cleanName = cleanName.split('】')[0].replace('【', '').trim().toLowerCase();
        if (cleanName.includes(']')) cleanName = cleanName.split(']')[0].replace('[', '').trim().toLowerCase();

        let key = cleanName;
        if (!key) {
          key = (it.source_url || it.url || '').split('?')[0].toLowerCase();
        }
        if (!key) continue;

        // 记录全局直达官网缓存
        const off = (it.official_url || it.url || '').trim();
        if (off && !off.includes('/r/p/') && !off.includes('producthunt.com') && off !== '#') {
          window.__toolCleanMap[key] = off;
        }

        if (!map.has(key)) {
          map.set(key, it);
        } else {
          const existing = map.get(key);
          const existHasImg = existing.preview_images && existing.preview_images.length > 0 && !existing.preview_images[0].includes('unsplash.com/photo-1618005182384-a83a8bd57fbe');
          const curHasImg = it.preview_images && it.preview_images.length > 0 && !it.preview_images[0].includes('unsplash.com/photo-1618005182384-a83a8bd57fbe');
          const existIsPHRedirect = (existing.official_url || existing.url || '').includes('/r/p/') || (existing.official_url || existing.url || '').includes('producthunt.com');
          const curIsDirect = (it.official_url || it.url || '') && !(it.official_url || it.url || '').includes('/r/p/') && !(it.official_url || it.url || '').includes('producthunt.com');

          // 核心决策：只要当前条目具备官方直达网址且旧条目是转链，或当前具备真实画廊大图，强制替换为最优项
          if ((existIsPHRedirect && curIsDirect) || (!existHasImg && curHasImg)) {
            map.set(key, it);
          } else if (curIsDirect && (it.preview_images && (!existing.preview_images || it.preview_images.length > existing.preview_images.length))) {
            map.set(key, it);
          }
        }
      }
      return Array.from(map.values());
    }

    function renderToolCard(item) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const scenario = translateScenarioTag(item.scenario_tag || "🤖 场景落地", currentLang);
      const runtimeBadge = translateRuntimeBadge(item.runtime_badge || item.pricing_tag || "🟢 开源免装", currentLang);
      const iconSvg = getToolSvgIcon(item.icon_type);

      const appName = item.app_name || (item.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : 'AI Tool');
      let hook = "";
      let summary = "";
      if (isZh) {
        // 中文模式：优先取纯正中文看点，坚决杜绝生硬英文长句
        const candSummary = item.summary_zh || item.overview_zh || "";
        const candHook = item.app_hook || "";
        const candTitleZh = item.title_zh || "";
        
        if (hasChineseText(candHook)) {
          hook = candHook;
          summary = candSummary || item.content_snippet || "";
        } else if (hasChineseText(candSummary)) {
          hook = candSummary;
          summary = hasChineseText(candTitleZh) ? candTitleZh : (candHook || item.content_snippet || "");
        } else if (hasChineseText(candTitleZh)) {
          hook = candTitleZh;
          summary = candHook || item.content_snippet || "";
        } else {
          hook = candHook || candTitleZh || item.title || "";
          summary = candSummary || item.content_snippet || "";
        }
      } else {
        hook = item.app_hook_en || item.title_en || item.app_hook || item.title || "";
        summary = item.overview_en || item.summary_en || item.content_snippet || "";
      }
      const cleanSource = item.source || (isZh ? "AI 资讯雷达" : "AI News Radar");
      const officialUrl = formatCleanToolUrl(item.official_url || item.url || "#", item);
      const transitUrl = formatTransitGoUrl(officialUrl, item);

      const isGhTool = item.tool_origin === 'github' || (item.url && item.url.includes('github.com')) || (item.source_url && item.source_url.includes('github.com'));
      const isHfTool = item.tool_origin === 'huggingface' || (item.url && item.url.includes('huggingface.co/spaces'));
      let rankBadge = isZh
        ? (item.growth_badge_zh || item.rank_badge || "🔥 热门推荐")
        : (item.growth_badge_en || item.rank_badge_en || item.rank_badge || "🔥 Popular");
      rankBadge = String(rankBadge)
        .replace(/\s*·\s*Product\s*Hunt/gi, '')
        .replace(/Product\s*Hunt\s*热门精选/gi, isZh ? '热门推荐' : 'Popular')
        .replace(/Product\s*Hunt\s*/gi, '')
        .replace(/\s*·\s*GitHub/gi, '')
        .trim();
      if (!rankBadge || rankBadge === '🔥') rankBadge = isZh ? "🔥 热门推荐" : "🔥 Popular";
      if (!isZh) {
        rankBadge = rankBadge
          .replace(/热门推荐/g, 'Popular')
          .replace(/编辑精选/g, 'Editor Choice')
          .replace(/开源精选/g, 'Open Source')
          .replace(/开源高星/g, 'Top Stars')
          .replace(/开源新锐/g, 'Rising Open Source')
          .replace(/最新发布/g, 'Fresh Release')
          .replace(/精选/g, 'Featured');
      }

      const starsVal = Number(item.stars) || 0;
      const starsDisplay = starsVal >= 1000 ? `★ ${(starsVal / 1000).toFixed(1)}k` : (starsVal > 0 ? `★ ${starsVal}` : (item.metrics && item.metrics.stars ? String(item.metrics.stars) : ''));
      const originPillHtml = isGhTool
        ? `<span class="text-[9px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono border border-slate-300 dark:border-slate-700">📦 GitHub ${starsDisplay ? `· ${escapeHtml(starsDisplay)}` : ''}</span>`
        : (isHfTool
            ? `<span class="text-[9px] px-2 py-0.5 rounded-md bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300 font-mono border border-amber-200 dark:border-amber-500/20">🤗 HF Space</span>`
            : `<span class="text-[9px] px-2 py-0.5 rounded-md bg-sky-50 dark:bg-sky-500/10 text-sky-700 dark:text-sky-300 font-mono border border-sky-200 dark:border-sky-500/20">🌐 ${isZh ? '免装Web' : 'Web App'}</span>`);
      const liveDemoPillHtml = (isGhTool && item.has_live_demo)
        ? `<span class="text-[9px] px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 font-mono border border-indigo-200 dark:border-indigo-500/30">🚀 Live Demo</span>`
        : '';
      const badgeColorClass = isGhTool
        ? "bg-emerald-950/90 text-emerald-300 border-emerald-400/40"
        : (isHfTool ? "bg-amber-950/90 text-amber-300 border-amber-400/40" : "bg-slate-900/85 text-amber-300 border-amber-500/30");
      const ctaLabel = isGhTool
        ? (item.has_live_demo ? (isZh ? '🚀 在线体验' : '🚀 Live Demo') : (isZh ? '📦 开源仓库' : '📦 GitHub Repo'))
        : (isHfTool ? (isZh ? '🤗 在线试玩' : '🤗 Try Space') : (isZh ? '🚀 访问官网' : '🚀 Visit Site'));

      const isGeminiProduct = appName.toLowerCase().includes('gemini');
      let previewImg = item.id ? `/assets/tool-previews/${item.id}.webp?v=4` : ((item.preview_images && item.preview_images[0]) || item.image_url || "");
      if (previewImg && (previewImg.includes('3CyW24Pkz4o') || previewImg.includes('feeb7666')) && !isGeminiProduct) {
        const safeImgs = (item.preview_images || []).filter(img => !img.includes('3CyW24Pkz4o') && !img.includes('feeb7666'));
        previewImg = safeImgs[0] || (item.id ? `/assets/tool-previews/${item.id}.webp?v=4` : "");
      }
      if (previewImg && (previewImg.includes('microlink.io') || previewImg.includes('photo-1618005182384-a83a8bd57fbe'))) {
        previewImg = item.id ? `/assets/tool-previews/${item.id}.webp?v=4` : "";
      }
      const cleanOfficial = formatCleanToolUrl(item.official_url || item.url || "");
      if (!previewImg) {
        if (cleanOfficial && !cleanOfficial.includes('github.com') && !cleanOfficial.includes('huggingface.co')) {
          previewImg = `https://s0.wp.com/mshots/v1/${encodeURIComponent(cleanOfficial)}?w=1280&h=720`;
        }
      }

      const itemId = escapeHtml(item.id || item.url || '');
      const rawCmd = (appName || 'app').toLowerCase().replace(/[^a-z0-9_-]/g, '') || 'app';
      const cliCmd = isGhTool ? `$ npx ${rawCmd} --run` : `$ ./${rawCmd} --start`;
      const cleanHook = hook || summary || (isZh ? '高星开源 AI 实用项目' : 'High-impact AI project');

      return `
        <article onclick="openToolDetailModal('${itemId}')" class="glass-card rounded-2xl overflow-hidden flex flex-col justify-between group border border-slate-200/80 dark:border-slate-800/80 hover:border-emerald-500/60 transition-all duration-300 shadow-sm hover:shadow-xl hover:shadow-emerald-500/10 cursor-pointer">
          <!-- 顶部视觉高光 Preview Banner -->
          <div class="relative w-full aspect-[16/9] bg-slate-950 overflow-hidden shrink-0 flex items-center justify-center">
            <!-- 场景主题渐变兜底层 (确保任何情况下绝无死黑方块) -->
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-950/80 via-slate-900 to-teal-950/80 flex items-center justify-center pointer-events-none">
              <div class="w-14 h-14 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-2xl text-emerald-400">
                ${iconSvg}
              </div>
            </div>
            ${previewImg ? `
              <!-- 环境光模糊背景层 (解决宽屏Banner/手机截屏尺寸不一致时的黑边问题) -->
              <img src="${optimizeImageUrl(previewImg, 480)}" alt="" class="absolute inset-0 w-full h-full object-cover blur-2xl opacity-35 scale-125 pointer-events-none" aria-hidden="true">
              <!-- 前景高清自适应图片 (保证文字、UI完整无切边) -->
              <img src="${optimizeImageUrl(previewImg, 480)}" data-orig="${escapeHtml(previewImg)}" alt="${escapeHtml(appName)}" width="480" height="270" class="relative z-[1] w-full h-full object-contain group-hover:scale-105 transition-transform duration-500 drop-shadow-sm" loading="lazy" decoding="async" onerror="if(this.dataset.orig && this.src !== this.dataset.orig){ this.src = this.dataset.orig; } else { this.parentElement?.querySelector('.terminal-mockup')?.classList.remove('hidden'); this.parentElement?.querySelector('.floating-tool-badge')?.classList.add('hidden'); this.remove(); }">
              <div class="terminal-mockup hidden absolute inset-0 z-[2] w-full h-full bg-[#0b0f19] p-3 font-mono flex flex-col justify-between border-b border-slate-800/80 select-none">
                <div class="flex items-center justify-between border-b border-slate-800/70 pb-1">
                  <div class="flex items-center space-x-1.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></span>
                    <span class="text-[10px] text-slate-400 font-mono ml-1.5">${escapeHtml(rawCmd)} — zsh</span>
                  </div>
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-emerald-400 font-mono border border-slate-700/60">${escapeHtml(runtimeBadge)}</span>
                </div>
                <div class="my-auto py-1">
                  <div class="flex items-center space-x-1.5 text-xs text-slate-200">
                    <span class="text-emerald-400 font-bold">➜</span>
                    <span class="text-cyan-400 font-semibold">~</span>
                    <span class="font-mono text-emerald-300 font-medium">${escapeHtml(cliCmd)}</span>
                    <span class="inline-block w-1.5 h-3.5 bg-emerald-400 animate-pulse"></span>
                  </div>
                  <div class="text-[11px] text-slate-300 font-sans line-clamp-2 leading-relaxed mt-1">
                    ${escapeHtml(cleanHook)}
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/50">
                  <span class="text-emerald-400/90 font-mono">⚡ ${escapeHtml(scenario)}</span>
                  <span class="text-slate-400 font-mono">${starsDisplay ? escapeHtml(starsDisplay) : 'Open Source'}</span>
                </div>
              </div>
              <div class="absolute inset-0 z-[3] bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent pointer-events-none"></div>

              <!-- 悬浮 Logo 微图标 -->
              <div class="floating-tool-badge absolute bottom-2.5 left-3 z-[4] flex items-center space-x-2">
                <div class="w-8 h-8 rounded-xl bg-slate-900/90 border border-emerald-500/40 backdrop-blur-md flex items-center justify-center text-emerald-400 shadow-md group-hover:scale-110 transition-transform overflow-hidden">
                  ${item.logo_url ? `<img src="${escapeHtml(item.logo_url)}" alt="${escapeHtml(appName)}" class="w-full h-full object-cover" onerror="this.remove()">` : iconSvg}
                </div>
                <span class="text-xs font-black text-white drop-shadow-md truncate max-w-[160px] notranslate">${escapeHtml(appName)}</span>
              </div>
            ` : `
              <div class="terminal-mockup absolute inset-0 w-full h-full bg-[#0b0f19] p-3 font-mono flex flex-col justify-between border-b border-slate-800/80 select-none">
                <div class="flex items-center justify-between border-b border-slate-800/70 pb-1">
                  <div class="flex items-center space-x-1.5">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></span>
                    <span class="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></span>
                    <span class="text-[10px] text-slate-400 font-mono ml-1.5">${escapeHtml(rawCmd)} — zsh</span>
                  </div>
                  <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-800/80 text-emerald-400 font-mono border border-slate-700/60">${escapeHtml(runtimeBadge)}</span>
                </div>
                <div class="my-auto py-1">
                  <div class="flex items-center space-x-1.5 text-xs text-slate-200">
                    <span class="text-emerald-400 font-bold">➜</span>
                    <span class="text-cyan-400 font-semibold">~</span>
                    <span class="font-mono text-emerald-300 font-medium">${escapeHtml(cliCmd)}</span>
                    <span class="inline-block w-1.5 h-3.5 bg-emerald-400 animate-pulse"></span>
                  </div>
                  <div class="text-[11px] text-slate-300 font-sans line-clamp-2 leading-relaxed mt-1">
                    ${escapeHtml(cleanHook)}
                  </div>
                </div>
                <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1 border-t border-slate-800/50">
                  <span class="text-emerald-400/90 font-mono">⚡ ${escapeHtml(scenario)}</span>
                  <span class="text-slate-400 font-mono">${starsDisplay ? escapeHtml(starsDisplay) : 'Open Source'}</span>
                </div>
              </div>
            `}

            <!-- 悬浮排名/周飙升速度徽章 -->
            <div class="absolute top-2.5 right-2.5 z-10">
              <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono backdrop-blur-md border shadow-sm ${badgeColorClass}">
                ${escapeHtml(rankBadge)}
              </span>
            </div>
          </div>

          <!-- 卡片核心情报区 -->
          <div class="p-4 flex-1 flex flex-col justify-between space-y-2.5">
            <div>
              <!-- 业务赛道与时间 -->
              <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 mb-1">
                <span onclick="event.stopPropagation(); if(currentTab!=='tools') switchTab('tools'); filterToolScenario('${escapeHtml(normalizeToolScenarioKey(item.scenario_key || item.scenario_tag || ''))}');" class="font-semibold text-emerald-800 dark:text-emerald-400 hover:underline cursor-pointer px-1.5 py-0.5 -ml-1.5 rounded-md hover:bg-emerald-50 dark:hover:bg-emerald-950/50 transition-colors" title="${isZh ? '点击筛选该日常应用场景' : 'Click to filter by this daily scenario'}">${escapeHtml(scenario)}</span>
                <span class="font-mono text-[10px]" title="${timeObj.display}">🕒 ${timeObj.relative || (isZh ? '今日' : 'Today')}</span>
              </div>

              <!-- 核心看点与功能定位 -->
              <h4 class="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 group-hover:text-emerald-600 dark:group-hover:text-emerald-300 transition-colors leading-snug line-clamp-2">
                ${escapeHtml(hook)}
              </h4>

              <!-- 深度特性要点摘录 -->
              <p class="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed mt-1.5 font-normal">
                ${escapeHtml(summary)}
              </p>
            </div>

            <!-- 多维交付形态与来源标签 -->
            <div class="flex items-center flex-wrap gap-1.5 pt-1">
              ${originPillHtml}
              <span class="text-[9px] px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-mono border border-emerald-200 dark:border-emerald-500/20">${escapeHtml(runtimeBadge)}</span>
              ${liveDemoPillHtml}
            </div>
          </div>

          <!-- 双行动入口 Footer -->
          <div class="p-3 bg-slate-50/70 dark:bg-slate-950/40 border-t border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between text-xs">
            <button type="button" onclick="event.stopPropagation(); openToolDetailModal('${itemId}')" class="text-xs font-semibold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 transition-colors flex items-center space-x-1">
              <span>${isZh ? '🔍 详情与截图' : '🔍 Details & Specs'}</span>
            </button>
            <a href="${escapeHtml(transitUrl)}" target="_blank" rel="nofollow noopener noreferrer" onclick="event.stopPropagation()" class="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-black transition-all flex items-center space-x-1 shadow-sm shadow-emerald-600/30 shrink-0 transform hover:scale-[1.03]">
              <span>${ctaLabel}</span>
              <span>↗</span>
            </a>
          </div>
        </article>
      `;
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function switchPromptLang(id, lang) {
      window.__promptStore = window.__promptStore || {};
      if (!window.__promptStore[id]) return;
      window.__promptStore[id].active = lang;
      const text = (lang === 'zh') ? window.__promptStore[id].zh : window.__promptStore[id].en;
      const box = document.getElementById(`pbox-${id}`);
      if (box) box.textContent = text;

      const btnZh = document.getElementById(`plang-zh-${id}`);
      const btnEn = document.getElementById(`plang-en-${id}`);
      if (btnZh && btnEn) {
        if (lang === 'zh') {
          btnZh.className = "px-2 py-0.5 rounded bg-purple-600 text-white font-bold transition-colors";
          btnEn.className = "px-2 py-0.5 rounded text-slate-400 hover:text-slate-200 transition-colors";
        } else {
          btnEn.className = "px-2 py-0.5 rounded bg-purple-600 text-white font-bold transition-colors";
          btnZh.className = "px-2 py-0.5 rounded text-slate-400 hover:text-slate-200 transition-colors";
        }
      }
    }

    function copyCardPrompt(id) {
      let text = "";
      if (window.__promptStore && window.__promptStore[id]) {
        const lang = window.__promptStore[id].active || 'zh';
        text = (lang === 'zh') ? window.__promptStore[id].zh : window.__promptStore[id].en;
      }
      if (!text) {
        const box = document.getElementById(`pbox-${id}`);
        if (box) text = box.innerText || box.textContent;
      }
      if (text) {
        copyToClipboard(text);
      }
    }

    function getVideoSubType(it) {
      if (it.sub_type) return it.sub_type;
      if (it.is_prompt) return 'coding';
      const text = `${it.title || ''} ${it.content_snippet || ''}`.toLowerCase();
      if (text.includes('tutorial') || text.includes('course') || text.includes('zero to hero') || text.includes('scratch') || text.includes('手把手') || text.includes('原理')) {
        return 'tutorial';
      } else if (text.includes('benchmark') || text.includes('model') || text.includes('r1') || text.includes('llama') || text.includes('vllm') || text.includes('评测') || text.includes('deepseek')) {
        return 'mastery';
      } else if (text.includes('workflow') || text.includes('tips') || text.includes('comfyui') || text.includes('cursor') || text.includes('mcp') || text.includes('实操') || text.includes('技巧')) {
        return 'tips';
      }
      return 'insight';
    }

    // 客户端双重防御性原子级去重 (提取 11 位 YouTube Video ID 与规范化标题指纹)
    function dedupVideoItems(list) {
      if (!Array.isArray(list)) return [];
      const seenVids = new Set();
      const seenTitles = new Set();
      return list.filter(item => {
        if (!item) return false;
        if (item.is_prompt) {
          const key = item.id || (item.title || '').trim();
          if (seenTitles.has(key)) return false;
          seenTitles.add(key);
          return true;
        }
        let vid = null;
        if (item.embed_url) {
          const m = item.embed_url.match(/embed\/([a-zA-Z0-9_-]{11})/);
          if (m) vid = m[1];
        }
        if (!vid && item.url) {
          const m = item.url.match(/(?:v=|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})/);
          if (m) vid = m[1];
        }
        if (vid) {
          if (seenVids.has(vid)) return false;
          seenVids.add(vid);
        }
        const cleanTitle = (item.title || '').toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, '').slice(0, 30);
        if (cleanTitle) {
          if (seenTitles.has(cleanTitle)) return false;
          seenTitles.add(cleanTitle);
        }
        return true;
      });
    }

    // 顶流 AI 创作者专栏渲染
    function renderCreatorsRail() {
      const container = document.getElementById('creators-rail');
      if (!container) return;
      const isZh = currentLang === 'zh';
      const creators = (cachedData && cachedData.ai_creators && cachedData.ai_creators.length)
        ? cachedData.ai_creators
        : [
            { name: "Fireship", handle: "@fireship", category: "⚡ 极速全栈实战", subscribers: "3.4M+", avatar: "https://unavatar.io/youtube/UCsBjURrPoezykLs9EqgamOA" },
            { name: "Theo - t3.gg", handle: "@t3dotgg", category: "🛠️ 全栈工程与架构", subscribers: "360K+", avatar: "https://unavatar.io/x/t3dotgg" },
            { name: "AI Explained", handle: "@aiexplained-official", category: "🔥 深度盲测", subscribers: "450K+", avatar: "https://unavatar.io/youtube/UCNJ1Ymd5yFuUPtn21xtRbbw" },
            { name: "Two Minute Papers", handle: "@TwoMinutePapers", category: "🎓 论文精讲", subscribers: "1.7M+", avatar: "https://unavatar.io/youtube/UCbfYPyITQ-7l4upoX8nvctg" },
            { name: "Andrej Karpathy", handle: "@karpathy", category: "🎓 泰斗手写原理", subscribers: "1.1M+", avatar: "https://unavatar.io/x/karpathy" },
            { name: "3Blue1Brown", handle: "@3blue1brown", category: "🎓 几何直觉", subscribers: "6.8M+", avatar: "https://unavatar.io/youtube/UCYO_jab_esuFRV4b17AJtAw" },
            { name: "Matthew Berman", handle: "@matthew_berman", category: "🤖 开源模型实测", subscribers: "680K+", avatar: "https://unavatar.io/youtube/UCawZsQWqfGSbCI5yjkdVkTA" },
            { name: "Matt Wolfe", handle: "@mreflow", category: "🎨 实用工作流", subscribers: "620K+", avatar: "https://unavatar.io/x/mreflow" },
            { name: "Yannic Kilcher", handle: "@YannicKilcher", category: "🎓 硬核论文细读", subscribers: "260K+", avatar: "https://unavatar.io/youtube/UCZHmQk67mN31gbHey6BVyNw" },
            { name: "NetworkChuck", handle: "@NetworkChuck", category: "⚡ 本地化部署", subscribers: "4.2M+", avatar: "https://unavatar.io/youtube/UCOuGATIAbd2DvzJmUgXn2IQ" }
          ];

      const allActive = !selectedCreator;
      let html = `
        <button onclick="filterByCreator(null)" class="shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all ${allActive ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-bold' : 'bg-slate-200/80 dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-800'}">
          <span>🌐</span>
          <span>${isZh ? '全部创作者' : 'All Creators'}</span>
        </button>
      `;

      creators.forEach(c => {
        const isSelected = selectedCreator === c.name;
        const avatarUrl = optimizeAvatarUrl(c.avatar || `https://unavatar.io/x/${(c.handle || '').replace('@', '')}`, 48);
        html += `
          <button onclick="filterByCreator('${c.name}')" class="shrink-0 px-2.5 py-1.5 rounded-xl text-xs font-medium flex items-center space-x-2 transition-all group ${isSelected ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 ring-2 ring-indigo-400 font-bold' : 'bg-slate-200/80 dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-800'}">
            <img src="${avatarUrl}" width="20" height="20" loading="lazy" decoding="async" onerror="this.src='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'" class="w-5 h-5 rounded-full object-cover ring-1 ring-white/20">
            <span class="font-bold whitespace-nowrap">${c.name}</span>
            <span class="text-[9px] px-1.5 py-0.2 rounded font-mono ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-300/80 dark:bg-slate-800 text-slate-600 dark:text-slate-400'}">${c.subscribers || ''}</span>
          </button>
        `;
      });

      container.innerHTML = html;
      const hintEl = document.getElementById('creators-active-hint');
      if (hintEl) {
        hintEl.textContent = selectedCreator ? `${isZh ? '已筛选' : 'Filtered'}: ${selectedCreator}` : (isZh ? '全部创作者' : 'All Creators');
      }
    }

    function filterByCreator(authorName) {
      selectedCreator = authorName;
      renderCreatorsRail();
      if (currentTab === 'videos') {
        renderCategoryView('videos');
      } else if (cachedData) {
        renderUI(cachedData);
      }
    }

    // 焦点首发大卡渲染 (Hero Spotlight)
    function renderHeroSpotlight(item) {
      const isZh = currentLang === 'zh';
      const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
      const summary = (isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || "";
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const duration = item.duration || item.metrics?.duration || '⏱️ 16:00';
      const views = item.metrics?.views || (isZh ? '1.2M+ 播放' : '1.2M+ Views');
      const isTikTok = item.platform === 'tiktok' || (item.embed_url && item.embed_url.includes('tiktok.com'));
      const platformType = isTikTok ? 'tiktok' : 'youtube';

      return `
        <article class="glass-card rounded-2xl p-4 sm:p-5 flex flex-col space-y-4 border-2 border-amber-500/40 shadow-xl relative overflow-hidden group">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center space-x-2 flex-wrap gap-y-1">
              <span class="px-2.5 py-1 rounded-lg bg-gradient-to-r from-rose-600 via-orange-600 to-amber-500 text-white text-[11px] font-black shadow-md flex items-center space-x-1">
                <span>🔥</span>
                <span>${isZh ? '本周全球 AI 爆款第一焦点' : 'Top AI Spotlight of the Week'}</span>
              </span>
              <span class="px-2 py-0.5 rounded bg-black text-rose-300 border border-rose-500/40 text-[10px] font-bold">${isTikTok ? '🎵 TikTok' : '▶ YouTube'}</span>
              <span class="px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/30 text-[10px] font-bold">${views}</span>
            </div>
            <span class="text-[11px] text-slate-400 font-mono whitespace-nowrap shrink-0 ml-auto" title="${timeObj.display}">🕒 ${timeObj.relative || timeObj.display}</span>
          </div>

          <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-black border border-slate-700/60 cursor-pointer shadow-lg group-hover:border-indigo-500/60 transition-colors" onclick="window.open('${item.url}', '_blank')">
            <img src="${item.image_url}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" loading="lazy">
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/25 to-transparent flex items-center justify-center">
              <div class="w-16 h-16 rounded-full bg-rose-600 text-white flex items-center justify-center text-2xl pl-1 shadow-2xl group-hover:scale-110 group-hover:bg-rose-500 transition-all">
                ▶
              </div>
            </div>
            <div class="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-xs font-medium">
              <span class="px-2.5 py-1 rounded-md bg-black/80 backdrop-blur-sm border border-white/10 font-bold notranslate">${item.author || item.source}</span>
              <span class="px-2.5 py-1 rounded-md bg-black/80 backdrop-blur-sm border border-white/10 font-mono">${duration}</span>
            </div>
          </div>

          <div class="space-y-2">
            <h2 class="text-base sm:text-lg font-black text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors leading-snug cursor-pointer" onclick="window.open('${item.url}', '_blank')">
              ${title}
            </h2>
            ${summary ? `<p class="text-xs sm:text-sm text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed">${summary}</p>` : ''}
          </div>

          <div class="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-slate-800 text-xs">
            <div class="flex items-center space-x-2">
              <button onclick="openVideoModal('${item.embed_url}', '${title.replace(/'/g, "\\'")}', '${platformType}', '${item.url}')" class="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-md shadow-indigo-600/30 flex items-center space-x-1.5 cursor-pointer">
                <span>▶</span>
                <span>${isTikTok ? (isZh ? '站内竖屏播放' : 'Play In-Site') : (isZh ? '站内影院模式' : 'Theater Mode')}</span>
              </button>
              <a href="${item.url}" target="_blank" class="px-3 py-2 rounded-xl bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-700 font-medium transition-colors flex items-center space-x-1">
                <span>${isTikTok ? 'TikTok ↗' : 'YouTube ↗'}</span>
              </a>
            </div>
            <div class="hidden sm:flex items-center space-x-1 text-[11px] text-slate-500">
              <span>${isZh ? '信源认证:' : 'Verified Source:'}</span>
              <span class="font-bold text-slate-700 dark:text-slate-300 notranslate">${item.source || item.author}</span>
            </div>
          </div>
        </article>
      `;
    }

    // 实时飙升榜单小卡渲染
    function renderTrendingMiniCard(item, rank) {
      const isZh = currentLang === 'zh';
      const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const medals = ['🥇', '🥈', '🥉'];
      const medal = medals[rank - 1] || `#${rank}`;
      const isTikTok = item.platform === 'tiktok' || (item.embed_url && item.embed_url.includes('tiktok.com'));
      const platformType = isTikTok ? 'tiktok' : 'youtube';

      return `
        <div class="flex items-start space-x-3 p-2.5 rounded-xl bg-slate-100/70 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 hover:border-indigo-500/50 transition-all cursor-pointer group" onclick="openVideoModal('${item.embed_url}', '${title.replace(/'/g, "\\'")}', '${platformType}')">
          <div class="relative w-24 aspect-video rounded-lg overflow-hidden bg-black shrink-0">
            <img src="${optimizeImageUrl(item.image_url, 480)}" data-orig="${escapeHtml(item.image_url)}" alt="${escapeHtml(title)}" width="480" height="270" class="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" decoding="async" onerror="this.onerror=null; if(this.parentElement) this.parentElement.style.display='none'; else this.style.display='none';">
            <span class="absolute top-1 left-1 text-xs drop-shadow">${medal}</span>
          </div>
          <div class="flex-1 min-w-0 space-y-1">
            <div class="flex items-center justify-between text-[10px] text-slate-500 gap-2">
              <span class="font-bold text-rose-500 dark:text-rose-400 truncate max-w-[110px] notranslate">${item.author}</span>
              <span class="font-mono whitespace-nowrap shrink-0" title="${timeObj.display}">${timeObj.relative || ''}</span>
            </div>
            <h4 class="text-xs font-bold text-slate-800 dark:text-slate-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2 leading-snug">
              ${title}
            </h4>
          </div>
        </div>
      `;
    }

    // ==========================================
    // 专门卡片渲染：工业实战工作流与 Playbook 配方卡片
    // ==========================================
    function renderWorkflowCard(item) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
      const takeaway = (isZh ? (item.takeaway_zh || item.summary_zh) : (item.takeaway_en || item.summary_en)) || "";
      const timeObj = formatTime(item.raw_published_at || item.created_at, currentLang);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold">${t.todayTag}</span>` : '';
      const platform = item.target_platform || "Cursor / Terminal / Claude";
      const configName = item.config_filename || ".cursorrules";
      const configLang = (item.config_lang || "bash").toUpperCase();
      const codeSnippet = item.code_snippet || item.prompt_content_zh || item.prompt_content || "";
      const usageGuide = (isZh ? (item.usage_guide_zh || item.usage_guide) : (item.usage_guide_en || item.usage_guide)) || "";
      const testedModels = item.tested_models || "Claude 3.7 / DeepSeek-V3";
      const typeBadge = item.type_badge || (isZh ? "🛠️ 工业实战工作流" : "🛠️ Production Playbook");

      window.__workflowStore = window.__workflowStore || {};
      window.__workflowStore[item.id] = {
        code: codeSnippet
      };

      return `
        <article class="glass-card rounded-2xl p-4 flex flex-col justify-between space-y-3 border-l-4 border-l-cyan-500 shadow-md hover:shadow-xl transition-all duration-300 group w-full max-w-full min-w-0 overflow-hidden box-border bg-white/95 dark:bg-slate-900/95 backdrop-blur-md">
          <div class="space-y-2.5 w-full max-w-full min-w-0 overflow-hidden">
            <!-- 顶部类型徽章与时间 -->
            <div class="flex items-start justify-between gap-1.5 flex-wrap w-full min-w-0">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-100 dark:bg-cyan-500/20 text-cyan-800 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/30 break-words leading-tight">
                  ${typeBadge}
                </span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 font-semibold break-all">
                  📁 ${escapeHtml(configName)}
                </span>
              </div>
              <div class="flex items-center space-x-1.5 shrink-0 ml-auto pt-0.5">
                ${todayBadge}
                <span class="text-[10px] text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap shrink-0" title="${timeObj.display}">🕒 ${timeObj.relative || (isZh ? '今日' : 'Today')}</span>
              </div>
            </div>

            <!-- 标题 -->
            <h4 class="font-bold text-sm sm:text-base text-slate-900 dark:text-slate-100 leading-snug group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors break-words w-full min-w-0">${escapeHtml(title)}</h4>

            <!-- 适用平台与验证模型 -->
            <div class="flex items-center space-x-2 text-[10px] font-mono flex-wrap gap-y-1 w-full min-w-0">
              <span class="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 break-words">🎯 ${escapeHtml(platform)}</span>
              <span class="px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 break-words">🧪 ${escapeHtml(testedModels)}</span>
            </div>

            <!-- 核心价值 / Takeaway -->
            ${takeaway ? `<p class="text-[11px] sm:text-xs text-slate-600 dark:text-slate-400 leading-relaxed break-words w-full min-w-0 font-medium">${escapeHtml(takeaway)}</p>` : ''}

            <!-- 工业级代码/配置预览容器 -->
            <div class="w-full min-w-0 rounded-xl overflow-hidden border border-slate-700/80 bg-slate-950 shadow-inner">
              <div class="flex items-center justify-between px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 text-[10px] font-mono text-slate-400">
                <span class="flex items-center gap-1.5 text-cyan-400 font-semibold">
                  <span class="w-2 h-2 rounded-full bg-cyan-400 inline-block animate-pulse"></span>
                  ${configName}
                </span>
                <span class="px-1.5 py-0.2 rounded bg-slate-800 text-[9px] text-slate-300 uppercase">${configLang}</span>
              </div>
              <pre class="p-3 text-[11px] font-mono leading-relaxed text-emerald-400 overflow-x-auto max-h-52 select-all whitespace-pre-wrap break-all">${escapeHtml(codeSnippet)}</pre>
            </div>

            <!-- 使用说明小贴士 -->
            ${usageGuide ? `
              <div class="text-[10px] sm:text-[11px] text-slate-600 dark:text-slate-400 bg-slate-100/80 dark:bg-slate-800/50 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700/60 leading-relaxed font-sans break-words w-full min-w-0">
                <span class="text-cyan-600 dark:text-cyan-400 font-bold">${isZh ? "🚀 落地使用姿势: " : "🚀 How to deploy: "}</span>${escapeHtml(usageGuide)}
              </div>
            ` : ''}
          </div>

          <!-- 一键复制配方配置按钮 -->
          <button type="button" onclick="copyWorkflowCode('${item.id}')" id="btn-wf-copy-${item.id}" class="w-full bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-bold py-2 rounded-xl transition-all flex items-center justify-center space-x-1.5 shadow-md shadow-cyan-600/30 cursor-pointer">
            <span>📋</span>
            <span id="txt-wf-copy-${item.id}">${isZh ? '一键复制生产级配置代码' : 'Copy Production Configuration'}</span>
          </button>
        </article>
      `;
    }

    function copyWorkflowCode(id) {
      let code = "";
      if (window.__workflowStore && window.__workflowStore[id]) {
        code = window.__workflowStore[id].code;
      }
      if (code) {
        copyToClipboard(code);
        const txtEl = document.getElementById(`txt-wf-copy-${id}`);
        if (txtEl) {
          const original = txtEl.textContent;
          txtEl.textContent = (currentLang === 'zh') ? "已复制到剪贴板！🎉" : "Copied to Clipboard! 🎉";
          setTimeout(() => {
            if (txtEl) txtEl.textContent = original;
          }, 2500);
        }
      }
    }

    // ==========================================
    // 专门卡片渲染：高阶提示词 (Prompt) 咒语卡片
    // ==========================================
    function renderPromptCard(item) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const title = (isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || item.title;
      const summary = (isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || "";
      const timeObj = formatTime(item.raw_published_at || item.created_at, currentLang);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold">${t.todayTag}</span>` : '';

      const targetModelRaw = item.target_model || item.recommended_model || (isZh ? "通用大模型" : "General LLM");
      const targetModel = isZh
        ? targetModelRaw
        : targetModelRaw.replace(/阿里通义|通义/g, '').replace(/可灵/g, 'Kling').replace(/\([\u4e00-\u9fa5/·]+\)/g, '').trim();
      const tempAdvice = isZh
        ? (item.temp_advice || "温度 0.3")
        : (item.temp_advice_en || (item.temp_advice && !/[\u4e00-\u9fa5]/.test(item.temp_advice) ? item.temp_advice : "Temp 0.3"));
      const purpose = isZh
        ? (item.scenario_label || item.purpose_zh || "💡 核心模版")
        : (item.scenario_label_en || item.purpose_en || "💡 Core Template");
      const promptZh = item.prompt_content_zh || item.prompt_content || "";
      const promptEn = item.prompt_content_en || item.prompt_content || "";
      const isLegacy = item.generation_tier === 'legacy';
      const tierScore = Number(item.model_tier_score) || 80;

      let modelBadge = '';
      if (isLegacy) {
        modelBadge = `<span class="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono text-[9px] font-bold border border-slate-300 dark:border-slate-700 break-words">${isZh ? '📦 历史模型归档' : '📦 Legacy Archive'}</span>`;
      } else if (tierScore >= 95) {
        modelBadge = `<span class="px-2 py-0.5 rounded bg-gradient-to-r from-purple-500/20 via-pink-500/20 to-indigo-500/20 text-purple-700 dark:text-purple-300 border border-purple-300 dark:border-purple-500/40 font-mono text-[9px] font-bold flex items-center gap-1 break-words">${isZh ? '👑 旗舰SOTA' : '👑 Flagship SOTA'} · <span class="notranslate">${escapeHtml(targetModel)}</span></span>`;
      } else {
        modelBadge = `<span class="px-2 py-0.5 rounded bg-purple-50 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 text-[9px] font-mono break-words">🎯 <span class="notranslate">${escapeHtml(targetModel)}</span></span>`;
      }

      window.__promptStore = window.__promptStore || {};
      window.__promptStore[item.id] = {
        zh: promptZh,
        en: promptEn,
        active: isZh ? 'zh' : 'en'
      };

      const activeText = isZh ? (promptZh || promptEn) : (promptEn || promptZh);
      const usageGuide = isZh
        ? (item.usage_guide_zh || item.usage_guide || "")
        : (item.usage_guide_en || (item.usage_guide && !/[\u4e00-\u9fa5]/.test(item.usage_guide) ? item.usage_guide : "Replace the bracketed variables with your parameters and run in the recommended model."));
      const variables = isZh
        ? (item.variables || [])
        : (item.variables_en || (item.variables || []).filter(v => !/[\u4e00-\u9fa5]/.test(v)));

      const variablesHtml = (variables && variables.length > 0)
        ? `<div class="flex items-center gap-1.5 flex-wrap pt-0.5 w-full min-w-0">
             <span class="text-[9px] text-slate-500 dark:text-slate-400 font-mono shrink-0">${isZh ? "参数占位符:" : "Variables:"}</span>
             ${variables.map(v => `<span class="px-1.5 py-0.2 rounded bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-500/30 font-mono text-[9px] break-all">${escapeHtml(v)}</span>`).join('')}
           </div>`
        : '';

      const sampleHeaderTitle = item.sample_output
        ? (isZh ? (item.sample_output.title || '实测生成效果') : (item.sample_output.title_en || (!/[\u4e00-\u9fa5]/.test(item.sample_output.title || '') && item.sample_output.title) || 'Verified Sample Output'))
        : '';

      const sampleOutputHtml = item.sample_output ? `
        <div class="mt-2 pt-2 border-t border-slate-200 dark:border-slate-800/60 w-full min-w-0">
          <button type="button" onclick="toggleSampleDrawer('${item.id}')" class="w-full py-1.5 px-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-900/80 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-800 text-[11px] text-purple-600 dark:text-purple-300 font-semibold flex items-center justify-between transition-colors cursor-pointer group shadow-sm">
            <span class="flex items-center gap-1.5 min-w-0 flex-1 text-left">
              <span>👀</span>
              <span id="sample-btn-txt-${item.id}" class="truncate">${t.viewSampleOutput || (isZh ? '查看实测效果样例 (Sample Output)' : 'View Sample Output')}</span>
            </span>
            <span id="sample-arrow-${item.id}" class="text-xs transition-transform duration-200 shrink-0 ml-1">▼</span>
          </button>
          <div id="sample-drawer-${item.id}" class="hidden mt-2 p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/90 border border-slate-200 dark:border-slate-800 space-y-2 w-full min-w-0 overflow-hidden">
            <div class="flex items-center justify-between text-[10px] text-slate-500 font-bold border-b border-slate-200 dark:border-slate-800 pb-1">
              <span class="truncate">✨ ${escapeHtml(sampleHeaderTitle)}</span>
              <span class="font-mono uppercase text-[9px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-500 shrink-0">${item.sample_output.type || 'text'}</span>
            </div>
            ${renderSampleOutputContent(item.id, item.sample_output)}
          </div>
        </div>
      ` : '';

      return `
        <article class="glass-card rounded-xl p-3.5 flex flex-col justify-between space-y-2.5 border-l-4 ${isLegacy ? 'border-l-slate-400 dark:border-l-slate-600 opacity-90' : 'border-l-purple-500'} shadow-md group w-full max-w-full min-w-0 overflow-hidden box-border">
          <div class="space-y-2 w-full max-w-full min-w-0 overflow-hidden">
            <div class="flex items-start justify-between gap-1.5 flex-wrap w-full min-w-0">
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-500/20 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 break-words whitespace-normal leading-tight max-w-[70%] inline-block">
                ${purpose}
              </span>
              <div class="flex items-center space-x-1.5 shrink-0 ml-auto pt-0.5">
                ${todayBadge}
                <span class="text-[10px] text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap shrink-0" title="${timeObj.display}">🕒 ${timeObj.relative || (isZh ? '今日' : 'Today')}</span>
              </div>
            </div>

            <h4 class="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100 leading-snug group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors break-words w-full min-w-0">${title}</h4>

            <div class="flex items-center space-x-1.5 text-[9px] font-mono flex-wrap gap-y-1 w-full min-w-0">
              ${modelBadge}
              <span class="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800 break-words">⚙️ ${tempAdvice}</span>
            </div>

            ${variablesHtml}

            ${summary ? `<p class="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed break-words w-full min-w-0">${summary}</p>` : ''}
            
            <div class="flex items-center justify-between mt-1 pt-1 border-t border-slate-200 dark:border-slate-800/60 w-full min-w-0">
              <span class="text-[10px] font-mono text-slate-500 dark:text-slate-400 shrink-0">${t.promptDirectives || (isZh ? "提示词指令:" : "Directives:")}</span>
              <div class="inline-flex rounded-md bg-slate-100 dark:bg-slate-900 p-0.5 border border-slate-200 dark:border-slate-800 text-[10px] shrink-0">
                <button type="button" onclick="switchPromptLang('${item.id}', 'zh')" id="plang-zh-${item.id}" class="px-2 py-0.5 rounded ${isZh ? 'bg-purple-600 text-white font-bold' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'} transition-colors cursor-pointer">🇨🇳 中文</button>
                <button type="button" onclick="switchPromptLang('${item.id}', 'en')" id="plang-en-${item.id}" class="px-2 py-0.5 rounded ${!isZh ? 'bg-purple-600 text-white font-bold' : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'} transition-colors cursor-pointer">🇬🇧 EN</button>
              </div>
            </div>

            <div id="pbox-${item.id}" class="notranslate bg-purple-50/70 dark:bg-slate-950/90 p-2.5 rounded-lg border border-purple-200/80 dark:border-slate-800 text-[11px] text-purple-950 dark:text-purple-200 font-mono leading-relaxed select-all whitespace-pre-wrap max-h-44 overflow-y-auto break-words break-all w-full max-w-full">${escapeHtml(activeText)}</div>

            ${sampleOutputHtml}

            ${usageGuide ? `
              <div class="text-[10px] text-slate-600 dark:text-slate-400 bg-slate-100/70 dark:bg-slate-900/50 p-2 rounded border border-slate-200 dark:border-slate-800/60 leading-relaxed font-sans break-words w-full min-w-0">
                <span class="text-purple-600 dark:text-purple-400 font-semibold">${t.promptUsageGuide || (isZh ? "💡 使用指南: " : "💡 Usage Guide: ")}</span>${escapeHtml(usageGuide)}
              </div>
            ` : ''}
          </div>

          <button type="button" onclick="copyCardPrompt('${item.id}')" class="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold py-1.5 rounded-lg transition-colors flex items-center justify-center space-x-1.5 shadow-md shadow-purple-600/30 cursor-pointer">
            <span>${t.copyPrompt || '一键复制提示词 📋'}</span>
          </button>
        </article>
      `;
    }

    // ==========================================
    // 专门卡片渲染：YouTube 实操与演示视频卡片
    // ==========================================
    // ==========================================
    // 专门卡片渲染：9:16 竖屏手机卡片 (Shorts & TikTok 沉浸式视效)
    // ==========================================
    function renderVerticalVideoCard(item) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const title = formatVideoTitle(item, currentLang);
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const isTikTok = item.platform === 'tiktok' || (item.embed_url && item.embed_url.includes('tiktok.com')) || (item.url && item.url.includes('tiktok.com'));
      const platformType = isTikTok ? 'tiktok' : 'shorts';
      const cleanSource = item.author || item.source || (isTikTok ? "TikTok Creator" : "YouTube Creator");
      const duration = item.duration || item.metrics?.duration || "⏱️ 00:45";
      const views = item.metrics?.views || (isZh ? "🔥 爆款热播" : "🔥 Trending");
      const jumpUrl = item.url || item.link || item.embed_url || "";
      const embedSrc = isTikTok 
        ? (item.embed_url || `https://www.tiktok.com/embed/v2/${item.video_id}`)
        : `https://www.youtube-nocookie.com/embed/${item.video_id}?enablejsapi=1&autoplay=0&mute=1&playsinline=1&rel=0&modestbranding=1`;
      const modalEmbedUrl = isTikTok 
        ? (item.embed_url || `https://www.tiktok.com/embed/v2/${item.video_id}`)
        : `https://www.youtube.com/embed/${item.video_id}?autoplay=1&mute=0`;

      return `
        <article class="vertical-video-card group relative flex flex-col justify-between glass-card rounded-2xl p-3.5 sm:p-4 border border-slate-200 dark:border-slate-800 hover:border-rose-500/50 dark:hover:border-rose-500/50 shadow-md hover:shadow-xl transition-all duration-300 bg-white/80 dark:bg-slate-900/90 backdrop-blur-md">
          <!-- 顶部创作者与平台标头 -->
          <div class="flex items-center justify-between pb-2">
            <div class="flex items-center space-x-2 truncate max-w-[170px]">
              <div class="w-6 h-6 rounded-full ${isTikTok ? 'bg-gradient-to-tr from-rose-600 to-pink-500' : 'bg-red-600'} text-white flex items-center justify-center text-[10px] font-black shrink-0 shadow-sm">
                ${isTikTok ? 'TT' : 'YT'}
              </div>
              <span class="text-xs font-bold text-slate-800 dark:text-slate-200 truncate notranslate" title="${cleanSource}">${cleanSource}</span>
            </div>
            <span class="px-2 py-0.5 rounded-full ${isTikTok ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30' : 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30'} border text-[10px] font-black shrink-0 flex items-center space-x-1">
              <span>${isTikTok ? '🎵 TikTok' : '🔴 Shorts'}</span>
            </span>
          </div>

          <!-- 9:16 沉浸竖屏视频播放视口 (首屏海报秒开，点击原位即播，绝不卡死/打扰) -->
          <div class="relative w-full aspect-[9/16] rounded-xl overflow-hidden bg-black shadow-inner my-1 group/player cursor-pointer select-none"
               data-embed-src="${embedSrc}"
               data-platform="${platformType}"
               onclick="mountInPlaceVerticalVideo(this.closest('.vertical-video-card'), '${embedSrc}', '${platformType}')">
            
            <!-- 原生海报封面 -->
            <img src="${item.image_url || ''}" class="absolute inset-0 w-full h-full object-cover group-hover/player:scale-105 transition-transform duration-500 ease-out" loading="lazy" alt="${title}">

            <!-- 原位播放器动态挂载槽 (点击后注入 iframe，平时不发送并发请求，彻底杜绝 TikTok 反爬风控与加载卡死) -->
            <div class="vertical-player-slot hidden absolute inset-0 w-full h-full z-10 bg-black"></div>

            <!-- 卡片封面操作引导层 (点击播放后自动隐去) -->
            <div class="vertical-cover-overlay absolute inset-0 w-full h-full z-20 flex flex-col justify-between p-3 bg-gradient-to-b from-black/60 via-transparent to-black/80 transition-opacity duration-300">
              <!-- 浮动控制栏：左侧取消静音 + 右侧全屏放大 -->
              <div class="flex items-center justify-between w-full pointer-events-none">
                <button type="button" onclick="event.stopPropagation(); toggleVideoCardMute(this)" data-muted="true" class="pointer-events-auto video-mute-btn px-2.5 py-1 rounded-full bg-black/80 hover:bg-rose-600 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-white/20 backdrop-blur-md" title="点击取消静音并播放">
                  <span>🔇</span><span>${isZh ? '取消静音' : 'Unmute'}</span>
                </button>
                <button type="button" onclick="event.stopPropagation(); openVideoModal('${modalEmbedUrl}', '${title.replace(/'/g, "\\'")}', '${platformType}', '${jumpUrl}')" class="pointer-events-auto px-2.5 py-1 rounded-full bg-black/80 hover:bg-rose-600 text-white font-bold text-[11px] shadow-lg transition-all flex items-center space-x-1 border border-white/20 backdrop-blur-md" title="单击全屏放大">
                  <span>⛶</span><span>${isZh ? '全屏放大' : 'Fullscreen'}</span>
                </button>
              </div>

              <!-- 中心播放按钮与引导 -->
              <div class="flex-1 flex flex-col items-center justify-center space-y-2 pointer-events-none">
                <button type="button" class="play-inplace-btn w-14 h-14 rounded-full ${isTikTok ? 'bg-gradient-to-tr from-rose-600 to-pink-500 group-hover/player:from-rose-500 group-hover/player:to-pink-400' : 'bg-red-600 group-hover/player:bg-red-500'} text-white flex items-center justify-center text-xl pl-1 shadow-2xl border-2 border-white/30 group-hover/player:scale-110 transition-all duration-300">
                  ▶
                </button>
                <span class="px-3 py-1 rounded-full bg-black/75 backdrop-blur-md text-white text-[11px] font-bold border border-white/20 shadow-md">
                  ${isZh ? '点击原位即开即看' : 'Click to Play'}
                </span>
              </div>

              <!-- 底部时长胶囊 -->
              <div class="flex items-center justify-end pointer-events-none">
                <span class="px-2 py-0.5 rounded-full bg-black/75 backdrop-blur-sm text-slate-200 text-[10px] font-mono border border-white/10 font-medium">
                  ${duration}
                </span>
              </div>
            </div>
          </div>

          <!-- 底部详情与直达原视频链接 -->
          <div class="pt-3 flex flex-col space-y-2">
            <!-- 标题 (点击亦可前往原视频) -->
            <h4 class="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100 line-clamp-2 leading-snug hover:text-rose-500 dark:hover:text-rose-400 transition-colors cursor-pointer" onclick="window.open('${jumpUrl}', '_blank')" title="${title}">
              ${title}
            </h4>

            <!-- 播放量与发布时间 -->
            <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              <span class="text-amber-500 dark:text-amber-400 font-bold">${views}</span>
              <span title="${timeObj.display}">🕒 ${timeObj.relative || timeObj.display}</span>
            </div>

            <!-- 专门的原视频直达大按钮 (醒目快捷) -->
            <a href="${jumpUrl}" target="_blank" rel="noopener noreferrer" class="w-full py-2 px-3 rounded-xl ${isTikTok ? 'bg-gradient-to-r from-rose-600 via-pink-600 to-rose-700 hover:from-rose-500 hover:to-pink-500 shadow-rose-600/20 hover:shadow-rose-600/40' : 'bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-600/20 hover:shadow-red-600/40'} text-white font-bold text-xs flex items-center justify-center space-x-1.5 shadow-md transition-all duration-200 mt-1">
              <span>${isTikTok ? (isZh ? "🎵 访问 TikTok 原视频" : "🎵 Watch on TikTok") : (isZh ? "🔴 访问 YouTube Shorts 原视频" : "🔴 Watch on YouTube Shorts")}</span>
              <span>↗</span>
            </a>
          </div>
        </article>
      `;
    }

    // ==========================================
    // 专门卡片渲染：16:9 横屏经典视频卡片 (YouTube 深度长视频)
    // ==========================================
    function renderHorizontalVideoCard(item) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const title = formatVideoTitle(item, currentLang);
      const summary = (isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || "";
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const todayBadge = timeObj.isToday ? `<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 text-[9px] font-bold shrink-0">${t.todayTag}</span>` : '';
      const cleanSource = item.author || item.source || "";
      const skillTag = isZh
        ? (item.purpose_zh || item.metrics?.skill_tag || '🎓 系统教学')
        : (item.purpose_en || '🎓 Masterclass');
      const duration = item.duration || item.metrics?.duration || '⏱️ 20:00';
      const jumpUrl = item.url || item.link || item.embed_url;

      return `
        <article class="glass-card rounded-xl p-3 flex flex-col justify-between space-y-2 group border-t-2 border-t-red-500/80 hover:border-red-500/60 transition-all select-none">
          <div class="space-y-2">
            <div class="relative w-full aspect-video rounded-lg overflow-hidden bg-slate-950 border border-slate-200 dark:border-slate-800 cursor-pointer"
              onmouseenter="startVideoHoverPreview(this, '${item.video_id || ''}', 'youtube')"
              onmouseleave="stopVideoHoverPreview(this)"
              onclick="window.open('${jumpUrl}', '_blank')">
              
              <img src="${item.image_url}" alt="${escapeHtml(title)}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy">
              
              <!-- 悬停静音预览挂载层 -->
              <div class="video-preview-slot absolute inset-0 w-full h-full pointer-events-none overflow-hidden"></div>

              <!-- 静音预览中发光提示胶囊 -->
              <div class="preview-indicator hidden absolute top-3 right-3 z-30 px-2.5 py-0.5 rounded-full bg-emerald-500/90 backdrop-blur-md text-white font-bold text-[9px] shadow-lg animate-pulse whitespace-nowrap flex items-center space-x-1 pointer-events-none">
                <span class="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
                <span>${isZh ? '静音预览中 · 单击直达原视频' : 'Muted Preview · Click for Video'}</span>
              </div>

              <div class="absolute inset-0 bg-black/30 flex items-center justify-center group-hover:bg-black/10 transition-colors pointer-events-none">
                <div class="w-11 h-11 rounded-full bg-red-600 text-white flex items-center justify-center text-base pl-0.5 shadow-xl group-hover:scale-110 transition-transform">
                  ▶
                </div>
              </div>

              <div class="absolute top-2 left-2 flex items-center space-x-1.5 flex-wrap z-20 pointer-events-none">
                <span class="px-2 py-0.5 rounded bg-red-600/90 text-white text-[9px] font-bold shadow">▶ YouTube</span>
                <span class="px-2 py-0.5 rounded bg-black/85 text-red-300 border border-red-500/40 text-[10px] font-bold">${skillTag}</span>
              </div>

              <!-- 缩略图底部操作条：站内播放入口 + 时长 -->
              <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between z-20">
                <button type="button" onclick="event.stopPropagation(); openVideoModal('${item.embed_url}', '${title.replace(/'/g, "\\'")}', 'youtube', '${jumpUrl}')" class="px-2 py-0.5 rounded bg-black/85 hover:bg-red-600 text-white text-[10px] font-bold border border-white/20 transition-all flex items-center space-x-1 shadow-lg" title="在站内弹窗播放">
                  <span>▶</span><span>${isZh ? '站内播放' : 'Watch Here'}</span>
                </button>
                <span class="bg-black/85 px-1.5 py-0.5 rounded text-[10px] font-mono text-white pointer-events-none border border-white/10">${duration}</span>
              </div>
            </div>

            <div class="flex items-center justify-between text-[10px] pt-1 gap-2">
              <div class="flex items-center space-x-1.5 truncate max-w-[160px]">
                <span class="text-red-600 dark:text-red-400 font-bold truncate notranslate">${cleanSource}</span>
                <a href="${jumpUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" class="text-[9px] px-1.5 py-0.5 rounded bg-slate-200/90 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/60 border border-slate-300 dark:border-slate-700 shrink-0 notranslate font-semibold transition-colors" title="Source">${isZh ? "原站 ↗" : "Source ↗"}</a>
              </div>
              <div class="flex items-center space-x-1.5 shrink-0 ml-auto">
                ${todayBadge}
                <span class="text-slate-500 dark:text-slate-400 font-mono whitespace-nowrap shrink-0" title="${timeObj.display}">🕒 ${timeObj.relative || timeObj.display}</span>
              </div>
            </div>

            <h4 class="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors line-clamp-2 leading-snug cursor-pointer" onclick="window.open('${jumpUrl}', '_blank')">
              ${title}
            </h4>

            ${summary ? `
              <p class="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                ${summary}
              </p>
            ` : ''}
          </div>

          ${item.tags && item.tags.length ? `
            <div class="flex items-center gap-1.5 flex-wrap pt-1">
              ${item.tags.map(tag => `<button type="button" onclick="event.stopPropagation(); executeTagSearch('${tag}')" class="text-[9px] font-medium px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-900/90 text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-950/60 border border-slate-200 dark:border-slate-800 transition-colors">#${tag}</button>`).join('')}
            </div>
          ` : ''}
        </article>
      `;
    }

    // 通用视频渲染路由分发
    function renderVideoCard(item) {
      const isVertical = item.aspect_ratio === '9:16' || item.platform === 'tiktok' || item.platform === 'shorts' || (item.url && item.url.includes('tiktok.com'));
      if (isVertical) {
        return renderVerticalVideoCard(item);
      }
      return renderHorizontalVideoCard(item);
    }

    function renderVideoOrPromptCard(item) {
      if (item && item.is_prompt) return renderPromptCard(item);
      return renderVideoCard(item);
    }

    // ==========================================
    // 渲染 UI 视图总入口
    // ==========================================
    // 全站跨分类智能检索视图渲染 (5 大独立分类全景)
    function renderSiteWideSearchResults(data) {
      const isZh = currentLang === 'zh';
      const newsHits = filterList(data.grouped?.news || data.news || data.industry_news || []);
      const celebHits = filterList(data.grouped?.celebrity || data.celebrity || data.leader_opinions || []);
      const toolsHits = filterList(data.grouped?.tools || data.tools || data.applied_tools || []);
      const allVideos = (data.grouped?.videos || data.videos || []).filter(it => !it.is_prompt);
      const allPrompts = data.grouped?.prompts || data.prompts || (data.grouped?.videos || data.videos || []).filter(it => it.is_prompt);
      const videosHits = dedupVideoItems(filterList(allVideos));
      const promptsHits = filterList(allPrompts);
      const totalHits = newsHits.length + celebHits.length + toolsHits.length + videosHits.length + promptsHits.length;

      const headingEl = document.getElementById('search-results-heading');
      if (headingEl) {
        headingEl.textContent = isZh ? `全站智能检索: "${searchQuery}"` : `Site-wide Search: "${searchQuery}"`;
      }
      const summaryEl = document.getElementById('search-results-summary');
      if (summaryEl) {
        summaryEl.textContent = isZh
          ? `共找到 ${totalHits} 条全站情报 · ⚡ 快讯 ${newsHits.length} 条 · 🐦 社交 ${celebHits.length} 条 · 🛠️ 工具 ${toolsHits.length} 条 · 🎬 视频 ${videosHits.length} 条 · 💡 提示词 ${promptsHits.length} 条`
          : `Found ${totalHits} intelligence items · ⚡ News: ${newsHits.length} · 🐦 Social: ${celebHits.length} · 🛠️ Tools: ${toolsHits.length} · 🎬 Videos: ${videosHits.length} · 💡 Prompts: ${promptsHits.length}`;
      }

      document.getElementById('search-count-news').textContent = newsHits.length;
      document.getElementById('search-count-celeb').textContent = celebHits.length;
      document.getElementById('search-count-tools').textContent = toolsHits.length;
      document.getElementById('search-count-videos').textContent = videosHits.length;
      const scPrompts = document.getElementById('search-count-prompts');
      if (scPrompts) scPrompts.textContent = promptsHits.length;

      document.getElementById('search-stream-news').innerHTML = newsHits.length > 0
        ? newsHits.map(renderNewsCard).join('')
        : `<div class="text-slate-500 text-xs py-8 text-center border border-slate-200 dark:border-slate-800/60 rounded-xl bg-slate-100/50 dark:bg-slate-900/40">${isZh ? '未找到匹配快讯' : 'No matching news'}</div>`;

      document.getElementById('search-stream-celeb').innerHTML = celebHits.length > 0
        ? celebHits.map(renderCelebrityCard).join('')
        : `<div class="text-slate-500 text-xs py-8 text-center border border-slate-200 dark:border-slate-800/60 rounded-xl bg-slate-100/50 dark:bg-slate-900/40">${isZh ? '未找到匹配大V发言' : 'No matching voices'}</div>`;

      document.getElementById('search-stream-tools').innerHTML = toolsHits.length > 0
        ? dedupToolItems(toolsHits).map(renderToolCard).join('')
        : `<div class="text-slate-500 text-xs py-8 text-center border border-slate-200 dark:border-slate-800/60 rounded-xl bg-slate-100/50 dark:bg-slate-900/40">${isZh ? '未找到匹配落地工具' : 'No matching tools'}</div>`;

      document.getElementById('search-stream-videos').innerHTML = videosHits.length > 0
        ? videosHits.map(renderVideoCard).join('')
        : `<div class="text-slate-500 text-xs py-8 text-center border border-slate-200 dark:border-slate-800/60 rounded-xl bg-slate-100/50 dark:bg-slate-900/40">${isZh ? '未找到匹配实战视频' : 'No matching videos'}</div>`;

      const sStreamPrompts = document.getElementById('search-stream-prompts');
      if (sStreamPrompts) {
        sStreamPrompts.innerHTML = promptsHits.length > 0
          ? promptsHits.map(renderPromptCard).join('')
          : `<div class="text-slate-500 text-xs py-8 text-center border border-slate-200 dark:border-slate-800/60 rounded-xl bg-slate-100/50 dark:bg-slate-900/40">${isZh ? '未找到匹配提示词' : 'No matching prompts'}</div>`;
      }
      applyCurrentTranslation();
    }

    let homeToolFilter = 'new'; // 'new' (今日最新入库) | 'surge' (本周飙升) | 'web' (商业Web) | 'demo' (免装秒玩)
    let homePromptFilter = 'wf'; // 'wf' (实战工作流) | 'prompt' (SOTA提示词)

    function switchHomeToolFilter(mode) {
      homeToolFilter = mode || 'new';
      const pills = {
        'new': 'home-tool-new',
        'surge': 'home-tool-surge',
        'web': 'home-tool-web',
        'demo': 'home-tool-demo'
      };
      Object.entries(pills).forEach(([k, id]) => {
        const el = document.getElementById(id);
        if (el) {
          if (k === homeToolFilter) {
            el.className = "home-tool-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-emerald-600 text-white shadow-sm flex items-center gap-1 transition-all cursor-pointer";
          } else {
            el.className = "home-tool-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1 transition-all cursor-pointer";
          }
        }
      });
      renderHomeTools();
    }

    function renderHomeTools(data) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const dataObj = data || cachedData || {};
      const allTools = (dataObj.grouped?.tools || dataObj.tools || dataObj.applied_tools) || [];
      const getToolOrigin = (it) => {
        if (it.tool_origin) return it.tool_origin;
        const u = String(it.official_url || it.url || '').toLowerCase();
        const su = String(it.source_url || '').toLowerCase();
        if (u.includes('github.com') || su.includes('github.com')) return 'github';
        if (u.includes('huggingface.co/spaces') || su.includes('huggingface.co/spaces')) return 'huggingface';
        return 'web';
      };
      const HOUSEHOLD_LEGACY_TOOLS = new Set([
        'cursor', 'bolt.new', 'bolt', 'claude code', 'claude-code',
        'ollama', 'perplexity', 'lm studio', 'lmstudio', 'whisper',
        'whisper webgpu', 'vllm', 'comfyui', 'dify', 'n8n', 'gamma',
        'excalidraw', 'open-webui', 'openwebui', 'jan', 'kokoro',
        'liveportrait', 'mineru', 'aider', 'openhands', 'tripo3d', 'triposr'
      ]);
      const getToolTime = (it) => {
        const tm = it.raw_published_at || it.processed_at || it.published_at || it.crawled_at;
        if (!tm) return 0;
        const d = new Date(tm).getTime();
        return isNaN(d) ? 0 : d;
      };

      let list = dedupToolItems(allTools).filter(it => {
        const nm = (it.app_name || '').toLowerCase().trim();
        const id = (it.id || '').toLowerCase().trim();
        if (HOUSEHOLD_LEGACY_TOOLS.has(nm) || id.startsWith('tool-') || it.is_curated_base) return false;
        if (getToolOrigin(it) === 'github') {
          const s = Number(it.stars) || (it.metrics ? Number(it.metrics.stars) || 0 : 0);
          const ws = Number(it.weekly_stars) || (it.metrics ? Number(it.metrics.weekly_stars) || 0 : 0);
          if (s > 0 && s < 200 && ws < 200) return false;
        }
        return true;
      });

      if (homeToolFilter === 'surge') {
        list.sort((a, b) => {
          const wkB = Number(b.weekly_stars) || (b.metrics ? Number(b.metrics.weekly_stars) || 0 : 0);
          const wkA = Number(a.weekly_stars) || (a.metrics ? Number(a.metrics.weekly_stars) || 0 : 0);
          if (wkB !== wkA) return wkB - wkA;
          const stB = Number(b.stars) || (b.metrics ? Number(b.metrics.stars) || 0 : 0);
          const stA = Number(a.stars) || (a.metrics ? Number(a.metrics.stars) || 0 : 0);
          if (stB !== stA) return stB - stA;
          return getToolTime(b) - getToolTime(a);
        });
      } else if (homeToolFilter === 'web') {
        list = list.filter(it => getToolOrigin(it) === 'web');
        list.sort((a, b) => getToolTime(b) - getToolTime(a));
      } else if (homeToolFilter === 'demo') {
        list = list.filter(it => it.has_live_demo || getToolOrigin(it) === 'web' || getToolOrigin(it) === 'huggingface' || (it.demo_url && it.demo_url.length > 5));
        list.sort((a, b) => getToolTime(b) - getToolTime(a));
      } else {
        // 'new' (今日最新入库): 严格按照筛选入库时间倒序排在首位
        list.sort((a, b) => {
          const tB = getToolTime(b);
          const tA = getToolTime(a);
          if (tB !== tA) return tB - tA;
          const wkB = Number(b.weekly_stars) || (b.metrics ? Number(b.metrics.weekly_stars) || 0 : 0);
          const wkA = Number(a.weekly_stars) || (a.metrics ? Number(a.metrics.weekly_stars) || 0 : 0);
          if (wkB !== wkA) return wkB - wkA;
          return (Number(b.utility_score) || 80) - (Number(a.utility_score) || 80);
        });
      }

      const displayTools = list.slice(0, 3);
      const streamTools = document.getElementById('stream-tools');
      if (streamTools) {
        streamTools.innerHTML = displayTools.length > 0
          ? displayTools.map(renderToolCard).join('')
          : `<div class="text-slate-400 text-xs py-3 px-2 text-center bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800">${t.noRecentTools}</div>`;
      }
      const txtViewAllTools = document.getElementById('txt-view-all-tools');
      if (txtViewAllTools) {
        txtViewAllTools.textContent = isZh ? `查看全部落地神器 (${allTools.length} 个) →` : `View All Applied Tools (${allTools.length}) →`;
      }
    }

    function switchHomePromptFilter(mode) {
      homePromptFilter = mode || 'wf';
      const pills = {
        'wf': 'home-prompt-wf',
        'prompt': 'home-prompt-prompt'
      };
      Object.entries(pills).forEach(([k, id]) => {
        const el = document.getElementById(id);
        if (el) {
          if (k === homePromptFilter) {
            el.className = "home-prompt-pill active px-2.5 py-1 rounded-lg text-xs font-bold bg-cyan-600 text-white shadow-sm flex items-center gap-1 transition-all cursor-pointer";
          } else {
            el.className = "home-prompt-pill px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 flex items-center gap-1 transition-all cursor-pointer";
          }
        }
      });
      renderHomePrompts();
    }

    function renderHomePrompts(data) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      const dataObj = data || cachedData || {};
      const allPrompts = (dataObj.grouped?.prompts || dataObj.prompts || (dataObj.grouped?.videos || dataObj.videos || []).filter(it => it.is_prompt)) || [];

      let list = allPrompts.slice();
      if (homePromptFilter === 'wf') {
        list = list.filter(it => it.is_workflow || it.sub_type === 'workflow');
      } else {
        list = list.filter(it => !it.is_workflow && it.sub_type !== 'workflow');
      }

      list.sort((a, b) => {
        const isLegA = a.generation_tier === 'legacy' ? 1 : 0;
        const isLegB = b.generation_tier === 'legacy' ? 1 : 0;
        if (isLegA !== isLegB) return isLegA - isLegB;
        const scoreA = Number(a.model_tier_score) || 80;
        const scoreB = Number(b.model_tier_score) || 80;
        if (scoreB !== scoreA) return scoreB - scoreA;
        const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
        const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
        return timeB - timeA;
      });

      const displayPrompts = list.slice(0, 3);
      const streamPrompts = document.getElementById('stream-prompts');
      if (streamPrompts) {
        streamPrompts.innerHTML = displayPrompts.length > 0
          ? displayPrompts.map(it => (it.is_workflow || it.sub_type === 'workflow') ? renderWorkflowCard(it) : renderPromptCard(it)).join('')
          : `<div class="text-slate-400 text-xs py-3 px-2 text-center bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800">${t.noRecentPrompts || (isZh ? '暂无提示词' : 'No prompts')}</div>`;
      }
      const txtViewAllPrompts = document.getElementById('txt-view-all-prompts');
      if (txtViewAllPrompts) {
        txtViewAllPrompts.textContent = isZh ? `查看全部实操与工作流 (${allPrompts.length} 条) →` : `View All Workflows & Prompts (${allPrompts.length}) →`;
      }
    }

    // ==========================================
    // 渲染 UI 视图总入口 (24 小时绝对新鲜拦截)
    // ==========================================
    function renderUI(data) {
      if (!data) return;
      const t = I18N[currentLang];
      const isZh = currentLang === 'zh';

      // 1. 获取全量各分类列表 (视频与提示词彻底独立)
      const allNews = data.grouped?.news || data.news || data.industry_news || [];
      const allCeleb = data.grouped?.celebrity || data.celebrity || data.leader_opinions || [];
      const allTools = dedupToolItems(data.grouped?.tools || data.tools || data.applied_tools || []);
      const allVideos = (data.grouped?.videos || data.videos || []).filter(it => !it.is_prompt);
      const allPrompts = data.grouped?.prompts || data.prompts || (data.grouped?.videos || data.videos || []).filter(it => it.is_prompt);

      // 更新导航角标总数
      const bAll = document.getElementById('badge-count-all');
      if (bAll) bAll.textContent = allNews.length + allCeleb.length + allTools.length + allVideos.length + allPrompts.length;
      const bNews = document.getElementById('badge-count-news');
      if (bNews) bNews.textContent = allNews.length;
      const bCeleb = document.getElementById('badge-count-celebrity');
      if (bCeleb) bCeleb.textContent = allCeleb.length;
      const bTools = document.getElementById('badge-count-tools');
      if (bTools) bTools.textContent = allTools.length;
      const bVideos = document.getElementById('badge-count-videos');
      if (bVideos) bVideos.textContent = allVideos.length;
      const bPrompts = document.getElementById('badge-count-prompts');
      if (bPrompts) bPrompts.textContent = allPrompts.length;
      const bArchive = document.getElementById('badge-count-archive');
      if (bArchive) {
        bArchive.textContent = data.archive_meta?.total_archived || (cachedArchiveData ? cachedArchiveData.items.length : 0);
      }

      // 实时同步社交雷达子角标与缓存
      const bLeader = document.getElementById('badge-count-leader');
      if (bLeader) bLeader.textContent = allCeleb.length;
      const bViral = document.getElementById('badge-count-viral');
      if (bViral) {
        const allViral = data.grouped?.viral_posts || data.viral_posts || (data.items ? data.items.filter(it => it.sub_category === 'viral_post' || (it.category === 'celebrity' && it.is_viral)) : []);
        bViral.textContent = allViral.length;
      }

      // 2. 模式判断：若当前激活了全站搜索，进入全景检索视图
      const isSearchActive = !!searchQuery;
      const viewSearch = document.getElementById('view-search');
      const viewAll = document.getElementById('view-all');
      const viewCat = document.getElementById('view-category');
      const topThreeSection = document.getElementById('top-three-section');

      if (isSearchActive) {
        if (viewSearch) viewSearch.classList.remove('hidden');
        if (viewAll) viewAll.classList.add('hidden');
        if (viewCat) viewCat.classList.add('hidden');
        if (topThreeSection) topThreeSection.classList.add('hidden');
        renderSiteWideSearchResults(data);
        return;
      } else {
        if (viewSearch) viewSearch.classList.add('hidden');
        if (topThreeSection) topThreeSection.classList.toggle('hidden', currentTab !== 'all');
        if (currentTab === 'all') {
          if (viewAll) viewAll.classList.remove('hidden');
          if (viewCat) viewCat.classList.add('hidden');
        } else {
          if (viewAll) viewAll.classList.add('hidden');
          if (viewCat) viewCat.classList.remove('hidden');
          const celebSubfilter = document.getElementById('celebrity-subfilter');
          const toolsSubfilter = document.getElementById('tools-subfilter');
          const videosSubfilter = document.getElementById('videos-subfilter');
          const promptsSubfilter = document.getElementById('prompts-subfilter');
          if (celebSubfilter) celebSubfilter.classList.toggle('hidden', currentTab !== 'celebrity' || socialViewMode !== 'leader');
          if (toolsSubfilter) toolsSubfilter.classList.toggle('hidden', currentTab !== 'tools');
          if (videosSubfilter) videosSubfilter.classList.toggle('hidden', currentTab !== 'videos');
          if (promptsSubfilter) promptsSubfilter.classList.toggle('hidden', currentTab !== 'prompts');
          const t = I18N[currentLang];
          const titleEl = document.getElementById('cat-view-title');
          const catTitles = {
            news: currentLang === 'zh' ? '⚡ 行业突发快讯专栏' : '⚡ Breaking AI News',
            celebrity: currentLang === 'zh' ? '🐦 社交雷达 · 𝕏 与前沿社区动态' : '🐦 Social Radar · 𝕏 & Community Pulse',
            tools: currentLang === 'zh' ? '🛠️ 场景落地·实用神器专栏' : '🛠️ Applied AI Tools Directory',
            videos: currentLang === 'zh' ? '🎬 实战视频·深度演示专栏' : '🎬 Hands-on Video Tutorials',
            prompts: currentLang === 'zh' ? '💡 提示词库·前沿模型实战咒语' : '💡 Prompt Bank · SOTA AI System Prompts'
          };
          if (titleEl) titleEl.textContent = catTitles[currentTab] || t.tabs[currentTab] || currentTab;

          const socialSwitcherWrap = document.getElementById('social-mode-switcher-wrap');
          if (socialSwitcherWrap) {
            socialSwitcherWrap.classList.toggle('hidden', currentTab !== 'celebrity');
          }
          renderCategoryView(currentTab);
        }
      }

      // 3. 渲染首页置顶：极客实测展厅 (48h 视频 Demo + 领袖精粹) 或 传统推文滚动栏
      const rawViralTweets = (data.viral_ticker_tweets && data.viral_ticker_tweets.length > 0)
        ? data.viral_ticker_tweets
        : (allCeleb && allCeleb.length > 0 ? allCeleb : (data.top_three || []));
      const viralTweets = rawViralTweets.filter(it => {
        if (it.category === 'celebrity' || it.platform === 'x') {
          return isWithin24Hours(it.raw_published_at) && isMeaningfulTweet(it);
        }
        return true;
      });
      const leadMedia = data.hero_media_showcase ? (data.hero_media_showcase.lead_media || data.hero_media_showcase.video) : null;
      renderViralTicker(viralTweets.length > 0 ? viralTweets : (data.top_three || []), leadMedia);

      // 计算极客实测 Demo 数量角标
      try {
        const bDemos = document.getElementById('badge-count-demos');
        if (bDemos) {
          const allCelebList = allCeleb || [];
          const allViralList = (data.grouped?.viral_posts || data.viral_posts || (data.items ? data.items.filter(it => (it.sub_category === 'viral_post' || (it.category === 'celebrity' && it.is_viral))) : [])) || [];
          const demosCount = allCelebList.concat(allViralList).filter(it => {
            if (!it) return false;
            if (it.has_video || it.video_url || it.is_hero_demo) return true;
            const txt = `${it.title || ''} ${it.title_zh || ''} ${it.full_text_en || ''} ${it.full_text_zh || ''} ${(it.spec_tags || []).join(' ')}`.toLowerCase();
            return /demo|hands[- ]?on|tested|benchmark|tutorial|workflow|实测|上手|跑分|实操|实录/i.test(txt);
          }).length;
          bDemos.textContent = `${demosCount || 24}+`;
        }
      } catch (err) {
        console.warn('badge-count-demos warning:', err);
      }

      try {
        if (document.getElementById('top-three-container')) {
          renderTopThree(data.top_three || []);
        }
      } catch (err) {
        console.error('Error rendering top-three:', err);
      }

      try {
        if (data.topic_focus && data.topic_focus.length > 0) {
          renderTopicFocus(data.topic_focus);
        }
      } catch (err) {
        console.error('Error rendering topic-focus:', err);
      }

      // 4. 渲染“综合全景”模式 (核心：首页严格展示重点推荐，与天梯榜等高对齐，各板块均支持一键直达完整专区)
      // A. 快讯板块 (News) - 与天梯图等高自适应，展示最新 18 条高价值快讯
      try {
        const recentNews = allNews.filter(it => isWithin24Hours(it.raw_published_at));
        const poolNews = recentNews.length >= 6 ? recentNews : allNews;
        const displayNews = poolNews.slice(0, 18);
        const streamNews = document.getElementById('stream-news');
        if (streamNews) {
          streamNews.innerHTML = displayNews.length > 0 
            ? displayNews.map((it, idx) => renderNewsCard(it, idx)).join('')
            : `<div class="text-slate-400 text-xs py-4 px-3 text-center bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800">${t.noRecentNews}</div>`;
        }
        const newsSubCount = document.getElementById('news-sub-count');
        if (newsSubCount) {
          newsSubCount.textContent = isZh ? `24h 实时 (${displayNews.length})` : `24h Live (${displayNews.length})`;
        }
        const txtViewAllNews = document.getElementById('txt-view-all-news');
        if (txtViewAllNews) {
          txtViewAllNews.textContent = isZh ? `查看全部行业快讯 (${allNews.length} 条) →` : `View All Breaking News (${allNews.length}) →`;
        }

        // 全站全量历史归档库入口横幅 (超 24 小时沉淀库，带完整多页翻查)
        const arcSecNews = document.getElementById('archive-section-news');
        const arcTxtNews = document.getElementById('txt-archive-news');
        const totalArchivedCount = data.archive_meta?.total_archived || (cachedArchiveData ? cachedArchiveData.items.length : 0);
        if (arcSecNews) {
          arcSecNews.classList.remove('hidden');
          if (arcTxtNews) {
            arcTxtNews.textContent = isZh
              ? `查看历史情报全量归档库 (已累计收录 ${totalArchivedCount} 篇)`
              : `View Full Historical Intelligence Archive (${totalArchivedCount} items)`;
          }
        }
      } catch (err) {
        console.error('Error rendering stream-news:', err);
      }

      // B. 领袖社交板块 (Celebrity) - 严格限定在 24 小时以内，过期清退，一个不留，清除无意义单句推文！
      try {
        let sideCelebList = allCeleb;
        const recentCeleb = sideCelebList.filter(it => isWithin24Hours(it.raw_published_at) && isMeaningfulTweet(it));
        recentCeleb.sort((a, b) => {
          const aPinned = isItemPinnedActive(a) ? 1 : 0;
          const bPinned = isItemPinnedActive(b) ? 1 : 0;
          if (aPinned !== bPinned) return bPinned - aPinned;
          const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
          const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
          return timeB - timeA;
        });
        const displayCeleb = recentCeleb.slice(0, 14);
        const streamCelebrity = document.getElementById('stream-celebrity');
        if (streamCelebrity) {
          streamCelebrity.innerHTML = displayCeleb.length > 0
            ? displayCeleb.map(renderCelebrityCard).join('')
            : `<div class="text-slate-400 text-xs py-3 px-2 text-center bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800">${t.noRecentCeleb}</div>`;
        }
        const celebSubCount = document.getElementById('celebrity-sub-count');
        if (celebSubCount) {
          celebSubCount.textContent = isZh ? `24h 实时 (${displayCeleb.length})` : `24h Live (${displayCeleb.length})`;
        }
        const txtViewAllCeleb = document.getElementById('txt-view-all-celebrity');
        if (txtViewAllCeleb) {
          txtViewAllCeleb.textContent = isZh ? `查看全部社交雷达 (${allCeleb.length} 条) →` : `View All Social Pulse (${allCeleb.length}) →`;
        }
      } catch (err) {
        console.error('Error rendering stream-celebrity:', err);
      }

      // C. 落地工具板块 (Tools) - 首页精选按多维筛选即时呈现 (默认今日最新入库 Top 3)
      try {
        renderHomeTools(data);
      } catch (err) {
        console.error('Error rendering stream-tools:', err);
      }

      // D. 视频演示板块 (Videos) - 首页仅精选 Top 2 实战演示
      try {
        const dedupedVideos = dedupVideoItems(allVideos);
        const displayVideos = dedupedVideos.slice(0, 2);
        const streamVideos = document.getElementById('stream-videos');
        if (streamVideos) {
          streamVideos.innerHTML = displayVideos.length > 0
            ? displayVideos.map(renderVideoCard).join('')
            : `<div class="text-slate-400 text-xs py-3 px-2 text-center bg-slate-100 dark:bg-slate-900/50 rounded-xl border border-slate-200 dark:border-slate-800">${t.noRecentVideos}</div>`;
        }
        const txtViewAllVideos = document.getElementById('txt-view-all-videos');
        if (txtViewAllVideos) {
          txtViewAllVideos.textContent = isZh ? `查看全部精选视频 (${dedupedVideos.length} 个) →` : `View All Hands-on Videos (${dedupedVideos.length}) →`;
        }
      } catch (err) {
        console.error('Error rendering stream-videos:', err);
      }

      // E. 提示词与实战工作流板块 (Prompts & Workflows) - 首页精选呈现 (默认实战工作流)
      try {
        renderHomePrompts(data);
      } catch (err) {
        console.error('Error rendering stream-prompts:', err);
      }

      // 5. 渲染 LMSYS Chatbot Arena Top 25 天梯榜
      try {
        const streamArena = document.getElementById('stream-arena');
        if (streamArena) {
          const arenaList = data.chatbot_arena || [];
          const arenaCards = arenaList.map(item => {
            const badgeText = isZh ? (item.badge || '') : (item.badge_en || item.badge || '');
            let rankBadgeClass = 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700';
            if (item.rank === 1) {
              rankBadgeClass = 'bg-gradient-to-r from-amber-400 to-amber-500 text-amber-950 font-black shadow-sm shadow-amber-400/50 ring-1 ring-amber-300';
            } else if (item.rank === 2) {
              rankBadgeClass = 'bg-gradient-to-r from-slate-200 to-slate-300 text-slate-900 font-black shadow-sm ring-1 ring-slate-300';
            } else if (item.rank === 3) {
              rankBadgeClass = 'bg-gradient-to-r from-amber-700 to-amber-800 text-amber-100 font-black shadow-sm ring-1 ring-amber-600';
            } else if (item.rank <= 10) {
              rankBadgeClass = 'bg-indigo-500/10 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 border border-indigo-500/30';
            }
            const badgeRow = badgeText ? `
              <div class="flex items-center pl-7 min-w-0">
                <span class="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-800 dark:text-amber-300 font-medium truncate max-w-full border border-amber-500/20">${escapeHtml(badgeText)}</span>
              </div>` : '';
            return `
              <div class="flex flex-col gap-1 p-2 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-950/60 dark:hover:bg-slate-900/80 border border-slate-200 dark:border-slate-800 hover:border-amber-500/50 transition-all group">
                <div class="flex items-center justify-between w-full min-w-0 gap-1.5">
                  <div class="flex items-center space-x-2 min-w-0 flex-1">
                    <span class="w-5 h-5 rounded-full ${rankBadgeClass} flex items-center justify-center text-[10px] font-bold font-mono shrink-0">
                      ${item.rank}
                    </span>
                    <span class="font-bold text-xs text-slate-900 dark:text-slate-100 truncate" title="${escapeHtml(item.model)}">${escapeHtml(item.model)}</span>
                    <span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-900 text-slate-600 dark:text-slate-400 font-mono border border-slate-300 dark:border-slate-800 shrink-0 notranslate">${escapeHtml(item.org)}</span>
                  </div>
                  <div class="text-right shrink-0 whitespace-nowrap">
                    <span class="text-xs font-mono font-bold text-amber-600 dark:text-amber-400">${item.elo}</span>
                    <span class="text-[9px] text-slate-500 ml-0.5 font-mono">${(item.elo && String(item.elo).includes('%')) ? 'Score' : 'Elo'}</span>
                  </div>
                </div>
                ${badgeRow}
              </div>
            `;
          }).join('');

          const footerNotice = arenaList.length > 0 ? `
            <div class="py-2 text-center border-t border-dashed border-slate-200 dark:border-slate-800/80 mt-1.5">
              <span class="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                ${isZh ? `✓ 全网 LMSYS 官方 Top ${arenaList.length} 强已全量就绪` : `✓ Top ${arenaList.length} Arena Rankings Loaded`}
                <a href="https://arena.ai/leaderboard" target="_blank" rel="noopener noreferrer" class="text-amber-500 hover:underline ml-1 font-semibold">arena.ai ↗</a>
              </span>
            </div>
          ` : '';

          streamArena.innerHTML = arenaCards ? (arenaCards + footerNotice) : `<div class="text-xs text-slate-500 py-2">${t.arenaNoMatch}</div>`;
        }
      } catch (err) {
        console.error('Error rendering stream-arena:', err);
      }

      // 6. 渲染 ArXiv 每日学术突破精选论文 (每日与 arXiv 实时同步)
      try {
        const streamArXiv = document.getElementById('stream-arxiv');
        if (streamArXiv) {
          const arxivList = (data.arxiv_papers || []).slice(0, 6);
          streamArXiv.innerHTML = arxivList.map(item => {
            const paperTitle = isZh ? (item.title_zh || item.title) : (item.title_en || item.title);
            const paperSpec = isZh ? item.spec : (item.spec_en || item.spec);
            const paperDate = isZh ? item.date : (item.date_en || item.date);
            const paperSummary = isZh ? (item.summary_zh || item.summary_en || "") : (item.summary_en || item.summary_zh || "");
            return `
              <a href="${item.url}" target="_blank" class="block p-3 rounded-xl bg-slate-50 hover:bg-slate-100 dark:bg-slate-950/60 dark:hover:bg-slate-900/80 border border-slate-200 dark:border-slate-800 hover:border-purple-500/50 transition-all group space-y-1.5">
                <div class="flex items-center justify-between text-[10px]">
                  <div class="flex items-center space-x-1.5">
                    <span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                    <span class="font-mono text-purple-600 dark:text-purple-400 font-bold">arXiv:${escapeHtml(item.arxiv_id)}</span>
                  </div>
                  <span class="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-700 dark:text-purple-300 border border-purple-500/20 font-mono font-medium">${escapeHtml(paperDate)}</span>
                </div>
                <h5 class="text-xs font-bold text-slate-900 dark:text-slate-100 group-hover:text-purple-600 dark:group-hover:text-purple-300 transition-colors leading-snug line-clamp-2">
                  ${escapeHtml(paperTitle)}
                </h5>
                ${paperSummary ? `<p class="text-[11px] text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed font-normal">${escapeHtml(paperSummary)}</p>` : ''}
                <div class="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 pt-0.5">
                  <span class="font-mono text-[9px] text-slate-500 dark:text-slate-400 truncate max-w-[220px]">⚡ ${escapeHtml(paperSpec)}</span>
                  <span class="text-purple-600 dark:text-purple-400 group-hover:translate-x-0.5 transition-transform shrink-0 font-semibold flex items-center space-x-0.5">
                    <span>${t.readPaper || '精读 →'}</span>
                  </span>
                </div>
              </a>
            `;
          }).join('') || `<div class="text-xs text-slate-500 py-2">${t.arxivNoMatch}</div>`;
        }
      } catch (err) {
        console.error('Error rendering stream-arxiv:', err);
      }

      // 7. 如果当前处于独立分类模式，重新刷新分类网格
      try {
        if (currentTab !== 'all' && currentTab !== 'archive') {
          renderCategoryView(currentTab);
        }
      } catch (err) {
        console.error('Error rendering category-view:', err);
      }
      applyCurrentTranslation();
      setTimeout(syncThreeColumnsHeight, 60);
    }

    // 动态同步“综合全景”核心栏（行业快讯、天梯榜）的等高对齐
    function syncThreeColumnsHeight() {
      // CSS Grid 响应式栅格布局（items-stretch）保障核心栏目自适应等高，彻底消除 JS 重复重排与掉帧
      const colArena = document.getElementById('section-col-arena');
      const colNews = document.getElementById('section-col-news');
      if (colArena && colArena.style.height) colArena.style.height = '';
      if (colNews && colNews.style.height) colNews.style.height = '';
    }

    // 全站高精度多字段多词检索过滤器
    function filterList(list, q = searchQuery) {
      if (!q) return list;
      const terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      return list.filter(item => {
        const tagsStr = Array.isArray(item.tags) ? item.tags.join(' ') : '';
        const specStr = Array.isArray(item.spec_tags) ? item.spec_tags.join(' ') : '';
        const metricsStr = item.metrics ? Object.values(item.metrics).join(' ') : '';
        const text = `${item.title || ''} ${item.title_en || ''} ${item.title_zh || ''} ${item.summary_zh || ''} ${item.summary_en || ''} ${item.content_snippet || ''} ${item.source || ''} ${item.author || ''} ${item.target_model || ''} ${item.recommended_model || ''} ${item.scenario_label || ''} ${item.scenario_tag || ''} ${item.purpose_zh || ''} ${item.purpose_en || ''} ${item.prompt_content_zh || ''} ${item.prompt_content_en || ''} ${tagsStr} ${specStr} ${metricsStr}`.toLowerCase();
        return terms.every(term => text.includes(term));
      });
    }


    // 专栏分页核心状态与交互逻辑 (每页默认 100 条，支持 30 / 50 / 100 自由切换与无缝翻页)
    function changeCategoryPage(p) {
      if (p < 1) return;
      categoryCurrentPage = p;
      renderCategoryView(currentTab);
      const el = document.getElementById('view-category');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function changeCategoryPageSize(sz) {
      const validSizes = [30, 50, 100];
      sz = Number(sz);
      if (!validSizes.includes(sz)) sz = 100;
      categoryPageSize = sz;
      try {
        localStorage.setItem('ainews_cat_page_size', String(sz));
      } catch(e) {}
      categoryCurrentPage = 1;
      renderCategoryView(currentTab);
      const el = document.getElementById('view-category');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function renderCategoryPagination(totalPages, totalItems, curPage, pageSize) {
      const pagination = document.getElementById('cat-pagination-container');
      if (!pagination) return;
      if (!totalItems || totalItems === 0 || (totalPages <= 1 && totalItems <= 30)) {
        pagination.innerHTML = '';
        pagination.classList.add('hidden');
        return;
      }
      pagination.classList.remove('hidden');

      const isZh = currentLang === 'zh';
      const cur = curPage;

      // 生成智能页码序列 (智能省略算法)
      const pageNumbers = [];
      if (totalPages <= 7) {
        for (let i = 1; i <= totalPages; i++) pageNumbers.push(i);
      } else {
        pageNumbers.push(1);
        if (cur > 3) pageNumbers.push('...');
        const start = Math.max(2, cur - 1);
        const end = Math.min(totalPages - 1, cur + 1);
        for (let i = start; i <= end; i++) pageNumbers.push(i);
        if (cur < totalPages - 2) pageNumbers.push('...');
        pageNumbers.push(totalPages);
      }

      const startItem = (cur - 1) * pageSize + 1;
      const endItem = Math.min(cur * pageSize, totalItems);

      const pageSizeOptions = [30, 50, 100];
      const sizeButtonsHtml = pageSizeOptions.map(sz => {
        const isActive = (sz === pageSize);
        const btnCls = isActive
          ? "bg-indigo-600 text-white font-bold shadow-sm shadow-indigo-600/30 border border-indigo-500"
          : "bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 font-semibold shadow-xs";
        return `<button type="button" onclick="changeCategoryPageSize(${sz})" class="px-2.5 py-1 rounded-md text-xs transition-all cursor-pointer ${btnCls}">${sz}</button>`;
      }).join('');

      let html = `
        <div class="flex flex-wrap items-center gap-3">
          <div class="text-xs text-slate-600 dark:text-slate-400 font-mono">
            ${isZh ? `显示第 <strong class="text-slate-900 dark:text-white font-bold">${startItem} - ${endItem}</strong> 条 · 共 <strong class="text-indigo-600 dark:text-indigo-400 font-bold">${totalItems}</strong> 条` : `Showing <strong class="text-slate-900 dark:text-white font-bold">${startItem}-${endItem}</strong> of <strong class="text-indigo-600 dark:text-indigo-400 font-bold">${totalItems}</strong>`}
          </div>
          <div class="flex items-center space-x-1.5 pl-3 border-l border-slate-200 dark:border-slate-800 text-xs">
            <span class="text-slate-700 dark:text-slate-300 font-semibold">${isZh ? '每页显示:' : 'Per page:'}</span>
            <div class="inline-flex p-0.5 rounded-lg bg-slate-200/70 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 space-x-1">
              ${sizeButtonsHtml}
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-1.5">
          <button type="button" onclick="changeCategoryPage(${cur - 1})" ${cur === 1 ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg text-xs font-bold ${cur === 1 ? 'opacity-35 cursor-not-allowed bg-slate-100 dark:bg-slate-800/40 text-slate-400 dark:text-slate-600 border border-slate-200 dark:border-slate-800' : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 hover:bg-indigo-600 hover:text-white border border-slate-300 dark:border-slate-700 cursor-pointer shadow-xs'} transition-all flex items-center space-x-1">
            <span>◀</span>
            <span class="hidden sm:inline">${isZh ? '上一页' : 'Prev'}</span>
          </button>
      `;

      pageNumbers.forEach(p => {
        if (p === '...') {
          html += `<span class="px-2 py-1 text-slate-500 dark:text-slate-400 font-mono text-xs font-bold">...</span>`;
        } else if (p === cur) {
          html += `<button type="button" class="w-8 h-8 rounded-lg text-xs font-bold bg-indigo-600 text-white shadow-sm shadow-indigo-600/30 border border-indigo-500 flex items-center justify-center">${p}</button>`;
        } else {
          html += `<button type="button" onclick="changeCategoryPage(${p})" class="w-8 h-8 rounded-lg text-xs font-bold bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-indigo-600 hover:text-white flex items-center justify-center transition-all cursor-pointer shadow-xs">${p}</button>`;
        }
      });

      html += `
          <button type="button" onclick="changeCategoryPage(${cur + 1})" ${cur === totalPages ? 'disabled' : ''} class="px-3 py-1.5 rounded-lg text-xs font-bold ${cur === totalPages ? 'opacity-35 cursor-not-allowed bg-slate-100 dark:bg-slate-800/40 text-slate-400 dark:text-slate-600 border border-slate-200 dark:border-slate-800' : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 hover:bg-indigo-600 hover:text-white border border-slate-300 dark:border-slate-700 cursor-pointer shadow-xs'} transition-all flex items-center space-x-1">
            <span class="hidden sm:inline">${isZh ? '下一页' : 'Next'}</span>
            <span>▶</span>
          </button>
        </div>
      `;

      pagination.innerHTML = html;
    }

    // 渲染独立专栏广场视图 (带分页控制，默认 100 条/页，支持 30/50/100 自由切换)
    function renderCategoryView(tab) {
      const container = document.getElementById('cat-grid-container');
      const spotlightEl = document.getElementById('celebrity-spotlight-banner');
      const t = I18N[currentLang];
      const isZh = currentLang === 'zh';

      if (!cachedData) {
        if (container) {
          container.className = "w-full";
          container.innerHTML = `
            <div class="py-16 text-center flex flex-col items-center justify-center space-y-3 text-slate-400">
              <div class="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin"></div>
              <p class="text-xs font-mono">${isZh ? '正在从全球雷达实时感知并载入最新前沿动态...' : 'Intercepting live frontier dispatches from global radar...'}</p>
            </div>
          `;
        }
        renderCategoryPagination(0, 0, 1, categoryPageSize);
        return;
      }

      if (tab !== 'celebrity' || socialViewMode === 'viral') {
        if (spotlightEl) {
          spotlightEl.classList.add('hidden');
          spotlightEl.innerHTML = '';
        }
      }

      if (tab === 'news') {
        const fullList = filterList(cachedData.grouped?.news || cachedData.news || cachedData.industry_news || []);
        const totalItems = fullList.length;
        if (totalItems === 0) {
          container.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5";
          container.innerHTML = `<div class="text-slate-500 text-center py-12 col-span-full">${t.newsNoMatch}</div>`;
          renderCategoryPagination(0, 0, 1, categoryPageSize);
        } else {
          const totalPages = Math.ceil(totalItems / categoryPageSize);
          if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
          if (categoryCurrentPage < 1) categoryCurrentPage = 1;
          const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
          const pageItems = fullList.slice(startIndex, startIndex + categoryPageSize);

          container.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5";
          container.innerHTML = pageItems.map(renderNewsCard).join('');
          renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
        }
      } else if (tab === 'celebrity') {
        const catTitle = document.getElementById('cat-view-title');
        const catDesc = document.getElementById('cat-view-desc');
        
        const allCelebRaw = (cachedData.grouped?.celebrity || cachedData.celebrity || cachedData.leader_opinions || (cachedData.items ? cachedData.items.filter(it => it.category === 'celebrity') : []));
        const allViralRaw = (cachedData.grouped?.viral_posts || cachedData.viral_posts || (cachedData.items ? cachedData.items.filter(it => (it.sub_category === 'viral_post' || (it.category === 'celebrity' && it.is_viral))) : []));

        const leaderCount = allCelebRaw.length;
        const viralCount = allViralRaw.length;
        const bLeader = document.getElementById('badge-count-leader');
        if (bLeader) bLeader.textContent = leaderCount;
        const bViral = document.getElementById('badge-count-viral');
        if (bViral) bViral.textContent = viralCount;

        if (socialViewMode === 'viral') {
          if (spotlightEl) {
            spotlightEl.classList.add('hidden');
            spotlightEl.innerHTML = '';
          }
          if (catTitle) catTitle.textContent = t.viralSectionTitle || (isZh ? '🔥 24小时全网平台爆帖 (𝕏 & Threads)' : '🔥 24h Viral Social Radar (𝕏 & Threads)');
          if (catDesc) catDesc.textContent = t.viralSectionDesc || (isZh ? '实时感知过去 24 小时内阅读量破万、点赞飙升的全球 AI 极客与开发者原生热帖' : 'Real-time radar tracking 10k+ views & surging AI threads across 𝕏 and Threads');

          let viralList = allViralRaw.slice();
          if (viralPlatformFilter !== 'all') {
            if (viralPlatformFilter === 'x' || viralPlatformFilter === 'threads') {
              viralList = viralList.filter(it => it.platform === viralPlatformFilter);
            } else if (viralPlatformFilter === 'surging' || viralPlatformFilter === 'breakthrough' || viralPlatformFilter === 'top_viral') {
              viralList = viralList.filter(it => it.trend_type === viralPlatformFilter);
            }
          }
          if (searchQuery) {
            viralList = filterList(viralList);
          }
          viralList.sort((a, b) => {
            const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
            const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
            return timeB - timeA;
          });

          const totalItems = viralList.length;
          if (totalItems === 0) {
            container.className = "w-full";
            container.innerHTML = `<div class="text-slate-500 text-center py-12">${t.viralNoMatch || '暂无爆帖'}</div>`;
            renderCategoryPagination(0, 0, 1, categoryPageSize);
          } else {
            const totalPages = Math.ceil(totalItems / categoryPageSize);
            if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
            if (categoryCurrentPage < 1) categoryCurrentPage = 1;
            const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
            const pageItems = viralList.slice(startIndex, startIndex + categoryPageSize);

            container.className = "w-full";
            container.innerHTML = renderViralPostsSection(pageItems);
            renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
          }
        } else if (socialViewMode === 'demos') {
          if (spotlightEl) {
            spotlightEl.classList.add('hidden');
            spotlightEl.innerHTML = '';
          }
          if (catTitle) catTitle.textContent = isZh ? '🎬 极客实测 Demo & 深度跑分' : '🎬 Hands-on Lab & Geek Demos';
          if (catDesc) catDesc.textContent = isZh ? '汇聚 48 小时内顶级极客真实敲代码、真机实录、模型跑分与实战工作流' : 'Curated hands-on demos, real-world benchmarks, and developer workflows from the past 48h';

          let demosList = allCelebRaw.concat(allViralRaw).filter(it => {
            if (it.has_video || it.video_url || it.is_hero_demo) return true;
            const txt = `${it.title || ''} ${it.title_zh || ''} ${it.full_text_en || ''} ${it.full_text_zh || ''} ${(it.spec_tags || []).join(' ')}`.toLowerCase();
            return /demo|hands[- ]?on|tested|benchmark|tutorial|workflow|实测|上手|跑分|实操|实录/i.test(txt);
          });
          const seen = new Set();
          demosList = demosList.filter(it => {
            const k = it.id || it.url;
            if (!k || seen.has(k)) return false;
            seen.add(k);
            return true;
          });
          if (searchQuery) {
            demosList = filterList(demosList);
          }
          demosList.sort((a, b) => {
            const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
            const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
            return timeB - timeA;
          });

          const totalItems = demosList.length;
          if (totalItems === 0) {
            container.className = "w-full";
            container.innerHTML = `<div class="text-slate-500 text-center py-12">${isZh ? '暂无实测 Demo' : 'No Hands-on Demos found'}</div>`;
            renderCategoryPagination(0, 0, 1, categoryPageSize);
          } else {
            const totalPages = Math.ceil(totalItems / categoryPageSize);
            if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
            if (categoryCurrentPage < 1) categoryCurrentPage = 1;
            const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
            const pageItems = demosList.slice(startIndex, startIndex + categoryPageSize);

            container.className = "w-full";
            container.innerHTML = renderCelebrityTimeline(pageItems);
            renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
          }
        } else {
          if (spotlightEl) {
            spotlightEl.classList.add('hidden');
            spotlightEl.innerHTML = '';
          }
          if (catTitle) catTitle.textContent = t.tabs.celebrity;
          if (catDesc) catDesc.textContent = isZh ? '实时捕捉全球 AI 顶尖实验室、核心架构师与先锋开发者的原生发声与前沿动态' : 'Real-time timeline tracking statements from AI labs and frontier creators';

          let list = filterList(allCelebRaw);

          if (socialPlatformFilter === 'company') {
            const coList = list.filter(isCompanyOrBrand);
            list = coList.length > 0 ? coList : allCelebRaw.filter(isCompanyOrBrand).slice(0, 20);
          } else if (socialPlatformFilter === 'person') {
            const peList = list.filter(it => !isCompanyOrBrand(it));
            list = peList.length > 0 ? peList : allCelebRaw.filter(it => !isCompanyOrBrand(it)).slice(0, 20);
          }
          list.sort((a, b) => {
            const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
            const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
            return timeB - timeA;
          });

          const totalItems = list.length;
          if (totalItems === 0) {
            container.className = "w-full";
            container.innerHTML = `<div class="text-slate-500 text-center py-12">${t.celebrityNoMatch || '暂无动态'}</div>`;
            renderCategoryPagination(0, 0, 1, categoryPageSize);
          } else {
            const totalPages = Math.ceil(totalItems / categoryPageSize);
            if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
            if (categoryCurrentPage < 1) categoryCurrentPage = 1;
            const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
            const pageItems = list.slice(startIndex, startIndex + categoryPageSize);

            container.className = "w-full";
            container.innerHTML = renderCelebrityTimeline(pageItems);
            renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
          }
        }
      } else if (tab === 'tools') {
        const getToolOrigin = (it) => {
          if (it.tool_origin) return it.tool_origin;
          const u = String(it.official_url || it.url || '').toLowerCase();
          const su = String(it.source_url || '').toLowerCase();
          if (u.includes('github.com') || su.includes('github.com')) return 'github';
          if (u.includes('huggingface.co/spaces') || su.includes('huggingface.co/spaces')) return 'huggingface';
          return 'web';
        };
        const HOUSEHOLD_LEGACY_TOOLS = new Set([
          'cursor', 'bolt.new', 'bolt', 'claude code', 'claude-code',
          'ollama', 'perplexity', 'lm studio', 'lmstudio', 'whisper',
          'whisper webgpu', 'vllm', 'comfyui', 'dify', 'n8n', 'gamma',
          'excalidraw', 'open-webui', 'openwebui', 'jan', 'kokoro',
          'liveportrait', 'mineru', 'aider', 'openhands', 'tripo3d', 'triposr'
        ]);

        let list = dedupToolItems(filterList(cachedData.grouped?.tools || cachedData.tools || cachedData.applied_tools || [])).filter(it => {
          const nm = (it.app_name || '').toLowerCase().trim();
          const id = (it.id || '').toLowerCase().trim();
          if (HOUSEHOLD_LEGACY_TOOLS.has(nm) || id.startsWith('tool-') || it.is_curated_base) return false;
          if (getToolOrigin(it) === 'github') {
            const s = Number(it.stars) || (it.metrics ? Number(it.metrics.stars) || 0 : 0);
            const ws = Number(it.weekly_stars) || (it.metrics ? Number(it.metrics.weekly_stars) || 0 : 0);
            if (s > 0 && s < 200 && ws < 200) return false;
          }
          return true;
        });

        if (toolOriginFilter === 'web') {
          list = list.filter(it => getToolOrigin(it) === 'web');
        } else if (toolOriginFilter === 'demo') {
          list = list.filter(it => it.has_live_demo || getToolOrigin(it) === 'web' || getToolOrigin(it) === 'huggingface' || (it.demo_url && it.demo_url.length > 5));
        } else if (toolOriginFilter === 'github') {
          list = list.filter(it => getToolOrigin(it) === 'github');
        } else if (toolOriginFilter === 'huggingface') {
          list = list.filter(it => getToolOrigin(it) === 'huggingface');
        }

        const getToolTime = (it) => {
          const t = it.raw_published_at || it.processed_at || it.published_at || it.crawled_at;
          if (!t) return 0;
          const d = new Date(t).getTime();
          return isNaN(d) ? 0 : d;
        };

        if (toolOriginFilter === 'surge') {
          list.sort((a, b) => {
            const wkB = Number(b.weekly_stars) || (b.metrics ? Number(b.metrics.weekly_stars) || 0 : 0);
            const wkA = Number(a.weekly_stars) || (a.metrics ? Number(a.metrics.weekly_stars) || 0 : 0);
            if (wkB !== wkA) return wkB - wkA;
            const stB = Number(b.stars) || (b.metrics ? Number(b.metrics.stars) || 0 : 0);
            const stA = Number(a.stars) || (a.metrics ? Number(a.metrics.stars) || 0 : 0);
            if (stB !== stA) return stB - stA;
            const tB = getToolTime(b);
            const tA = getToolTime(a);
            return tB - tA;
          });
        } else {
          list.sort((a, b) => {
            const tB = getToolTime(b);
            const tA = getToolTime(a);
            if (tB !== tA) return tB - tA;
            const wkB = Number(b.weekly_stars) || (b.metrics ? Number(b.metrics.weekly_stars) || 0 : 0);
            const wkA = Number(a.weekly_stars) || (a.metrics ? Number(a.metrics.weekly_stars) || 0 : 0);
            if (wkB !== wkA) return wkB - wkA;
            const utB = Number(b.utility_score) || 80;
            const utA = Number(a.utility_score) || 80;
            if (utB !== utA) return utB - utA;
            const stB = Number(b.stars) || (b.metrics ? Number(b.metrics.stars) || 0 : 0);
            const stA = Number(a.stars) || (a.metrics ? Number(a.metrics.stars) || 0 : 0);
            return stB - stA;
          });
        }
        updateToolScenarioCounts(list);
        if (toolScenarioFilter && toolScenarioFilter !== 'all') {
          list = list.filter(it => normalizeToolScenarioKey(it.scenario_key || it.scenario_tag || '') === toolScenarioFilter);
        }

        const totalItems = list.length;
        if (totalItems === 0) {
          container.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5";
          container.innerHTML = `<div class="text-slate-500 text-center py-12 col-span-full">${t.toolsNoMatch}</div>`;
          renderCategoryPagination(0, 0, 1, categoryPageSize);
        } else {
          const totalPages = Math.ceil(totalItems / categoryPageSize);
          if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
          if (categoryCurrentPage < 1) categoryCurrentPage = 1;
          const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
          const pageItems = list.slice(startIndex, startIndex + categoryPageSize);

          container.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5";
          container.innerHTML = pageItems.map(renderToolCard).join('');
          renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
        }
      } else if (tab === 'videos') {
        let rawList = (cachedData.grouped?.videos || cachedData.videos || []).filter(it => !it.is_prompt);
        let allRankedList = dedupVideoItems(filterList(rawList));

        const isYtItem = it => (it.platform === 'youtube' || it.platform === 'shorts' || (it.url && (it.url.includes('youtube.com') || it.url.includes('youtu.be'))) || (it.embed_url && it.embed_url.includes('youtube')) || (it.platform !== 'tiktok' && !(it.url && it.url.includes('tiktok.com'))));
        const isVerticalItem = it => (it.aspect_ratio === '9:16' || it.platform === 'tiktok' || it.platform === 'shorts' || (it.url && it.url.includes('tiktok.com')));
        const isYtLongItem = it => isYtItem(it) && !isVerticalItem(it);
        const isYtShortItem = it => isYtItem(it) && isVerticalItem(it);
        const isTtItem = it => (it.platform === 'tiktok' || (it.url && it.url.includes('tiktok.com')));

        let list = allRankedList;
        if (videoPlatformFilter === 'youtube') {
          list = list.filter(isYtItem);
        } else if (videoPlatformFilter === 'youtube-long') {
          list = list.filter(isYtLongItem);
        } else if (videoPlatformFilter === 'youtube-shorts') {
          list = list.filter(isYtShortItem);
        } else if (videoPlatformFilter === 'tiktok') {
          list = list.filter(isTtItem);
        }

        if (videoSubFilter && videoSubFilter !== 'all') {
          if (videoSubFilter === 'viral') {
            list = list.filter(it => it.is_viral || it.sub_type === 'viral' || (it.tags && it.tags.some(t => t.includes('爆点') || t.includes('爆款') || t.includes('飙升'))));
          } else {
            list = list.filter(it => (it.sub_type || getVideoSubType(it)) === videoSubFilter);
          }
        }
        if (selectedCreator) {
          list = list.filter(it => it.author === selectedCreator);
        }

        const totalItems = list.length;
        if (totalItems === 0) {
          container.className = "w-full";
          container.innerHTML = `<div class="text-slate-500 text-center py-12">${t.videosNoMatch}</div>`;
          renderCategoryPagination(0, 0, 1, categoryPageSize);
        } else {
          const totalPages = Math.ceil(totalItems / categoryPageSize);
          if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
          if (categoryCurrentPage < 1) categoryCurrentPage = 1;
          const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
          const pageItems = list.slice(startIndex, startIndex + categoryPageSize);

          if (videoPlatformFilter === 'youtube-shorts' || videoPlatformFilter === 'tiktok') {
            container.className = "space-y-3";
            container.innerHTML = `
              <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                ${pageItems.map(renderVerticalVideoCard).join('')}
              </div>
            `;
          } else if (videoPlatformFilter === 'youtube-long') {
            container.className = "space-y-3";
            container.innerHTML = `
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                ${pageItems.map(renderHorizontalVideoCard).join('')}
              </div>
            `;
          } else {
            container.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5";
            container.innerHTML = pageItems.map(it => isVerticalItem(it) ? renderVerticalVideoCard(it) : renderHorizontalVideoCard(it)).join('');
          }
          renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
        }
      } else if (tab === 'prompts') {
        let rawList = cachedData.grouped?.prompts || cachedData.prompts || (cachedData.grouped?.videos || cachedData.videos || []).filter(it => it.is_prompt);

        if (promptSubmodeFilter === 'workflow') {
          rawList = rawList.filter(it => it.is_workflow || it.sub_type === 'workflow');
        } else if (promptSubmodeFilter === 'prompt') {
          rawList = rawList.filter(it => !it.is_workflow && it.sub_type !== 'workflow');
        }

        if (promptGenerationFilter === 'sota') {
          rawList = rawList.filter(it => it.generation_tier !== 'legacy');
        } else if (promptGenerationFilter === 'legacy') {
          rawList = rawList.filter(it => it.generation_tier === 'legacy');
        }

        if (promptCategoryFilter && promptCategoryFilter !== 'all') {
          rawList = rawList.filter(it => {
            if (it.category === promptCategoryFilter) return true;
            if (it.sub_type === promptCategoryFilter) return true;
            if (it.scenario_key === promptCategoryFilter) return true;
            if (promptCategoryFilter === 'code') {
              return it.category === 'code' || it.sub_type === 'coding' || it.model_family === 'coding' || (it.scenario_label && it.scenario_label.includes('编程')) || (it.title_zh && (it.title_zh.includes('代码') || it.title_zh.includes('重构') || it.title_zh.includes('开发') || it.title_zh.includes('cursor') || it.title_zh.includes('rules'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('code') || tg.toLowerCase().includes('coding')));
            }
            if (promptCategoryFilter === 'novel') {
              return it.category === 'novel' || (it.scenario_label && it.scenario_label.includes('短剧')) || (it.title_zh && (it.title_zh.includes('短剧') || it.title_zh.includes('小说') || it.title_zh.includes('剧本') || it.title_zh.includes('创作'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('writing') || tg.toLowerCase().includes('story')));
            }
            if (promptCategoryFilter === 'analysis') {
              return it.category === 'analysis' || (it.scenario_label && it.scenario_label.includes('分析')) || (it.title_zh && (it.title_zh.includes('分析') || it.title_zh.includes('Excel') || it.title_zh.includes('指标') || it.title_zh.includes('推理'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('reasoning') || tg.toLowerCase().includes('analysis')));
            }
            if (promptCategoryFilter === 'report') {
              return it.category === 'report' || (it.scenario_label && it.scenario_label.includes('报告')) || (it.title_zh && (it.title_zh.includes('报告') || it.title_zh.includes('述职') || it.title_zh.includes('总结') || it.title_zh.includes('公关'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('report') || tg.toLowerCase().includes('business')));
            }
            if (promptCategoryFilter === 'travel') {
              return it.category === 'travel' || (it.scenario_label && it.scenario_label.includes('旅行')) || (it.title_zh && (it.title_zh.includes('旅行') || it.title_zh.includes('行程') || it.title_zh.includes('攻略'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('travel')));
            }
            if (promptCategoryFilter === 'image') {
              return it.category === 'image' || it.sample_output?.type === 'image' || (it.scenario_label && it.scenario_label.includes('生图')) || (it.title_zh && (it.title_zh.includes('生图') || it.title_zh.includes('Flux') || it.title_zh.includes('Midjourney') || it.title_zh.includes('绘画'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('image') || tg.toLowerCase().includes('midjourney') || tg.toLowerCase().includes('flux')));
            }
            if (promptCategoryFilter === 'video') {
              return it.category === 'video' || it.sample_output?.type === 'video' || (it.scenario_label && it.scenario_label.includes('视效')) || (it.title_zh && (it.title_zh.includes('视频') || it.title_zh.includes('运镜') || it.title_zh.includes('Wan') || it.title_zh.includes('Sora'))) || (it.tags && it.tags.some(tg => tg.toLowerCase().includes('video') || tg.toLowerCase().includes('sora') || tg.toLowerCase().includes('wan')));
            }
            return (it.model_family === promptCategoryFilter) ||
                   (it.recommended_model && it.recommended_model.toLowerCase().includes(promptCategoryFilter.replace('_', ''))) ||
                   (it.target_model && it.target_model.toLowerCase().includes(promptCategoryFilter.replace('_', ''))) ||
                   (it.id && it.id.toLowerCase().includes(promptCategoryFilter)) ||
                   (it.tags && it.tags.some(tg => tg.toLowerCase().includes(promptCategoryFilter.replace('_', ''))));
          });
        }

        let list = filterList(rawList);
        list.sort((a, b) => {
          const scoreA = Number(a.model_tier_score) || 80;
          const scoreB = Number(b.model_tier_score) || 80;
          if (scoreB !== scoreA) return scoreB - scoreA;
          const timeA = a.raw_published_at ? new Date(a.raw_published_at).getTime() : 0;
          const timeB = b.raw_published_at ? new Date(b.raw_published_at).getTime() : 0;
          return timeB - timeA;
        });

        const totalItems = list.length;
        if (totalItems === 0) {
          container.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5";
          container.innerHTML = `<div class="text-slate-500 text-center py-12 col-span-full text-xs bg-slate-100/50 dark:bg-slate-900/40 rounded-xl border border-slate-200 dark:border-slate-800/80 p-8 space-y-2">
               <p class="text-sm font-semibold text-slate-700 dark:text-slate-300">${isZh ? (promptGenerationFilter === 'legacy' ? '📦 历史模型归档库暂无此类内容' : '💡 该场景下暂无提示词或实战工作流') : 'No matching prompts or workflows'}</p>
               <p class="text-slate-400 text-xs">${isZh ? '可切换上方“内容类型”或选择“全部场景”查阅更多' : 'Try switching content type or selecting all scenarios'}</p>
             </div>`;
          renderCategoryPagination(0, 0, 1, categoryPageSize);
        } else {
          const totalPages = Math.ceil(totalItems / categoryPageSize);
          if (categoryCurrentPage > totalPages) categoryCurrentPage = totalPages;
          if (categoryCurrentPage < 1) categoryCurrentPage = 1;
          const startIndex = (categoryCurrentPage - 1) * categoryPageSize;
          const pageItems = list.slice(startIndex, startIndex + categoryPageSize);

          container.className = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5";
          container.innerHTML = pageItems.map(it => (it.is_workflow || it.sub_type === 'workflow') ? renderWorkflowCard(it) : renderPromptCard(it)).join('');
          renderCategoryPagination(totalPages, totalItems, categoryCurrentPage, categoryPageSize);
        }
      }
      applyCurrentTranslation();
    }

    // 加载数据 (高性能智能缓存版)
    async function loadNews(isManual = false) {
      const refreshBtn = document.getElementById('refresh-btn-text');
      if (isManual && refreshBtn) refreshBtn.textContent = '...';

      try {
        const fetchUrl = isManual ? `/data/latest_news.json?t=${Date.now()}` : `/data/latest_news.json?t=${Math.floor(Date.now() / 60000)}`;
        const res = await fetch(fetchUrl, {
          cache: isManual ? 'reload' : 'no-cache'
        });
        if (!res.ok) throw new Error("HTTP error " + res.status);
        const data = await res.json();

        // 智能兼容：若服务端精简了 items，动态构建 items 集合，确保向下兼容
        if (data.grouped && !data.items) {
          data.items = [];
          ['news', 'celebrity', 'tools', 'videos', 'prompts'].forEach(k => {
            if (Array.isArray(data.grouped[k])) data.items.push(...data.grouped[k]);
          });
        }

        // 动态载入前沿模型提示词库与工业实战工作流配方库 (Workflows & Prompts Library)
        try {
          const [wfRes, promptRes] = await Promise.all([
            fetch('/data/curated_workflows_library.json', { cache: isManual ? 'reload' : 'no-cache' }).catch(() => null),
            fetch('/data/curated_prompts_library.json', { cache: isManual ? 'reload' : 'no-cache' }).catch(() => null)
          ]);
          let extraPrompts = [];
          if (wfRes && wfRes.ok) {
            const wfData = await wfRes.json();
            if (Array.isArray(wfData)) {
              extraPrompts.push(...wfData.map(w => ({
                ...w,
                is_workflow: true,
                is_prompt: true,
                category: 'prompts',
                sub_type: 'workflow',
                generation_tier: 'sota',
                model_tier_score: 98,
                prompt_content_zh: w.code_snippet,
                prompt_content_en: w.code_snippet,
                prompt_content: w.code_snippet,
                summary_zh: w.takeaway_zh,
                summary_en: w.takeaway_en,
                recommended_model: w.tested_models
              })));
            }
          }
          if (promptRes && promptRes.ok) {
            const promptData = await promptRes.json();
            if (Array.isArray(promptData)) {
              extraPrompts.push(...promptData.map(p => ({ ...p, is_prompt: true, category: 'prompts' })));
            }
          }
          if (extraPrompts.length > 0) {
            const existingPrompts = data.grouped?.prompts || data.prompts || [];
            const extraIds = new Set(extraPrompts.map(p => p.id));
            const mergedPrompts = [
              ...extraPrompts,
              ...existingPrompts.filter(p => !extraIds.has(p.id))
            ];
            if (!data.grouped) data.grouped = {};
            data.grouped.prompts = mergedPrompts;
            data.prompts = mergedPrompts;
          }
        } catch (e) {
          console.warn("curated prompt/workflow library fetch fallback:", e);
        }

        // 性能防护锁：仅当已完成首次渲染且后台轮询版本未变时才跳过
        const isSameUpdate = window._hasInitialRendered && cachedData && cachedData.updated_at && data.updated_at && (cachedData.updated_at === data.updated_at);
        cachedData = data;
        if (isSameUpdate && !isManual) {
          refreshCountdown = 180;
          return;
        }
        window._hasInitialRendered = true;

        // 轻量保存最新更新时间戳，避免将数兆数据序列化进 sessionStorage 导致主线程 GC 挂起与存储超限
        try {
          sessionStorage.setItem('ainews_updated_at', data.updated_at || '');
        } catch (e) {}

        // 核心防打扰：如果当前在视频专区且为定时后台轮询，仅静默更新缓存，绝不粗暴清空 DOM 重绘视频卡片
        if (currentTab === 'videos' && !isManual) {
          refreshCountdown = 180;
          return;
        }

        renderUI(data);
        refreshCountdown = 180;
      } catch (err) {
        console.error("加载数据失败:", err);
      } finally {
        if (refreshBtn) refreshBtn.textContent = I18N[currentLang].refreshBtn;
      }
    }

    // 复制 Prompt 到剪贴板
    function copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        const toast = document.getElementById('copy-toast');
        const toastMsg = document.getElementById('copy-toast-msg');
        toastMsg.textContent = I18N[currentLang].copySuccess;
        toast.classList.remove('translate-y-16', 'opacity-0');
        setTimeout(() => {
          toast.classList.add('translate-y-16', 'opacity-0');
        }, 2200);
      });
    }

    // 视频弹窗操作 (自适应 16:9 横屏与 9:16 竖屏短视频，支持外部直达)
    function openVideoModal(embedUrl, title, platform, directUrl) {
      const modal = document.getElementById('video-modal');
      const dialog = document.getElementById('modal-video-dialog');
      const aspect = document.getElementById('modal-video-aspect');
      const iframe = document.getElementById('modal-video-iframe');
      const titleEl = document.getElementById('modal-video-title');
      const directLink = document.getElementById('modal-video-direct-link');
      const fallbackBtn = document.getElementById('modal-video-fallback-btn');

      if (!embedUrl) return;

      const isVertical = platform === 'tiktok' || platform === 'shorts' || embedUrl.includes('tiktok.com') || embedUrl.includes('/shorts/');

      if (isVertical) {
        if (dialog) dialog.className = "bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden max-w-sm w-full shadow-2xl relative transition-all duration-200";
        if (aspect) aspect.className = "relative w-full aspect-[9/16] bg-black flex items-center justify-center";
      } else {
        if (dialog) dialog.className = "bg-slate-900 border border-slate-700 rounded-2xl overflow-hidden max-w-3xl w-full shadow-2xl relative transition-all duration-200";
        if (aspect) aspect.className = "relative w-full aspect-video bg-black flex items-center justify-center";
      }

      const autoplayUrl = embedUrl.includes('youtube') 
        ? embedUrl + (embedUrl.includes('?') ? '&autoplay=1' : '?autoplay=1')
        : embedUrl;
      iframe.src = autoplayUrl;

      if (titleEl) titleEl.textContent = title || I18N[currentLang].modalVideoTitle;
      const jumpUrl = directUrl || embedUrl;
      if (directLink) directLink.href = jumpUrl;
      if (fallbackBtn) fallbackBtn.href = jumpUrl;

      modal.classList.remove('hidden');
    }

    function closeVideoModal() {
      const modal = document.getElementById('video-modal');
      const iframe = document.getElementById('modal-video-iframe');
      if (iframe) iframe.src = "";
      if (modal) modal.classList.add('hidden');
    }

    // ==========================================
    // 专访与深度长文富文本排版引擎 (Rich Interview & Article Formatter)
    // ==========================================
    function formatRichArticleContent(rawText, isZh) {
      if (!rawText || typeof rawText !== 'string') return '';
      const rawParas = rawText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 25);
      if (rawParas.length === 0) return `<p class="leading-relaxed text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-normal">${escapeHtml(rawText)}</p>`;

      const renderPara = (p) => {
        const clean = p.replace(/^&[a-z]+;\s*/i, '').trim();
        // 1. 识别记者/采访提问 (Q: / 问: / 简短问句且包含问号)
        const isQ = clean.startsWith('Q:') || clean.startsWith('问：') || clean.startsWith('问:') || 
                    (clean.endsWith('?') && clean.length < 260) || (clean.endsWith('？') && clean.length < 260) ||
                    (/^([A-Z][a-zA-Z\s]+[：:])/.test(clean) && clean.length < 260 && (clean.includes('?') || clean.includes('？')));

        if (isQ) {
          const qText = clean.replace(/^(?:Q:?|问[：:])\s*/i, '');
          return `
            <div class="my-2.5 p-3 rounded-xl bg-indigo-50/90 dark:bg-indigo-950/50 border-l-4 border-indigo-500 font-semibold text-slate-900 dark:text-slate-100 text-xs sm:text-sm shadow-sm flex items-start gap-2.5">
              <span class="text-indigo-600 dark:text-indigo-400 font-bold shrink-0">💬 ${isZh ? '提问' : 'Q'}:</span>
              <span class="flex-1 leading-relaxed">${escapeHtml(qText)}</span>
            </div>
          `;
        }

        // 2. 识别受访领袖发言 (如 Altman: / Sam: / 奥特曼:)
        if (/^(?:Altman|Sam|奥特曼|山姆)[：:]/i.test(clean)) {
          const aText = clean.replace(/^(?:Altman|Sam|奥特曼|山姆)[：:]\s*/i, '');
          return `
            <div class="my-2 pl-3.5 py-2 text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed border-l-2 border-emerald-500/80 bg-emerald-50/40 dark:bg-emerald-950/30 rounded-r-xl p-3 space-y-1">
              <div class="font-bold text-[11px] text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                <span>🎙️</span>
                <span>山姆·奥特曼 (Sam Altman)</span>
              </div>
              <p class="leading-relaxed font-normal">${escapeHtml(aText)}</p>
            </div>
          `;
        }

        // 3. 常规段落与报道叙述
        return `
          <p class="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-normal">${escapeHtml(clean)}</p>
        `;
      };

      if (rawParas.length <= 6) {
        return `<div class="space-y-3">${rawParas.map(renderPara).join('')}</div>`;
      }

      const initialBatch = rawParas.slice(0, 6).map(renderPara).join('');
      const remainingBatch = rawParas.slice(6).map(renderPara).join('');
      const expandId = 'modal-full-article-' + Math.random().toString(36).substring(2, 8);

      return `
        <div class="space-y-3">
          ${initialBatch}
          <div id="${expandId}" class="hidden space-y-3 pt-2 border-t border-dashed border-slate-200 dark:border-slate-800">
            ${remainingBatch}
          </div>
          <button type="button" onclick="const f=document.getElementById('${expandId}'); const b=this; if(f.classList.contains('hidden')){ f.classList.remove('hidden'); b.innerHTML='▲ ${isZh ? '收起部分实录' : 'Collapse Article'}'; } else { f.classList.add('hidden'); b.innerHTML='▼ ${isZh ? `展开阅读完整访谈实录 (共 ${rawParas.length} 段)` : `Expand Full Transcript (${rawParas.length} paragraphs)`}'; }" class="w-full py-2.5 px-4 text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50/70 dark:bg-indigo-950/40 hover:bg-indigo-100/80 dark:hover:bg-indigo-900/60 rounded-xl border border-indigo-200/80 dark:border-indigo-800/80 transition-all flex items-center justify-center gap-1.5 cursor-pointer shadow-sm">
            ▼ ${isZh ? `展开阅读完整访谈实录 (共 ${rawParas.length} 段)` : `Expand Full Transcript (${rawParas.length} paragraphs)`}
          </button>
        </div>
      `;
    }

    // ==========================================
    // 资讯概要简报控制器 (News Briefing & Natural Synthesis)
    // ==========================================
    function openAiNewsModal(newsId) {
      if (!cachedData) return;
      const t = I18N[currentLang] || I18N.zh;
      const isZh = currentLang === 'zh';
      const allNews = [
        ...(cachedData.grouped?.news || []),
        ...(cachedData.news || []),
        ...(cachedData.top_three || []),
        ...(cachedData.grouped?.celebrity || []),
        ...(cachedData.items || []),
        ...(cachedData.industry_news || []),
        ...(cachedData.grouped?.tools || []),
        ...(cachedData.grouped?.videos || []),
        ...(cachedData.grouped?.prompts || [])
      ];

      const matches = allNews.filter(it => String(it.id) === String(newsId));
      let item = matches.find(it => it.image_url && !it.image_url.includes('techmeme.com') && !it.image_url.includes('pml.png')) || matches[0];
      if (!item && String(newsId).startsWith('top_')) {
        const topIdx = parseInt(newsId.replace('top_', ''), 10);
        item = (cachedData.top_three || [])[topIdx];
      }
      if (!item) {
        const urlMatches = allNews.filter(it => (it.url && it.url === newsId) || (it.title && it.title === newsId));
        item = urlMatches.find(it => it.image_url && !it.image_url.includes('techmeme.com') && !it.image_url.includes('pml.png')) || urlMatches[0];
      }
      if (!item) return;

      const analysis = item.ai_analysis || {};
      let rawTitle = '';
      if (isZh) {
        rawTitle = (item.title_zh && /[\u4e00-\u9fa5]/.test(item.title_zh)) ? item.title_zh : (item.title || '资讯概要');
      } else {
        rawTitle = (item.title_en && !/[\u4e00-\u9fa5]/.test(item.title_en)) ? item.title_en : (item.title || 'News Briefing');
        if (/[\u4e00-\u9fa5]/.test(rawTitle) && item.title_en) {
          rawTitle = item.title_en;
        }
      }
      
      // 深度清洗标题杂质 (彻底滤除开头的 "消息来源:" / "Sources:" / "据报道" / 记者署名 / 尾部外媒括号)
      const cleanTitle = rawTitle
        .replace(/^(?:消息来源|消息称|知情人士称|知情人士透露|知情人透露|据知情人士|据知情人|据外媒|据报道|外媒称|外媒报道|传|报道称|Sources?|Report|Reports?|Exclusive|Analysis)[：:，,\s]+/i, '')
        .replace(/消息来源[：:]\s*/g, '')
        .replace(/^[A-Za-z\s.\'\-]+[：:]\s*/, '')
        .replace(/[\(（][^()（）]*?(?:The Information|Forbes|Financial Times|Guardian|Bloomberg|TechCrunch|Reuters|The Verge|FedScoop|Wall Street Journal|New York Times|Wired|Ars Technica|CNBC|Business Insider|金融时报|纽约时报|彭博|路透|福布斯|卫报)[^()（）]*?[\)）][。.\s]*$/i, '')
        .replace(/[\(（]@[A-Za-z0-9_]+[\)）][。.\s]*$/i, '')
        .replace(/[\(（][^()（）]*?\/[^()（）]*?[\)）][。.\s]*$/, '')
        .replace(/[\(（][^()（）]*?(?:译|文|图|编辑)[）\)][。.\s]*$/, '')
        .replace(/([。！？；，、])\1+/g, '$1')
        .trim();

      const source = item.source || (isZh ? '官方快讯' : 'Official News');
      const timeObj = formatTime(item.raw_published_at, currentLang);

      // 1. 核心简报段落 (Briefing / Summary) - 严格语言隔离，严防中英杂交
      let rawBriefing = '';
      if (isZh) {
        // 中文模式：优先使用高品质中文简报与中文摘要，严格过滤纯英文
        const zhCandidates = [
          analysis.briefing_zh,
          item.summary_zh,
          analysis.digest_zh,
          item.content_snippet_zh
        ];
        const validZh = zhCandidates.find(c => c && typeof c === 'string' && /[\u4e00-\u9fa5]/.test(c) && c.trim().length > 10);
        rawBriefing = validZh || cleanTitle;
      } else {
        // 英文模式：严格过滤任何中文字符，优先使用原版英文摘要与原版英文简报
        const enCandidates = [
          analysis.briefing_en,
          analysis.digest_en,
          item.summary_en,
          item.content_snippet,
          item.title_en
        ];
        const validEn = enCandidates.find(c => {
          if (!c || typeof c !== 'string') return false;
          const s = c.trim();
          if (s.length < 10) return false;
          if (/[\u4e00-\u9fa5]/.test(s)) return false; // 严禁含中文字符
          if (s.includes('Executive Briefing: In ') || s.includes('Context: ')) return false; // 严禁残留旧模板
          // 如果是以截断符结尾（如 ... 或 …）且存在完整简报或标题，优先选用完整内容
          if ((s.endsWith('...') || s.endsWith('…')) && (analysis.briefing_en || item.title_en)) return false;
          return true;
        });
        rawBriefing = validEn || cleanTitle;
      }

      // 清洗简报段落杂质，过滤搜索引擎聚合器噪音与机械模板废话，保证自然通畅真实
      let briefingText = String(rawBriefing)
        .replace(/^Executive Briefing:\s*(?:In [^,]+,\s*)?[^:]*advanced a key development:\s*/i, '')
        .replace(/^Executive Briefing:\s*/i, '')
        .replace(/^Context:\s*/i, '')
        .replace(/^(?:消息来源|消息称|知情人士称|知情人士透露|知情人透露|据知情人士|据知情人|据外媒|据报道|外媒称|外媒报道|传|报道称|Sources?|Report|Reports?|Exclusive)[：:，,\s]+/i, '')
        .replace(/消息来源[：:]\s*/g, '')
        .replace(/正式推进关键动向[：:]\s*/g, '')
        .replace(/全面的最新新闻报道[，,]?\s*(?:从|由)?\s*(?:Google|谷歌|b谷歌)\s*新闻(?:汇总|聚合)?[^。！]*[。！]?/gi, '')
        .replace(/(?:从|由)\s*(?:世界各地的|Google|谷歌|b谷歌)\s*(?:新闻|来源)?[^。！]*?(?:汇总|聚合)[^。！]*?[。！]?/gi, '')
        .replace(/Comprehensive up-to-date news coverage, aggregated from sources all over the world by Google News\.?/gi, '')
        .replace(/A comprehensive overview of the latest news stories from around the world aggregated from Google News sources\.?/gi, '')
        .replace(/aggregated from sources all over the world by Google News/gi, '')
        .replace(/行业核心力量围绕[“\"'][^”\"']*?[”\"']加速推进关键技术攻坚与工程落地[，,]?力求在激烈的产业竞赛中确立先发优势[。！]?/g, '')
        .replace(/[\(（][^()（）]*?(?:The Information|Forbes|Financial Times|Guardian|Bloomberg|TechCrunch|Reuters|The Verge|FedScoop|Wall Street Journal|New York Times|Wired|Ars Technica|CNBC|Business Insider|金融时报|纽约时报|彭博|路透|福布斯|卫报)[^()（）]*?[\)）][。.\s]*$/i, '')
        .replace(/[\(（]@[A-Za-z0-9_]+[\)）][。.\s]*$/i, '')
        .replace(/[\(（][^()（）]*?\/[^()（）]*?[\)）][。.\s]*$/, '')
        .replace(/([。！？；，、])\1+/g, '$1')
        .trim();

      // 智能补全截断残句：若简报被 RSS 截断且标题具有更丰富事实细节，有机补充完整事实
      if (briefingText.endsWith('...') || briefingText.endsWith('…')) {
        briefingText = briefingText.replace(/[\.\s…]+$/, '.');
        if (cleanTitle && cleanTitle.length > briefingText.length && !cleanTitle.toLowerCase().includes(briefingText.toLowerCase().slice(0, 25))) {
          briefingText += (isZh ? ` 据悉：${cleanTitle}。` : ` Context: ${cleanTitle}.`);
        }
      }

      // 英文模式终极防护：如果处理后的文本仍意外混入了汉字，坚决回退到纯英文标题
      if (!isZh && /[\u4e00-\u9fa5]/.test(briefingText)) {
        briefingText = (item.title_en && !/[\u4e00-\u9fa5]/.test(item.title_en)) ? item.title_en : cleanTitle;
      }

      // 2. AI 点评 (仅当存在高价值针对性深度分析时保留；模板化/对不上/无有效分析时坚决隐藏，杜绝硬套话)
      let insightText = isZh
        ? (analysis.insight_zh || analysis.takeaway_zh || item.ai_hot_take_zh || item.insight_zh || '')
        : (analysis.insight_en || analysis.takeaway_en || item.ai_hot_take_en || item.insight_en || '');

      // 过滤前缀标签
      let cleanInsight = String(insightText || '')
        .replace(/^(?:【(?:AI\s*点评|AI点评|AI\s*Hot\s*Take|行业研判|深度洞察|专家点评)】|\[(?:AI\s*Hot\s*Take|AI\s*Commentary|AI\s*Takeaway)\])\s*/i, '')
        .trim();

      // 保证事实简报为主体：若 AI 点评比事实简报还长，且简报偏短，适度精简点评保留核心神评，保持视觉与逻辑平衡
      if (cleanInsight && briefingText && cleanInsight.length > briefingText.length) {
        const sentences = isZh
          ? cleanInsight.split(/(?<=[。！？])/)
          : cleanInsight.split(/(?<=[.!?])\s+/);
        if (sentences.length > 1) {
          cleanInsight = sentences.slice(0, 2).join(isZh ? '' : ' ').trim();
        }
      }

      // 识别是否为低质模版句或对不上的假套话与跨语言污染
      const isGenericTemplate = (text) => {
        if (!text || text.length < 10) return true;
        const s = String(text);
        if (!isZh && /[\u4e00-\u9fa5]/.test(s)) return true; // 英文模式下出现任何汉字直接判定为无效
        if (isZh && !/[\u4e00-\u9fa5]/.test(s)) return true; // 中文模式下纯英文直接判定为无效
        return s.includes('正在加速布局以构筑关键护城河') ||
               s.includes('正在加速技术卡位') ||
               s.includes('经受住效率与成本的双重检验') ||
               s.includes('经受住算力成本与用户留存的双重检验') ||
               s.includes('【行业研判】该动态折射出当前AI产业链') ||
               s.includes('科技圈的公关通稿向来习惯把精打细算') ||
               s.includes('剥开宣传层面的光环') ||
               s.includes('商业世界的法则向来残酷') ||
               s.includes('行业各方正在加速技术卡位') ||
               s.includes('查尔斯国王') ||
               s.includes('聚焦该事件') ||
               s.includes('Reflects the ongoing transition towards sustainable deployment') ||
               s.includes('commercial maturity, and balanced governance') ||
               s.includes('Reflects the transition towards commercial maturity') ||
               s.includes('Executive Briefing:') ||
               s.includes('全球产业与技术前沿一线');
      };

      const hasValidInsight = cleanInsight && !isGenericTemplate(cleanInsight);

      // 写入 DOM 节点 (信源仅在标题栏呈现，正文杜绝冗余；六要素自然融合在正文中，不搞机械卡片)
      const modal = document.getElementById('ai-news-modal');
      const badgeEl = document.getElementById('ai-modal-badge');
      const sourceTagEl = document.getElementById('ai-modal-source-tag');
      const timeTagEl = document.getElementById('ai-modal-time-tag');
      const titleEl = document.getElementById('ai-modal-title');
      const briefingTitleEl = document.getElementById('ai-modal-briefing-title');
      const summaryEl = document.getElementById('ai-modal-summary-text');
      const insightTitleEl = document.getElementById('ai-modal-insight-title');
      const insightEl = document.getElementById('ai-modal-insight-text');
      const sourceBtnEl = document.getElementById('ai-modal-source-btn');
      const sourceBtnTextEl = document.getElementById('ai-modal-source-btn-text');

      // 写入配图 (原文配图优先展示，支持多图缩略条，滤除通用重复占位图与裂图)
      const imageWrapEl = document.getElementById('ai-modal-image-wrap');
      const imageEl = document.getElementById('ai-modal-image');
      const galleryStripEl = document.getElementById('ai-modal-gallery-strip');
      const imgHintEl = document.getElementById('ai-modal-image-hint');

      if (imgHintEl) {
        imgHintEl.textContent = t.aiModalImageHint || (isZh ? '点击查看原图' : 'Click to view full image');
      }

      const allImages = [];
      const primaryImg = item.image_url || item.cover_image || (item.media_assets && item.media_assets.cover_image);
      if (primaryImg && typeof primaryImg === 'string') allImages.push(primaryImg.trim());
      const inlines = item.inline_images || (item.media_assets && item.media_assets.inline_images) || [];
      inlines.forEach(img => {
        if (img && typeof img === 'string' && !allImages.includes(img.trim())) allImages.push(img.trim());
      });

      let validImages = allImages.filter(img => 
        img && typeof img === 'string' &&
        img.trim().length > 12 &&
        !img.includes('pml.png') &&
        !img.includes('techmeme.com/img') &&
        !img.includes('techmeme.com/pml') &&
        !img.includes('techmeme_sq') &&
        !img.includes('pixel') &&
        !img.includes('spacer') &&
        !img.includes('photo-1526374965328') &&
        !img.includes('photo-1485827404703') &&
        !img.includes('photo-1618005182384-a83a8bd57fbe') &&
        !img.includes('photo-1620712943543') &&
        !img.includes('photo-1558494949-ef010cbdcc31') &&
        !img.includes('lh3.googleusercontent.com') &&
        !img.includes('260915_thespark') &&
        !img.includes('6b72d2fb-fbfe-41f2')
      ).map(img => {
        let upgraded = img;
        if (upgraded.includes('i.ytimg.com/vi/') && upgraded.includes('/hqdefault.jpg')) {
          upgraded = upgraded.replace('/hqdefault.jpg', '/maxresdefault.jpg');
        }
        return upgraded;
      });

      if (imageWrapEl && imageEl) {
        if (validImages.length > 0) {
          imageEl.src = validImages[0];
          imageEl.alt = cleanTitle || '资讯原文配图';
          imageWrapEl.classList.remove('hidden');

          if (galleryStripEl) {
            if (validImages.length > 1) {
              galleryStripEl.innerHTML = validImages.map((img) => `
                <button type="button" onclick="document.getElementById('ai-modal-image').src='${img.replace(/'/g, "\\'")}'" class="w-14 h-14 rounded-lg overflow-hidden border-2 border-slate-300 dark:border-slate-700 hover:border-indigo-500 focus:border-indigo-500 shrink-0 bg-slate-900 transition-all opacity-80 hover:opacity-100 cursor-pointer">
                  <img src="${img}" alt="${escapeHtml(cleanTitle)} preview" class="w-full h-full object-cover" onerror="this.parentElement.remove()">
                </button>
              `).join('');
              galleryStripEl.classList.remove('hidden');
            } else {
              galleryStripEl.innerHTML = '';
              galleryStripEl.classList.add('hidden');
            }
          }
        } else {
          imageEl.src = '';
          imageWrapEl.classList.add('hidden');
          if (galleryStripEl) {
            galleryStripEl.innerHTML = '';
            galleryStripEl.classList.add('hidden');
          }
        }
      }

      if (badgeEl) badgeEl.textContent = t.aiModalBadge || (isZh ? '资讯概要' : 'News Briefing');
      if (sourceTagEl) sourceTagEl.textContent = `${t.sourceLabel || '信源:'} ${source}`;
      if (timeTagEl) timeTagEl.textContent = `🕒 ${timeObj.relative || timeObj.display}`;
      if (titleEl) titleEl.textContent = cleanTitle;
      if (briefingTitleEl) briefingTitleEl.textContent = t.aiModalBriefingTitle || (isZh ? '事件脉络速览' : 'Executive News Briefing');
      if (summaryEl) summaryEl.textContent = briefingText;

      // 深度报道长文实录展示控制：严格质量校验，未抓取到实质全文/仅为单句摘要导语时彻底隐藏
      const originalCardEl = document.getElementById('ai-modal-original-card');
      const originalTitleEl = document.getElementById('ai-modal-original-title');
      const originalTextEl = document.getElementById('ai-modal-original-text');
      const origContentEn = String(item.article_content || item.original_content || '').trim();
      const origContentZh = String(item.article_content_zh || '').trim();
      
      // 实质性长文判断函数：排除抓取失败回退的单句导语、短摘要、标题复读或已被速览包含的碎片
      const isSubstantiveCoverage = (text, lang) => {
        if (!text) return false;
        const clean = text.replace(/[\r\n\t]/g, ' ').replace(/\s+/g, ' ').trim();
        const cleanBriefing = (briefingText || '').replace(/[\r\n\t]/g, ' ').replace(/\s+/g, ' ').trim();
        const cleanT = (cleanTitle || '').replace(/[\r\n\t]/g, ' ').replace(/\s+/g, ' ').trim();
        
        // 1. 完全相同或包含关系过滤（避免重复展示相同句子）
        if (clean === cleanBriefing || clean === cleanT) return false;
        if (cleanBriefing && (cleanBriefing.includes(clean) || clean.includes(cleanBriefing))) return false;
        if (cleanT && (cleanT.includes(clean) || clean.includes(cleanT))) return false;

        if (lang === 'zh') {
          const zhCount = (clean.match(/[\u4e00-\u9fa5]/g) || []).length;
          // 中文必须至少 80 个汉字，且汉字占比高于 25%
          if (zhCount < 80 || (zhCount / (clean.length || 1)) < 0.25) return false;
          return true;
        } else {
          // 英文必须至少 220 字符（排除抓不到全文时仅有的一句 RSS Description）
          if (clean.length < 220) return false;
          // 长度若明显少于 AI 概要，绝非深度原文
          if (cleanBriefing && clean.length <= cleanBriefing.length * 0.7 && clean.length < 320) return false;
          // 排除纯中文泄露
          if (/[\u4e00-\u9fa5]/.test(clean)) return false;
          return true;
        }
      };

      const hasValidZh = isSubstantiveCoverage(origContentZh, 'zh');
      const hasValidEn = isSubstantiveCoverage(origContentEn, 'en');

      if (originalCardEl && originalTextEl) {
        if (isZh) {
          if (hasValidZh) {
            originalCardEl.classList.remove('hidden');
            if (originalTitleEl) originalTitleEl.textContent = '深度报道与访谈实录';
            originalTextEl.innerHTML = formatRichArticleContent(origContentZh, true);
          } else if (hasValidEn) {
            // 中文模式下但有实质英文深度长文：以优雅的参考折叠框呈现，绝不破坏中文阅读流与被审核抓取
            originalCardEl.classList.remove('hidden');
            if (originalTitleEl) originalTitleEl.textContent = '📰 英文报道原文精选 (参考)';
            originalTextEl.innerHTML = `
              <details open class="group">
                <summary class="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline select-none py-1 flex items-center justify-between cursor-pointer">
                  <span>📰 权威媒体报道核心实录 (完整段落)</span>
                  <span class="text-slate-400 group-open:rotate-180 transition-transform text-xs">▼</span>
                </summary>
                <div class="mt-2.5 pt-2 border-t border-slate-200 dark:border-slate-800 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-normal whitespace-pre-line space-y-2">
                  ${formatRichArticleContent(origContentEn, false)}
                </div>
              </details>
            `;
          } else {
            originalCardEl.classList.add('hidden');
            originalTextEl.innerHTML = '';
          }
        } else {
          // 英文模式：仅当具备真实英文实质深度长文时展示，未抓到全文时直接隐藏
          if (hasValidEn) {
            originalCardEl.classList.remove('hidden');
            if (originalTitleEl) originalTitleEl.textContent = 'Original Coverage & In-depth Story';
            originalTextEl.innerHTML = formatRichArticleContent(origContentEn, false);
          } else {
            originalCardEl.classList.add('hidden');
            originalTextEl.innerHTML = '';
          }
        }
      }

      // AI 点评展示控制：若缺乏针对性有效点评或命中假套话，则直接隐藏该区域
      const insightCardEl = document.getElementById('ai-modal-insight-card');
      if (insightCardEl) {
        if (hasValidInsight) {
          insightCardEl.classList.remove('hidden');
          if (insightTitleEl) insightTitleEl.textContent = t.aiModalInsightTitle || (isZh ? 'AI 点评' : 'AI Hot Take');
          if (insightEl) insightEl.textContent = cleanInsight;
        } else {
          insightCardEl.classList.add('hidden');
        }
      }

      // 深度检测是否为顶级硬付费墙媒体 (The Information, Bloomberg, WSJ, FT, etc.)
      const isPaywalled = (() => {
        if (item.is_paywalled) return true;
        const s = (source || item.source || '').toLowerCase();
        const u = (item.url || '').toLowerCase();
        const paywallKeywords = ['the information', 'bloomberg', 'wsj', 'wall street journal', 'financial times', 'ft.com', 'theinformation.com', 'bloomberg.com', 'wsj.com'];
        return paywallKeywords.some(k => s.includes(k) || u.includes(k));
      })();

      // 付费墙专属横幅提示控制
      const paywallNoticeEl = document.getElementById('ai-modal-paywall-notice');
      const paywallTextEl = document.getElementById('ai-modal-paywall-text');
      if (paywallNoticeEl && paywallTextEl) {
        if (isPaywalled) {
          paywallNoticeEl.classList.remove('hidden');
          paywallTextEl.textContent = isZh
            ? `本条情报为《${source}》独家付费报道（源站设有硬付费墙，非订阅会员将跳转付费购买页）。AI 资讯雷达已为您提炼并结构化呈现核心内幕事实，站内即可通读。`
            : `Exclusive scoop from ${source} (paywall-protected; direct link requires subscription). AI News Radar has structured and unpacked all core intelligence facts above for seamless reading.`;
        } else {
          paywallNoticeEl.classList.add('hidden');
        }
      }

      if (sourceBtnEl) {
        sourceBtnEl.href = item.url || '#';
      }
      if (sourceBtnTextEl) {
        if (isPaywalled) {
          sourceBtnTextEl.textContent = isZh ? '前往源站 ↗ (需付费订阅)' : 'Read Source ↗ (Paywalled)';
        } else {
          sourceBtnTextEl.textContent = t.aiModalSourceBtn || (isZh ? '阅读原文 / 直达报道' : 'Read Full Story');
        }
      }

      // 现场视频报道提示栏控制
      const videoBadgeEl = document.getElementById('ai-modal-video-badge');
      const videoTextEl = document.getElementById('ai-modal-video-text');
      const videoBtnEl = document.getElementById('ai-modal-video-btn');
      const videoBtnTextEl = document.getElementById('ai-modal-video-btn-text');
      const hasVideo = !!(item.has_video || (item.media_assets && item.media_assets.has_video) || (item.video_url && item.video_url.length > 5));

      if (videoBadgeEl) {
        if (hasVideo) {
          videoBadgeEl.classList.remove('hidden');
          if (videoTextEl) {
            videoTextEl.textContent = isZh ? `原文包含 ${source} 一线现场独家视频报道` : `Original coverage includes live video report from ${source}`;
          }
          if (videoBtnEl) {
            videoBtnEl.href = item.video_url || item.url || '#';
          }
          if (videoBtnTextEl) {
            videoBtnTextEl.textContent = isZh ? '播放视频' : 'Watch Video';
          }
        } else {
          videoBadgeEl.classList.add('hidden');
        }
      }

      if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
      }

      // 如果当前使用了整站实时翻译引擎，主动调用一次动态翻译
      applyCurrentTranslation();
    }

    function closeAiNewsModal() {
      const modal = document.getElementById('ai-news-modal');
      const imageWrapEl = document.getElementById('ai-modal-image-wrap');
      const imageEl = document.getElementById('ai-modal-image');
      const galleryStripEl = document.getElementById('ai-modal-gallery-strip');
      const videoBadgeEl = document.getElementById('ai-modal-video-badge');
      if (imageWrapEl && imageEl) {
        imageEl.src = '';
        imageWrapEl.classList.add('hidden');
        if (galleryStripEl) {
          galleryStripEl.innerHTML = '';
          galleryStripEl.classList.add('hidden');
        }
      }
      if (videoBadgeEl) {
        videoBadgeEl.classList.add('hidden');
      }
      const originalCardEl = document.getElementById('ai-modal-original-card');
      if (originalCardEl) {
        originalCardEl.classList.add('hidden');
      }
      if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
      }
    }

    // ==========================================
    // 24小时全网平台爆帖视图与交互控制器
    // ==========================================
    function switchSocialViewMode(mode) {
      socialViewMode = mode;
      categoryCurrentPage = 1;
      const btnLeader = document.getElementById('btn-social-mode-leader');
      const btnDemos = document.getElementById('btn-social-mode-demos');
      const btnViral = document.getElementById('btn-social-mode-viral');
      const badgeLeader = document.getElementById('badge-count-leader');
      const badgeDemos = document.getElementById('badge-count-demos');
      const badgeViral = document.getElementById('badge-count-viral');
      const celebSubfilter = document.getElementById('celebrity-subfilter');
      const viralSubfilter = document.getElementById('viral-platform-subfilter');

      if (btnLeader) {
        btnLeader.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-all flex items-center space-x-2 whitespace-nowrap shrink-0";
      }
      if (badgeLeader) {
        badgeLeader.className = "px-2 py-0.5 rounded-full text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 font-mono font-bold";
      }
      if (btnDemos) {
        btnDemos.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-all flex items-center space-x-2 whitespace-nowrap shrink-0";
      }
      if (badgeDemos) {
        badgeDemos.className = "px-2 py-0.5 rounded-full text-[11px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 font-mono font-bold";
      }
      if (btnViral) {
        btnViral.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-all flex items-center space-x-2 whitespace-nowrap shrink-0";
      }
      if (badgeViral) {
        badgeViral.className = "px-2 py-0.5 rounded-full text-[11px] bg-rose-500/10 dark:bg-rose-500/20 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-500/30 font-mono font-bold";
      }

      if (mode === 'viral') {
        if (btnViral) {
          btnViral.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 bg-rose-600 text-white shadow-sm shadow-rose-600/30 whitespace-nowrap shrink-0";
        }
        if (badgeViral) {
          badgeViral.className = "px-2 py-0.5 rounded-full text-[11px] bg-white/20 text-white border border-white/30 font-mono font-bold";
        }
        if (celebSubfilter) celebSubfilter.classList.add('hidden');
        if (viralSubfilter) viralSubfilter.classList.remove('hidden');
      } else if (mode === 'demos') {
        if (btnDemos) {
          btnDemos.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 bg-emerald-600 text-white shadow-sm shadow-emerald-600/30 whitespace-nowrap shrink-0";
        }
        if (badgeDemos) {
          badgeDemos.className = "px-2 py-0.5 rounded-full text-[11px] bg-white/20 text-white border border-white/30 font-mono font-bold";
        }
        if (celebSubfilter) celebSubfilter.classList.add('hidden');
        if (viralSubfilter) viralSubfilter.classList.add('hidden');
      } else {
        if (btnLeader) {
          btnLeader.className = "px-4 py-2 rounded-lg text-xs sm:text-sm font-bold transition-all flex items-center space-x-2 bg-sky-600 text-white shadow-sm shadow-sky-600/30 whitespace-nowrap shrink-0";
        }
        if (badgeLeader) {
          badgeLeader.className = "px-2 py-0.5 rounded-full text-[11px] bg-white/20 text-white border border-white/30 font-mono font-bold";
        }
        if (celebSubfilter) celebSubfilter.classList.remove('hidden');
        if (viralSubfilter) viralSubfilter.classList.add('hidden');
      }

      renderCategoryView('celebrity');
    }

    function filterViralPlatform(plat) {
      viralPlatformFilter = plat;
      categoryCurrentPage = 1;
      const buttons = document.querySelectorAll('.viral-filter-btn');
      buttons.forEach(b => {
        b.className = "viral-filter-btn px-2.5 py-1 rounded-lg text-xs font-medium bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all";
      });
      const activeBtn = document.getElementById(`viral-filter-${plat}`);
      if (activeBtn) {
        activeBtn.className = "viral-filter-btn active px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-600 text-white shadow-sm shadow-rose-600/30 transition-all";
      }
      renderCategoryView('celebrity');
    }

    // ==========================================
    // 全网平台爆帖 · 单列原生社交流 (Threads & 𝕏 Native Feed)
    // 告别假推文与404链接，直显真实原帖、配图、AI视频预览与极客终端
    // 单击卡片即时展开完整层级连推 (Thread 1/n, 2/n) 与讨论区，包含嵌入图片
    // ==========================================

    const cardLangState = {};

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    function formatSocialText(text) {
      if (!text) return '';
      const lines = text.split(/\n+/).map(l => l.trim()).filter(Boolean);
      return lines.map(line => {
        let formatted = escapeHtml(line);
        // 高亮 #标签 与 @提及
        formatted = formatted.replace(/#([\w\u4e00-\u9fa5]+)/g, '<span class="text-rose-500 hover:underline cursor-pointer font-medium">#$1</span>');
        formatted = formatted.replace(/@([a-zA-Z0-9_]+)/g, '<span class="text-sky-500 hover:underline cursor-pointer font-medium">@$1</span>');
        return `<p class="leading-relaxed mb-2 text-slate-800 dark:text-slate-100">${formatted}</p>`;
      }).join('');
    }

    function detectSocialMediaType(item) {
      const textLower = ((item.title || '') + ' ' + (item.full_text_en || '') + ' ' + (item.spec_tags || []).join(' ')).toLowerCase();
      if (item.image_url) return 'image';
      if (textLower.includes('seedance') || textLower.includes('dreamina') || textLower.includes('wan 2.1') || textLower.includes('kling') || textLower.includes('fastvideo') || textLower.includes('video') || (item.spec_tags && item.spec_tags.some(t => t.includes('视频')))) {
        return 'video';
      }
      if (textLower.includes('flux') || textLower.includes('midjourney') || textLower.includes('sref') || textLower.includes('comfyui') || textLower.includes('generative ui')) {
        return 'art_prompt';
      }
      if (textLower.includes('vibe coding') || textLower.includes('claude code') || textLower.includes('cursor') || textLower.includes('mcp') || textLower.includes('jarvis') || textLower.includes('mla') || textLower.includes('attention') || textLower.includes('context caching') || textLower.includes('factory')) {
        return 'code_terminal';
      }
      return 'text';
    }

    function renderSocialMediaPreview(item, mediaType, isZh) {
      const itemId = escapeHtml(item.id || item.url || '');
      const textLower = ((item.title || '') + ' ' + (item.full_text_en || '')).toLowerCase();

      if (mediaType === 'image' && item.image_url) {
        return `
          <div class="mt-3.5 rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 shadow-md">
            <img src="${escapeHtml(item.image_url)}" alt="Attached media" class="w-full h-auto max-h-[480px] object-cover hover:scale-[1.01] transition-transform duration-300 cursor-pointer" onclick="openImageLightbox('${escapeHtml(item.image_url)}', event)">
          </div>
        `;
      }

      if (mediaType === 'video') {
        let videoModel = 'Seedance 2.5 电影级原生视频';
        if (textLower.includes('kling') || textLower.includes('可灵')) videoModel = '快手可灵 Kling 3.0 高清实测';
        else if (textLower.includes('wan 2.1') || textLower.includes('通义')) videoModel = '阿里通义 Wan 2.1 4K 生成';
        else if (textLower.includes('hailuo') || textLower.includes('minimax') || textLower.includes('fasth3')) videoModel = 'MiniMax Hailuo / FastVideo 9x 加速';
        else if (textLower.includes('comfyui')) videoModel = 'ComfyUI 广告级产品视频工作流';

        let promptSnippet = '';
        const m = (item.full_text_zh || item.full_text_en || '').match(/Prompt[：:\s]+([^\n]+)/i);
        if (m) {
          promptSnippet = m[1].trim();
        } else if (item.title && (item.title.includes('Seedance') || item.title.includes('Prompt'))) {
          promptSnippet = item.title;
        }

        return `
          <div class="mt-3.5 rounded-2xl overflow-hidden border border-slate-800/80 bg-gradient-to-b from-slate-900 via-slate-950 to-black p-3.5 sm:p-4 relative group shadow-xl">
            <div class="flex items-center justify-between mb-3 text-xs">
              <span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 font-mono text-[11px] font-bold border border-rose-500/30">
                🎬 ${videoModel}
              </span>
              <span class="text-slate-400 font-mono text-[10px] bg-slate-800/70 px-2 py-0.5 rounded-full border border-slate-700/50">4K · 60fps · 电影级运镜</span>
            </div>
            
            <div class="relative w-full aspect-video rounded-xl bg-gradient-to-br from-slate-800/90 via-slate-900 to-black flex flex-col items-center justify-center border border-slate-700/60 overflow-hidden cursor-pointer group-hover:border-rose-500/40 transition-all" onclick="event.stopPropagation(); toggleThreadComments('viral-card-${escapeHtml(itemId)}', '${itemId}')">
              <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(244,63,94,0.18),transparent_70%)]"></div>
              
              <div class="w-14 h-14 rounded-full bg-rose-600/90 hover:bg-rose-500 text-white flex items-center justify-center shadow-lg shadow-rose-600/50 group-hover:scale-110 transition-all z-10">
                <svg class="w-6 h-6 fill-current translate-x-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
              </div>
              <span class="text-xs font-semibold text-slate-200 mt-2.5 z-10 tracking-wide">${isZh ? '点击展开连推 Prompt 与完整演示' : 'Click to preview AI dynamic video stream & thread'}</span>
              
              <div class="absolute bottom-2.5 right-3 text-[10px] font-mono text-slate-300 bg-black/70 px-2.5 py-1 rounded-md backdrop-blur border border-white/10">
                GEN-3 CINEMA · MULTI-SHOT
              </div>
            </div>

            ${promptSnippet ? `
              <div class="mt-3 text-[11px] font-mono text-slate-300 bg-black/50 p-2.5 rounded-xl border border-slate-800 leading-relaxed">
                <span class="text-rose-400 font-bold">✨ Generation Prompt:</span> ${escapeHtml(promptSnippet)}
              </div>
            ` : ''}
          </div>
        `;
      }

      if (mediaType === 'art_prompt') {
        return `
          <div class="mt-3.5 rounded-2xl border border-purple-500/30 bg-gradient-to-br from-purple-950/30 via-slate-900/80 to-slate-950 p-4 shadow-lg">
            <div class="flex items-center justify-between mb-2 text-xs">
              <span class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 font-mono text-[11px] font-bold border border-purple-500/30">
                🎨 Midjourney v7 / FLUX.1 生图工程工作流
              </span>
              <span class="text-purple-400 font-mono text-[10px]">Prompt & Architecture</span>
            </div>
            <div class="text-xs font-mono text-slate-200 bg-black/60 p-3 rounded-xl border border-purple-900/40 leading-relaxed">
              <span class="text-purple-400">/imagine prompt:</span> ${escapeHtml(item.title || '')} <span class="text-slate-400">--v 7.0 --style raw --ar 16:9 --quality 2</span>
            </div>
          </div>
        `;
      }

      if (mediaType === 'code_terminal') {
        let terminalTitle = 'bash - agentic-software-factory';
        let codeSnippet = '';
        if (textLower.includes('vibe coding') || textLower.includes('cursor')) {
          terminalTitle = 'vibe-coding · cursor-composer';
          codeSnippet = `$ cursor --composer "Refactor performance bottlenecks and add integration test coverage"\n✔ Architecture synthesized across repository\n✔ Zero-regression tests passing: 421/421\n🚀 Deployed to production`;
        } else if (textLower.includes('mcp')) {
          terminalTitle = 'mcp-server · legacy-refactor-agent';
          codeSnippet = `[MCP] Connecting to filesystem & postgres servers...\n[Claude 4.6 Thinking] Dissecting monolithic architecture\n✔ Automated test suite executed: 421/421 passing`;
        } else {
          terminalTitle = 'agentic-factory · spec-to-pipeline';
          codeSnippet = `[Spec] Synthesized from architect requirements\n[Agent Swarm] 8 concurrent PR branches generated\n[Sandbox Evals] Fuzzing and load-testing complete. Auto-merged branch #4`;
        }

        return `
          <div class="mt-3.5 rounded-2xl border border-slate-800 bg-slate-950 p-3.5 font-mono text-xs shadow-xl">
            <div class="flex items-center justify-between pb-2 border-b border-slate-800/80 mb-2.5 text-[11px] text-slate-400">
              <div class="flex items-center space-x-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-rose-500/90"></span>
                <span class="w-2.5 h-2.5 rounded-full bg-amber-500/90"></span>
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500/90"></span>
                <span class="ml-2 text-slate-300 font-semibold">${terminalTitle}</span>
              </div>
              <span class="text-[10px] text-slate-500">vibe-coding · terminal</span>
            </div>
            <pre class="text-slate-300 text-[11px] sm:text-xs leading-relaxed overflow-x-auto p-1 font-mono whitespace-pre-wrap">${codeSnippet}</pre>
          </div>
        `;
      }

      return '';
    }

    function renderThreadAndComments(item, cardKey, isZh) {
      const threadReplies = item.thread_replies || [];
      const commentsList = item.comments_list || [];

      let threadHtml = '';
      if (threadReplies.length > 0) {
        threadHtml = `
          <div class="mb-3.5">
            <div class="text-[11px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider font-mono mb-2 flex items-center gap-1.5">
              <span>🧵</span> <span>${isZh ? '作者原帖后续连推与层级回复' : 'Author Continuous Thread Replies'}</span>
            </div>
            <div class="space-y-3 relative pl-3 sm:pl-4 border-l-2 border-rose-300 dark:border-rose-900/60 ml-3 sm:ml-4 my-2">
              ${threadReplies.map((reply, rIdx) => {
                const replyText = isZh ? (reply.content_zh || reply.content_en) : (reply.content_en || reply.content_zh);
                const replyTime = isZh ? (reply.time || '1小时前') : (reply.time_en || '1h ago');
                const replyImg = reply.image_url ? `
                  <div class="mt-2.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 shadow-md">
                    <img src="${escapeHtml(reply.image_url)}" alt="Thread attached image" class="w-full h-auto max-h-[380px] object-cover hover:scale-[1.01] transition-transform cursor-pointer" onclick="event.stopPropagation(); window.open('${escapeHtml(reply.image_url)}', '_blank')">
                  </div>
                ` : '';
                return `
                  <div class="pt-1.5 pb-2">
                    <div class="flex items-center space-x-2 text-xs">
                      <img src="${escapeHtml(reply.author_avatar || item.author_avatar)}" alt="${escapeHtml(reply.author || item.author)} avatar" class="w-6 h-6 rounded-full ring-1 ring-rose-400 object-cover bg-slate-900" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=${escapeHtml(reply.author||'user')}'">
                      <span class="font-bold text-slate-900 dark:text-slate-100 text-xs">${escapeHtml(reply.author || item.author)}</span>
                      <span class="px-1.5 py-0.5 rounded-md bg-rose-500/15 text-rose-600 dark:text-rose-400 font-mono text-[10px] font-bold">作者连推 · ${reply.step || `${rIdx+1}楼`}</span>
                      <span class="text-slate-400 text-[10px] font-mono">${replyTime}</span>
                      ${reply.likes ? `<span class="text-rose-500 text-[10px] font-mono ml-auto">❤️ ${reply.likes}</span>` : ''}
                    </div>
                    <div class="text-[13px] sm:text-[14px] leading-relaxed text-slate-800 dark:text-slate-200 mt-1.5 pl-8 select-text">
                      ${formatSocialText(replyText)}
                      ${replyImg}
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      }

      let commentsHtml = '';
      if (commentsList.length > 0) {
        commentsHtml = `
          <div class="pt-2 border-t border-slate-100 dark:border-slate-800/60">
            <div class="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider font-mono mb-2 flex items-center gap-1.5">
              <span>💬</span> <span>${isZh ? '全网高赞讨论与深度热评' : 'Community Discussion & Hot Takes'}</span>
            </div>
            <div class="space-y-2.5">
              ${commentsList.map(c => {
                const cText = isZh ? (c.content_zh || c.content || c.content_en) : (c.content_en || c.content || c.content_zh);
                const cTime = isZh ? (c.time || '2小时前') : (c.time_en || '2h ago');
                const cImg = c.image_url ? `
                  <div class="mt-2 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 max-w-sm">
                    <img src="${escapeHtml(c.image_url)}" class="w-full h-auto object-cover cursor-pointer" onclick="event.stopPropagation(); window.open('${escapeHtml(c.image_url)}', '_blank')">
                  </div>
                ` : '';
                return `
                  <div class="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/70 border border-slate-200/70 dark:border-slate-800/70 text-xs">
                    <div class="flex items-center justify-between mb-1.5">
                      <div class="flex items-center space-x-2">
                        <img src="${escapeHtml(c.avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=' + (c.author||'user'))}" alt="${escapeHtml(c.author)} avatar" class="w-5 h-5 rounded-full object-cover">
                        <span class="font-bold text-slate-900 dark:text-slate-200">${escapeHtml(c.author)}</span>
                        <span class="text-slate-400 text-[10px] font-mono">${escapeHtml(c.handle || '')}</span>
                      </div>
                      <div class="flex items-center space-x-2 text-[10px] font-mono text-slate-400">
                        <span>${cTime}</span>
                        ${c.likes ? `<span class="text-rose-500 font-semibold">❤️ ${c.likes}</span>` : ''}
                      </div>
                    </div>
                    <div class="text-[12.5px] text-slate-700 dark:text-slate-300 leading-relaxed pl-7 select-text">
                      ${escapeHtml(cText)}
                      ${cImg}
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>
        `;
      } else {
        commentsHtml = `
          <div class="text-center py-3 text-xs text-slate-400 font-mono">
            <span>${isZh ? '点击下方链接直达海外平台参与该推文实时互动' : 'Click the platform link below to view live discussion on X'}</span>
          </div>
        `;
      }

      return `
        <div id="thread-section-${cardKey}" class="hidden mt-3.5 pt-3.5 border-t border-slate-200/80 dark:border-slate-800/80 space-y-3">
          ${threadHtml}
          ${commentsHtml}
          <div class="flex justify-center pt-2">
            <button type="button" onclick="event.stopPropagation(); toggleThreadComments('${cardKey}', '${escapeHtml(item.id||item.url||'')}')" class="text-xs text-slate-400 hover:text-rose-500 font-mono flex items-center gap-1 cursor-pointer py-1 px-3 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <span>▲</span> <span>${isZh ? '收起连推与讨论' : 'Collapse Replies'}</span>
            </button>
          </div>
        </div>
      `;
    }

    function toggleThreadComments(cardKey, itemId) {
      const section = document.getElementById(`thread-section-${cardKey}`);
      const icon = document.getElementById(`toggle-icon-${cardKey}`);
      const label = document.getElementById(`toggle-label-${cardKey}`);
      if (!section) return;

      const isHidden = section.classList.contains('hidden');
      const isZh = currentLang === 'zh';
      if (isHidden) {
        section.classList.remove('hidden');
        if (icon) icon.textContent = '▲';
        if (label) label.textContent = isZh ? '收起连推与讨论' : 'Hide Replies';
      } else {
        section.classList.add('hidden');
        if (icon) icon.textContent = '💬';
        if (label) label.textContent = isZh ? '展开完整连推与评论' : 'Show Thread & Replies';
      }
    }

    function handleCardClick(cardKey, itemId, event) {
      if (event.target.closest('a, button, input, select, textarea, pre, img')) {
        return;
      }
      toggleThreadComments(cardKey, itemId);
    }

    function toggleCardLanguage(cardKey, itemId) {
      const isZhSystem = currentLang === 'zh';
      const currentState = cardLangState[cardKey] || (isZhSystem ? 'zh' : 'en');
      const nextLang = currentState === 'zh' ? 'en' : 'zh';
      cardLangState[cardKey] = nextLang;

      const allItems = [
        ...(cachedData.items || []),
        ...(cachedData.grouped?.viral_posts || cachedData.viral_posts || []),
        ...(cachedData.grouped?.celebrity || cachedData.celebrity || [])
      ];
      const item = allItems.find(it => String(it.id) === String(itemId) || it.url === itemId || it.title === itemId);
      if (!item) return;

      const textContainer = document.getElementById(`post-text-${cardKey}`);
      const langBtn = document.getElementById(`lang-btn-${cardKey}`);

      if (textContainer) {
        const newText = nextLang === 'zh'
          ? (item.full_text_zh || item.title_zh || item.title)
          : (item.full_text_en || item.title_en || item.title);
        textContainer.innerHTML = formatSocialText(newText);
      }

      if (langBtn) {
        langBtn.textContent = nextLang === 'zh'
          ? (isZhSystem ? '查看英文原文' : 'View English Original')
          : (isZhSystem ? '查看中文译文' : 'Translate to Chinese');
      }

      // 同步刷新连推与评论区语言
      const threadSection = document.getElementById(`thread-section-${cardKey}`);
      if (threadSection) {
        const wasVisible = !threadSection.classList.contains('hidden');
        threadSection.outerHTML = renderThreadAndComments(item, cardKey, nextLang === 'zh');
        const newSec = document.getElementById(`thread-section-${cardKey}`);
        if (newSec && wasVisible) {
          newSec.classList.remove('hidden');
        }
      }
    }

    function renderViralPostsSection(list) {
      const isZh = currentLang === 'zh';
      const t = I18N[currentLang];
      // 过滤掉所有已删除或已确认无效的推文
      const liveList = (list || []).filter(it => !it.id.startsWith('viral_x_levelsio') && !it.url.includes('2099981245892182012'));

      if (!liveList || liveList.length === 0) {
        return `
          <div class="text-center py-16 px-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 w-full">
            <span class="text-4xl block mb-2">🔥</span>
            <h3 class="font-bold text-slate-800 dark:text-slate-200 text-sm mb-1">${t.viralNoMatch || '暂无符合条件的平台爆帖'}</h3>
            <p class="text-xs text-slate-500 dark:text-slate-400">${isZh ? '过去 24 小时未探测到该分类下满足爆发指标的 AI 贴文，雷达系统持续嗅探中...' : 'No viral threads detected matching criteria in the past 24 hours.'}</p>
          </div>
        `;
      }

      return `
        <div class="space-y-5">
          <!-- 热门动态顶部热度全景统计横幅：根据各平台受众体量差异化设定指标 -->
          <div class="w-full flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-4 py-3 rounded-2xl bg-gradient-to-r from-rose-500/10 via-amber-500/5 to-transparent border border-rose-500/20 text-xs shadow-sm">
            <div class="flex items-center space-x-2 text-rose-600 dark:text-rose-300 font-medium">
              <span class="text-base">🚀</span>
              <span>${isZh ? `已捕获 <strong>${liveList.length}</strong> 条过去 24h 全网现象级 AI 热门动态 · 100% 真实探针存活保障 · 单击推文直显完整连推与图文回复` : `Tracking <strong>${liveList.length}</strong> verified trending AI threads across 𝕏 & Threads in the last 24h`}</span>
            </div>
            <div class="flex items-center space-x-3 text-slate-500 font-mono text-[11px] shrink-0" title="${isZh ? '针对各平台用户基数差异化设定指标：𝕏 侧重万级阅读与千赞，Threads 侧重高互动度与社区热评' : 'Platform-tailored metrics: 𝕏 for views/likes, Threads for replies/likes'}">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>${isZh ? '𝕏 指标: 浏览>1万/赞>1千 | Threads 指标: 赞>50/热评>20' : '𝕏: Views>10k/Likes>1k | Threads: Likes>50/Replies>20'}</span>
            </div>
          </div>

          <!-- 全宽多列网格流 (自适应 1/2/3 列，无缝铺满宽屏，彻底告别单列狭窄) -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            ${liveList.map((item, idx) => renderViralPostCard(item, idx)).join('')}
          </div>
        </div>
      `;
    }

    function renderViralPostCard(item, index) {
      const isZh = currentLang === 'zh';
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const isThreads = item.platform === 'threads' || (item.url && item.url.includes('threads.net'));
      const itemId = escapeHtml(item.id || item.url || `viral-${index}`);
      const cardKey = `viral-card-${index !== undefined ? index : Math.random().toString(36).slice(2, 7)}`;

      const m = item.metrics || {};
      let views = m.views || '24.5k';
      views = String(views).replace(/[^0-9.kKmM]/g, '') || '24.5k';
      let likes = m.likes || m.upvotes || '1.8k';
      likes = String(likes).replace(/[^0-9.kKmM]/g, '') || '1.8k';
      let comments = m.comments || '240';
      comments = String(comments).replace(/[^0-9.kKmM]/g, '') || '240';
      let retweets = m.retweets || '310';
      retweets = String(retweets).replace(/[^0-9.kKmM]/g, '') || '310';

      const author = escapeHtml(item.author || (isThreads ? (isZh ? 'Threads 极客' : 'Threads Geek') : (isZh ? '𝕏 极客' : '𝕏 Geek')));
      const handle = escapeHtml(item.author_handle || (author ? '@' + author.replace(/[^a-zA-Z0-9_]/g, '') : '@viral'));
      const avatar = escapeHtml(optimizeAvatarUrl(item.author_avatar || `https://unavatar.io/x/${handle.replace('@','')}`, 80));

      const platformBadge = isThreads
        ? `<span class="px-2 py-0.5 rounded-lg bg-purple-500/10 text-purple-800 dark:text-purple-300 border border-purple-500/30 text-[10px] font-bold shrink-0 flex items-center gap-1">${isZh ? '🧵 Threads 热帖' : '🧵 Threads Viral'}</span>`
        : `<span class="px-2 py-0.5 rounded-lg bg-sky-500/10 text-sky-800 dark:text-sky-300 border border-sky-500/30 text-[10px] font-bold shrink-0 flex items-center gap-1">${isZh ? '𝕏 平台爆款' : '𝕏 Viral Hit'}</span>`;

      let surgeText = item.surge_badge || (isZh ? '⚡ 24h 飙升' : '⚡ 24h Surge');
      if (!isZh && item.surge_badge) {
        surgeText = item.surge_badge
          .replace(/飙升/g, 'Surge')
          .replace(/爆款/g, 'Viral')
          .replace(/阅读/g, 'Views');
      }
      const surgeBadge = `<span class="px-2 py-0.5 rounded-lg bg-gradient-to-r from-rose-500/15 to-amber-500/15 text-rose-800 dark:text-rose-300 border border-rose-500/30 text-[10px] font-bold shrink-0 flex items-center gap-1 shadow-sm"><span class="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping"></span>${escapeHtml(surgeText)}</span>`;

      const mediaType = detectSocialMediaType(item);
      const mediaHtml = renderSocialMediaPreview(item, mediaType, isZh);

      const initialText = isZh ? (item.full_text_zh || item.title_zh || item.title) : (item.full_text_en || item.title_en || item.title);
      const formattedBody = formatSocialText(initialText);

      const tags = isZh ? (item.spec_tags || []) : (item.spec_tags_en || item.spec_tags || []);
      const tagsHtml = tags.length > 0
        ? `<div class="flex items-center gap-1.5 flex-wrap pt-2">${tags.map(s => `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800/90 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700/60">#${escapeHtml(s)}</span>`).join('')}</div>`
        : '';

      const threadCommentsHtml = renderThreadAndComments(item, cardKey, isZh);

      return `
        <article id="${cardKey}" class="glass-card rounded-2xl p-4 sm:p-5 border border-slate-200/90 dark:border-slate-800/90 hover:border-rose-400/50 dark:hover:border-rose-500/40 transition-all bg-white/95 dark:bg-slate-900/90 shadow-sm hover:shadow-md cursor-pointer" onclick="handleCardClick('${cardKey}', '${itemId}', event)">
          <!-- 头部：作者信息、发布时间、平台徽章与飙升速度 -->
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center space-x-3 min-w-0">
              <div class="relative shrink-0">
                <img src="${avatar}" alt="${author} avatar" width="40" height="40" class="w-10 h-10 sm:w-11 sm:h-11 rounded-full ring-2 ${isThreads ? 'ring-purple-400/80' : 'ring-sky-400/80'} object-cover shadow-sm bg-slate-900" loading="lazy" decoding="async" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=${author}'">
                <span class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full ${isThreads ? 'bg-purple-600' : 'bg-sky-500'} text-white flex items-center justify-center text-[9px] font-black ring-1 ring-white dark:ring-slate-900 shadow">✓</span>
              </div>
              <div class="min-w-0">
                <div class="flex items-center space-x-1.5 flex-wrap">
                  <a href="${escapeHtml(item.url)}" target="_blank" onclick="event.stopPropagation()" class="font-extrabold text-[14px] sm:text-[15px] text-slate-900 dark:text-slate-100 hover:text-rose-600 dark:hover:text-rose-400 transition-colors notranslate">${author}</a>
                  <span class="text-slate-400 text-xs">·</span>
                  <span class="text-[11px] font-mono text-slate-400 dark:text-slate-500 shrink-0">${timeObj.display || timeObj.relative}</span>
                </div>
                <div class="flex items-center space-x-1.5">
                  <span class="text-slate-500 dark:text-slate-400 text-xs font-mono truncate notranslate">${handle}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center space-x-1.5 shrink-0">
              ${platformBadge}
              ${surgeBadge}
            </div>
          </div>

          <!-- 正文内容：10行以内不折叠直显；>10行超长帖优雅折叠并在阅读时展开 -->
          <div class="mt-3.5 select-text">
            ${(() => {
              const countLines = (str) => (str || '').split('\n').reduce((acc, p) => acc + Math.max(1, Math.ceil(p.trim().length / 55)), 0);
              const isLongPost = countLines(initialText) > 10;
              if (!isLongPost) {
                return `
                  <div id="post-text-${cardKey}" class="text-[14px] sm:text-[15px] leading-relaxed text-slate-800 dark:text-slate-100 font-normal">
                    ${formattedBody}
                  </div>
                  <div class="flex items-center justify-end mt-2 pt-1 border-t border-slate-100/60 dark:border-slate-800/40">
                    <button type="button" onclick="event.stopPropagation(); toggleCardLanguage('${cardKey}', '${itemId}')" class="inline-flex items-center gap-1 text-[11px] font-medium text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 py-1 px-2.5 rounded-lg bg-rose-50/80 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/50 border border-rose-200/60 dark:border-rose-800/60 transition-all cursor-pointer">
                      <span>🌐</span>
                      <span id="lang-btn-${cardKey}">${isZh ? '查看英文原文' : 'Translate to Chinese'}</span>
                    </button>
                  </div>
                `;
              }
              return `
                <div class="relative">
                  <div id="post-text-${cardKey}" class="tweet-content-box text-[14px] sm:text-[15px] leading-relaxed text-slate-800 dark:text-slate-100 font-normal overflow-hidden transition-all duration-300" style="display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 10; max-height: 260px;" data-expanded="false">
                    ${formattedBody}
                  </div>
                  <div class="tweet-fade-overlay absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-white/95 dark:from-slate-900/95 to-transparent pointer-events-none transition-opacity"></div>
                </div>
                <div class="flex items-center justify-between mt-2 pt-1 border-t border-slate-100/60 dark:border-slate-800/40">
                  <button type="button" onclick="event.stopPropagation(); toggleTweetExpand(this)" class="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 dark:text-rose-400 hover:text-rose-700 dark:hover:text-rose-300 py-0.5 px-2.5 rounded-md bg-rose-50 dark:bg-rose-500/10 hover:bg-rose-100 dark:hover:bg-rose-500/20 transition-all border border-rose-200/60 dark:border-rose-500/20 group/exp cursor-pointer">
                    <span>${isZh ? '展开阅读全文' : 'Read full post'}</span>
                    <span class="text-[10px] group-hover/exp:translate-y-0.5 transition-transform">↓</span>
                  </button>
                  <button type="button" onclick="event.stopPropagation(); toggleCardLanguage('${cardKey}', '${itemId}')" class="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-300 py-1 px-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/60 dark:border-slate-700/60 transition-all cursor-pointer">
                    <span>🌐</span>
                    <span id="lang-btn-${cardKey}">${isZh ? '查看英文原文' : 'Translate to Chinese'}</span>
                  </button>
                </div>
              `;
            })()}
          </div>

          <!-- 配图、AI 动态视频流或终端代码直显容器 -->
          ${mediaHtml}

          <!-- 标签体系 -->
          ${tagsHtml}

          <!-- 底部原生社交交互指标与连推直通车 -->
          <div class="flex items-center justify-between pt-3.5 mt-3.5 border-t border-slate-100 dark:border-slate-800/80 text-xs text-slate-500 dark:text-slate-400 font-mono">
            <div class="flex items-center space-x-3 sm:space-x-5 text-[11px]">
              <span class="flex items-center space-x-1 hover:text-sky-500 cursor-pointer transition-colors" onclick="event.stopPropagation(); toggleThreadComments('${cardKey}', '${itemId}')" title="${isZh ? (isThreads ? 'Threads 社区热评 (点击展开)' : '回复讨论 (点击展开)') : 'Replies & Thread'}">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                <span>${comments}</span>
              </span>
              <span class="flex items-center space-x-1 hover:text-emerald-500 transition-colors" title="${isZh ? (isThreads ? 'Threads 转发 / 转帖' : '转推 / 转发') : 'Reposts'}">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                <span>${retweets}</span>
              </span>
              <span class="flex items-center space-x-1 hover:text-rose-500 transition-colors text-rose-500/80" title="${isZh ? (isThreads ? 'Threads 点赞' : '点赞') : 'Likes'}">
                <svg class="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                <span>${likes}</span>
              </span>
              ${!isThreads && views ? `
              <span class="flex items-center space-x-1 hover:text-blue-500 transition-colors" title="${isZh ? '全网阅读浏览' : 'Views'}">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                <span>${views}</span>
              </span>` : ''}
            </div>

            <div class="flex items-center space-x-2">
              <button type="button" onclick="event.stopPropagation(); toggleThreadComments('${cardKey}', '${itemId}')" class="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 text-[11px] font-semibold transition-all flex items-center space-x-1 cursor-pointer">
                <span id="toggle-icon-${cardKey}">💬</span>
                <span id="toggle-label-${cardKey}">${isZh ? '展开完整连推与讨论' : 'Show Thread & Replies'}</span>
              </button>
              <a href="${escapeHtml(item.url)}" target="_blank" onclick="event.stopPropagation()" class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-[11px] font-medium transition-all flex items-center space-x-0.5">
                <span>${isThreads ? (isZh ? 'Threads 原帖' : 'Threads Post') : (isZh ? '𝕏 原文' : '𝕏 Post')}</span>
                <span>↗</span>
              </a>
            </div>
          </div>

          <!-- 单击卡片即时展开：作者后续连推 (1/n, 2/n) 与讨论区 (包含嵌入图片) -->
          ${threadCommentsHtml}
        </article>
      `;
    }

    // ==========================================
    // 领袖观点·社交推文与网友热评弹窗控制器 (Social Post & Netizen Hot Takes)
    // 支持双层架构：Tier 1 核心引言Key Takeaway + Tier 2 完整原帖逐段阅读 (双语动态切换)
    // ==========================================
    let currentSocialModalItem = null;
    let currentSocialModalLang = 'zh';

    function openSocialPostModal(postId) {
      if (!cachedData) return;
      const isZhSystem = currentLang === 'zh';
      const allCelebs = [
        ...(cachedData.items || []).filter(it => it.category === 'celebrity' || it.sub_category === 'viral_post' || it.is_viral),
        ...(cachedData.grouped?.celebrity || cachedData.celebrity || cachedData.leader_opinions || []),
        ...(cachedData.grouped?.viral_posts || cachedData.viral_posts || []),
        ...(cachedData.top_three || [])
      ];

      const item = allCelebs.find(it => String(it.id) === String(postId)) ||
                   allCelebs.find(it => it.url === postId || it.title === postId);
      if (!item) return;

      currentSocialModalItem = item;
      // 随系统语言自适应初始展示语言
      currentSocialModalLang = isZhSystem ? 'zh' : 'en';

      renderSocialModalData();

      const modal = document.getElementById('social-post-modal');
      if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
      }
    }

    function renderSocialModalData() {
      const item = currentSocialModalItem;
      if (!item) return;

      const isZhSystem = currentLang === 'zh';
      const viewingZh = currentSocialModalLang === 'zh';
      const isThreads = item.platform === 'threads' || (item.url && item.url.includes('threads.net'));
      const isX = !isThreads && (item.platform === 'x' || (item.source && item.source.includes('Twitter')) || (item.url && (item.url.includes('x.com') || item.url.includes('twitter.com'))));

      // 1. 头部标识与图标
      const iconWrap = document.getElementById('social-modal-icon-wrap');
      const badgeEl = document.getElementById('social-modal-badge');
      const platTagEl = document.getElementById('social-modal-platform-tag');
      const timeTagEl = document.getElementById('social-modal-time-tag');

      const timeObj = formatTime(item.raw_published_at, currentLang);

      if (isThreads) {
        if (iconWrap) {
          iconWrap.className = "w-9 h-9 rounded-xl bg-purple-500/10 dark:bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-500 text-lg font-bold shrink-0";
          iconWrap.innerHTML = '🧵';
        }
        if (badgeEl) badgeEl.textContent = isZhSystem ? (item.is_viral ? '🧵 Threads 全网 24h 爆款热帖' : '🧵 Threads 前沿动态') : '🧵 Threads Viral Thread';
        if (platTagEl) {
          platTagEl.className = "text-xs font-mono px-2 py-0.5 rounded-md bg-purple-50 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-500/30 font-semibold truncate";
          platTagEl.textContent = isZhSystem ? '🧵 Threads 极客热帖' : '🧵 Threads Hot Thread';
        }
      } else if (isX) {
        if (iconWrap) {
          iconWrap.className = "w-9 h-9 rounded-xl bg-sky-500/10 dark:bg-sky-500/20 border border-sky-500/30 flex items-center justify-center text-sky-500 text-lg font-bold shrink-0";
          iconWrap.innerHTML = '𝕏';
        }
        if (badgeEl) badgeEl.textContent = isZhSystem ? (item.is_viral ? '𝕏 (Twitter) 全网 24h 平台爆款' : '𝕏 (Twitter) 前沿社区动态') : (item.is_viral ? '𝕏 24h Viral Hit' : '𝕏 Frontier Post');
        if (platTagEl) {
          platTagEl.className = "text-xs font-mono px-2 py-0.5 rounded-md bg-sky-50 dark:bg-sky-950/80 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-500/30 font-semibold truncate";
          platTagEl.textContent = isZhSystem ? (item.is_viral ? '𝕏 平台爆款' : '𝕏 社交动态') : '𝕏 Trending';
        }
      } else {
        if (iconWrap) {
          iconWrap.className = "w-9 h-9 rounded-xl bg-orange-500/10 dark:bg-orange-500/20 border border-orange-500/30 flex items-center justify-center text-orange-500 text-lg font-bold shrink-0";
          iconWrap.innerHTML = '🔥';
        }
        if (badgeEl) badgeEl.textContent = isZhSystem ? '全球社交平台 深度热帖' : 'Global Social Hot Thread';
        if (platTagEl) {
          platTagEl.className = "text-xs font-mono px-2 py-0.5 rounded-md bg-orange-50 dark:bg-orange-950/80 text-orange-700 dark:text-orange-300 border border-orange-200 dark:border-orange-500/30 font-semibold truncate";
          platTagEl.textContent = isZhSystem ? '社交深度热议' : 'Social Hot Thread';
        }
      }

      if (timeTagEl) timeTagEl.textContent = `🕒 ${timeObj.display || timeObj.relative}`;

      // 2. 作者身份信息
      const avatarEl = document.getElementById('social-modal-avatar');
      const authorEl = document.getElementById('social-modal-author');
      const handleEl = document.getElementById('social-modal-handle');
      const verifiedEl = document.getElementById('social-modal-verified');
      const specTagsEl = document.getElementById('social-modal-spec-tags');

      if (avatarEl) {
        if (isThreads) {
          avatarEl.src = item.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${encodeURIComponent(item.author || 'Threads')}`;
          avatarEl.onerror = () => { avatarEl.src = 'https://api.dicebear.com/7.x/bottts/svg?seed=Threads'; };
          avatarEl.className = "w-12 h-12 rounded-full border-2 border-purple-400/60 object-cover shrink-0 shadow-md";
        } else if (isX) {
          avatarEl.src = optimizeAvatarUrl(item.author_avatar || `https://unavatar.io/x/${(item.author_handle || 'x').replace('@','')}`, 96);
          avatarEl.onerror = () => { avatarEl.src = 'https://api.dicebear.com/7.x/bottts/svg?seed=VIP'; };
          avatarEl.className = "w-12 h-12 rounded-full border-2 border-sky-400/60 object-cover shrink-0 shadow-md";
        } else {
          avatarEl.src = item.author_avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=VIP';
          avatarEl.className = "w-12 h-12 rounded-full border-2 border-orange-500/60 object-cover shrink-0 shadow-md bg-orange-500/10 p-1";
        }
      }

      if (authorEl) authorEl.textContent = item.author || (isThreads ? 'Threads 开发者' : 'AI 开发者');
      if (handleEl) handleEl.textContent = item.author_handle || (isThreads ? '@threads' : '@x');
      if (verifiedEl) verifiedEl.style.display = (item.metrics?.verified || isX || isThreads) ? 'flex' : 'none';

      if (specTagsEl) {
        if (item.spec_tags && item.spec_tags.length > 0) {
          specTagsEl.innerHTML = item.spec_tags.map(s => `<span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-sky-50 dark:bg-sky-950/70 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-500/30"># ${s}</span>`).join('');
          specTagsEl.classList.remove('hidden');
        } else {
          specTagsEl.classList.add('hidden');
        }
      }

      // 3. Tier 1: 核心引言 / 核心看点 (速读摘要)
      const quoteLabelEl = document.getElementById('social-modal-quote-label');
      const quoteTextEl = document.getElementById('social-modal-quote-text');
      if (quoteLabelEl) {
        quoteLabelEl.textContent = isZhSystem ? '核心引言 · 观点提炼' : 'Executive Quote · Key Takeaway';
      }
      if (quoteTextEl) {
        const quote = isZhSystem
          ? (item.full_text_zh || item.quote_zh || item.title_zh || item.title)
          : (item.full_text_en || item.quote_en || item.title_en || item.title);
        quoteTextEl.textContent = quote;
      }

      // 4. Tier 2: 📜 大V发文原帖正文与双语切换 (100% 忠实，随语言自适应)
      const fullTextTitleEl = document.getElementById('social-modal-fulltext-title');
      const fullTextContentEl = document.getElementById('social-modal-fulltext-content');
      const langBadgeEl = document.getElementById('social-modal-lang-mode-badge');
      const langToggleText = document.getElementById('social-modal-lang-toggle-text');
      const wordCountEl = document.getElementById('social-modal-wordcount');

      if (fullTextTitleEl) {
        if (item.is_viral) {
          fullTextTitleEl.textContent = isZhSystem ? '平台爆款正文原帖' : 'Full Viral Authentic Post';
        } else {
          fullTextTitleEl.textContent = isZhSystem ? '大V发文正文原帖' : 'Full Authentic Post';
        }
      }

      let textToDisplay = '';
      if (viewingZh) {
        textToDisplay = item.full_text_zh || item.summary_zh || item.title_zh || item.title || '';
      } else {
        textToDisplay = item.full_text_en || item.content_snippet || item.title_en || item.title || '';
      }

      if (fullTextContentEl) {
        fullTextContentEl.textContent = textToDisplay;
      }

      // 动态呈现社交原帖的多媒体资产 (原图/相册/视频)
      const mediaContentEl = document.getElementById('social-modal-media-content');
      if (mediaContentEl) {
        const imgUrl = item.image_url || (item.media_urls && item.media_urls[0]) || (item.photos && item.photos[0]);
        const allMediaUrls = item.media_urls || (item.photos ? item.photos : (imgUrl ? [imgUrl] : []));
        const videoSrc = item.video_url;
        const hasVideo = item.has_video || videoSrc || (item.url && item.url.includes('/video/'));

        if (videoSrc) {
          mediaContentEl.innerHTML = `
            <div class="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-black shadow-md mt-3">
              <video src="${escapeHtml(videoSrc)}" controls poster="${imgUrl ? escapeHtml(imgUrl) : ''}" class="w-full max-h-96 object-contain rounded-xl" preload="metadata"></video>
            </div>`;
        } else if (hasVideo && imgUrl) {
          mediaContentEl.innerHTML = `
            <div class="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 relative group/media cursor-pointer shadow-md mt-3" onclick="window.open('${item.url}', '_blank')">
              <img src="${escapeHtml(imgUrl)}" alt="Tweet video" class="w-full max-h-80 object-cover rounded-xl group-hover/media:scale-[1.01] transition-transform duration-300" onerror="this.parentElement.style.display='none'">
              <div class="absolute inset-0 bg-slate-950/40 flex items-center justify-center group-hover/media:bg-slate-950/20 transition-colors">
                <div class="w-14 h-14 rounded-full bg-sky-500/90 text-white flex items-center justify-center shadow-xl group-hover/media:scale-110 transition-transform">
                  <svg class="w-6 h-6 fill-current ml-0.5" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </div>
              </div>
              <div class="absolute bottom-2.5 right-2.5 px-2.5 py-1 rounded-md bg-black/75 backdrop-blur-sm text-xs font-mono text-white flex items-center gap-1.5">
                <span>🎬</span>
                <span>${isZhSystem ? '播放原帖视频 ↗' : 'Play Video on 𝕏 ↗'}</span>
              </div>
            </div>`;
        } else if (allMediaUrls && allMediaUrls.length > 1) {
          mediaContentEl.innerHTML = `
            <div class="grid grid-cols-2 gap-2 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 shadow-md mt-3">
              ${allMediaUrls.slice(0, 4).map(u => `
                <div class="relative overflow-hidden aspect-video bg-slate-900 group/img cursor-pointer" onclick="window.open('${escapeHtml(u)}', '_blank')">
                  <img src="${escapeHtml(u)}" alt="Tweet media" class="w-full h-full object-cover group-hover/img:scale-105 transition-transform duration-300" onerror="this.parentElement.style.display='none'">
                </div>
              `).join('')}
            </div>`;
        } else if (imgUrl) {
          mediaContentEl.innerHTML = `
            <div class="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-900 shadow-md cursor-pointer max-h-96 mt-3" onclick="window.open('${escapeHtml(imgUrl)}', '_blank')">
              <img src="${escapeHtml(imgUrl)}" alt="Tweet media" class="w-full h-full max-h-96 object-cover rounded-xl hover:scale-[1.01] transition-transform duration-300" onerror="this.parentElement.style.display='none'">
            </div>`;
        } else {
          mediaContentEl.innerHTML = '';
        }
      }

      if (langBadgeEl) {
        langBadgeEl.textContent = viewingZh
          ? (isZhSystem ? '中文忠实译文' : 'Chinese Translation')
          : (isZhSystem ? '英文原帖 · 100% 原文' : 'English Original (Verbatim)');
        langBadgeEl.className = viewingZh
          ? "text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/30 font-bold shrink-0"
          : "text-[10px] font-mono px-2 py-0.5 rounded bg-sky-500/15 text-sky-800 dark:text-sky-300 border border-sky-500/30 font-bold shrink-0";
      }

      if (langToggleText) {
        langToggleText.textContent = viewingZh
          ? (isZhSystem ? '切换为英文原帖' : 'View English Original')
          : (isZhSystem ? '切换为中文译文' : 'View Chinese Translation');
      }

      if (wordCountEl) {
        wordCountEl.textContent = viewingZh
          ? `共约 ${textToDisplay.length} 字 · 原篇忠实逐段呈现`
          : `${textToDisplay.split(/\s+/).filter(Boolean).length} words · Verbatim Full Post`;
      }

      // 5. 真实互动指标 (真实性第一：仅展示真实源数据，绝不虚构数字)
      const m = item.metrics || {};
      const viewsEl = document.getElementById('social-modal-views');
      const likesEl = document.getElementById('social-modal-likes');
      const commentsEl = document.getElementById('social-modal-comments-count');
      const retweetsEl = document.getElementById('social-modal-retweets');

      if (viewsEl) viewsEl.textContent = m.views || '-';
      if (likesEl) likesEl.textContent = m.likes || m.upvotes || '-';
      if (commentsEl) commentsEl.textContent = m.comments || '-';
      if (retweetsEl) retweetsEl.textContent = m.retweets || '-';

      // 6. 网友精选神评与社区交锋 (真实性第一：绝不伪造虚假评论，真实引导至 𝕏 原文查看数万条真实热议)
      const commentsContainer = document.getElementById('social-modal-comments-list');
      if (commentsContainer) {
        let commentsList = item.comments_list || [];

        // 如果原帖存在作者连推回复 (Thread 1/n, 2/n)，先在弹窗顶部完整呈现连推与配图
        let modalThreadsHtml = '';
        if (item.thread_replies && item.thread_replies.length > 0) {
          modalThreadsHtml = `
            <div class="mb-4 pb-4 border-b border-slate-200 dark:border-slate-800">
              <div class="text-[11px] font-bold text-rose-600 dark:text-rose-400 uppercase tracking-wider font-mono mb-2.5 flex items-center gap-1.5">
                <span>🧵</span> <span>${viewingZh ? '作者原帖后续连推与层级回复' : 'Author Continuous Thread Replies'}</span>
              </div>
              <div class="space-y-3 pl-3.5 border-l-2 border-rose-300 dark:border-rose-900/60 ml-2">
                ${item.thread_replies.map((reply, rIdx) => {
                  const rText = viewingZh ? (reply.content_zh || reply.content_en) : (reply.content_en || reply.content_zh);
                  const rTime = viewingZh ? (reply.time || '1小时前') : (reply.time_en || '1h ago');
                  const rImg = reply.image_url ? `
                    <div class="mt-2.5 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-slate-950 shadow-md">
                      <img src="${reply.image_url}" alt="Thread image" class="w-full h-auto max-h-[360px] object-cover hover:scale-[1.01] transition-transform cursor-pointer" onclick="window.open('${reply.image_url}', '_blank')">
                    </div>
                  ` : '';
                  return `
                    <div class="pt-1 pb-2">
                      <div class="flex items-center space-x-2 text-xs">
                        <img src="${reply.author_avatar || item.author_avatar}" class="w-6 h-6 rounded-full ring-1 ring-rose-400 object-cover bg-slate-900" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=user'">
                        <span class="font-bold text-slate-900 dark:text-slate-100 text-xs">${reply.author || item.author}</span>
                        <span class="px-1.5 py-0.5 rounded-md bg-rose-500/15 text-rose-600 dark:text-rose-400 font-mono text-[10px] font-bold">连推 · ${reply.step || `${rIdx+1}楼`}</span>
                        <span class="text-slate-400 text-[10px] font-mono">${rTime}</span>
                        ${reply.likes ? `<span class="text-rose-500 text-[10px] font-mono ml-auto">❤️ ${reply.likes}</span>` : ''}
                      </div>
                      <div class="text-[13px] leading-relaxed text-slate-800 dark:text-slate-200 mt-1.5 pl-8 select-text">
                        <p class="mb-1">${rText.replace(/\n/g, '<br>')}</p>
                        ${rImg}
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        }

        const commentsCardsHtml = commentsList.map(c => {
          const cContent = viewingZh ? (c.content_zh || c.content || c.content_en) : (c.content_en || c.content || c.content_zh);
          const cTime = viewingZh ? (c.time || '20分钟前') : (c.time_en || '20m ago');
          const cImg = c.image_url ? `
            <div class="mt-2 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 max-w-sm">
              <img src="${c.image_url}" class="w-full h-auto object-cover cursor-pointer" onclick="window.open('${c.image_url}', '_blank')">
            </div>
          ` : '';
          return `
            <div class="p-3 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800/80 space-y-1.5 transition-all hover:border-slate-300 dark:hover:border-slate-700">
              <div class="flex items-center justify-between gap-2">
                <div class="flex items-center space-x-2 min-w-0">
                  <img src="${c.avatar || 'https://api.dicebear.com/7.x/bottts/svg?seed=user'}" class="w-6 h-6 rounded-full border border-slate-300 dark:border-slate-700 object-cover shrink-0" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=user'">
                  <div class="flex items-center space-x-1.5 min-w-0">
                    <span class="font-bold text-xs text-slate-800 dark:text-slate-200 truncate notranslate">${c.author}</span>
                    <span class="text-[11px] text-slate-400 font-mono truncate notranslate">${c.handle || ''}</span>
                  </div>
                </div>
                <div class="flex items-center space-x-2 text-[10px] text-slate-400 font-mono shrink-0">
                  <span>${cTime}</span>
                  <span class="text-rose-500 font-semibold flex items-center gap-0.5">👍 <span class="notranslate">${c.likes || '1.2k'}</span></span>
                </div>
              </div>
              <div class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pl-8 select-text">
                <p>${cContent}</p>
                ${cImg}
              </div>
            </div>
          `;
        }).join('');

        if (!modalThreadsHtml && !commentsCardsHtml) {
          commentsContainer.innerHTML = `
            <div class="p-4 sm:p-5 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center space-y-2.5">
              <div class="w-9 h-9 mx-auto rounded-full bg-sky-500/10 text-sky-500 flex items-center justify-center text-base">
                💬
              </div>
              <div>
                <h4 class="text-xs sm:text-sm font-bold text-slate-800 dark:text-slate-200">${isZhSystem ? '前往 𝕏 原文查看实时热评与社区交锋' : 'View Real-time Replies & Discussion on 𝕏'}</h4>
                <p class="text-[11px] text-slate-400 mt-1 max-w-md mx-auto leading-relaxed">${isZhSystem ? '本站遵循真实性第一原则，不编造虚假网友评论。请点击下方“直达 𝕏 原推”参与全球开发者实时深度讨论。' : 'We strictly preserve data integrity without synthetic comments. Click below to join the discussion on 𝕏.'}</p>
              </div>
              <div class="pt-1">
                <a href="${item.url}" target="_blank" class="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-600 text-white text-xs font-semibold shadow transition-all">
                  <span>${isZhSystem ? '直达 𝕏 原推实时讨论区' : 'Open 𝕏 Thread'}</span>
                  <span>↗</span>
                </a>
              </div>
            </div>
          `;
        } else {
          commentsContainer.innerHTML = modalThreadsHtml + commentsCardsHtml;
        }
      }

      // 7. AI 独家点评
      const aiWrapEl = document.getElementById('social-modal-ai-insight-wrap');
      const aiTextEl = document.getElementById('social-modal-ai-insight');
      if (aiWrapEl && aiTextEl) {
        const insight = isZhSystem
          ? (item.ai_analysis?.insight_zh || item.ai_analysis?.takeaway_zh)
          : (item.ai_analysis?.takeaway_en || item.ai_analysis?.insight_zh);
        if (insight && !insight.includes('【行业研判】该动态折射出当前AI产业链')) {
          aiTextEl.textContent = insight.replace(/^【.*?】\s*/, '');
          aiWrapEl.classList.remove('hidden');
        } else {
          aiWrapEl.classList.add('hidden');
        }
      }

      // 8. 外部直达链接按钮
      const linkBtn = document.getElementById('social-modal-link-btn');
      const linkText = document.getElementById('social-modal-link-text');
      if (linkBtn) {
        linkBtn.href = item.url || '#';
        if (linkText) {
          if (isThreads) {
            linkText.textContent = isZhSystem ? '直达 Threads 原帖 / 互动' : 'View on Threads / Join Conversation';
          } else if (isX) {
            linkText.textContent = isZhSystem ? '直达 𝕏 原推 / 加入讨论' : 'View on 𝕏 / Join Thread';
          } else {
            linkText.textContent = isZhSystem ? '直达原帖 / 加入讨论' : 'View Original Thread';
          }
        }
      }
    }

    function toggleSocialModalLanguage() {
      currentSocialModalLang = currentSocialModalLang === 'zh' ? 'en' : 'zh';
      renderSocialModalData();
    }

    function closeSocialPostModal() {
      const modal = document.getElementById('social-post-modal');
      if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
      }
      currentSocialModalItem = null;
    }

    // ==========================================
    // 落地工具·抓取情报与交互式预览画廊控制器 (Tool Detail & Screenshot Gallery Modal)
    // ==========================================
    let currentToolModalItem = null;
    let currentToolImages = [];
    let currentToolImageIndex = 0;

    function openToolDetailModal(toolId) {
      if (!cachedData) return;
      const allTools = [
        ...(cachedData.grouped?.tools || cachedData.tools || []),
        ...(cachedData.items || []).filter(it => it.category === 'tools' || it.category === 'applied_tools')
      ];
      const dedupedTools = dedupToolItems(allTools);

      let item = dedupedTools.find(it => String(it.id) === String(toolId)) ||
                 allTools.find(it => String(it.id) === String(toolId)) ||
                 dedupedTools.find(it => it.url === toolId || it.source_url === toolId || it.official_url === toolId || it.title === toolId) ||
                 allTools.find(it => it.url === toolId || it.source_url === toolId || it.official_url === toolId || it.title === toolId);
      if (!item) return;

      // 始终优先选用去重合并后的最优版本（具备真实官网直达链接与完整实测画廊大图）
      const rawTitle = item.app_name || (item.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : '');
      let cleanApp = rawTitle.replace(/^[【\[].*?[】\]]\s*/, '').trim().toLowerCase();
      if (cleanApp.includes('】')) cleanApp = cleanApp.split('】')[0].replace('【', '').trim().toLowerCase();
      if (cleanApp.includes(']')) cleanApp = cleanApp.split(']')[0].replace('[', '').trim().toLowerCase();
      if (cleanApp) {
        const best = dedupedTools.find(it => {
          const r = it.app_name || (it.title ? it.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : '');
          let n = r.replace(/^[【\[].*?[】\]]\s*/, '').trim().toLowerCase();
          if (n.includes('】')) n = n.split('】')[0].replace('【', '').trim().toLowerCase();
          if (n.includes(']')) n = n.split(']')[0].replace('[', '').trim().toLowerCase();
          return n === cleanApp;
        });
        if (best) item = best;
      }

      currentToolModalItem = item;
      const isZh = currentLang === 'zh';
      const timeObj = formatTime(item.raw_published_at, currentLang);
      const iconSvg = getToolSvgIcon(item.icon_type);

      const titleEl = document.getElementById('tool-modal-title');
      const rankBadgeEl = document.getElementById('tool-modal-rank-badge');
      const scenarioEl = document.getElementById('tool-modal-scenario');
      const timeEl = document.getElementById('tool-modal-time');
      const iconWrapEl = document.getElementById('tool-modal-icon-wrap');
      const officialBtnEl = document.getElementById('tool-modal-official-btn');
      const visitTextEl = document.getElementById('tool-modal-visit-text');
      const hookEl = document.getElementById('tool-modal-hook');
      const overviewEl = document.getElementById('tool-modal-overview');
      const featuresListEl = document.getElementById('tool-modal-features-list');

      const pricingEl = document.getElementById('tool-modal-spec-pricing');
      const runtimeEl = document.getElementById('tool-modal-spec-runtime');
      const specScenarioEl = document.getElementById('tool-modal-spec-scenario');
      const specSourceEl = document.getElementById('tool-modal-spec-source');

      const appName = item.app_name || (item.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : 'AI 工具');
      let hook = "";
      let overviewText = "";
      if (isZh) {
        const candSummary = item.summary_zh || item.overview_zh || "";
        const candHook = item.app_hook || "";
        const candTitleZh = item.title_zh || "";
        if (hasChineseText(candHook)) {
          hook = candHook;
          overviewText = candSummary || item.content_snippet || candHook;
        } else if (hasChineseText(candSummary)) {
          hook = candSummary;
          overviewText = hasChineseText(candTitleZh) ? candTitleZh : (candHook || item.content_snippet || candSummary);
        } else if (hasChineseText(candTitleZh)) {
          hook = candTitleZh;
          overviewText = candHook || item.content_snippet || candTitleZh;
        } else {
          hook = candHook || candTitleZh || item.title || "";
          overviewText = candSummary || item.content_snippet || hook;
        }
      } else {
        hook = item.app_hook_en || item.title_en || item.app_hook || item.title || "";
        overviewText = item.overview_en || item.summary_en || item.content_snippet || hook;
      }
      const officialUrl = formatCleanToolUrl(item.official_url || item.url || "#", item);
      const sourceUrl = item.source_url || item.url || "#";
      const sourceName = isZh
        ? (item.source || "AI 资讯雷达")
        : (item.source === "AI 资讯雷达" || !item.source ? "AI News Radar" : item.source.replace("AI 资讯雷达", "AI News Radar"));

      if (titleEl) titleEl.textContent = appName;
      if (rankBadgeEl) {
        let rankText = isZh
          ? (item.growth_badge_zh || item.rank_badge || '🔥 热门推荐')
          : (item.growth_badge_en || item.rank_badge_en || item.rank_badge || '🔥 Popular');
        rankText = String(rankText)
          .replace(/\s*·\s*Product\s*Hunt/gi, '')
          .replace(/Product\s*Hunt\s*热门精选/gi, isZh ? '热门推荐' : 'Popular')
          .replace(/Product\s*Hunt\s*/gi, '')
          .replace(/\s*·\s*GitHub/gi, '')
          .trim();
        if (!rankText || rankText === '🔥') rankText = isZh ? '🔥 热门推荐' : '🔥 Popular';
        if (!isZh) {
          rankText = rankText
            .replace(/热门推荐/g, 'Popular')
            .replace(/编辑精选/g, 'Editor Choice')
            .replace(/开源精选/g, 'Open Source')
            .replace(/开源高星/g, 'Top Stars')
            .replace(/开源新锐/g, 'Rising Open Source')
            .replace(/最新发布/g, 'Fresh Release')
            .replace(/精选/g, 'Featured');
        }
        rankBadgeEl.textContent = rankText;
      }
      if (scenarioEl) scenarioEl.textContent = translateScenarioTag(item.scenario_tag, currentLang);
      if (timeEl) timeEl.textContent = `🕒 ${timeObj.display || timeObj.relative || (isZh ? '今日' : 'Today')}`;
      if (iconWrapEl) {
        if (item.logo_url) {
          iconWrapEl.innerHTML = `<img src="${escapeHtml(item.logo_url)}" alt="${escapeHtml(appName)}" class="w-full h-full object-cover rounded-2xl">`;
        } else {
          iconWrapEl.innerHTML = iconSvg;
        }
      }
      
      if (officialBtnEl) {
        officialBtnEl.href = formatTransitGoUrl(officialUrl, item);
        officialBtnEl.setAttribute('rel', 'nofollow noopener noreferrer');
      }
      const isGhModal = item.tool_origin === 'github' || (item.url && item.url.includes('github.com')) || (item.source_url && item.source_url.includes('github.com'));
      if (visitTextEl) {
        visitTextEl.textContent = isGhModal
          ? (item.has_live_demo ? (isZh ? '🚀 在线体验 / 官网' : '🚀 Live Demo / Site') : (isZh ? '📦 访问开源仓库' : '📦 Visit GitHub Repo'))
          : (isZh ? '🚀 访问官网' : '🚀 Visit Website');
      }
      if (hookEl) hookEl.textContent = hook;

      if (overviewEl) overviewEl.textContent = overviewText;

      const galleryLabelEl = document.getElementById('tool-modal-gallery-label');
      const overviewLabelEl = document.getElementById('tool-modal-overview-label');
      const featuresLabelEl = document.getElementById('tool-modal-features-label');
      if (galleryLabelEl) galleryLabelEl.textContent = isZh ? '实测截图与画廊展示' : 'Product Screenshots & UI Gallery';
      if (overviewLabelEl) overviewLabelEl.textContent = isZh ? '核心亮点与解决痛点' : 'Core Overview & Problem Solved';
      if (featuresLabelEl) featuresLabelEl.textContent = isZh ? '核心功能要点清单' : 'Key Features & Technical Capabilities';

      const features = isZh ? (item.features_zh || []) : (item.features_en || []);
      if (featuresListEl) {
        if (features.length > 0) {
          featuresListEl.innerHTML = features.map(f => `
            <li class="flex items-start space-x-2.5">
              <span class="text-emerald-500 font-bold shrink-0 mt-0.5">✓</span>
              <span class="leading-relaxed">${escapeHtml(f)}</span>
            </li>
          `).join('');
          featuresListEl.parentElement.classList.remove('hidden');
        } else {
          featuresListEl.parentElement.classList.add('hidden');
        }
      }

      if (pricingEl) pricingEl.textContent = translatePricingTag(item.pricing_tag, currentLang);
      if (runtimeEl) runtimeEl.textContent = translateRuntimeBadge(item.runtime_badge, currentLang);
      if (specScenarioEl) specScenarioEl.textContent = translateScenarioTag(item.scenario_tag, currentLang);
      if (specSourceEl) specSourceEl.textContent = sourceName;

      // 轮播画廊设置 (严禁 Gemini 官方宣传物料泄露到其它独立产品)
      const isGeminiItem = (item.app_name || item.title || '').toLowerCase().includes('gemini');
      let galleryImages = (item.preview_images && item.preview_images.length > 0)
        ? [...item.preview_images]
        : (item.image_url ? [item.image_url] : []);
      if (!isGeminiItem) {
        galleryImages = galleryImages.filter(img => !img.includes('3CyW24Pkz4o') && !img.includes('feeb7666'));
      }
      galleryImages = galleryImages.filter(img => !img.includes('photo-1618005182384-a83a8bd57fbe') && !img.includes('microlink.io'));

      currentToolImages = galleryImages;
      currentToolImageIndex = 0;
      updateToolCarousel();

      const modal = document.getElementById('tool-detail-modal');
      if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
      }
    }

    function updateToolCarousel() {
      const imgEl = document.getElementById('tool-carousel-image');
      const counterEl = document.getElementById('tool-carousel-counter');
      const dotsEl = document.getElementById('tool-carousel-dots');
      const prevBtn = document.getElementById('tool-carousel-prev');
      const nextBtn = document.getElementById('tool-carousel-next');
      const container = imgEl ? imgEl.parentElement : null;
      let terminalEl = document.getElementById('tool-modal-terminal-mockup');

      if (!currentToolImages || currentToolImages.length === 0) {
        if (imgEl) imgEl.style.display = 'none';
        if (counterEl) counterEl.textContent = 'CLI Terminal';
        if (dotsEl) dotsEl.classList.add('hidden');
        if (prevBtn) prevBtn.classList.add('hidden');
        if (nextBtn) nextBtn.classList.add('hidden');

        if (container) {
          const item = currentToolModalItem || {};
          const appName = item.app_name || (item.title ? item.title.split(':')[0].replace(/^[【\[].*?[】\]]\s*/, '') : 'AI CLI');
          const rawCmd = (appName || 'app').toLowerCase().replace(/[^a-z0-9_-]/g, '') || 'app';
          const isGh = item.tool_origin === 'github' || (item.url && item.url.includes('github.com'));
          const cliCmd = isGh ? `$ npx ${rawCmd} --run` : `$ ./${rawCmd} --start`;
          const hookText = (currentLang === 'zh' ? (item.app_hook || item.title_zh || item.summary_zh) : (item.app_hook_en || item.title_en || item.summary_en)) || (currentLang === 'zh' ? '高星开源 AI 实用项目' : 'High-performance AI engine');
          const scenarioText = translateScenarioTag(item.scenario_tag || '🤖 场景落地', currentLang);
          const runtimeText = translateRuntimeBadge(item.runtime_badge || item.pricing_tag || '🟢 开源免装', currentLang);

          if (!terminalEl) {
            terminalEl = document.createElement('div');
            terminalEl.id = 'tool-modal-terminal-mockup';
            container.appendChild(terminalEl);
          }
          terminalEl.className = 'w-full h-full bg-[#0b0f19] p-5 font-mono flex flex-col justify-between text-left select-none';
          terminalEl.style.display = 'flex';
          terminalEl.innerHTML = `
            <div class="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
              <div class="flex items-center space-x-2">
                <span class="w-3 h-3 rounded-full bg-[#ff5f56]"></span>
                <span class="w-3 h-3 rounded-full bg-[#ffbd2e]"></span>
                <span class="w-3 h-3 rounded-full bg-[#27c93f]"></span>
                <span class="text-xs text-slate-400 font-mono ml-2">${escapeHtml(rawCmd)} — bash</span>
              </div>
              <span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-emerald-400 font-mono border border-slate-700/60">${escapeHtml(runtimeText)}</span>
            </div>
            <div class="my-auto py-3 space-y-2">
              <div class="flex items-center space-x-2 text-sm text-slate-200">
                <span class="text-emerald-400 font-bold">➜</span>
                <span class="text-cyan-400 font-semibold">~</span>
                <span class="font-mono text-emerald-300 font-medium">${escapeHtml(cliCmd)}</span>
                <span class="inline-block w-2 h-4 bg-emerald-400 animate-pulse"></span>
              </div>
              <div class="text-xs text-slate-300 font-sans leading-relaxed max-w-xl">
                ${escapeHtml(hookText)}
              </div>
              <div class="text-[11px] text-slate-500 font-mono pt-1">
                ✓ Architecture verified · Headless engine · Open Source
              </div>
            </div>
            <div class="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-800/60">
              <span class="text-emerald-400 font-mono">⚡ ${escapeHtml(scenarioText)}</span>
              <span class="text-slate-400 font-mono">${item.stars ? `★ ${item.stars}` : 'GitHub Repository'}</span>
            </div>
          `;
        }
        return;
      }

      if (terminalEl) terminalEl.style.display = 'none';
      if (currentToolImageIndex < 0) currentToolImageIndex = currentToolImages.length - 1;
      if (currentToolImageIndex >= currentToolImages.length) currentToolImageIndex = 0;

      if (imgEl) {
        imgEl.style.display = 'block';
        imgEl.onerror = function() {
          this.onerror = null;
          this.style.display = 'none';
          if (terminalEl) terminalEl.style.display = 'flex';
        };
        imgEl.src = currentToolImages[currentToolImageIndex];
      }
      if (counterEl) {
        counterEl.textContent = `${currentToolImageIndex + 1} / ${currentToolImages.length}`;
      }

      if (dotsEl) {
        if (currentToolImages.length <= 1) {
          dotsEl.classList.add('hidden');
        } else {
          dotsEl.classList.remove('hidden');
          dotsEl.innerHTML = currentToolImages.map((_, idx) => `
            <button type="button" onclick="setToolCarouselSlide(${idx})" class="w-2 h-2 rounded-full transition-all ${idx === currentToolImageIndex ? 'bg-white w-5' : 'bg-white/40 hover:bg-white/70'}" title="切换至第 ${idx+1} 张截图"></button>
          `).join('');
        }
      }

      if (prevBtn && nextBtn) {
        if (currentToolImages.length <= 1) {
          prevBtn.classList.add('hidden');
          nextBtn.classList.add('hidden');
        } else {
          prevBtn.classList.remove('hidden');
          nextBtn.classList.remove('hidden');
        }
      }
    }

    function prevToolCarouselSlide() {
      currentToolImageIndex--;
      updateToolCarousel();
    }

    function nextToolCarouselSlide() {
      currentToolImageIndex++;
      updateToolCarousel();
    }

    function setToolCarouselSlide(idx) {
      currentToolImageIndex = idx;
      updateToolCarousel();
    }

    function openToolImageLightbox() {
      if (currentToolImages && currentToolImages[currentToolImageIndex]) {
        window.open(currentToolImages[currentToolImageIndex], '_blank');
      }
    }

    function closeToolDetailModal() {
      const modal = document.getElementById('tool-detail-modal');
      if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
      }
      currentToolModalItem = null;
    }

    // ==========================================
    // 法律合规与隐私政策控制 (满足 Google AdSense 审核强制要求)
    // ==========================================
    const LEGAL_DOCS = {
      privacy: {
        title_zh: "隐私政策",
        title_en: "Privacy Policy",
        content_zh: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">隐私政策</h3>
          <p class="text-[11px] text-slate-500">生效日期：2026年1月1日 | 最近更新：2026年9月14日</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">1. 概述</h4>
          <p>AI 资讯雷达 (ainewsradar.xyz) 极为重视用户的隐私保护。本政策阐明了当您访问和使用本网站时，我们如何处理信息及保护您的数据权益。</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">2. Cookie 与第三方广告供应商声明</h4>
          <p><strong>Google 是本站的第三方广告供应商，使用 Cookie 在本站投放广告：</strong></p>
          <ul class="list-disc pl-4 space-y-1 my-1 text-slate-600 dark:text-slate-300">
            <li>Google 等第三方供应商会根据用户此前对本网站或其他网站的访问情况使用 Cookie（包括 DART Cookie）投放广告。</li>
            <li>Google 使用广告 Cookie，使它及其合作伙伴能够根据用户对本网站和/或互联网上其他网站的访问情况向他们投放符合兴趣的相关广告。</li>
            <li><strong>用户选择停用个性化广告：</strong>您可以随时访问 <a href="https://www.google.com/settings/ads" target="_blank" class="text-indigo-500 underline font-medium">Google 广告设置</a> 选择停用个性化广告。</li>
            <li>您还可以通过访问 <a href="https://www.aboutads.info/choices/" target="_blank" class="text-indigo-500 underline font-medium">www.aboutads.info</a>，选择停用第三方供应商为投放个性化广告而使用的 Cookie。</li>
          </ul>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">3. 日志文件与分析</h4>
          <p>与许多其他网站一样，本网站会利用日志文件和匿名分析指标（如浏览器类型、访问时间、引用页面、语言偏好）。这些信息不包含任何个人身份识别信息，仅用于分析趋势、维护系统安全与优化网站性能。</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">4. 外部链接与数据安全</h4>
          <p>本站收录并链接至第三方外部平台（如官方网站、YouTube、𝕏 等）。我们对这些第三方网站的内容或隐私政策不承担责任，建议用户查阅相关网站的隐私声明。</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">5. 联系与咨询</h4>
          <p>如果您对本隐私政策或广告合规有任何疑问，可联系站长团队邮箱：<a href="mailto:contact@ainewsradar.xyz" class="text-indigo-500 underline">contact@ainewsradar.xyz</a>。</p>
        `,
        content_en: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">Privacy Policy</h3>
          <p class="text-[11px] text-slate-500">Effective Date: January 1, 2026 | Last Updated: September 14, 2026</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">1. Overview</h4>
          <p>AI News Radar (ainewsradar.xyz) takes your privacy seriously. This policy explains how information is handled when you visit and use our website.</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">2. Cookies and Third-Party Advertising</h4>
          <p><strong>Google is a third-party vendor on our site and uses cookies to serve ads:</strong></p>
          <ul class="list-disc pl-4 space-y-1 my-1 text-slate-600 dark:text-slate-300">
            <li>Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites.</li>
            <li>Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to this site and/or other sites on the Internet.</li>
            <li><strong>Opting Out:</strong> Users may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" target="_blank" class="text-indigo-500 underline font-medium">Google Ads Settings</a>.</li>
            <li>Alternatively, users can opt out of third-party vendor use of cookies for personalized advertising by visiting <a href="https://www.aboutads.info/choices/" target="_blank" class="text-indigo-500 underline font-medium">www.aboutads.info</a>.</li>
          </ul>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">3. Log Files & Analytics</h4>
          <p>Like many websites, AI News Radar utilizes log files and anonymous technical analytics (such as browser type, timestamps, referring pages, language preferences). This information does not contain personally identifiable data and is solely used to analyze trends, administer the site, and improve performance.</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">4. Outbound Links & External Services</h4>
          <p>Our platform indexes and links to official third-party resources (such as product homepages, YouTube, 𝕏). We have no control over and assume no responsibility for the content, privacy policies, or practices of any third-party sites.</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">5. Contact Information</h4>
          <p>If you have any questions or concerns regarding our privacy practices, please contact us at: <a href="mailto:contact@ainewsradar.xyz" class="text-indigo-500 underline">contact@ainewsradar.xyz</a>.</p>
        `
      },
      terms: {
        title_zh: "服务条款",
        title_en: "Terms of Service",
        content_zh: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">服务条款</h3>
          <p class="text-[11px] text-slate-500">生效日期：2026年1月1日</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">1. 接受条款</h4>
          <p>通过访问 ainewsradar.xyz，您同意受本服务条款的约束。如果您不同意这些条款，请勿使用本网站。</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">2. 资讯内容与免责声明</h4>
          <p>本站提供的 AI 行业动态、社交前沿精选、落地神器及实操提示词仅供学习与学术参考之用。本站按“现状”提供服务，不对任何内容的绝对准确性、时效性或由此产生的商业损失承担法律责任。</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">3. 知识产权与署名</h4>
          <p>本站所有聚合引用的第三方商标、博主名片、论文摘要、工具软件均属于其各自合法持有者所有。本站恪守合理使用（Fair Use）原则，所有外部内容均附有明确来源署名和原生链接直达。</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">4. 广告与商业赞助</h4>
          <p>本站可能展示由 Google AdSense 等合作伙伴提供的赞助商广告。用户与广告主的任何互动或交易均由用户与广告主自行负责。</p>
        `,
        content_en: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">Terms of Service</h3>
          <p class="text-[11px] text-slate-500">Effective Date: January 1, 2026</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">1. Acceptance of Terms</h4>
          <p>By accessing and browsing ainewsradar.xyz, you agree to be bound by these Terms of Service. If you do not agree, please discontinue using the service.</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">2. Content & Disclaimer</h4>
          <p>The AI intelligence, social intercepts, applied tools, and engineering prompts aggregated on this platform are provided solely for educational, research, and technical reference purposes. The service is provided "AS IS", without warranties of completeness, merchantability, or fitness for a particular purpose.</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">3. Intellectual Property & Fair Use</h4>
          <p>All third-party trademarks, creator profiles, papers, and software tools cited or indexed belong to their respective rightful owners. We adhere strictly to Fair Use principles; all external materials feature direct attribution and official outbound links.</p>

          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">4. Advertising & Sponsored Content</h4>
          <p>This website may display commercial advertisements served by partners such as Google AdSense. Any interaction or transaction between users and advertisers is strictly between the respective parties.</p>
        `
      },
      about: {
        title_zh: "关于本站",
        title_en: "About Us",
        content_zh: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">关于 AI 资讯雷达</h3>
          <p class="mt-2 leading-relaxed"><strong>AI 资讯雷达 (ainewsradar.xyz)</strong> 致力于为全球开发者、科研人员、AI 创业者与技术发烧友打造纯净、高效的 24 小时 AI 前沿科技风向标。</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">🌟 我们的核心价值：</h4>
          <ul class="list-disc pl-4 space-y-1.5 my-2 text-slate-600 dark:text-slate-300">
            <li><strong>⚡ 突发大事件与行业快讯</strong>：高频监控全球 AI 突破，提炼核心结论；</li>
            <li><strong>🐦 社交雷达前沿动态</strong>：实时抓取业界前沿团队与开发者在 𝕏 等社交平台的真实思想交锋；</li>
            <li><strong>🛠️ 落地实用神器</strong>：筛选验证免装即用 WebGPU 与生产力应用，严格按真实发布时间排列；</li>
            <li><strong>🎬 实战演示与教程视频</strong>：汇聚全球顶尖 AI 创作者的深度拆解与实战；</li>
            <li><strong>💡 工业级高阶提示词库</strong>：精选可直接用于生产力提效的结构化系统级 Prompt。</li>
          </ul>

          <p class="mt-3 text-[11px] text-slate-500">欢迎联系站长团队与我们交流合作，共同推动 AI 应用创新！</p>
        `,
        content_en: `
          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">About AI News Radar</h3>
          <p class="mt-2 leading-relaxed"><strong>AI News Radar (ainewsradar.xyz)</strong> is dedicated to providing a clutter-free, real-time 24-hour intelligence hub for developers, researchers, founders, and AI enthusiasts worldwide.</p>
          
          <h4 class="font-bold text-slate-800 dark:text-slate-200 mt-3">🌟 Core Capabilities & Focus:</h4>
          <ul class="list-disc pl-4 space-y-1.5 my-2 text-slate-600 dark:text-slate-300">
            <li><strong>⚡ Breaking Intelligence & Industry News</strong>: High-frequency tracking of global AI breakthroughs with extracted key takeaways;</li>
            <li><strong>🐦 Social Radar & Frontier Intercepts</strong>: Real-time authentic posts from AI pioneers and labs on 𝕏 and Threads;</li>
            <li><strong>🛠️ Applied AI Tools & Production Utilities</strong>: Verified, zero-install WebGPU and developer tools sorted strictly by real release dates;</li>
            <li><strong>🎬 Hands-on Masterclasses & Video Demos</strong>: Curated video walkthroughs and system architecture lessons from top global creators;</li>
            <li><strong>💡 Production-Grade System Prompt Library</strong>: Structured, high-yield system prompts ready for engineering workflows.</li>
          </ul>

          <p class="mt-3 text-[11px] text-slate-500">Feel free to reach out to our team at <a href="mailto:contact@ainewsradar.xyz" class="text-indigo-500 underline">contact@ainewsradar.xyz</a> for partnerships and feedback!</p>
        `
      }
    };

    function openLegalModal(tab = 'privacy') {
      const modal = document.getElementById('legal-modal');
      switchLegalTab(tab);
      modal.classList.remove('hidden');
    }

    function closeLegalModal() {
      const modal = document.getElementById('legal-modal');
      modal.classList.add('hidden');
    }

    function switchLegalTab(tab) {
      const isZh = currentLang === 'zh';
      ['privacy', 'terms', 'about'].forEach(t => {
        const btn = document.getElementById(`legal-tab-${t}`);
        if (btn) {
          if (t === 'privacy') btn.textContent = isZh ? '隐私政策' : 'Privacy Policy';
          if (t === 'terms') btn.textContent = isZh ? '服务条款' : 'Terms of Service';
          if (t === 'about') btn.textContent = isZh ? '关于本站' : 'About Us';
          if (t === tab) {
            btn.className = "text-xs font-bold px-3 py-1.5 rounded-lg bg-indigo-600 text-white transition-colors";
          } else {
            btn.className = "text-xs font-medium px-3 py-1.5 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors";
          }
        }
      });

      const container = document.getElementById('legal-content');
      if (container && LEGAL_DOCS[tab]) {
        container.innerHTML = isZh ? (LEGAL_DOCS[tab].content_zh || LEGAL_DOCS[tab].content) : (LEGAL_DOCS[tab].content_en || LEGAL_DOCS[tab].content);
      }
    }

    // 倒计时与定时轮询
    setInterval(() => {
      refreshCountdown--;
      const timer = document.getElementById('timer');
      if (timer) timer.textContent = refreshCountdown;
      if (refreshCountdown <= 0) {
        loadNews();
      }
    }, 1000);

    // 安全初始化 Google AdSense 广告单元（严格排查未初始化 ins 元素，彻底杜绝 TagError）
    try {
      const uninitAds = document.querySelectorAll('ins.adsbygoogle:not([data-adsbygoogle-status])');
      uninitAds.forEach(() => {
        (adsbygoogle = window.adsbygoogle || []).push({});
      });
    } catch (e) {}

    // 全局快捷键监听 (Esc 键关闭弹窗，左右箭头切换轮播)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeVideoModal();
        closeLegalModal();
        closeAiNewsModal();
        closeSocialPostModal();
        closeToolDetailModal();
      }
      const toolModal = document.getElementById('tool-detail-modal');
      if (toolModal && !toolModal.classList.contains('hidden')) {
        if (e.key === 'ArrowLeft') prevToolCarouselSlide();
        if (e.key === 'ArrowRight') nextToolCarouselSlide();
      }
    });

    // 启动前快速尝试从会话缓存恢复，杜绝大 JSON 异步拉取间隙的空白屏
    try {
      sessionStorage.removeItem('ainews_cached_data');
      sessionStorage.removeItem('ainews_cached_data_v52');
      const cachedStr = sessionStorage.getItem('ainews_cached_data_v53');
      if (cachedStr && !cachedData) {
        const parsed = JSON.parse(cachedStr);
        if (parsed && (Date.now() - (parsed._saved_at || 0) < 300000)) {
          cachedData = parsed;
          renderUI(parsed);
          window._hasInitialRendered = true;
        }
      }
    } catch (e) {}

    // 初始化路由与语言状态 (英文为主站 English-First，不污染持久化配置)
    setLanguage(currentLang, false);
    const initHashTab = getTabFromHash();
    if (initHashTab) {
      switchTab(initHashTab, false);
    }
    loadNews();
    window.addEventListener('hashchange', handleHashNavigation);
    let resizeSyncTimer = null;
    window.addEventListener('resize', () => {
      clearTimeout(resizeSyncTimer);
      resizeSyncTimer = setTimeout(() => {
        syncThreeColumnsHeight();
        fitViralTickerHeight();
      }, 100);
    });

    window.switchSocialViewMode = switchSocialViewMode;
    window.filterSocialPlatform = filterSocialPlatform;
    window.filterViralPlatform = filterViralPlatform;
    window.flipViralTicker = flipViralTicker;
    window.toggleViralTickerPause = toggleViralTickerPause;
    window.switchHomeToolFilter = switchHomeToolFilter;
    window.switchHomePromptFilter = switchHomePromptFilter;
    window.changeCategoryPage = changeCategoryPage;
    window.changeCategoryPageSize = changeCategoryPageSize;
    window.switchTopicFocus = switchTopicFocus;
    window.toggleTopicFocusCollapse = toggleTopicFocusCollapse;
    window.playHeroLeadVideo = playHeroLeadVideo;
    window.openImageLightbox = openImageLightbox;
    window.closeImageLightbox = closeImageLightbox;
    window.renderHeroMediaShowcase = renderHeroMediaShowcase;
    window.renderViralTicker = renderViralTicker;
    window.renderLeadVideoCard = renderLeadVideoCard;

    const runLangCheck = () => {
      initTranslateEngine();
      checkAndShowLangSuggestion();
    };

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(runLangCheck, 300);
    } else {
      window.addEventListener('DOMContentLoaded', () => {
        handleHashNavigation();
        syncThreeColumnsHeight();
        setTimeout(runLangCheck, 300);
      });
    }
    setTimeout(runLangCheck, 600);
