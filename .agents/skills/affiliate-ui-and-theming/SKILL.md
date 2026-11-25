---
name: affiliate-ui-and-theming
description: Guides Amazon Associates showcase visual engineering, optical mix-blend product staging, strict contextual relevance gating, and Light/Dark/Auto theme synchronization across static AI News Radar pages. Use when editing monetization.js, page_theme.js, affiliate catalog scripts, or static page generators in tool_news_publisher.py.
---

# Affiliate Showcase UI & Static Theme Synchronization

## 1. Product Photography & Dark-Mode Optical Blending

1. **Never run pixel flood-fill background removal on compressed studio photos**:
   - Automated alpha cutouts on white studio shots create jagged halo noise, shadow islands under glasses/frames, and eat into light-colored hardware edges.
   - Always keep pristine RGB studio WebPs fetched cleanly via `tools/fetch_affiliate_images.py` (`curl_cffi` `impersonate="chrome"` + OpenLibrary fallback -> `480px` WebP in `public/images/products/`).
2. **Optical Stage Blending (`public/js/monetization.js`)**:
   - Place hardware/device cutouts edge-to-edge on matte light / cool-silver gradient stages and apply `mix-blend-mode: multiply` so white studio backgrounds dissolve optically into the stage while preserving natural shadows.
   - Keep book covers (`O'Reilly` / technical paperbacks) on `.ainr-photo-book` with `mix-blend-mode: normal` (with subtle dark-mode brightness softening) so white cover typography and illustrations are not darkened or muddied.

## 2. Card Layout, Copy Hygiene & Relevance Gating

1. **100% Real Photos & Minimal Copy**:
   - Every product card must render a real local `.webp` photo (`/images/products/...`).
   - Do not show verbose commission disclosures or dense paragraph blurbs in card headers; use concise headers (`亚马逊好物精选` / `Amazon Picks`).
2. **Distinct Placement Archetypes**:
   - **Mid-article Spotlight (`article-native`, `.ainr-spot`)**: Render **at most 1** horizontal editorial spotlight card strictly aligned with the article topic. Score using ASCII word boundaries (`containsTag`), downweight generic brand/broad terms (`WEAK_GENERIC_TAGS` at `0.25x`), and enforce `minScore: 14`; if nothing qualifies, hide the container cleanly with zero height rather than showing an off-topic product.
   - **Bottom / Tool / Homepage Shelves (`article-bottom`, `tool-native`, `home-mid-leaderboard`, `home-bottom-native`)**: Render 6-card showcases with page-wide deduplication so the same product never repeats across placements on one page.
3. **Catalog Validation & Sync**:
   - After editing `data/affiliate_products.json`, run:
     ```bash
     python tools/build_affiliate_catalog.py
     ```
   - Enforces catalog completeness (>= 100 items), `tag=purrpulse-20`, zero `$` prices, local `.webp` presence, and syncs `PRODUCT_POOL` into `public/js/monetization.js`.

## 3. Static Page Light/Dark/Auto Theme Sync (`page_theme.js` + `tool_news_publisher.py`)

Static `/news/` and `/tools/` HTML pages use Tailwind Play CDN (`cdn.tailwindcss.com`), which defaults to `media` dark mode unless explicitly configured for `class`.

1. **Mandatory `<head>` configuration (`TAILWIND_THEME_HEAD`)**:
   - Always declare `tailwind.config = { darkMode: 'class' };` alongside a synchronous Zero-FOUC initializer reading `localStorage.getItem('theme') || 'auto'` and toggling `document.documentElement.classList` (`dark`) before first paint.
2. **Synced Theme Switcher (`public/js/page_theme.js`)**:
   - Expose `setPageTheme` / `applyPageTheme`, listen to cross-tab `storage` events on `'theme'` and live OS `prefers-color-scheme` changes when in `'auto'`, and wire `observeThemeChanges` in `public/js/monetization.js` so affiliate surfaces adapt smoothly on toggle.
   - In `build_theme_toggle_html(is_zh)`, ensure button `title` attributes match page language (`is_zh ? zh : en`) so English static pages contain zero leaked Chinese strings.
