/**
 * AI News Radar - Unified Monetization & Native Partner Engine (v1.0)
 *
 * Strategy for early-stage, high-value AI/Developer traffic:
 *   Layer 1 (Active by default, AdBlock-immune, highest RPM):
 *     - Bilingual (EN / ZH) Curated AI Infrastructure & SaaS Affiliate Native Cards
 *     - Direct "Promote Your AI Tool / Sponsor" self-serve CTA
 *   Layer 2 (Zero-traffic-minimum clean display — plug in your IDs below):
 *     - A-Ads (Anonymous Ads): lightweight pure HTML/CSS iframe, zero CLS, dark-mode safe
 *     - Adsterra Native Banner: global fill native widget (NO popunders / NO redirects)
 *   Layer 3 (Scale-up ready):
 *     - EthicalAds (developer-first privacy ads)
 *     - Google AdSense (flip enabled: true when ready for re-review)
 *
 * Performance guarantees:
 *   - Deferred script execution + IntersectionObserver lazy mounting (0ms LCP impact)
 *   - Fixed min-height containers (CLS = 0)
 *   - Automatic graceful fallback to Layer 1 Native Cards if ad network is unconfigured or blocked
 */
(function () {
  'use strict';

  // =========================================================================
  // 1. CENTRALIZED AD NETWORK & AFFILIATE CONFIGURATION
  //    Replace placeholder IDs / affiliate URLs as soon as your accounts are active.
  // =========================================================================
  var CONFIG = window.AINR_MONETIZATION_CONFIG || {
    networks: {
      // A-Ads (https://a-ads.com) — Instant approval, 0 traffic minimum, accepts .xyz
      // Create an "Adaptive" ad unit and paste its numeric unitId below.
      aads: {
        enabled: false,
        leaderboardUnitId: '', // e.g. '2345678' (728x90 / Adaptive)
        inContentUnitId: '',   // e.g. '2345679' (Adaptive / 468x60)
        mobileUnitId: ''       // e.g. '2345680' (320x100 / Adaptive)
      },

      // Adsterra Native Banner (https://adsterra.com) — 0 traffic minimum, global fill
      // IMPORTANT: Use ONLY "Native Banner" format. Never enable Popunder / Social Bar.
      adsterra: {
        enabled: false,
        containerId: '',       // e.g. 'container-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        scriptSrc: ''          // e.g. '//pl12345678.highrevenuenetwork.com/.../invoke.js'
      },

      // EthicalAds (https://www.ethicalads.io) — Upgrade target at 10k-50k+ dev pageviews/mo
      ethicalads: {
        enabled: false,
        publisher: ''          // e.g. 'ainewsradar'
      },

      // Google AdSense — Keep false while unapproved to avoid wasted network requests.
      // Flip to true when re-submitting for AdSense review.
      adsense: {
        enabled: false,
        client: 'ca-pub-4912808437101130'
      }
    },

    // Direct sponsorship / tool-listing contact URLs
    sponsorUrl: {
      en: '/contact#sponsor',
      zh: '/zh/contact#sponsor'
    },

    // =========================================================================
    // Layer 1: High-Intent AI & Dev Affiliate Partners (Replace `url` with your tracking links)
    // =========================================================================
    partners: {
      en: [
        {
          id: 'elevenlabs-voice',
          badge: 'VOICE AGENT API',
          accent: 'indigo',
          icon: '🎙️',
          name: 'ElevenLabs Frontier Voice AI',
          tagline: 'Industry-leading real-time voice streaming, voice cloning, and Conversational AI Agents for builders.',
          cta: 'Try Voice AI Free',
          url: 'https://try.elevenlabs.io/bwnugci42q5y'
        },
        {
          id: 'hostinger-vps',
          badge: 'AI HOSTING',
          accent: 'emerald',
          icon: '🚀',
          name: 'High-Speed NVMe VPS & n8n Hosting',
          tagline: 'Self-host AI Agents, MCP servers, and n8n automation workflows with 1-click templates.',
          cta: 'Explore Plans',
          // Replace with your Hostinger / Impact affiliate link
          url: 'https://www.hostinger.com/vps-hosting?ref=ainewsradar'
        },
        {
          id: 'sponsor-direct-en',
          badge: 'FEATURED SLOT',
          accent: 'amber',
          icon: '✨',
          name: 'Promote Your AI Tool on AI News Radar',
          tagline: 'Reach frontier AI engineers, indie builders, and technical decision-makers daily.',
          cta: 'Submit / Sponsor',
          url: '/contact#sponsor',
          internal: true
        }
      ],
      zh: [
        {
          id: 'siliconflow-api',
          badge: '大模型 API',
          accent: 'indigo',
          icon: '⚡',
          name: 'SiliconFlow 硅基流动推理云',
          tagline: '一站式调用前沿开源大模型 API，低延迟高并发推理，注册即领免费开发者体验额度。',
          cta: '领取 API 额度',
          // 替换为你的硅基流动邀请返佣链接 (https://cloud.siliconflow.cn)
          url: 'https://cloud.siliconflow.cn/?ref=ainewsradar'
        },
        {
          id: 'autodl-gpu',
          badge: 'GPU 算力',
          accent: 'emerald',
          icon: '🖥️',
          name: 'AutoDL / 弹性 GPU 算力集群',
          tagline: '按小时弹性租用高性能 GPU，一键部署开源推理模型、微调框架与本地 Agent 工作流。',
          cta: '查看算力方案',
          // 替换为你的 AutoDL / 算力平台邀请返佣链接
          url: 'https://www.autodl.com/?ref=ainewsradar'
        },
        {
          id: 'cloud-dev-cn',
          badge: '开发者特惠',
          accent: 'sky',
          icon: '☁️',
          name: '云服务器与 AI 应用部署专享',
          tagline: '高性价比轻量云主机与容器集群，快速上线 n8n 工作流、MCP 服务与个人 AI 站点。',
          cta: '获取开发者优惠',
          // 替换为你的阿里云 / 腾讯云 / 火山引擎推广返佣链接
          url: 'https://www.aliyun.com/?ref=ainewsradar'
        },
        {
          id: 'sponsor-direct-zh',
          badge: '品牌直投',
          accent: 'amber',
          icon: '✨',
          name: '置顶推广你的 AI 产品与工具',
          tagline: '精准触达一线 AI 工程师、全栈开发者与科技决策者，支持工具库置顶与原生专题合作。',
          cta: '申请置顶合作',
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
    // Flagship articles / light pages without .dark class
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
      '.ainr-card{position:relative;display:flex;align-items:center;justify-content:space-between;gap:14px;padding:14px 18px;border-radius:16px;text-decoration:none;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;}',
      '.ainr-card:hover{transform:translateY(-1px);}',
      '.ainr-theme-light .ainr-card{background:linear-gradient(135deg,rgba(255,255,255,0.96),rgba(248,250,252,0.96));border:1px solid rgba(203,213,225,0.85);color:#0f172a;box-shadow:0 4px 16px -6px rgba(15,23,42,0.08);}',
      '.ainr-theme-light .ainr-card:hover{border-color:rgba(99,102,241,0.45);box-shadow:0 10px 24px -10px rgba(79,70,229,0.18);}',
      '.ainr-theme-dark .ainr-card{background:linear-gradient(135deg,rgba(15,23,42,0.82),rgba(15,23,42,0.62));border:1px solid rgba(51,65,85,0.75);color:#f1f5f9;box-shadow:0 8px 24px -12px rgba(0,0,0,0.55);backdrop-filter:blur(12px);}',
      '.ainr-theme-dark .ainr-card:hover{border-color:rgba(129,140,248,0.55);box-shadow:0 12px 28px -10px rgba(99,102,241,0.22);}',
      '.ainr-grid-3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;}',
      '.ainr-grid-2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;}',
      '@media (max-width:900px){.ainr-grid-3{grid-template-columns:1fr;}}',
      '@media (max-width:720px){.ainr-grid-2{grid-template-columns:1fr;}.ainr-card{flex-direction:column;align-items:flex-start;}}',
      '.ainr-meta-bar{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;font-size:11px;letter-spacing:.03em;}',
      '.ainr-theme-light .ainr-meta-bar{color:#64748b;}',
      '.ainr-theme-dark .ainr-meta-bar{color:#94a3b8;}',
      '.ainr-pill{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;letter-spacing:.04em;text-transform:uppercase;}',
      '.ainr-pill-indigo{background:rgba(99,102,241,0.12);color:#6366f1;border:1px solid rgba(99,102,241,0.25);}',
      '.ainr-pill-emerald{background:rgba(16,185,129,0.12);color:#10b981;border:1px solid rgba(16,185,129,0.25);}',
      '.ainr-pill-sky{background:rgba(14,165,233,0.12);color:#0ea5e9;border:1px solid rgba(14,165,233,0.25);}',
      '.ainr-pill-amber{background:rgba(245,158,11,0.12);color:#f59e0b;border:1px solid rgba(245,158,11,0.25);}',
      '.ainr-cta{flex-shrink:0;display:inline-flex;align-items:center;gap:4px;padding:7px 13px;border-radius:10px;font-size:12px;font-weight:700;white-space:nowrap;transition:background .15s ease;}',
      '.ainr-theme-light .ainr-cta{background:#4f46e5;color:#ffffff;}',
      '.ainr-theme-light .ainr-card:hover .ainr-cta{background:#4338ca;}',
      '.ainr-theme-dark .ainr-cta{background:rgba(99,102,241,0.2);color:#c7d2fe;border:1px solid rgba(129,140,248,0.35);}',
      '.ainr-theme-dark .ainr-card:hover .ainr-cta{background:#4f46e5;color:#ffffff;border-color:#6366f1;}',
      '.ainr-title{font-size:13.5px;font-weight:800;line-height:1.35;margin:0;}',
      '.ainr-desc{font-size:12px;line-height:1.48;margin:4px 0 0;opacity:0.8;}',
      '.ainr-sponsor-link{color:inherit;text-decoration:none;opacity:0.78;font-weight:600;transition:opacity .15s ease;}',
      '.ainr-sponsor-link:hover{opacity:1;text-decoration:underline;}',
      '.ainr-iframe-wrap{display:flex;align-items:center;justify-content:center;width:100%;overflow:hidden;border-radius:12px;}'
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
    wrap.className = 'ainr-iframe-wrap';
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
    // Graceful AdBlock recovery if iframe is blocked/collapsed
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
    // EthicalAds script (only when enabled)
    if (CONFIG.networks.ethicalads && CONFIG.networks.ethicalads.enabled && CONFIG.networks.ethicalads.publisher) {
      if (!document.querySelector('script[src*="ethicalads.min.js"]')) {
        var ea = document.createElement('script');
        ea.async = true;
        ea.src = 'https://media.ethicalads.io/media/client/ethicalads.min.js';
        document.head.appendChild(ea);
      }
    }
    // Google AdSense (only when explicitly re-enabled)
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
  // 4. NATIVE FORMAT RENDERERS (4 FORMATS: LEADERBOARD, GRID, GATEWAY, IN-CONTENT, MOBILE)
  // =========================================================================
  function renderCardHtml(p, compact) {
    var pillClass = 'ainr-pill-' + (p.accent || 'indigo');
    return (
      '<a class="ainr-card" ' + linkAttrs(p) + '>' +
        '<div style="min-width:0;flex:1;">' +
          '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">' +
            '<span style="font-size:15px;line-height:1;">' + esc(p.icon) + '</span>' +
            '<span class="ainr-pill ' + pillClass + '">' + esc(p.badge) + '</span>' +
            '<h4 class="ainr-title">' + esc(p.name) + '</h4>' +
          '</div>' +
          (compact ? '' : '<p class="ainr-desc">' + esc(p.tagline) + '</p>') +
        '</div>' +
        '<span class="ainr-cta">' + esc(p.cta) + ' ↗</span>' +
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
    var items = pickPartners(lang, 3, 1);
    el.innerHTML =
      '<div class="ainr-slot ' + getThemeClass(el) + '">' +
        renderMetaBar(lang, 'RECOMMENDED AI INFRASTRUCTURE & DEVELOPER PARTNERS', '精选 AI 算力、API 与开发者生态推荐') +
        '<div class="ainr-grid-3">' +
          items.map(function (p) { return renderCardHtml(p, false); }).join('') +
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

    // Route by format: try configured third-party network first, fallback cleanly to Layer 1 Native
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
      }, { rootMargin: '260px 0px' });

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
