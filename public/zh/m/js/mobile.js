/**
 * mobile.js - High-Performance Mobile Web App Controller
 * Dedicated lightweight engine for mobile screens (< 768px).
 * Focused on News (资讯), Social Signals (社交推文), and Videos (实战视频).
 */

(function() {
  'use strict';

  // 1. Language & Environment State
  const isZh = Boolean(
    window.__IS_ZH || 
    window.location.pathname.startsWith('/zh') || 
    new URLSearchParams(window.location.search).get('lang') === 'zh'
  );

  let currentSiteLang = localStorage.getItem('ai_radar_user_site_lang');
  if (!currentSiteLang) {
    currentSiteLang = isZh ? 'chinese_simplified' : 'english';
  }

  // Complete 31 Global Languages (100% parity with Desktop)
  const ALL_SITE_LANGUAGES = [
    // 🌟 Popular Languages (常用热门语种)
    { id: 'english', flag: '🇬🇧', code: 'EN', nameZh: '英语', nameEn: 'English (Global)', native: 'English', group: 'popular' },
    { id: 'chinese_simplified', flag: '🇨🇳', code: '简', nameZh: '简体中文', nameEn: 'Chinese (Simplified)', native: '简体中文', group: 'popular' },
    { id: 'chinese_traditional', flag: '🇭🇰', code: '繁', nameZh: '繁体中文', nameEn: 'Chinese (Traditional)', native: '繁體中文', group: 'popular' },
    { id: 'japanese', flag: '🇯🇵', code: 'JA', nameZh: '日语', nameEn: 'Japanese', native: '日本語', group: 'popular' },
    { id: 'korean', flag: '🇰🇷', code: 'KO', nameZh: '韩语', nameEn: 'Korean', native: '한국어', group: 'popular' },
    { id: 'deutsch', flag: '🇩🇪', code: 'DE', nameZh: '德语', nameEn: 'German', native: 'Deutsch', group: 'popular' },
    { id: 'french', flag: '🇫🇷', code: 'FR', nameZh: '法语', nameEn: 'French', native: 'Français', group: 'popular' },
    { id: 'spanish', flag: '🇪🇸', code: 'ES', nameZh: '西班牙语', nameEn: 'Spanish', native: 'Español', group: 'popular' },
    { id: 'russian', flag: '🇷🇺', code: 'RU', nameZh: '俄语', nameEn: 'Russian', native: 'Русский', group: 'popular' },
    { id: 'arabic', flag: '🇸🇦', code: 'AR', nameZh: '阿拉伯语', nameEn: 'Arabic', native: 'العربية', group: 'popular' },

    // 🌍 European Languages (欧洲主要语言)
    { id: 'portuguese', flag: '🇵🇹', code: 'PT', nameZh: '葡萄牙语', nameEn: 'Portuguese', native: 'Português', group: 'european' },
    { id: 'italian', flag: '🇮🇹', code: 'IT', nameZh: '意大利语', nameEn: 'Italian', native: 'Italiano', group: 'european' },
    { id: 'dutch', flag: '🇳🇱', code: 'NL', nameZh: '荷兰语', nameEn: 'Dutch', native: 'Nederlands', group: 'european' },
    { id: 'polish', flag: '🇵🇱', code: 'PL', nameZh: '波兰语', nameEn: 'Polish', native: 'Polski', group: 'european' },
    { id: 'ukrainian', flag: '🇺🇦', code: 'UK', nameZh: '乌克兰语', nameEn: 'Ukrainian', native: 'Українська', group: 'european' },
    { id: 'swedish', flag: '🇸🇪', code: 'SV', nameZh: '瑞典语', nameEn: 'Swedish', native: 'Svenska', group: 'european' },
    { id: 'norwegian', flag: '🇳🇴', code: 'NO', nameZh: '挪威语', nameEn: 'Norwegian', native: 'Norsk', group: 'european' },
    { id: 'danish', flag: '🇩🇰', code: 'DA', nameZh: '丹麦语', nameEn: 'Danish', native: 'Dansk', group: 'european' },
    { id: 'finnish', flag: '🇫🇮', code: 'FI', nameZh: '芬兰语', nameEn: 'Finnish', native: 'Suomi', group: 'european' },
    { id: 'czech', flag: '🇨🇿', code: 'CS', nameZh: '捷克语', nameEn: 'Czech', native: 'Čeština', group: 'european' },
    { id: 'hungarian', flag: '🇭🇺', code: 'HU', nameZh: '匈牙利语', nameEn: 'Hungarian', native: 'Magyar', group: 'european' },
    { id: 'romanian', flag: '🇷🇴', code: 'RO', nameZh: '罗马尼亚语', nameEn: 'Romanian', native: 'Română', group: 'european' },
    { id: 'greek', flag: '🇬🇷', code: 'EL', nameZh: '希腊语', nameEn: 'Greek', native: 'Ελληνικά', group: 'european' },

    // 🌏 Asia-Pacific & Others (亚太及全球语种)
    { id: 'hindi', flag: '🇮🇳', code: 'HI', nameZh: '印地语', nameEn: 'Hindi', native: 'हिन्दी', group: 'apac' },
    { id: 'vietnamese', flag: '🇻🇳', code: 'VI', nameZh: '越南语', nameEn: 'Vietnamese', native: 'Tiếng Việt', group: 'apac' },
    { id: 'thai', flag: '🇹🇭', code: 'TH', nameZh: '泰语', nameEn: 'Thai', native: 'ภาษาไทย', group: 'apac' },
    { id: 'indonesian', flag: '🇮🇩', code: 'ID', nameZh: '印尼语', nameEn: 'Indonesian', native: 'Bahasa Indonesia', group: 'apac' },
    { id: 'malay', flag: '🇲🇾', code: 'MS', nameZh: '马来语', nameEn: 'Malay', native: 'Bahasa Melayu', group: 'apac' },
    { id: 'filipino', flag: '🇵🇭', code: 'FIL', nameZh: '菲律宾语', nameEn: 'Filipino', native: 'Filipino', group: 'apac' },
    { id: 'turkish', flag: '🇹🇷', code: 'TR', nameZh: '土耳其语', nameEn: 'Turkish', native: 'Türkçe', group: 'apac' },
    { id: 'hebrew', flag: '🇮🇱', code: 'HE', nameZh: '希伯来语', nameEn: 'Hebrew', native: 'עברית', group: 'apac' }
  ];

  const LANG_GROUPS = {
    popular: { en: '🌟 Popular Languages', zh: '🌟 常用热门语种' },
    european: { en: '🌍 European Languages', zh: '🌍 欧洲主要语言' },
    apac: { en: '🌏 Asia-Pacific & Global', zh: '🌏 亚太及全球语种' }
  };

  const I18N = {
    zh: {
      appName: 'AI 资讯雷达',
      mobileEdition: '移动专版',
      live: '实时更新',
      refresh: '刷新',
      searchPlaceholder: '搜索 AI 快讯、推文与实战视频...',
      tabNews: '行业资讯',
      tabSocial: '社交推文',
      tabVideos: '实战视频',
      tabTop: '今日必读',
      filterAll: '全部',
      filterBreaking: '⚡ 突发快讯',
      filterDeep: '📰 深度报道',
      filterModel: '🚀 模型发布',
      filterLeader: '👑 领袖观点',
      filterOfficial: '🏢 官方旗舰',
      filterViral: '🔥 24h飙升',
      filterTutorial: '🛠️ 实战教学',
      filterInsight: '💡 前沿评测',
      loadMore: '加载更多',
      noMore: '已加载全部精彩内容',
      noMatch: '暂无符合条件的动态',
      readFull: '阅读全文 & 深度解析 →',
      viewOriginal: '直达源站 ↗',
      openOnX: '在 𝕏 查看原文 ↗',
      modalTitle: '资讯深度解析',
      briefingTitle: '🎯 核心事实提炼 (5W1H)',
      insightTitle: '🤖 AI 智库犀利研判',
      coverageTitle: '📰 深度报道原文实录',
      toggleLangZh: '查看中文译文',
      toggleLangEn: '查看英文原文',
      switchToDesktop: '💻 切换至电脑完整版',
      justNow: '刚刚',
      minsAgo: '分钟前',
      hoursAgo: '小时前',
      daysAgo: '天前',
      views: '浏览',
      likes: '赞',
      retweets: '转推',
      copiedToast: '链接已复制到剪贴板！',
      shareTitle: '分享 AI 动态',
      aiTakePrefix: 'AI 研判',
      sourceBtn: '源站 ↗',
      shareBtn: '分享',
      suggestTitle: '语言偏好提示',
      suggestEnDesc: '检测到您的系统语言为英文，是否切换至英文原版？',
      suggestZhDesc: '检测到您的系统语言为中文，是否切换至中文精翻版？',
      suggestSwitchBtn: '立即切换',
      suggestDismissBtn: '保持现状'
    },
    en: {
      appName: 'AI News Radar',
      mobileEdition: 'Mobile App',
      live: 'LIVE',
      refresh: 'Refresh',
      searchPlaceholder: 'Search news, leader tweets & videos...',
      tabNews: 'Intel & News',
      tabSocial: 'Social Signals',
      tabVideos: 'Hands-on Videos',
      tabTop: 'Top 3 Digest',
      filterAll: 'All',
      filterBreaking: '⚡ Breaking',
      filterDeep: '📰 In-Depth',
      filterModel: '🚀 Models',
      filterLeader: '👑 Tech Leaders',
      filterOfficial: '🏢 Official Labs',
      filterViral: '🔥 24h Viral',
      filterTutorial: '🛠️ Tutorials',
      filterInsight: '💡 Breakdowns',
      loadMore: 'Load More',
      noMore: 'All caught up!',
      noMatch: 'No results match your criteria',
      readFull: 'Read Full Story & AI Take →',
      viewOriginal: 'Original Source ↗',
      openOnX: 'View on 𝕏 ↗',
      modalTitle: 'Intelligence Briefing',
      briefingTitle: '🎯 Core Fact Briefing (5W1H)',
      insightTitle: '🤖 AI Hot Take & Analysis',
      coverageTitle: '📰 Full In-Depth Coverage',
      toggleLangZh: 'View Chinese Translation',
      toggleLangEn: 'View English Original',
      switchToDesktop: '💻 Switch to Desktop Version',
      justNow: 'just now',
      minsAgo: 'm ago',
      hoursAgo: 'h ago',
      daysAgo: 'd ago',
      views: 'views',
      likes: 'likes',
      retweets: 'RT',
      copiedToast: 'Link copied to clipboard!',
      shareTitle: 'Share AI Intel',
      aiTakePrefix: 'AI Hot Take',
      sourceBtn: 'Source ↗',
      shareBtn: 'Share',
      suggestTitle: 'Language Preference',
      suggestEnDesc: 'Detected English system locale. Switch to English edition?',
      suggestZhDesc: 'Detected Chinese system locale. Switch to Chinese edition?',
      suggestSwitchBtn: 'Switch Now',
      suggestDismissBtn: 'Keep Current'
    }
  };

  const t = isZh ? I18N.zh : I18N.en;

  // 2. Global Runtime State
  let cachedData = null;
  let currentTab = 'news'; // 'news' | 'social' | 'videos' | 'top'
  let currentFilter = 'all';
  let searchQuery = '';
  let displayLimit = 20;
  const PAGE_STEP = 20;
  const tweetLangState = {};

  // 3. Theme Init
  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'auto';
    const isDark = savedTheme === 'dark' || (savedTheme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.classList.toggle('dark', isDark);
    updateThemeIcon(isDark);
  }

  function toggleTheme() {
    const isCurrentlyDark = document.documentElement.classList.contains('dark');
    const newIsDark = !isCurrentlyDark;
    document.documentElement.classList.toggle('dark', newIsDark);
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
    updateThemeIcon(newIsDark);
  }

  function updateThemeIcon(isDark) {
    const iconEl = document.getElementById('theme-icon');
    if (iconEl) {
      iconEl.textContent = isDark ? '🌙' : '☀️';
    }
  }

  // 4. Traditional Chinese Engine Lazy Loader
  function ensureChineseConverter(cb) {
    if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
      if (typeof cb === 'function') cb();
      return;
    }
    if (typeof cb === 'function') {
      window._zhConvWaiters = window._zhConvWaiters || [];
      window._zhConvWaiters.push(cb);
    }
    if (window._zhConvLoading) return;
    window._zhConvLoading = true;
    const script = document.createElement('script');
    script.src = '/js/chinese_converter.js';
    script.async = true;
    script.onload = () => {
      window._zhConvLoading = false;
      const waiters = window._zhConvWaiters || [];
      window._zhConvWaiters = [];
      waiters.forEach(fn => { try { fn(); } catch (e) {} });
    };
    script.onerror = () => {
      window._zhConvLoading = false;
      window._zhConvWaiters = [];
    };
    document.head.appendChild(script);
  }

  // 5. Time & Text Formatting
  function formatTimeAgo(timeStr) {
    if (!timeStr) return '';
    try {
      const dt = new Date(timeStr.replace('Z', '+00:00'));
      const diffSecs = Math.floor((Date.now() - dt.getTime()) / 1000);
      if (diffSecs < 60) return t.justNow;
      if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}${t.minsAgo}`;
      if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}${t.hoursAgo}`;
      return `${Math.floor(diffSecs / 86400)}${t.daysAgo}`;
    } catch (e) {
      return '';
    }
  }

  function optimizeImageUrl(url, width = 480) {
    if (!url || typeof url !== 'string') return '';
    const clean = url.trim();
    if (!clean || clean === 'null' || clean === 'none') return '';
    if (clean.startsWith('/') || clean.startsWith('./')) return clean;
    if (clean.includes('wsrv.nl')) return clean;
    return `https://wsrv.nl/?url=${encodeURIComponent(clean)}&w=${width}&output=webp&q=80`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // 6. Toast Notification Helper
  function showToast(msg) {
    let toast = document.getElementById('mobile-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'mobile-toast';
      document.body.appendChild(toast);
    }
    toast.innerHTML = `
      <div class="px-4 py-2.5 rounded-2xl bg-slate-900/95 dark:bg-white/95 text-white dark:text-slate-900 text-xs font-bold shadow-2xl backdrop-blur-md flex items-center gap-2 border border-slate-700/50 dark:border-slate-200/50 notranslate">
        <span>✨</span>
        <span>${escapeHtml(msg)}</span>
      </div>
    `;
    toast.classList.add('show');
    if (window._toastTimer) clearTimeout(window._toastTimer);
    window._toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 2400);
  }

  // 7. Data Loading & Extraction
  async function loadData(forceRefresh = false) {
    const feedContainer = document.getElementById('mobile-feed');
    if (!cachedData || forceRefresh) {
      if (feedContainer) {
        feedContainer.innerHTML = renderSkeleton();
      }
      try {
        const url = forceRefresh ? `/data/latest_news.json?t=${Date.now()}` : '/data/latest_news.json';
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        cachedData = await res.json();
      } catch (err) {
        console.error('Failed to load data:', err);
        if (feedContainer) {
          feedContainer.innerHTML = `
            <div class="p-8 text-center text-slate-500">
              <p class="text-3xl mb-2">⚠️</p>
              <p class="text-sm font-medium mb-4">${isZh ? '数据加载异常，请点击刷新重试' : 'Failed to load updates. Please tap retry.'}</p>
              <button type="button" onclick="window.MobileApp.refresh()" class="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold shadow-md active:scale-95">
                ${t.refresh}
              </button>
            </div>
          `;
        }
        return;
      }
    }

    renderCurrentView();

    // If Traditional Chinese was requested, convert DOM
    if (isZh && currentSiteLang === 'chinese_traditional') {
      ensureChineseConverter(() => {
        if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
          setTimeout(() => {
            try { window.ChineseConverter.convertDomToTraditional(); } catch (e) {}
          }, 30);
        }
      });
    }
  }

  // 8. Dynamic Sub-filters
  function renderSubFilters() {
    const subFilterWrap = document.getElementById('sub-filter-bar');
    if (!subFilterWrap) return;

    let filters = [];
    if (currentTab === 'news') {
      filters = [
        { id: 'all', label: t.filterAll },
        { id: 'breaking', label: t.filterBreaking },
        { id: 'deep', label: t.filterDeep },
        { id: 'model', label: t.filterModel }
      ];
    } else if (currentTab === 'social') {
      filters = [
        { id: 'all', label: t.filterAll },
        { id: 'leader', label: t.filterLeader },
        { id: 'official', label: t.filterOfficial },
        { id: 'viral', label: t.filterViral }
      ];
    } else if (currentTab === 'videos') {
      filters = [
        { id: 'all', label: t.filterAll },
        { id: 'tutorial', label: t.filterTutorial },
        { id: 'insight', label: t.filterInsight }
      ];
    } else {
      subFilterWrap.innerHTML = '';
      subFilterWrap.classList.add('hidden');
      return;
    }

    subFilterWrap.classList.remove('hidden');
    subFilterWrap.innerHTML = `
      <div class="flex items-center gap-2 overflow-x-auto no-scrollbar px-3 py-2">
        ${filters.map(f => {
          const isActive = currentFilter === f.id;
          const activeClass = isActive
            ? 'bg-indigo-600 text-white shadow-xs font-bold'
            : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200/60 dark:border-slate-800 font-medium';
          return `
            <button 
              type="button"
              onclick="window.MobileApp.setFilter('${f.id}')"
              class="px-3 py-1 rounded-full text-xs whitespace-nowrap transition-all touch-card ${activeClass}"
            >
              ${f.label}
            </button>
          `;
        }).join('')}
      </div>
    `;
  }

  // 9. Render Current Feed View
  function renderCurrentView() {
    if (!cachedData) return;
    const feedContainer = document.getElementById('mobile-feed');
    if (!feedContainer) return;

    renderSubFilters();

    let items = [];
    if (currentTab === 'news') {
      items = (cachedData.grouped && cachedData.grouped.news) || [];
      if (currentFilter === 'breaking') {
        items = items.filter(it => it.is_breaking || (it.tags && it.tags.some(tg => tg.includes('突发') || tg.includes('Breaking'))));
      } else if (currentFilter === 'deep') {
        items = items.filter(it => (it.article_content || it.article_content_zh) && String(it.article_content || it.article_content_zh).length > 200);
      } else if (currentFilter === 'model') {
        items = items.filter(it => {
          const txt = `${it.title} ${it.title_zh || ''} ${it.title_en || ''}`.toLowerCase();
          return /model|claude|gpt|gemini|deepseek|qwen|flux|reasoning|weights/i.test(txt);
        });
      }
    } else if (currentTab === 'social') {
      items = (cachedData.grouped && cachedData.grouped.celebrity) || (cachedData.celebrity) || [];
      if (currentFilter === 'leader') {
        items = items.filter(it => it.entity_type === 'person' || !it.author_handle || ['sama', 'karpathy', 'ylecun', 'demishassabis', 'elonmusk'].includes(it.author_handle.toLowerCase()));
      } else if (currentFilter === 'official') {
        items = items.filter(it => it.entity_type === 'organization' || ['openai', 'anthropicai', 'claudeai', 'deepseek_ai', 'googledeepmind'].includes((it.author_handle || '').toLowerCase()));
      } else if (currentFilter === 'viral') {
        items = items.filter(it => it.is_viral || it.surge_badge);
      }
    } else if (currentTab === 'videos') {
      items = (cachedData.grouped && cachedData.grouped.videos) || [];
      if (currentFilter === 'tutorial') {
        items = items.filter(it => it.sub_type === 'tutorial' || (it.title || '').includes('教学') || (it.title || '').includes('Tutorial'));
      } else if (currentFilter === 'insight') {
        items = items.filter(it => it.sub_type !== 'tutorial');
      }
    } else if (currentTab === 'top') {
      items = cachedData.top_three || [];
    }

    // Search filter
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      items = items.filter(it => {
        const corpus = `${it.title || ''} ${it.title_zh || ''} ${it.title_en || ''} ${it.summary_zh || ''} ${it.summary_en || ''} ${it.author || ''} ${it.source || ''}`.toLowerCase();
        return corpus.includes(q);
      });
    }

    if (items.length === 0) {
      feedContainer.innerHTML = `
        <div class="py-16 text-center text-slate-400">
          <p class="text-3xl mb-2">🔍</p>
          <p class="text-xs font-medium">${t.noMatch}</p>
        </div>
      `;
      return;
    }

    const visibleItems = items.slice(0, displayLimit);
    let htmlCards = '';

    if (currentTab === 'news') {
      htmlCards = visibleItems.map((it, idx) => renderNewsCard(it, idx)).join('');
    } else if (currentTab === 'social') {
      htmlCards = visibleItems.map((it, idx) => renderSocialCard(it, idx)).join('');
    } else if (currentTab === 'videos') {
      htmlCards = visibleItems.map((it, idx) => renderVideoCard(it, idx)).join('');
    } else if (currentTab === 'top') {
      htmlCards = visibleItems.map((it, idx) => renderTopCard(it, idx)).join('');
    }

    const hasMore = items.length > displayLimit;
    const loadMoreButton = hasMore ? `
      <div class="pt-4 pb-8 text-center">
        <button 
          type="button"
          onclick="window.MobileApp.loadMore()" 
          class="w-full py-3 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-200 text-xs font-bold rounded-2xl shadow-card active:scale-98 transition-all"
        >
          ${t.loadMore} (${visibleItems.length}/${items.length})
        </button>
      </div>
    ` : `
      <div class="py-6 text-center text-[11px] text-slate-400 dark:text-slate-600 font-medium">
        — ${t.noMore} —
      </div>
    `;

    feedContainer.innerHTML = `
      <div class="space-y-3 px-3 py-2">
        ${htmlCards}
        ${loadMoreButton}
      </div>
    `;

    // Apply Traditional Chinese if active
    if (isZh && currentSiteLang === 'chinese_traditional') {
      if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
        try { window.ChineseConverter.convertDomToTraditional(); } catch (e) {}
      }
    }
  }

  // 10. Card Renderers
  function renderNewsCard(item, idx = 0) {
    const title = escapeHtml((isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || '');
    const summary = escapeHtml((isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || '');
    const source = escapeHtml(item.source || 'AI Radar');
    const timeAgo = formatTimeAgo(item.raw_published_at);
    const imgUrl = item.image_url ? optimizeImageUrl(item.image_url, 480) : '';
    const hasDeepArticle = Boolean((item.article_content || item.article_content_zh) && String(item.article_content || item.article_content_zh).length > 200);
    const insightText = item.ai_analysis && (isZh ? item.ai_analysis.insight_zh : item.ai_analysis.insight_en);

    return `
      <article 
        class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 shadow-card touch-card transition-all cursor-pointer"
        onclick="window.MobileApp.openArticle('${item.id}')"
      >
        <div class="flex items-center justify-between text-[11px] mb-2">
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 font-semibold font-mono text-[10px]">
              ${source}
            </span>
            ${item.is_breaking ? `<span class="px-1.5 py-0.5 rounded bg-rose-500 text-white font-bold text-[9px]">⚡ ${isZh ? '突发' : 'BREAKING'}</span>` : ''}
            ${hasDeepArticle ? `<span class="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 font-bold text-[9px]">📰 ${isZh ? '深度实录' : 'IN-DEPTH'}</span>` : ''}
          </div>
          <span class="text-slate-400 font-mono text-[10px] shrink-0">${timeAgo}</span>
        </div>

        <h3 class="text-[15px] font-bold text-slate-900 dark:text-slate-100 leading-snug mb-2 line-clamp-3">
          ${title}
        </h3>

        ${summary ? `
          <p class="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-3 line-clamp-2">
            ${summary}
          </p>
        ` : ''}

        ${imgUrl ? `
          <div class="rounded-xl overflow-hidden aspect-video bg-slate-100 dark:bg-slate-800 mb-3 border border-slate-100 dark:border-slate-800/60">
            <img src="${imgUrl}" width="480" height="270" alt="${title}" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async" onerror="this.parentElement.style.display='none'">
          </div>
        ` : ''}

        ${insightText ? `
          <div class="p-2.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200/50 dark:border-purple-800/40 text-[11px] text-purple-900 dark:text-purple-200 leading-relaxed flex items-start gap-1.5 mb-3">
            <span class="text-xs">🤖</span>
            <div class="line-clamp-2">
              <span class="font-bold mr-1">${t.aiTakePrefix}:</span>${escapeHtml(insightText)}
            </div>
          </div>
        ` : ''}

        <div class="flex items-center justify-between pt-2.5 border-t border-slate-100 dark:border-slate-800/60 text-[11px]">
          <span class="text-indigo-600 dark:text-indigo-400 font-bold flex items-center gap-1">
            <span>${t.readFull}</span>
          </span>
          <div class="flex items-center gap-2" onclick="event.stopPropagation()">
            ${item.url ? `
              <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 text-[10px] font-semibold flex items-center gap-0.5">
                ${t.sourceBtn}
              </a>
            ` : ''}
            <button type="button" onclick="window.MobileApp.shareArticle('${item.id}')" class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 text-[10px] font-semibold flex items-center gap-1" title="${t.shareBtn}">
              🔗
            </button>
          </div>
        </div>
      </article>
    `;
  }

  function renderSocialCard(item, idx = 0) {
    const authorName = escapeHtml(item.author || 'AI Pioneer');
    const authorHandle = escapeHtml(item.author_handle || '');
    const authorRole = escapeHtml(isZh ? (item.author_role || item.author_role_en || '') : (item.author_role_en || item.author_role || ''));
    const avatar = item.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${authorHandle || 'vip'}`;
    const timeAgo = formatTimeAgo(item.raw_published_at);
    
    const textZh = item.full_text_zh || item.quote_zh || item.summary_zh || item.title_zh || '';
    const textEn = item.full_text_en || item.quote_en || item.summary_en || item.title_en || item.title || '';
    
    const currentMode = tweetLangState[item.id] || (isZh ? 'zh' : 'en');
    let displayText = currentMode === 'zh' ? (textZh || textEn) : (textEn || textZh);
    displayText = escapeHtml(displayText);

    const hasBilingual = Boolean(textZh && textEn && textZh.trim() !== textEn.trim());
    const rawUrl = item.url || (authorHandle && item.status_id ? `https://x.com/${authorHandle}/status/${item.status_id}` : '#');
    const metrics = item.metrics || {};
    const mediaList = item.media_urls || (item.image_url ? [item.image_url] : []);

    return `
      <article class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 shadow-card touch-card transition-all">
        <div class="flex items-start justify-between mb-2.5">
          <div class="flex items-center gap-2.5">
            <img src="${avatar}" width="40" height="40" decoding="async" alt="${authorName}" class="w-10 h-10 rounded-full object-cover border border-slate-200 dark:border-slate-700 bg-slate-100" onerror="this.src='https://api.dicebear.com/7.x/bottts/svg?seed=vip'">
            <div>
              <div class="flex items-center gap-1">
                <span class="font-bold text-sm text-slate-900 dark:text-slate-100">${authorName}</span>
                <span class="text-blue-500 text-xs">✓</span>
              </div>
              <div class="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono">
                ${authorHandle ? `<span>@${authorHandle}</span>` : ''}
                <span>·</span>
                <span>${timeAgo}</span>
              </div>
            </div>
          </div>
          ${authorRole ? `
            <span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-semibold font-mono truncate max-w-[120px]">
              ${authorRole}
            </span>
          ` : ''}
        </div>

        <p class="text-[14px] text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-line mb-3 font-normal" id="tweet-text-${item.id}">
          ${displayText}
        </p>

        ${hasBilingual ? `
          <div class="mb-3">
            <button 
              type="button"
              onclick="window.MobileApp.toggleTweetLang('${item.id}')"
              class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[10px] font-semibold text-indigo-600 dark:text-indigo-400 border border-slate-200/50 dark:border-slate-700/50 active:scale-95 transition-transform"
            >
              <span>🌐</span>
              <span id="tweet-toggle-btn-${item.id}">${currentMode === 'zh' ? t.toggleLangEn : t.toggleLangZh}</span>
            </button>
          </div>
        ` : ''}

        ${mediaList.length > 0 ? `
          <div class="rounded-xl overflow-hidden mb-3 aspect-video bg-slate-100 dark:bg-slate-800 border border-slate-100 dark:border-slate-800/60">
            <img src="${optimizeImageUrl(mediaList[0], 640)}" width="640" height="360" alt="Tweet media" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async">
          </div>
        ` : ''}

        <div class="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-2.5 border-t border-slate-100 dark:border-slate-800/60">
          <div class="flex items-center gap-3">
            ${metrics.views ? `<span>👁️ ${metrics.views}</span>` : ''}
            ${metrics.likes ? `<span>❤️ ${metrics.likes}</span>` : ''}
            ${metrics.retweets ? `<span>🔁 ${metrics.retweets}</span>` : ''}
          </div>
          <a href="${rawUrl}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 dark:text-indigo-400 font-bold flex items-center gap-1 hover:underline">
            <span>${t.openOnX}</span>
          </a>
        </div>
      </article>
    `;
  }

  function renderVideoCard(item, idx = 0) {
    const title = escapeHtml((isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || '');
    const author = escapeHtml(item.author || 'AI Creator');
    const timeAgo = formatTimeAgo(item.raw_published_at);
    const imgUrl = item.image_url ? optimizeImageUrl(item.image_url, 640) : '';
    const videoUrl = item.url || '#';
    const subType = item.sub_type === 'tutorial' ? (isZh ? '🛠️ 实战教学' : '🛠️ Tutorial') : (isZh ? '💡 架构剖析' : '💡 Breakdown');

    return `
      <a 
        href="${videoUrl}" 
        target="_blank" 
        rel="noopener noreferrer"
        class="block bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl overflow-hidden shadow-card touch-card transition-all"
      >
        <div class="relative aspect-video bg-slate-900">
          ${imgUrl ? `
            <img src="${imgUrl}" width="640" height="360" alt="${title}" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async">
          ` : ''}
          <div class="absolute inset-0 bg-black/35 flex items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-rose-600/95 text-white flex items-center justify-center text-lg pl-1 shadow-xl">
              ▶
            </div>
          </div>
          <span class="absolute bottom-2 right-2 px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-xs text-white text-[10px] font-mono font-bold">
            ${subType}
          </span>
        </div>

        <div class="p-3.5">
          <h3 class="text-[14px] font-bold text-slate-900 dark:text-slate-100 leading-snug line-clamp-2 mb-2">
            ${title}
          </h3>
          <div class="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono">
            <span>${author}</span>
            <span>${timeAgo}</span>
          </div>
        </div>
      </a>
    `;
  }

  function renderTopCard(item, index) {
    const title = escapeHtml((isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || '');
    const summary = escapeHtml((isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || '');
    const insight = item.ai_analysis && (isZh ? item.ai_analysis.insight_zh : item.ai_analysis.insight_en);
    const source = escapeHtml(item.source || 'AI Radar');

    return `
      <article 
        class="bg-gradient-to-br from-indigo-50/70 via-purple-50/40 to-slate-50 dark:from-indigo-950/40 dark:via-purple-950/30 dark:to-slate-900 border border-indigo-200/70 dark:border-indigo-800/60 rounded-2xl p-4 shadow-card touch-card transition-all cursor-pointer"
        onclick="window.MobileApp.openArticle('${item.id}')"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-gradient-to-tr from-indigo-600 to-rose-500 text-white text-xs font-black flex items-center justify-center shadow-xs">
              #${index + 1}
            </span>
            <span class="font-bold text-xs text-indigo-700 dark:text-indigo-300">${isZh ? '今日核心突破' : 'Core Breakthrough'}</span>
          </div>
          <span class="text-[10px] font-mono text-slate-400">${source}</span>
        </div>

        <h3 class="text-base font-bold text-slate-900 dark:text-slate-100 leading-snug mb-2">
          ${title}
        </h3>

        ${summary ? `
          <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed mb-3">
            ${summary}
          </p>
        ` : ''}

        ${insight ? `
          <div class="p-2.5 rounded-xl bg-white/80 dark:bg-slate-900/80 border border-indigo-100 dark:border-indigo-900/60 text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed flex items-start gap-1.5">
            <span>💡</span>
            <div class="font-medium">
              <span class="font-bold mr-1">${t.aiTakePrefix}:</span>${escapeHtml(insight)}
            </div>
          </div>
        ` : ''}
      </article>
    `;
  }

  function renderSkeleton() {
    return Array.from({ length: 4 }).map(() => `
      <div class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 space-y-3 shimmer-box shadow-card">
        <div class="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-full h-5 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-3/4 h-5 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-full h-16 bg-slate-100 dark:bg-slate-800/50 rounded-xl"></div>
      </div>
    `).join('');
  }

  // 11. Article Detail Bottom Sheet Modal
  function openArticleModal(itemId) {
    if (!cachedData) return;
    let found = null;
    const allPools = [
      ...((cachedData.grouped && cachedData.grouped.news) || []),
      ...(cachedData.top_three || [])
    ];
    for (const it of allPools) {
      if (String(it.id) === String(itemId)) {
        found = it;
        break;
      }
    }
    if (!found) return;

    const modalOverlay = document.getElementById('article-modal-overlay');
    const modalContent = document.getElementById('article-modal-content');
    if (!modalOverlay || !modalContent) return;

    const title = escapeHtml((isZh ? (found.title_zh || found.title) : (found.title_en || found.title)) || '');
    const source = escapeHtml(found.source || 'AI Radar');
    const url = found.url || '#';
    const analysis = found.ai_analysis || {};
    const briefing = escapeHtml(isZh ? (analysis.briefing_zh || found.summary_zh || found.content_snippet) : (analysis.briefing_en || found.summary_en || found.content_snippet));
    const insight = escapeHtml(isZh ? analysis.insight_zh : analysis.insight_en);

    // Full text with ad noise cleaning
    let fullText = isZh ? (found.article_content_zh || found.article_content || '') : (found.article_content || found.article_content_zh || '');
    fullText = String(fullText).trim();

    const adNoise = [
      /want more .*? in your (?:news )?feed/i,
      /add \w+ (?:in|to) google/i,
      /想要在新闻源中看到更多/i,
      /在\s*google\s*中添加/i,
      /have a tip\??/i,
      /contact this reporter/i,
      /有小费吗/i,
      /联系记者/i,
      /安全共享信息/i,
      /sharing information securely/i
    ];

    const paras = fullText
      ? fullText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 20 && !adNoise.some(r => r.test(p)))
      : [];

    modalContent.innerHTML = `
      <!-- Pull handle -->
      <div class="pt-2.5 pb-1 flex justify-center cursor-pointer" onclick="window.MobileApp.closeArticle()">
        <div class="w-10 h-1 bg-slate-300 dark:bg-slate-700 rounded-full"></div>
      </div>

      <div class="sticky top-0 z-10 flex items-center justify-between px-4 py-2.5 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800">
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 text-xs font-bold font-mono">
            ${source}
          </span>
          <span class="text-xs text-slate-400 font-mono">${formatTimeAgo(found.raw_published_at)}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <button 
            type="button"
            onclick="window.MobileApp.shareArticle('${found.id}')"
            class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center justify-center font-bold text-sm active:scale-90"
            title="${t.shareBtn}"
          >
            🔗
          </button>
          <button 
            type="button"
            onclick="window.MobileApp.closeArticle()" 
            class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center justify-center font-bold text-sm active:scale-90"
          >
            ✕
          </button>
        </div>
      </div>

      <div class="p-4 space-y-4 overflow-y-auto max-h-[78vh] pb-14 no-scrollbar">
        <h2 class="text-lg font-bold text-slate-900 dark:text-slate-100 leading-snug">
          ${title}
        </h2>

        ${briefing ? `
          <div class="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/80 space-y-2">
            <h4 class="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
              ${t.briefingTitle}
            </h4>
            <p class="text-xs text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
              ${briefing}
            </p>
          </div>
        ` : ''}

        ${insight ? `
          <div class="p-3.5 rounded-2xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200/60 dark:border-purple-800/60 space-y-2">
            <h4 class="text-xs font-bold text-purple-900 dark:text-purple-200 flex items-center gap-1.5">
              ${t.insightTitle}
            </h4>
            <p class="text-xs text-purple-950 dark:text-purple-100 leading-relaxed font-medium">
              ${insight}
            </p>
          </div>
        ` : ''}

        ${paras.length > 0 ? `
          <div class="space-y-3 pt-2 border-t border-slate-200/60 dark:border-slate-800">
            <h4 class="text-xs font-bold text-slate-900 dark:text-slate-100">
              ${t.coverageTitle}
            </h4>
            <div class="space-y-3 text-[13px] text-slate-700 dark:text-slate-300 leading-relaxed">
              ${paras.map(p => `<p class="whitespace-pre-line">${escapeHtml(p)}</p>`).join('')}
            </div>
          </div>
        ` : ''}

        <div class="pt-4 border-t border-slate-200/80 dark:border-slate-800">
          <a 
            href="${url}" 
            target="_blank" 
            rel="noopener noreferrer"
            class="block w-full py-3 text-center bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-md active:scale-98 transition-all"
          >
            ${t.viewOriginal}
          </a>
        </div>
      </div>
    `;

    modalOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    // Click outside to dismiss
    modalOverlay.onclick = (e) => {
      if (e.target === modalOverlay) closeArticleModal();
    };
  }

  function closeArticleModal() {
    const modalOverlay = document.getElementById('article-modal-overlay');
    if (modalOverlay) {
      modalOverlay.classList.add('hidden');
    }
    document.body.style.overflow = '';
  }

  // 12. Tweet Language In-Place Toggle
  function toggleTweetLang(itemId) {
    if (!cachedData) return;
    const tweets = (cachedData.grouped && cachedData.grouped.celebrity) || (cachedData.celebrity) || [];
    const found = tweets.find(it => String(it.id) === String(itemId));
    if (!found) return;

    const current = tweetLangState[itemId] || (isZh ? 'zh' : 'en');
    const next = current === 'zh' ? 'en' : 'zh';
    tweetLangState[itemId] = next;

    const textZh = found.full_text_zh || found.quote_zh || found.summary_zh || found.title_zh || '';
    const textEn = found.full_text_en || found.quote_en || found.summary_en || found.title_en || found.title || '';
    const textEl = document.getElementById(`tweet-text-${itemId}`);
    const btnEl = document.getElementById(`tweet-toggle-btn-${itemId}`);

    if (textEl) {
      textEl.textContent = next === 'zh' ? (textZh || textEn) : (textEn || textZh);
    }
    if (btnEl) {
      btnEl.textContent = next === 'zh' ? t.toggleLangEn : t.toggleLangZh;
    }
  }

  // 13. Navigation Tab Switching & Hash Persistence
  function switchTab(newTab) {
    if (currentTab === newTab && currentFilter === 'all') return;
    currentTab = newTab;
    currentFilter = 'all';
    displayLimit = 20;

    // Update URL hash without causing page jump
    try {
      if (history.replaceState) {
        history.replaceState(null, '', '#' + newTab);
      } else {
        window.location.hash = '#' + newTab;
      }
    } catch (e) {}

    // Update top tabs
    document.querySelectorAll('[data-tab-target]').forEach(el => {
      const isTarget = el.dataset.tabTarget === newTab;
      if (isTarget) {
        el.className = 'flex-1 py-2.5 text-center text-xs font-bold text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 transition-all';
      } else {
        el.className = 'flex-1 py-2.5 text-center text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all';
      }
    });

    // Update bottom dock
    document.querySelectorAll('[data-dock-target]').forEach(el => {
      const isTarget = el.dataset.dockTarget === newTab;
      el.classList.toggle('text-indigo-600', isTarget);
      el.classList.toggle('dark:text-indigo-400', isTarget);
      el.classList.toggle('text-slate-400', !isTarget);
      const dot = el.querySelector('.dock-active-dot');
      if (dot) dot.classList.toggle('opacity-100', isTarget);
      if (dot) dot.classList.toggle('opacity-0', !isTarget);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
    renderCurrentView();
  }

  function setFilter(filterId) {
    currentFilter = filterId;
    displayLimit = 20;
    renderCurrentView();
  }

  function loadMore() {
    displayLimit += PAGE_STEP;
    renderCurrentView();
  }

  function handleSearch(evt) {
    searchQuery = evt.target.value || '';
    displayLimit = 20;
    const clearBtn = document.getElementById('mobile-search-clear');
    if (clearBtn) {
      clearBtn.classList.toggle('hidden', !searchQuery);
    }
    renderCurrentView();
  }

  function clearSearch() {
    const input = document.getElementById('mobile-search-input');
    if (input) {
      input.value = '';
      searchQuery = '';
      const clearBtn = document.getElementById('mobile-search-clear');
      if (clearBtn) clearBtn.classList.add('hidden');
      displayLimit = 20;
      renderCurrentView();
    }
  }

  function toggleSearchBox() {
    const box = document.getElementById('mobile-search-box');
    if (!box) return;
    box.classList.toggle('hidden');
    if (!box.classList.contains('hidden')) {
      const input = document.getElementById('mobile-search-input');
      if (input) input.focus();
    }
  }

  // 14. Mobile Language Switcher Action Sheet (All 31 Languages Supported)
  function renderLanguagePickerList(query = '') {
    const container = document.getElementById('lang-picker-list');
    if (!container) return;

    const q = (query || '').trim().toLowerCase();
    const filtered = q
      ? ALL_SITE_LANGUAGES.filter(item => 
          item.id.toLowerCase().includes(q) || 
          item.native.toLowerCase().includes(q) || 
          item.nameEn.toLowerCase().includes(q) || 
          item.nameZh.includes(q) ||
          item.code.toLowerCase().includes(q)
        )
      : ALL_SITE_LANGUAGES;

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="py-8 text-center text-slate-400 text-xs">
          ${isZh ? '未找到相关语言' : 'No matching languages found'}
        </div>
      `;
      return;
    }

    const groups = ['popular', 'european', 'apac'];
    let html = '';

    groups.forEach(grp => {
      const groupItems = filtered.filter(it => it.group === grp);
      if (groupItems.length === 0) return;

      const groupTitle = isZh ? LANG_GROUPS[grp].zh : LANG_GROUPS[grp].en;
      html += `
        <div class="pt-2 pb-1 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-1">
          ${groupTitle}
        </div>
        <div class="space-y-1.5">
          ${groupItems.map(item => {
            const isSelected = (currentSiteLang === item.id);
            const activeCardStyle = isSelected
              ? 'bg-indigo-50/80 dark:bg-indigo-950/50 border-indigo-300 dark:border-indigo-700 font-bold'
              : 'bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border-slate-200/80 dark:border-slate-700/80';
            const subName = isZh ? item.nameZh : item.nameEn;
            return `
              <button 
                type="button"
                onclick="window.MobileApp.selectLanguage('${item.id}')"
                class="w-full p-2.5 rounded-xl flex items-center justify-between border touch-card cursor-pointer transition-colors ${activeCardStyle}"
              >
                <div class="flex items-center gap-3">
                  <span class="text-xl">${item.flag}</span>
                  <div class="text-left">
                    <div class="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <span>${item.native}</span>
                      ${isSelected ? `<span class="px-1 py-0.2 rounded bg-indigo-600 text-white text-[9px] font-bold">Active</span>` : ''}
                    </div>
                    <div class="text-[10px] text-slate-500 dark:text-slate-400 font-medium">${subName}</div>
                  </div>
                </div>
                ${isSelected ? '<span class="text-indigo-600 dark:text-indigo-400 font-bold text-sm">✓</span>' : '<span class="text-slate-300 dark:text-slate-600 text-xs">→</span>'}
              </button>
            `;
          }).join('')}
        </div>
      `;
    });

    container.innerHTML = html;
  }

  function filterLanguageList(e) {
    const q = e && e.target ? e.target.value : '';
    renderLanguagePickerList(q);
  }

  function openLangPicker() {
    const modal = document.getElementById('lang-picker-modal');
    if (modal) {
      renderLanguagePickerList('');
      const searchInput = document.getElementById('lang-picker-search');
      if (searchInput) searchInput.value = '';
      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      modal.onclick = (e) => {
        if (e.target === modal) closeLangPicker();
      };
    }
  }

  function closeLangPicker() {
    const modal = document.getElementById('lang-picker-modal');
    if (modal) {
      modal.classList.add('hidden');
    }
    document.body.style.overflow = '';
  }

  function selectLanguage(targetLang) {
    closeLangPicker();
    const search = window.location.search || '';
    const hash = window.location.hash || (currentTab && currentTab !== 'all' ? '#' + currentTab : '');

    // 1. Simplified Chinese (Native pre-rendered Chinese SSG)
    if (targetLang === 'chinese_simplified') {
      localStorage.setItem('ai_radar_user_site_lang', 'chinese_simplified');
      localStorage.setItem('ai_radar_user_lang', 'zh');
      if (!window.location.pathname.startsWith('/zh')) {
        window.location.href = '/zh/m' + search + hash;
        return;
      }
      currentSiteLang = 'chinese_simplified';
      if (window.ChineseConverter && window.ChineseConverter.revertDomToSimplified) {
        try { window.ChineseConverter.revertDomToSimplified(); } catch (e) {}
      }
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      updateLangButtonLabel('chinese_simplified');
      showToast('已切换至简体中文');
      return;
    }

    // 2. Traditional Chinese (Native Chinese SSG + ChineseConverter)
    if (targetLang === 'chinese_traditional') {
      localStorage.setItem('ai_radar_user_site_lang', 'chinese_traditional');
      localStorage.setItem('ai_radar_user_lang', 'zh');
      if (!window.location.pathname.startsWith('/zh')) {
        window.location.href = '/zh/m' + search + hash;
        return;
      }
      currentSiteLang = 'chinese_traditional';
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      ensureChineseConverter(() => {
        if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
          try { window.ChineseConverter.convertDomToTraditional(); } catch (e) {}
        }
      });
      updateLangButtonLabel('chinese_traditional');
      showToast('已切換至繁體中文');
      return;
    }

    // 3. English (Native pre-rendered Global English SSG)
    if (targetLang === 'english') {
      localStorage.setItem('ai_radar_user_site_lang', 'english');
      localStorage.setItem('ai_radar_user_lang', 'en');
      if (window.location.pathname.startsWith('/zh')) {
        window.location.href = '/m' + search + hash;
        return;
      }
      currentSiteLang = 'english';
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      updateLangButtonLabel('english');
      showToast('Switched to English');
      return;
    }

    // 4. All other 28 global languages via Translate.js Client Edge engine
    localStorage.setItem('ai_radar_user_site_lang', targetLang);
    currentSiteLang = targetLang;
    if (window.ChineseConverter && window.ChineseConverter.revertDomToSimplified) {
      try { window.ChineseConverter.revertDomToSimplified(); } catch (e) {}
    }
    loadTranslatePlugin(targetLang);
  }

  function updateLangButtonLabel(lang) {
    const flagEl = document.getElementById('lang-btn-flag');
    const textEl = document.getElementById('lang-btn-text');
    if (!flagEl || !textEl) return;
    const found = ALL_SITE_LANGUAGES.find(it => it.id === lang);
    if (found) {
      flagEl.textContent = found.flag;
      textEl.textContent = found.code;
    } else {
      flagEl.textContent = '🌐';
      textEl.textContent = 'Lang';
    }
  }

  function loadTranslatePlugin(targetLang) {
    const exec = () => {
      try {
        if (typeof translate !== 'undefined') {
          translate.selectLanguageTag.show = false;
          translate.service.use('client.edge');
          translate.language.setLocal(window.location.pathname.startsWith('/zh') ? 'chinese_simplified' : 'english');
          translate.ignore.class.push('notranslate');
          translate.ignore.id.push('lang-picker-modal');
          translate.ignore.id.push('article-modal-overlay');
          translate.execute();
          translate.changeLanguage(targetLang);
          updateLangButtonLabel(targetLang);
          const langObj = ALL_SITE_LANGUAGES.find(it => it.id === targetLang);
          const name = langObj ? (isZh ? langObj.nameZh : langObj.nameEn) : targetLang;
          showToast(isZh ? `已实时翻译为 ${name}` : `Translated to ${name}`);
        }
      } catch (err) {
        console.warn('Translate execution error:', err);
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

  function switchLanguage() {
    openLangPicker();
  }

  // Switch to Desktop preserving category tab & queries
  function switchToDesktop() {
    sessionStorage.setItem('prefer_desktop', '1');
    const hashMapping = {
      news: '#news',
      social: '#celebrity',
      videos: '#videos',
      top: '#all'
    };
    const targetHash = hashMapping[currentTab] || ('#' + currentTab);
    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set('view', 'desktop');
    const targetBase = isZh ? '/zh' : '';
    window.location.href = (targetBase || '/') + '?' + searchParams.toString() + targetHash;
  }

  // 15. Article Share Helper
  async function shareArticle(itemId) {
    const allPools = [
      ...((cachedData && cachedData.grouped && cachedData.grouped.news) || []),
      ...((cachedData && cachedData.top_three) || [])
    ];
    const found = allPools.find(it => String(it.id) === String(itemId));
    const title = found ? (isZh ? (found.title_zh || found.title) : (found.title_en || found.title)) : 'AI News Radar';
    const shareUrl = found && found.url ? found.url : window.location.href;

    if (navigator.share) {
      try {
        await navigator.share({
          title: title,
          text: title,
          url: shareUrl
        });
        return;
      } catch (e) {}
    }

    // Clipboard fallback
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(shareUrl);
        showToast(t.copiedToast);
      } else {
        const input = document.createElement('input');
        input.value = shareUrl;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        document.body.removeChild(input);
        showToast(t.copiedToast);
      }
    } catch (e) {
      showToast(shareUrl);
    }
  }

  // 16. Floating Back to Top Button
  function initMobileBackToTop() {
    const btn = document.getElementById('btn-back-to-top');
    if (!btn) return;
    window.addEventListener('scroll', () => {
      if (window.scrollY > 300) {
        btn.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-3');
        btn.classList.add('opacity-100', 'pointer-events-auto', 'translate-y-0');
      } else {
        btn.classList.add('opacity-0', 'pointer-events-none', 'translate-y-3');
        btn.classList.remove('opacity-100', 'pointer-events-auto', 'translate-y-0');
      }
    }, { passive: true });
    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // 17. Smart Visitor Language Suggestion
  function checkAndShowLangSuggestion() {
    try {
      if (sessionStorage.getItem('ai_radar_m_lang_dismissed')) return;
      const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
      const isChineseEnv = navLang.startsWith('zh');
      const isEnglishEnv = navLang.startsWith('en');

      const banner = document.getElementById('mobile-lang-suggest-banner');
      if (!banner) return;

      if (isChineseEnv && !isZh) {
        banner.innerHTML = `
          <div class="mx-3 my-2 p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/80 dark:border-indigo-800/70 flex items-center justify-between gap-2 shadow-xs notranslate">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-sm">🌐</span>
              <p class="text-[11px] text-indigo-950 dark:text-indigo-200 truncate font-medium">
                ${t.suggestZhDesc}
              </p>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button 
                type="button"
                onclick="window.MobileApp.selectLanguage('chinese_simplified')" 
                class="px-2 py-1 rounded-lg bg-indigo-600 text-white font-bold text-[10px] shadow-xs active:scale-95 cursor-pointer"
              >
                ${t.suggestSwitchBtn}
              </button>
              <button 
                type="button"
                onclick="window.MobileApp.dismissLangSuggest()" 
                class="text-slate-400 hover:text-slate-600 text-xs px-1 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
        `;
        banner.classList.remove('hidden');
      } else if (isEnglishEnv && isZh) {
        banner.innerHTML = `
          <div class="mx-3 my-2 p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/80 border border-indigo-200/80 dark:border-indigo-800/70 flex items-center justify-between gap-2 shadow-xs notranslate">
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-sm">🌐</span>
              <p class="text-[11px] text-indigo-950 dark:text-indigo-200 truncate font-medium">
                ${t.suggestEnDesc}
              </p>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button 
                type="button"
                onclick="window.MobileApp.selectLanguage('english')" 
                class="px-2 py-1 rounded-lg bg-indigo-600 text-white font-bold text-[10px] shadow-xs active:scale-95 cursor-pointer"
              >
                ${t.suggestSwitchBtn}
              </button>
              <button 
                type="button"
                onclick="window.MobileApp.dismissLangSuggest()" 
                class="text-slate-400 hover:text-slate-600 text-xs px-1 cursor-pointer"
              >
                ✕
              </button>
            </div>
          </div>
        `;
        banner.classList.remove('hidden');
      }
    } catch (e) {}
  }

  function dismissLangSuggest() {
    try {
      sessionStorage.setItem('ai_radar_m_lang_dismissed', '1');
      const banner = document.getElementById('mobile-lang-suggest-banner');
      if (banner) banner.classList.add('hidden');
    } catch (e) {}
  }

  // 18. Expose to Window
  window.MobileApp = {
    init() {
      try {
        sessionStorage.removeItem('prefer_desktop');
      } catch (e) {}
      
      initTheme();

      // Check saved language preference from localStorage
      const savedSiteLang = localStorage.getItem('ai_radar_user_site_lang');
      if (savedSiteLang) {
        currentSiteLang = savedSiteLang;
        if (savedSiteLang === 'chinese_traditional' && isZh) {
          ensureChineseConverter(() => {
            if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
              window.ChineseConverter.convertDomToTraditional();
            }
          });
        } else if (savedSiteLang !== 'english' && savedSiteLang !== 'chinese_simplified' && savedSiteLang !== 'chinese_traditional') {
          loadTranslatePlugin(savedSiteLang);
        }
      }
      updateLangButtonLabel(currentSiteLang);

      // Parse URL hash to activate requested tab
      const rawHash = (window.location.hash || '').replace('#', '').trim().toLowerCase();
      if (rawHash === 'social' || rawHash === 'celebrity') {
        currentTab = 'social';
      } else if (rawHash === 'videos') {
        currentTab = 'videos';
      } else if (rawHash === 'top' || rawHash === 'top3') {
        currentTab = 'top';
      } else {
        currentTab = 'news';
      }

      // Sync active tab state to navigation DOM
      document.querySelectorAll('[data-tab-target]').forEach(el => {
        const isTarget = el.dataset.tabTarget === currentTab;
        if (isTarget) {
          el.className = 'flex-1 py-2.5 text-center text-xs font-bold text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400 transition-all';
        } else {
          el.className = 'flex-1 py-2.5 text-center text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-all';
        }
      });
      document.querySelectorAll('[data-dock-target]').forEach(el => {
        const isTarget = el.dataset.dockTarget === currentTab;
        el.classList.toggle('text-indigo-600', isTarget);
        el.classList.toggle('dark:text-indigo-400', isTarget);
        el.classList.toggle('text-slate-400', !isTarget);
        const dot = el.querySelector('.dock-active-dot');
        if (dot) dot.classList.toggle('opacity-100', isTarget);
        if (dot) dot.classList.toggle('opacity-0', !isTarget);
      });

      // Check URL query parameters for search
      const q = new URLSearchParams(window.location.search).get('q');
      if (q) {
        searchQuery = q;
        const input = document.getElementById('mobile-search-input');
        if (input) input.value = q;
        const searchBox = document.getElementById('mobile-search-box');
        if (searchBox) searchBox.classList.remove('hidden');
      }

      loadData();
      initMobileBackToTop();
      checkAndShowLangSuggestion();
    },
    refresh() {
      const refreshBtn = document.getElementById('refresh-btn-icon');
      if (refreshBtn) refreshBtn.classList.add('animate-spin');
      loadData(true).finally(() => {
        setTimeout(() => {
          if (refreshBtn) refreshBtn.classList.remove('animate-spin');
        }, 500);
      });
    },
    switchTab,
    setFilter,
    loadMore,
    handleSearch,
    clearSearch,
    toggleSearchBox,
    openArticle: openArticleModal,
    closeArticle: closeArticleModal,
    toggleTheme,
    openLangPicker,
    closeLangPicker,
    selectLanguage,
    filterLanguageList,
    renderLanguagePickerList,
    switchLanguage,
    switchToDesktop,
    shareArticle,
    toggleTweetLang,
    dismissLangSuggest
  };

  // Bootstrap when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.MobileApp.init());
  } else {
    window.MobileApp.init();
  }

})();
