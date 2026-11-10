/**
 * mobile.js - High-Performance Mobile Web App Controller
 * Dedicated lightweight engine for mobile screens (< 768px).
 * Focused strictly on News (资讯), Social Tweets (社交推文), and Videos (实战视频).
 */

(function() {
  'use strict';

  // 1. Language & Environment
  const isZh = Boolean(
    window.__IS_ZH || 
    window.location.pathname.startsWith('/zh') || 
    new URLSearchParams(window.location.search).get('lang') === 'zh'
  );

  const I18N = {
    zh: {
      appName: 'AI 资讯雷达',
      mobileEdition: '移动专版',
      live: '实时更新',
      refresh: '刷新',
      searchPlaceholder: '搜索 AI 快讯、推文与视频...',
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
      readFull: '阅读全文 & AI解读 →',
      viewOriginal: '直达源站 ↗',
      openOnX: '在 𝕏 查看原文 ↗',
      modalTitle: '资讯深度解析',
      briefingTitle: '🎯 核心事实提炼 (5W1H)',
      insightTitle: '🤖 AI 智库犀利研判',
      coverageTitle: '📰 深度报道原文实录',
      toggleLangZh: '中文译文',
      toggleLangEn: '英文原文',
      switchToDesktop: '💻 切换至电脑完整版',
      justNow: '刚刚',
      minsAgo: '分钟前',
      hoursAgo: '小时前',
      daysAgo: '天前',
      views: '浏览',
      likes: '赞',
      retweets: '转推'
    },
    en: {
      appName: 'AI News Radar',
      mobileEdition: 'Mobile App',
      live: 'LIVE',
      refresh: 'Refresh',
      searchPlaceholder: 'Search news, tweets & videos...',
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
      toggleLangZh: 'Chinese',
      toggleLangEn: 'English',
      switchToDesktop: '💻 Switch to Desktop Version',
      justNow: 'just now',
      minsAgo: 'm ago',
      hoursAgo: 'h ago',
      daysAgo: 'd ago',
      views: 'views',
      likes: 'likes',
      retweets: 'RT'
    }
  };

  const t = isZh ? I18N.zh : I18N.en;

  // 2. Global State
  let cachedData = null;
  let currentTab = 'news'; // 'news' | 'social' | 'videos' | 'top'
  let currentFilter = 'all';
  let searchQuery = '';
  let displayLimit = 20;
  const PAGE_STEP = 20;

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

  // 4. Time Formatting
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

  // 5. Image & Avatar URL Optimization
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

  // 6. Data Loading & Extraction
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
              <button onclick="window.MobileApp.refresh()" class="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold shadow-md active:scale-95">
                ${t.refresh}
              </button>
            </div>
          `;
        }
        return;
      }
    }

    renderCurrentView();
  }

  // 7. Sub-filters for current tab
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
            : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium';
          return `
            <button 
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

  // 8. Render Current Channel View
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
          <p class="text-xs">${t.noMatch}</p>
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
          onclick="window.MobileApp.loadMore()" 
          class="w-full py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-xs font-bold rounded-2xl shadow-xs active:scale-98 transition-all"
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
  }

  // 9. Card Renderers
  function renderNewsCard(item, idx = 0) {
    const title = escapeHtml((isZh ? (item.title_zh || item.title) : (item.title_en || item.title)) || '');
    const summary = escapeHtml((isZh ? (item.summary_zh || item.content_snippet) : (item.summary_en || item.content_snippet)) || '');
    const source = escapeHtml(item.source || 'AI Radar');
    const timeAgo = formatTimeAgo(item.raw_published_at);
    const imgUrl = item.image_url ? optimizeImageUrl(item.image_url, 480) : '';
    const hasDeepArticle = Boolean((item.article_content || item.article_content_zh) && String(item.article_content || item.article_content_zh).length > 200);
    const insightText = item.ai_analysis && (isZh ? item.ai_analysis.insight_zh : item.ai_analysis.insight_en);

    return `
      <div 
        class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 shadow-xs touch-card transition-all cursor-pointer"
        onclick="window.MobileApp.openArticle('${item.id}')"
      >
        <div class="flex items-center justify-between text-[11px] mb-2">
          <div class="flex items-center gap-1.5">
            <span class="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold font-mono">
              ${source}
            </span>
            ${item.is_breaking ? `<span class="px-1.5 py-0.5 rounded bg-rose-500 text-white font-bold text-[10px]">⚡ ${isZh ? '突发' : 'BREAKING'}</span>` : ''}
            ${hasDeepArticle ? `<span class="px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 font-bold text-[10px]">📰 ${isZh ? '深度实录' : 'IN-DEPTH'}</span>` : ''}
          </div>
          <span class="text-slate-400 font-mono text-[10px]">${timeAgo}</span>
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
          <div class="rounded-xl overflow-hidden aspect-video bg-slate-100 dark:bg-slate-800 mb-3">
            <img src="${imgUrl}" width="480" height="270" alt="${title}" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async" onerror="this.parentElement.style.display='none'">
          </div>
        ` : ''}

        ${insightText ? `
          <div class="p-2.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200/50 dark:border-purple-800/40 text-[11px] text-purple-900 dark:text-purple-200 leading-relaxed flex items-start gap-1.5 mb-3">
            <span class="text-xs">🤖</span>
            <span class="line-clamp-2">${escapeHtml(insightText)}</span>
          </div>
        ` : ''}

        <div class="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800/60 text-[11px] text-indigo-600 dark:text-indigo-400 font-bold">
          <span>${t.readFull}</span>
          <span class="text-slate-400">↗</span>
        </div>
      </div>
    `;
  }

  function renderSocialCard(item, idx = 0) {
    const authorName = escapeHtml(item.author || 'AI Pioneer');
    const authorHandle = escapeHtml(item.author_handle || '');
    const authorRole = escapeHtml(isZh ? (item.author_role || item.author_role_en || '') : (item.author_role_en || item.author_role || ''));
    const avatar = item.author_avatar || `https://api.dicebear.com/7.x/bottts/svg?seed=${authorHandle || 'vip'}`;
    const timeAgo = formatTimeAgo(item.raw_published_at);
    const contentZh = item.full_text_zh || item.quote_zh || item.summary_zh || item.title_zh || '';
    const contentEn = item.full_text_en || item.quote_en || item.summary_en || item.title_en || item.title || '';
    const displayContent = escapeHtml(isZh ? (contentZh || contentEn) : (contentEn || contentZh));
    const rawUrl = item.url || (authorHandle && item.status_id ? `https://x.com/${authorHandle}/status/${item.status_id}` : '#');
    const metrics = item.metrics || {};

    const mediaList = item.media_urls || (item.image_url ? [item.image_url] : []);

    return `
      <div class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 shadow-xs touch-card transition-all">
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
            <span class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-[10px] font-semibold font-mono truncate max-w-[110px]">
              ${authorRole}
            </span>
          ` : ''}
        </div>

        <p class="text-[14px] text-slate-800 dark:text-slate-200 leading-relaxed whitespace-pre-line mb-3 font-normal">
          ${displayContent}
        </p>

        ${mediaList.length > 0 ? `
          <div class="rounded-xl overflow-hidden mb-3 aspect-video bg-slate-100 dark:bg-slate-800">
            <img src="${optimizeImageUrl(mediaList[0], 640)}" width="640" height="360" alt="Tweet media" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async">
          </div>
        ` : ''}

        <div class="flex items-center justify-between text-[11px] text-slate-400 font-mono pt-2 border-t border-slate-100 dark:border-slate-800/60">
          <div class="flex items-center gap-4">
            ${metrics.views ? `<span>👁️ ${metrics.views}</span>` : ''}
            ${metrics.likes ? `<span>❤️ ${metrics.likes}</span>` : ''}
            ${metrics.retweets ? `<span>🔁 ${metrics.retweets}</span>` : ''}
          </div>
          <a href="${rawUrl}" target="_blank" rel="noopener noreferrer" class="text-indigo-600 dark:text-indigo-400 font-bold flex items-center gap-0.5">
            <span>${t.openOnX}</span>
          </a>
        </div>
      </div>
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
        class="block bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl overflow-hidden shadow-xs touch-card transition-all"
      >
        <div class="relative aspect-video bg-slate-900">
          ${imgUrl ? `
            <img src="${imgUrl}" width="640" height="360" alt="${title}" class="w-full h-full object-cover" ${idx === 0 ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'} decoding="async">
          ` : ''}
          <div class="absolute inset-0 bg-black/30 flex items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-rose-600/90 text-white flex items-center justify-center text-lg pl-1 shadow-lg">
              ▶
            </div>
          </div>
          <span class="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/75 text-white text-[10px] font-mono font-bold">
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
      <div 
        class="bg-gradient-to-br from-indigo-50/60 to-purple-50/40 dark:from-indigo-950/30 dark:to-purple-950/20 border border-indigo-200/60 dark:border-indigo-800/50 rounded-2xl p-4 shadow-xs touch-card transition-all cursor-pointer"
        onclick="window.MobileApp.openArticle('${item.id}')"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold flex items-center justify-center">
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
            <span class="font-medium">${escapeHtml(insight)}</span>
          </div>
        ` : ''}
      </div>
    `;
  }

  function renderSkeleton() {
    return Array.from({ length: 4 }).map(() => `
      <div class="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-4 space-y-3 shimmer-box">
        <div class="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-full h-5 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-3/4 h-5 bg-slate-200 dark:bg-slate-800 rounded"></div>
        <div class="w-full h-16 bg-slate-100 dark:bg-slate-800/50 rounded-xl"></div>
      </div>
    `).join('');
  }

  // 10. Article Detail Sheet / Modal
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
      <div class="sticky top-0 z-10 flex items-center justify-between p-4 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800">
        <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 text-xs font-bold font-mono">
            ${source}
          </span>
          <span class="text-xs text-slate-400 font-mono">${formatTimeAgo(found.raw_published_at)}</span>
        </div>
        <button onclick="window.MobileApp.closeArticle()" class="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 flex items-center justify-center font-bold text-base active:scale-90">
          ✕
        </button>
      </div>

      <div class="p-4 space-y-5 overflow-y-auto max-h-[82vh] pb-12">
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
  }

  function closeArticleModal() {
    const modalOverlay = document.getElementById('article-modal-overlay');
    if (modalOverlay) {
      modalOverlay.classList.add('hidden');
    }
    document.body.style.overflow = '';
  }

  // 11. Navigation Tab Switching
  function switchTab(newTab) {
    if (currentTab === newTab && currentFilter === 'all') return;
    currentTab = newTab;
    currentFilter = 'all';
    displayLimit = 20;

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
    renderCurrentView();
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

  function switchToDesktop() {
    sessionStorage.setItem('prefer_desktop', '1');
    const target = isZh ? '/zh/?view=desktop' : '/?view=desktop';
    window.location.href = target;
  }

  function switchLanguage() {
    const target = isZh ? '/m' : '/zh/m';
    window.location.href = target;
  }

  // 12. Expose to Window
  window.MobileApp = {
    init() {
      try {
        sessionStorage.removeItem('prefer_desktop');
      } catch (e) {}
      initTheme();
      loadData();
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
    toggleSearchBox,
    openArticle: openArticleModal,
    closeArticle: closeArticleModal,
    toggleTheme,
    switchLanguage,
    switchToDesktop
  };

  document.addEventListener('DOMContentLoaded', window.MobileApp.init);
})();
