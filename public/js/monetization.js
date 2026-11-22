/**
 * AI News Radar - Unified Monetization & Native Partner Engine (v2.0)
 *
 * Visual Graphic Ad Showcase & Performance Engine:
 *   - Visual Graphic Banners & Rich Thumbnails for every partner card
 *   - Dual Layouts: Horizontal Leaderboard Strip & 3-Column Visual Grid
 *   - Zero Cumulative Layout Shift (CLS = 0) with reserved min-heights
 *   - Dark/Light Theme Auto-Adaptation (Glassmorphism + Neon Accents)
 *   - Deferred loading + IntersectionObserver (0ms LCP impact)
 *   - AdBlock-proof native affiliate routing
 */
(function () {
  'use strict';

  // =========================================================================
  // 1. CENTRALIZED AD NETWORK & AFFILIATE CONFIGURATION
  // =========================================================================
  var CONFIG = window.AINR_MONETIZATION_CONFIG || {
    networks: {
      aads: {
        enabled: false,
        leaderboardUnitId: '',
        inContentUnitId: '',
        mobileUnitId: ''
      },
      adsterra: {
        enabled: false,
        containerId: '',
        scriptSrc: ''
      },
      ethicalads: {
        enabled: false,
        publisher: ''
      },
      adsense: {
        enabled: false,
        client: 'ca-pub-4912808437101130'
      }
    },

    sponsorUrl: {
      en: '/contact#sponsor',
      zh: '/zh/contact#sponsor'
    },

    partners: {
      en: [
        {
          id: 'elevenlabs-voice',
          badge: 'VOICE AGENT API',
          accent: 'indigo',
          icon: '🎙️',
          name: 'ElevenLabs Frontier Voice AI',
          tagline: 'Industry-leading real-time voice streaming, voice cloning, and multilingual speech synthesis.',
          cta: 'Try Voice AI Free',
          hint: 'Free 10,000 Credits/mo',
          image: '/images/partners/elevenlabs_banner.svg',
          url: 'https://try.elevenlabs.io/bwnugci42q5y'
        },
        {
          id: 'elevenlabs-agents',
          badge: 'CONVERSATIONAL AGENTS',
          accent: 'sky',
          icon: '⚡',
          name: 'ElevenLabs Conversational AI Agents',
          tagline: 'Deploy voice-first AI agents in minutes. Real-time WebRTC, ultra-low latency & full SDK support.',
          cta: 'Build Voice Agent',
          hint: 'Latency < 150ms · WebRTC',
          image: '/images/partners/elevenlabs_agents_banner.svg',
          url: 'https://try.elevenlabs.io/bwnugci42q5y'
        },
        {
          id: 'sponsor-direct-en',
          badge: 'FEATURED SLOT',
          accent: 'amber',
          icon: '✨',
          name: 'Promote Your AI Tool on AI News Radar',
          tagline: 'Reach 50,000+ frontier AI engineers, builders, and technical decision-makers daily.',
          cta: 'Submit / Sponsor',
          hint: 'Direct Booking ↗',
          image: '/images/partners/sponsor_banner.svg',
          url: '/contact#sponsor',
          internal: true
        }
      ],
      zh: [
        {
          id: 'elevenlabs-voice-zh',
          badge: '语音合成 & 声音克隆',
          accent: 'indigo',
          icon: '🎙️',
          name: 'ElevenLabs 全球领先 AI 语音与合成',
          tagline: '好莱坞级超逼真声音克隆、多语言实时语音合成与流式开发接口，注册送 10,000 免费额度。',
          cta: '免费体验语音 AI',
          hint: '每月免费领 10,000 额度',
          image: '/images/partners/elevenlabs_banner.svg',
          url: 'https://try.elevenlabs.io/bwnugci42q5y'
        },
        {
          id: 'elevenlabs-agents-zh',
          badge: '对话式语音智能体 SDK',
          accent: 'sky',
          icon: '⚡',
          name: 'ElevenLabs 对话式语音智能体平台',
          tagline: '零配置快速搭建低延迟语音交互智能体，原生支持 WebRTC 与 WebSocket，毫秒级流式响应。',
          cta: '搭建语音智能体',
          hint: '超低延迟 · WebRTC 原生支持',
          image: '/images/partners/elevenlabs_agents_banner.svg',
          url: 'https://try.elevenlabs.io/bwnugci42q5y'
        },
        {
          id: 'sponsor-direct-zh',
          badge: '品牌直投',
          accent: 'amber',
          icon: '✨',
          name: '置顶推广你的 AI 产品与工具',
          tagline: '每日精准触达数万名一线 AI 工程师、独立开发者与科技决策者，支持工具库置顶与官方合作。',
          cta: '申请置顶合作',
          hint: '官方展位直投 ↗',
          image: '/images/partners/sponsor_banner.svg',
          url: '/zh/contact#sponsor',
          internal: true
        }
      ]
    }
  };

  // =========================================================================
  // 2. HELPERS & THEME / LANGUAGE DETECTION
  // =========================================================================
  function isZhPage() {
    var path = (window.location && window.location.pathname) || '';
    var lang = (document.documentElement && document.documentElement.lang) || '';
    return path.indexOf('/zh') === 0 || lang.toLowerCase().indexOf('zh') === 0;
  }

  function isDarkPage() {
    var html = document.documentElement;
    if (html && html.classList && html.classList.contains('dark')) return true;
    return false;
  }

  function esc(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function pickPartners(lang, count, offset) {
    var list = (CONFIG.partners && CONFIG.partners[lang]) || CONFIG.partners.en;
    var out = [];
    for (var i = 0; i < Math.min(count, list.length); i++) {
      out.push(list[(i + (offset || 0)) % list.length]);
    }
    return out;
  }

  function injectStylesOnce() {
    if (document.getElementById('ainr-monetization-css')) return;
    var style = document.createElement('style');
    style.id = 'ainr-monetization-css';
    style.textContent = [
      '.ainr-slot{box-sizing:border-box;width:100%;font-family:Inter,system-ui,-apple-system,sans-serif;}',
      
      /* Horizontal Leaderboard Card */
      '.ainr-card{position:relative;display:flex;align-items:center;gap:14px;padding:10px 14px;border-radius:14px;text-decoration:none;transition:transform .18s cubic-bezier(0.16,1,0.3,1),border-color .18s ease,box-shadow .18s ease;overflow:hidden;}',
      '.ainr-card:hover{transform:translateY(-1.5px);}',
      '.ainr-theme-light .ainr-card{background:linear-gradient(135deg,#ffffff,#f8fafc);border:1px solid #cbd5e1;color:#0f172a;box-shadow:0 4px 16px -6px rgba(15,23,42,0.08);}',
      '.ainr-theme-light .ainr-card:hover{border-color:#818cf8;box-shadow:0 10px 24px -10px rgba(99,102,241,0.22);}',
      '.ainr-theme-dark .ainr-card{background:linear-gradient(135deg,rgba(15,23,42,0.92),rgba(15,23,42,0.72));border:1px solid rgba(51,65,85,0.85);color:#f1f5f9;box-shadow:0 8px 24px -12px rgba(0,0,0,0.55);backdrop-filter:blur(12px);}',
      '.ainr-theme-dark .ainr-card:hover{border-color:rgba(129,140,248,0.65);box-shadow:0 12px 28px -10px rgba(99,102,241,0.3);}',

      /* Card Thumbnail Image */
      '.ainr-thumb{position:relative;width:140px;height:80px;flex-shrink:0;border-radius:9px;overflow:hidden;background:#090d16;border:1px solid rgba(255,255,255,0.08);box-shadow:0 3px 10px rgba(0,0,0,0.25);}',
      '.ainr-thumb img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s ease;}',
      '.ainr-card:hover .ainr-thumb img{transform:scale(1.05);}',
      '.ainr-thumb-badge{position:absolute;top:5px;left:5px;font-size:8.5px;font-weight:800;padding:1.5px 5.5px;border-radius:4px;background:rgba(15,23,42,0.88);backdrop-filter:blur(4px);color:#f8fafc;border:1px solid rgba(255,255,255,0.18);letter-spacing:.04em;text-transform:uppercase;z-index:2;line-height:1.2;}',

      /* Card Body & Meta */
      '.ainr-body{min-width:0;flex:1;}',
      '.ainr-pill-row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:3px;}',
      '.ainr-pill{display:inline-flex;align-items:center;gap:3px;font-size:9.5px;font-weight:800;padding:1.5px 7px;border-radius:999px;letter-spacing:.04em;text-transform:uppercase;line-height:1.3;}',
      '.ainr-pill-indigo{background:rgba(99,102,241,0.15);color:#818cf8;border:1px solid rgba(99,102,241,0.3);}',
      '.ainr-pill-emerald{background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);}',
      '.ainr-pill-sky{background:rgba(14,165,233,0.15);color:#38bdf8;border:1px solid rgba(14,165,233,0.3);}',
      '.ainr-pill-amber{background:rgba(245,158,11,0.15);color:#fbbf24;border:1px solid rgba(245,158,11,0.3);}',
      '.ainr-verified{font-size:9.5px;font-weight:700;color:#10b981;letter-spacing:.02em;}',
      '.ainr-title{font-size:13.5px;font-weight:800;line-height:1.3;margin:0;letter-spacing:-0.01em;}',
      '.ainr-desc{font-size:11.5px;line-height:1.42;margin:3px 0 0;opacity:0.82;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}',

      /* Action CTA */
      '.ainr-action-wrap{flex-shrink:0;display:flex;flex-direction:column;align-items:flex-end;gap:4px;}',
      '.ainr-cta{display:inline-flex;align-items:center;gap:4px;padding:6.5px 13px;border-radius:9px;font-size:11.5px;font-weight:700;white-space:nowrap;transition:background .15s ease,transform .15s ease;}',
      '.ainr-theme-light .ainr-cta{background:#4f46e5;color:#ffffff;box-shadow:0 2px 8px rgba(79,70,229,0.25);}',
      '.ainr-theme-light .ainr-card:hover .ainr-cta{background:#4338ca;}',
      '.ainr-theme-dark .ainr-cta{background:rgba(99,102,241,0.25);color:#e0e7ff;border:1px solid rgba(129,140,248,0.4);}',
      '.ainr-theme-dark .ainr-card:hover .ainr-cta{background:#4f46e5;color:#ffffff;border-color:#6366f1;}',
      '.ainr-sub-hint{font-size:10px;font-weight:600;opacity:0.65;letter-spacing:.02em;}',

      /* 3-Column Visual Grid Showcase (home-bottom-native) */
      '.ainr-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;}',
      '.ainr-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;}',
      '.ainr-grid-card{position:relative;display:flex;flex-direction:column;border-radius:16px;text-decoration:none;overflow:hidden;transition:transform .2s cubic-bezier(0.16,1,0.3,1),border-color .2s ease,box-shadow .2s ease;}',
      '.ainr-grid-card:hover{transform:translateY(-2.5px);}',
      '.ainr-theme-light .ainr-grid-card{background:#ffffff;border:1px solid #cbd5e1;color:#0f172a;box-shadow:0 4px 16px -6px rgba(15,23,42,0.08);}',
      '.ainr-theme-light .ainr-grid-card:hover{border-color:#818cf8;box-shadow:0 12px 28px -10px rgba(99,102,241,0.2);}',
      '.ainr-theme-dark .ainr-grid-card{background:linear-gradient(135deg,rgba(15,23,42,0.92),rgba(15,23,42,0.72));border:1px solid rgba(51,65,85,0.85);color:#f1f5f9;box-shadow:0 8px 24px -12px rgba(0,0,0,0.55);}',
      '.ainr-theme-dark .ainr-grid-card:hover{border-color:rgba(129,140,248,0.65);box-shadow:0 14px 32px -10px rgba(99,102,241,0.35);}',

      /* Grid Card Image Banner */
      '.ainr-grid-thumb{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;background:#090d16;}',
      '.ainr-grid-thumb img{width:100%;height:100%;object-fit:cover;display:block;transition:transform .35s ease;}',
      '.ainr-grid-card:hover .ainr-grid-thumb img{transform:scale(1.04);}',
      '.ainr-grid-content{padding:14px 16px 16px;display:flex;flex-direction:column;flex:1;}',
      '.ainr-grid-content .ainr-title{font-size:14.5px;margin:4px 0 0;}',
      '.ainr-grid-content .ainr-desc{font-size:12px;margin:6px 0 14px;flex:1;}',
      '.ainr-grid-footer{display:flex;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(148,163,184,0.18);}',

      /* Meta Bar */
      '.ainr-meta-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;font-size:11px;letter-spacing:.03em;}',
      '.ainr-theme-light .ainr-meta-bar{color:#64748b;}',
      '.ainr-theme-dark .ainr-meta-bar{color:#94a3b8;}',
      '.ainr-sponsor-link{color:inherit;text-decoration:none;opacity:0.78;font-weight:600;transition:opacity .15s ease;}',
      '.ainr-sponsor-link:hover{opacity:1;text-decoration:underline;}',

      /* Responsive Breakpoints */
      '@media (max-width:1024px){.ainr-grid-3{grid-template-columns:1fr;}}',
      '@media (max-width:900px){.ainr-grid-2{grid-template-columns:1fr;}}',
      '@media (max-width:640px){.ainr-card{flex-direction:column;align-items:flex-start;}.ainr-thumb{width:100%;height:140px;}.ainr-action-wrap{width:100%;flex-direction:row;justify-content:space-between;align-items:center;margin-top:10px;}}'
    ].join('');
    document.head.appendChild(style);
  }

  function getThemeClass(el) {
    if (el && el.getAttribute('data-ad-theme') === 'dark') return 'ainr-theme-dark';
    if (el && el.getAttribute('data-ad-theme') === 'light') return 'ainr-theme-light';
    return isDarkPage() ? 'ainr-theme-dark' : 'ainr-theme-light';
  }

  function linkAttrs(partner) {
    if (partner.internal) {
      return 'href="' + esc(partner.url) + '"';
    }
    return 'href="' + esc(partner.url) + '" target="_blank" rel="sponsored noopener noreferrer"';
  }

  // =========================================================================
  // 3. THIRD-PARTY NETWORK RENDERERS (WITH SAFE FALLBACK)
  // =========================================================================
  function tryMountAAds(el, unitId, fallbackFn) {
    if (!CONFIG.networks.aads.enabled || !unitId) return false;
    var wrap = document.createElement('div');
    wrap.style.cssText = 'display:flex;justify-content:center;width:100%;overflow:hidden;border-radius:12px;';
    var iframe = document.createElement('iframe');
    iframe.setAttribute('data-aa', String(unitId));
    iframe.src = '//ad.a-ads.com/' + encodeURIComponent(unitId) + '?size=Adaptive';
    iframe.style.cssText = 'width:100%;max-width:728px;height:90px;border:0;padding:0;overflow:hidden;background-color:transparent;';
    iframe.setAttribute('loading', 'lazy');
    iframe.setAttribute('title', 'Sponsored Advertisement');
    var loaded = false;
    iframe.onload = function () { loaded = true; };
    iframe.onerror = function () { fallbackFn(); };
    wrap.appendChild(iframe);
    el.innerHTML = '';
    el.appendChild(wrap);
    setTimeout(function () {
      if (!loaded && iframe.clientHeight < 20) {
        fallbackFn();
      }
    }, 3200);
    return true;
  }

  function tryMountAdsterraNative(el, fallbackFn) {
    var cfg = CONFIG.networks.adsterra;
    if (!cfg.enabled || !cfg.containerId || !cfg.scriptSrc) return false;
    el.innerHTML = '';
    var box = document.createElement('div');
    box.id = cfg.containerId;
    el.appendChild(box);
    var s = document.createElement('script');
    s.async = true;
    s.setAttribute('data-cfasync', 'false');
    s.src = cfg.scriptSrc;
    s.onerror = function () { fallbackFn(); };
    el.appendChild(s);
    setTimeout(function () {
      if (box.children.length === 0) {
        fallbackFn();
      }
    }, 3500);
    return true;
  }

  function maybeLoadGlobalNetworks() {
    if (CONFIG.networks.ethicalads && CONFIG.networks.ethicalads.enabled && CONFIG.networks.ethicalads.publisher) {
      if (!document.querySelector('script[src*="ethicalads.min.js"]')) {
        var ea = document.createElement('script');
        ea.async = true;
        ea.src = 'https://media.ethicalads.io/media/client/ethicalads.min.js';
        document.head.appendChild(ea);
      }
    }
    if (CONFIG.networks.adsense && CONFIG.networks.adsense.enabled && CONFIG.networks.adsense.client) {
      if (!document.querySelector('script[src*="adsbygoogle.js"]')) {
        var ga = document.createElement('script');
        ga.async = true;
        ga.crossOrigin = 'anonymous';
        ga.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(CONFIG.networks.adsense.client);
        document.head.appendChild(ga);
      }
    }
  }

  // =========================================================================
  // 4. NATIVE FORMAT RENDERERS WITH REAL IMAGES & BANNERS
  // =========================================================================
  function renderCardHtml(p, compact) {
    var pillClass = 'ainr-pill-' + (p.accent || 'indigo');
    var imageHtml = p.image
      ? '<div class="ainr-thumb">' +
          '<img src="' + esc(p.image) + '" alt="' + esc(p.name) + '" loading="lazy" decoding="async" />' +
          '<span class="ainr-thumb-badge">' + esc(p.badge) + '</span>' +
        '</div>'
      : '';

    return (
      '<a class="ainr-card" ' + linkAttrs(p) + '>' +
        imageHtml +
        '<div class="ainr-body">' +
          '<div class="ainr-pill-row">' +
            '<span class="ainr-pill ' + pillClass + '">✦ ' + esc(p.badge) + '</span>' +
            '<span class="ainr-verified">✓ Official</span>' +
          '</div>' +
          '<h4 class="ainr-title">' + esc(p.name) + '</h4>' +
          (compact ? '' : '<p class="ainr-desc">' + esc(p.tagline) + '</p>') +
        '</div>' +
        '<div class="ainr-action-wrap">' +
          '<span class="ainr-cta">' + esc(p.cta) + ' ↗</span>' +
          '<span class="ainr-sub-hint">' + esc(p.hint || 'Special Offer') + '</span>' +
        '</div>' +
      '</a>'
    );
  }

  function renderGridCardHtml(p) {
    var pillClass = 'ainr-pill-' + (p.accent || 'indigo');
    var imageHtml = p.image
      ? '<div class="ainr-grid-thumb">' +
          '<img src="' + esc(p.image) + '" alt="' + esc(p.name) + '" loading="lazy" decoding="async" />' +
          '<span class="ainr-thumb-badge">' + esc(p.badge) + '</span>' +
        '</div>'
      : '';

    return (
      '<a class="ainr-grid-card" ' + linkAttrs(p) + '>' +
        imageHtml +
        '<div class="ainr-grid-content">' +
          '<div class="ainr-pill-row">' +
            '<span class="ainr-pill ' + pillClass + '">✦ ' + esc(p.badge) + '</span>' +
            '<span class="ainr-verified">✓ Partner</span>' +
          '</div>' +
          '<h4 class="ainr-title">' + esc(p.name) + '</h4>' +
          '<p class="ainr-desc">' + esc(p.tagline) + '</p>' +
          '<div class="ainr-grid-footer">' +
            '<span class="ainr-sub-hint">' + esc(p.hint || 'Verified Resource') + '</span>' +
            '<span class="ainr-cta">' + esc(p.cta) + ' ↗</span>' +
          '</div>' +
        '</div>' +
      '</a>'
    );
  }

  function renderMetaBar(lang, labelEn, labelZh) {
    var sponsorHref = CONFIG.sponsorUrl[lang] || '/contact#sponsor';
    var leftText = lang === 'zh' ? labelZh : labelEn;
    var rightText = lang === 'zh' ? '成为合作伙伴 / 提交产品 ↗' : 'Sponsor / Feature Your Tool ↗';
    return (
      '<div class="ainr-meta-bar">' +
        '<span>✦ ' + esc(leftText) + '</span>' +
        '<a class="ainr-sponsor-link" href="' + esc(sponsorHref) + '">' + esc(rightText) + '</a>' +
      '</div>'
    );
  }

  function renderNativeLeaderboard(el, lang) {
    var items = pickPartners(lang, 2, 0);
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'PARTNER SPOTLIGHT · SPONSORED', '优选生态伙伴 · 合作推荐') +
        '<div class="ainr-grid-2">' +
          items.map(function (p) { return renderCardHtml(p, false); }).join('') +
        '</div>' +
      '</div>';
  }

  function renderNativeShowcaseGrid(el, lang) {
    var items = pickPartners(lang, 3, 0);
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'RECOMMENDED AI INFRASTRUCTURE & DEVELOPER PARTNERS', '精选 AI 算力、API 与开发者生态推荐') +
        '<div class="ainr-grid-3">' +
          items.map(function (p) { return renderGridCardHtml(p); }).join('') +
        '</div>' +
      '</div>';
  }

  function renderNativeInContent(el, lang, offset) {
    var items = pickPartners(lang, 1, offset || 0);
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'SPONSORED DEVELOPER RESOURCE', '开发者算力与工具推荐 · 合作') +
        renderCardHtml(items[0], false) +
      '</div>';
  }

  function renderNativeGateway(el, lang) {
    var items = pickPartners(lang, 1, 0);
    el.innerHTML =
      '<div class="ainr-slot ainr-theme-dark">' +
        renderMetaBar(lang, 'FEATURED AI PARTNER', '精选 AI 生态伙伴') +
        renderCardHtml(items[0], false) +
      '</div>';
  }

  function renderNativeMobile(el, lang) {
    var items = pickPartners(lang, 1, 0);
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'SPONSORED', '合作推荐') +
        renderCardHtml(items[0], true) +
      '</div>';
  }

  // =========================================================================
  // 5. SLOT ROUTER & LAZY-LOAD OBSERVER
  // =========================================================================
  function mountSlot(el) {
    if (!el || el.getAttribute('data-ad-mounted') === '1') return;
    el.setAttribute('data-ad-mounted', '1');

    var slotType = el.getAttribute('data-ad-slot') || 'article-native';
    var lang = isZhPage() ? 'zh' : 'en';

    if (slotType === 'home-mid-leaderboard') {
      var fallbackMid = function () { renderNativeLeaderboard(el, lang); };
      if (!tryMountAAds(el, CONFIG.networks.aads.leaderboardUnitId, fallbackMid)) {
        fallbackMid();
      }
      return;
    }

    if (slotType === 'home-bottom-native') {
      var fallbackBot = function () { renderNativeShowcaseGrid(el, lang); };
      if (!tryMountAdsterraNative(el, fallbackBot)) {
        fallbackBot();
      }
      return;
    }

    if (slotType === 'gateway-card') {
      renderNativeGateway(el, lang);
      return;
    }

    if (slotType === 'mobile-feed-native') {
      var fallbackMob = function () { renderNativeMobile(el, lang); };
      if (!tryMountAAds(el, CONFIG.networks.aads.mobileUnitId, fallbackMob)) {
        fallbackMob();
      }
      return;
    }

    if (slotType === 'tool-native') {
      var fallbackTool = function () { renderNativeInContent(el, lang, 1); };
      if (!tryMountAAds(el, CONFIG.networks.aads.inContentUnitId, fallbackTool)) {
        fallbackTool();
      }
      return;
    }

    // Default: article-native / daily-native
    var fallbackArt = function () { renderNativeInContent(el, lang, 0); };
    if (!tryMountAAds(el, CONFIG.networks.aads.inContentUnitId, fallbackArt)) {
      fallbackArt();
    }
  }

  function observeThemeChanges() {
    if (typeof MutationObserver === 'undefined') return;
    var observer = new MutationObserver(function () {
      var dark = isDarkPage();
      var slots = document.querySelectorAll('.ainr-slot');
      for (var i = 0; i < slots.length; i++) {
        var parent = slots[i].parentElement;
        if (parent && parent.getAttribute('data-ad-theme')) continue;
        slots[i].classList.toggle('ainr-theme-dark', dark);
        slots[i].classList.toggle('ainr-theme-light', !dark);
      }
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
  }

  function init() {
    injectStylesOnce();
    maybeLoadGlobalNetworks();
    observeThemeChanges();

    var slots = document.querySelectorAll('[data-ad-slot]');
    if (!slots.length) return;

    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          if (entries[i].isIntersecting) {
            mountSlot(entries[i].target);
            io.unobserve(entries[i].target);
          }
        }
      }, { rootMargin: '300px 0px' });

      for (var j = 0; j < slots.length; j++) {
        io.observe(slots[j]);
      }
    } else {
      for (var k = 0; k < slots.length; k++) {
        mountSlot(slots[k]);
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
