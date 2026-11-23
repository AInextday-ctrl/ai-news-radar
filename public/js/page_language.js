/**
 * AI News Radar - Unified Static Page Multi-Language & Translation Engine (v2.0)
 *
 * Provides full 31-language dynamic translation across all static article detail pages,
 * tool pages, and flagship editorial reports (e.g. /news/{id}.html, /zh/news/{id}.html,
 * /tools/{id}.html, /articles/{id}.html).
 *
 * Features:
 *   - Auto-detects user language preference from localStorage ('ai_radar_user_site_lang')
 *   - Instantly triggers Translate.js Client Edge engine for any of 28 non-ZH/non-EN languages
 *   - Full 31-language action sheet modal with live search & grouped lists
 *   - Seamless 1-click native switching between English and Simplified Chinese editions
 *   - Traditional Chinese conversion via ChineseConverter
 *   - Self-mounting UI: automatically enhances existing static header navigation
 */
(function () {
  'use strict';

  var isZh = window.location.pathname.startsWith('/zh');
  var savedSiteLang = localStorage.getItem('ai_radar_user_site_lang') || '';
  var currentSiteLang = savedSiteLang || (isZh ? 'chinese_simplified' : 'english');

  var ALL_SITE_LANGUAGES = [
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

  var LANG_GROUPS = {
    popular: { en: '🌟 Popular Languages', zh: '🌟 常用热门语种' },
    european: { en: '🌍 European Languages', zh: '🌍 欧洲主要语言' },
    apac: { en: '🌏 Asia-Pacific & Global', zh: '🌏 亚太及全球语种' }
  };

  function showToast(msg) {
    var toast = document.createElement('div');
    toast.className = 'fixed bottom-8 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-2xl bg-slate-900/90 dark:bg-slate-100/90 text-white dark:text-slate-900 text-xs font-bold shadow-2xl backdrop-blur-md z-50 transition-all duration-300 notranslate flex items-center gap-2';
    toast.innerHTML = '<span>🌐</span><span>' + msg + '</span>';
    document.body.appendChild(toast);
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translate(-50%, 10px)';
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 2400);
  }

  function updateButtonLabel(lang) {
    var flagEl = document.getElementById('page-lang-flag');
    var textEl = document.getElementById('page-lang-text');
    if (!flagEl || !textEl) return;
    var found = ALL_SITE_LANGUAGES.find(function (it) { return it.id === lang; });
    if (found) {
      flagEl.textContent = found.flag;
      textEl.textContent = found.native;
    } else {
      flagEl.textContent = '🌐';
      textEl.textContent = 'Lang';
    }
  }

  function ensureChineseConverter(callback) {
    if (window.ChineseConverter) {
      if (callback) callback();
      return;
    }
    var script = document.createElement('script');
    script.src = 'https://res.zvo.cn/chinese/chinese.js';
    script.async = true;
    script.onload = function () {
      if (callback) callback();
    };
    document.body.appendChild(script);
  }

  function loadTranslateEngine(targetLang) {
    var exec = function () {
      try {
        if (typeof translate !== 'undefined') {
          translate.selectLanguageTag.show = false;
          translate.service.use('client.edge');
          translate.language.setLocal(isZh ? 'chinese_simplified' : 'english');
          if (translate.listener) {
            translate.listener.use = true;
            if (!translate.listener.isStart && typeof translate.listener.addListener === 'function') {
              try { translate.listener.addListener(); } catch (e) {}
            }
          }
          if (translate.node && typeof translate.node.refresh === 'function') {
            try { translate.node.refresh(); } catch (e) {}
          }
          translate.ignore.class.push('notranslate');
          translate.ignore.id.push('page-lang-modal');
          translate.ignore.tag.push('code');
          translate.ignore.tag.push('pre');
          if (translate.changeLanguage) {
            try { translate.changeLanguage(targetLang); } catch (e) {}
          }
          if (translate.execute) {
            try { translate.execute(); } catch (e) {}
          }
          updateButtonLabel(targetLang);

          var langObj = ALL_SITE_LANGUAGES.find(function (it) { return it.id === targetLang; });
          var name = langObj ? (isZh ? langObj.nameZh : langObj.nameEn) : targetLang;
          showToast(isZh ? ('已实时翻译为 ' + name) : ('Translated to ' + name));

          // Post-hydration catch
          setTimeout(function () {
            try {
              if (translate.changeLanguage) translate.changeLanguage(targetLang);
              if (translate.execute) translate.execute();
            } catch (e) {}
          }, 100);
          setTimeout(function () {
            try {
              if (translate.execute) translate.execute();
            } catch (e) {}
          }, 350);
        }
      } catch (err) {
        console.warn('Translate execution notice:', err);
      }
    };

    if (typeof translate === 'undefined') {
      var script = document.createElement('script');
      script.src = 'https://res.zvo.cn/translate/translate.js';
      script.async = true;
      script.onload = exec;
      document.body.appendChild(script);
    } else {
      exec();
    }
  }

  function getEquivalentPageUrl(targetLang) {
    var path = window.location.pathname;
    var search = window.location.search;
    var hash = window.location.hash;

    if (targetLang === 'english') {
      if (path.startsWith('/zh')) {
        return path.replace(/^\/zh/, '') + search + hash;
      }
      return path + search + hash;
    }

    if (targetLang === 'chinese_simplified' || targetLang === 'chinese_traditional') {
      if (!path.startsWith('/zh')) {
        return '/zh' + path + search + hash;
      }
      return path + search + hash;
    }

    return path + search + hash;
  }

  function selectLanguage(targetLang) {
    closePicker();
    currentSiteLang = targetLang;
    localStorage.setItem('ai_radar_user_site_lang', targetLang);

    // 1. Simplified Chinese
    if (targetLang === 'chinese_simplified') {
      localStorage.setItem('ai_radar_user_lang', 'zh');
      if (!isZh) {
        window.location.href = getEquivalentPageUrl('chinese_simplified');
        return;
      }
      if (window.ChineseConverter && window.ChineseConverter.revertDomToSimplified) {
        try { window.ChineseConverter.revertDomToSimplified(); } catch (e) {}
      }
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      updateButtonLabel('chinese_simplified');
      showToast('已切换至简体中文');
      return;
    }

    // 2. Traditional Chinese
    if (targetLang === 'chinese_traditional') {
      localStorage.setItem('ai_radar_user_lang', 'zh');
      if (!isZh) {
        window.location.href = getEquivalentPageUrl('chinese_traditional');
        return;
      }
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      ensureChineseConverter(function () {
        if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
          try { window.ChineseConverter.convertDomToTraditional(); } catch (e) {}
        }
      });
      updateButtonLabel('chinese_traditional');
      showToast('已切換至繁體中文');
      return;
    }

    // 3. English
    if (targetLang === 'english') {
      localStorage.setItem('ai_radar_user_lang', 'en');
      if (isZh) {
        window.location.href = getEquivalentPageUrl('english');
        return;
      }
      if (typeof translate !== 'undefined' && translate.reset) {
        try { translate.reset(); } catch (e) {}
      }
      updateButtonLabel('english');
      showToast('Switched to English');
      return;
    }

    // 4. All other 28 languages via Translate.js edge translation
    if (window.ChineseConverter && window.ChineseConverter.revertDomToSimplified) {
      try { window.ChineseConverter.revertDomToSimplified(); } catch (e) {}
    }
    if (window._hasTranslateExecuted && currentSiteLang && currentSiteLang !== targetLang && currentSiteLang !== 'english' && currentSiteLang !== 'chinese_simplified') {
      window.location.reload();
      return;
    }
    window._hasTranslateExecuted = true;
    loadTranslateEngine(targetLang);
  }

  function renderLanguageList(query) {
    var container = document.getElementById('page-lang-list');
    if (!container) return;

    var q = (query || '').trim().toLowerCase();
    var filtered = q
      ? ALL_SITE_LANGUAGES.filter(function (it) {
          return it.id.toLowerCase().includes(q) ||
            it.native.toLowerCase().includes(q) ||
            it.nameEn.toLowerCase().includes(q) ||
            it.nameZh.includes(q) ||
            it.code.toLowerCase().includes(q);
        })
      : ALL_SITE_LANGUAGES;

    if (filtered.length === 0) {
      container.innerHTML = '<div class="py-8 text-center text-slate-400 text-xs">' +
        (isZh ? '未找到相关语言' : 'No matching languages found') +
        '</div>';
      return;
    }

    var groups = ['popular', 'european', 'apac'];
    var html = '';

    groups.forEach(function (grp) {
      var groupItems = filtered.filter(function (it) { return it.group === grp; });
      if (groupItems.length === 0) return;

      var groupTitle = isZh ? LANG_GROUPS[grp].zh : LANG_GROUPS[grp].en;
      html += '<div class="pt-2 pb-1 text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider px-1">' +
        groupTitle +
        '</div>' +
        '<div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">';

      groupItems.forEach(function (item) {
        var isSelected = (currentSiteLang === item.id);
        var activeStyle = isSelected
          ? 'bg-indigo-50/90 dark:bg-indigo-950/60 border-indigo-300 dark:border-indigo-700 font-bold'
          : 'bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border-slate-200/80 dark:border-slate-700/80';
        var subName = isZh ? item.nameZh : item.nameEn;

        html += '<button type="button" onclick="window.PageLanguage.selectLanguage(\'' + item.id + '\')" class="w-full p-2.5 rounded-xl flex items-center justify-between border touch-card cursor-pointer transition-colors text-left ' + activeStyle + '">' +
          '<div class="flex items-center gap-2.5">' +
          '<span class="text-xl shrink-0">' + item.flag + '</span>' +
          '<div>' +
          '<div class="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">' +
          '<span>' + item.native + '</span>' +
          (isSelected ? '<span class="px-1 py-0.2 rounded bg-indigo-600 text-white text-[9px] font-bold">Active</span>' : '') +
          '</div>' +
          '<div class="text-[10px] text-slate-500 dark:text-slate-400 font-medium">' + subName + '</div>' +
          '</div>' +
          '</div>' +
          (isSelected ? '<span class="text-indigo-600 dark:text-indigo-400 font-bold text-sm">✓</span>' : '<span class="text-slate-300 dark:text-slate-600 text-xs">→</span>') +
          '</button>';
      });

      html += '</div>';
    });

    container.innerHTML = html;
  }

  function filterList(e) {
    var q = e && e.target ? e.target.value : '';
    renderLanguageList(q);
  }

  function openPicker() {
    var modal = document.getElementById('page-lang-modal');
    if (modal) {
      renderLanguageList('');
      var searchInput = document.getElementById('page-lang-search');
      if (searchInput) searchInput.value = '';
      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
      modal.onclick = function (e) {
        if (e.target === modal) closePicker();
      };
    }
  }

  function closePicker() {
    var modal = document.getElementById('page-lang-modal');
    if (modal) {
      modal.classList.add('hidden');
    }
    document.body.style.overflow = '';
  }

  function mountModal() {
    if (document.getElementById('page-lang-modal')) return;

    var modalHtml = [
      '<div id="page-lang-modal" class="hidden fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center animate-fade-in notranslate">',
      '  <div class="w-full sm:max-w-lg bg-white dark:bg-slate-900 rounded-t-3xl sm:rounded-2xl p-4 sm:p-5 shadow-2xl animate-slide-up border border-slate-200/80 dark:border-slate-800 flex flex-col" style="height: 80vh; max-height: 80vh; overflow: hidden;">',
      '    <div class="pt-1 pb-2 flex justify-center cursor-pointer shrink-0" onclick="window.PageLanguage.closePicker()">',
      '      <div class="w-10 h-1 bg-slate-300 dark:bg-slate-700 rounded-full"></div>',
      '    </div>',
      '    <div class="flex items-center justify-between mb-3 pb-2 border-b border-slate-100 dark:border-slate-800 shrink-0">',
      '      <div class="flex items-center gap-2">',
      '        <span class="text-xl">🌐</span>',
      '        <div>',
      '          <h3 class="text-sm font-bold text-slate-900 dark:text-slate-100">' + (isZh ? '选择全球语言版本 (31种)' : 'Select Language Edition (31 Languages)') + '</h3>',
      '          <p class="text-[11px] text-slate-500 dark:text-slate-400">' + (isZh ? '整站资讯实录、5W1H与研报实时智能编译' : 'Real-time intelligence translation powered by Client Edge') + '</p>',
      '        </div>',
      '      </div>',
      '      <button type="button" onclick="window.PageLanguage.closePicker()" class="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 text-sm font-bold cursor-pointer">✕</button>',
      '    </div>',
      '    <div class="relative mb-2.5 shrink-0">',
      '      <input id="page-lang-search" type="search" placeholder="' + (isZh ? '搜索 31 种全球语言 (英语/日语/法语/德语)...' : 'Search 31 languages (English, Japanese, French, Spanish)...') + '" oninput="window.PageLanguage.filterList(event)" class="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500">',
      '      <span class="absolute left-2.5 top-2 text-xs text-slate-400">🔍</span>',
      '    </div>',
      '    <div id="page-lang-list" class="flex-1 space-y-2 pr-1" style="flex: 1 1 0%; min-height: 0; overflow-y: auto;"></div>',
      '    <div class="pt-2 text-center border-t border-slate-100 dark:border-slate-800 shrink-0">',
      '      <span class="text-[10px] text-slate-400 font-medium tracking-tight">↕ ' + (isZh ? '滚动查看全部 31 种全球语言 · 支持即时无缝切换' : 'Scroll to explore all 31 languages · Instant on-the-fly translation') + '</span>',
      '    </div>',
      '  </div>',
      '</div>'
    ].join('\n');

    var wrap = document.createElement('div');
    wrap.innerHTML = modalHtml;
    document.body.appendChild(wrap.firstElementChild);
  }

  function mountHeaderButton() {
    var existingBtn = document.getElementById('btn-page-lang-picker');
    if (existingBtn) {
      updateButtonLabel(currentSiteLang);
      return;
    }

    // Look for header navigation container
    var header = document.querySelector('header');
    if (!header) return;

    var rightGroup = header.querySelector('.flex.items-center.gap-2') ||
                     header.querySelector('nav') ||
                     header.querySelector('.flex.items-center.space-x-4') ||
                     header.querySelector('div:last-child');
    if (!rightGroup) return;

    var btn = document.createElement('button');
    btn.id = 'btn-page-lang-picker';
    btn.type = 'button';
    btn.onclick = openPicker;
    btn.className = 'px-2.5 py-1 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 transition-all flex items-center gap-1.5 shadow-xs cursor-pointer notranslate';
    btn.title = isZh ? '切换全站 31 种多语言版本' : 'Switch between 31 language editions';

    var currentObj = ALL_SITE_LANGUAGES.find(function (it) { return it.id === currentSiteLang; });
    var curFlag = currentObj ? currentObj.flag : (isZh ? '🇨🇳' : '🇬🇧');
    var curText = currentObj ? currentObj.native : (isZh ? '简体中文' : 'English');

    btn.innerHTML = '<span id="page-lang-flag">' + curFlag + '</span>' +
      '<span id="page-lang-text">' + curText + '</span>' +
      '<span class="text-[10px] text-slate-400">▼</span>';

    rightGroup.insertBefore(btn, rightGroup.firstChild);
    rightGroup.classList.add('notranslate');
  }

  function init() {
    // Only mount on static standalone landing pages (e.g. /news/..., /tools/..., /articles/...)
    // Avoid conflicting with the SPA on / and /zh and /m
    if (document.getElementById('site-lang-container') || document.getElementById('mobile-feed')) {
      return;
    }

    mountHeaderButton();
    mountModal();

    // Safety retries in case DOM was still parsing or hydrating
    setTimeout(mountHeaderButton, 80);
    setTimeout(mountHeaderButton, 350);

    // Auto-sync with user's site-wide language preference (Inherited from Home or previous choices)
    if (savedSiteLang) {
      currentSiteLang = savedSiteLang;
      updateButtonLabel(savedSiteLang);

      // If user chose Simplified Chinese but landed on an English page, seamlessly navigate to Chinese edition
      if (savedSiteLang === 'chinese_simplified') {
        if (!isZh) {
          window.location.replace(getEquivalentPageUrl('chinese_simplified'));
          return;
        }
      } else if (savedSiteLang === 'chinese_traditional') {
        // If user chose Traditional Chinese but landed on an English page, navigate to Chinese edition and convert
        if (!isZh) {
          window.location.replace(getEquivalentPageUrl('chinese_traditional'));
          return;
        }
        ensureChineseConverter(function () {
          if (window.ChineseConverter && window.ChineseConverter.convertDomToTraditional) {
            window.ChineseConverter.convertDomToTraditional();
            setTimeout(function () {
              try { window.ChineseConverter.convertDomToTraditional(); } catch (e) {}
            }, 250);
          }
        });
      } else if (savedSiteLang === 'english') {
        // If user chose English but landed on a Chinese page, seamlessly navigate to English edition
        if (isZh) {
          window.location.replace(getEquivalentPageUrl('english'));
          return;
        }
      } else {
        // Any of the other 28 global languages (e.g. Japanese, Korean, French, German, Spanish...):
        // Immediately trigger Client Edge translation for full-page coverage!
        loadTranslateEngine(savedSiteLang);
      }
    } else {
      updateButtonLabel(isZh ? 'chinese_simplified' : 'english');
    }
  }

  window.PageLanguage = {
    openPicker: openPicker,
    closePicker: closePicker,
    selectLanguage: selectLanguage,
    filterList: filterList,
    init: init
  };
  window.openPageLangPicker = openPicker;
  window.closePageLangPicker = closePicker;
  window.selectPageLanguage = selectLanguage;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
