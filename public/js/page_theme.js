/**
 * AI News Radar - Static Detail Page Theme Synchronization Engine (v1.0)
 *
 * Syncs Light / Dark / Auto theme preference from localStorage ('theme')
 * across all /news/, /zh/news/, /tools/, and /zh/tools/ static pages.
 * Automatically notifies Tailwind (darkMode: 'class') and monetization cards.
 */
(function () {
  'use strict';

  function getStoredTheme() {
    try {
      return localStorage.getItem('theme') || 'auto';
    } catch (e) {
      return 'auto';
    }
  }

  function resolveIsDark(mode) {
    var prefersDark = false;
    try {
      prefersDark = !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
    } catch (e) {}
    return mode === 'dark' || (mode === 'auto' && prefersDark);
  }

  function updateToggleButtons(mode) {
    var activeCls = 'px-2 py-1 text-xs rounded-md transition-all bg-indigo-600 text-white font-bold shadow-xs flex items-center cursor-pointer';
    var inactiveCls = 'px-2 py-1 text-xs rounded-md transition-all text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white font-medium flex items-center cursor-pointer';

    var btnLight = document.getElementById('theme-btn-light');
    var btnDark = document.getElementById('theme-btn-dark');
    var btnAuto = document.getElementById('theme-btn-auto');

    if (btnLight) btnLight.className = (mode === 'light') ? activeCls : inactiveCls;
    if (btnDark) btnDark.className = (mode === 'dark') ? activeCls : inactiveCls;
    if (btnAuto) btnAuto.className = ((mode === 'auto') ? activeCls : inactiveCls).replace('flex items-center', 'hidden sm:inline-flex items-center');
  }

  function applyPageTheme() {
    var mode = getStoredTheme();
    var isDark = resolveIsDark(mode);
    document.documentElement.classList.toggle('dark', isDark);
    updateToggleButtons(mode);
  }

  function setPageTheme(mode) {
    if (mode !== 'light' && mode !== 'dark' && mode !== 'auto') mode = 'auto';
    try {
      localStorage.setItem('theme', mode);
    } catch (e) {}
    applyPageTheme();
  }

  window.setPageTheme = setPageTheme;
  window.applyPageTheme = applyPageTheme;
  if (!window.setTheme) {
    window.setTheme = setPageTheme;
  }

  // Follow OS theme changes live when mode is 'auto'
  try {
    if (window.matchMedia) {
      var mq = window.matchMedia('(prefers-color-scheme: dark)');
      var onChange = function () {
        if (getStoredTheme() === 'auto') applyPageTheme();
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    }
  } catch (e) {}

  // Cross-tab instant synchronization when theme is switched on homepage or another tab
  window.addEventListener('storage', function (e) {
    if (e && e.key === 'theme') {
      applyPageTheme();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyPageTheme);
  } else {
    applyPageTheme();
  }
})();
