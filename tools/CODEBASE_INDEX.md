# AI News Radar - 代码库架构、规则与符号极速索引 (Codebase Fast Index v2.0)

> **生成时间**: `2026-11-28 01:54:32 UTC` | **代码文件**: `124` 个 | **索引符号**: `1448` 个 | **注册信源**: `34` 个 | **作用域规则**: `3` 个 | **本地技能**: `3` 个
> **更新机制**: 由 `tools/fast_index.py` 驱动，经 `tools/verify_code_integrity.py` 与 `.git/hooks/pre-commit` 自动增量同步刷新。

---

## 1. 项目作用域规则与技能预算表 (Scoped Rules & Skills)

| 规则文件 | 作用域 | 体积 / 上限 (24,000 B) | 预算占比 | 状态 |
| :--- | :--- | :--- | :--- | :--- |
| [`AGENTS.md`](../AGENTS.md) | `.` | `14,416 B` | `60.1%` | `OK` |
| [`crawlers/AGENTS.md`](../crawlers/AGENTS.md) | `crawlers` | `6,509 B` | `27.1%` | `OK` |
| [`public/AGENTS.md`](../public/AGENTS.md) | `public` | `4,664 B` | `19.4%` | `OK` |

| 工作区技能 (Skill) | 路径 | 体积 | 适用场景 |
| :--- | :--- | :--- | :--- |
| **`affiliate-ui-and-theming`** | [`.agents/skills/affiliate-ui-and-theming/SKILL.md`](../.agents/skills/affiliate-ui-and-theming/SKILL.md) | `3,922 B` | Guides Amazon Associates showcase visual engineering, optical mix-blend product staging, strict contextual rel... |
| **`codebase-fast-index`** | [`.agents/skills/codebase-fast-index/SKILL.md`](../.agents/skills/codebase-fast-index/SKILL.md) | `3,225 B` | Fast codebase, scoped-rules, and data store indexing for AI News Radar. Use when locating functions, classes, ... |
| **`firebase-deploy-and-cache`** | [`.agents/skills/firebase-deploy-and-cache/SKILL.md`](../.agents/skills/firebase-deploy-and-cache/SKILL.md) | `5,507 B` | Diagnoses GitHub Actions deployment failures and stale Firebase Hosting rollouts, resolves HTTP 429 Hosting st... |

---

## 2. 核心架构与功能分层 (Architectural Tiers)

### 信源抓取与解析层 (Dedicated Source Crawlers)
*31 个隔离权威信源爬虫、通用内容过滤器（content_filters.py）与统一路由导出（__init__.py）。*

- [`crawlers/__init__.py`](../crawlers/__init__.py) (3.9 KB): `No exported symbols`
- [`crawlers/anthropic_crawler.py`](../crawlers/anthropic_crawler.py) (28.1 KB): `is_anthropic_url, extract_anthropic_article, crawl_anthropic`
- [`crawlers/arstechnica_crawler.py`](../crawlers/arstechnica_crawler.py) (31.0 KB): `is_arstechnica_url, crawl_arstechnica`
- [`crawlers/bbc_crawler.py`](../crawlers/bbc_crawler.py) (29.6 KB): `is_bbc_url, crawl_bbc`
- [`crawlers/bloomberg_crawler.py`](../crawlers/bloomberg_crawler.py) (89.4 KB): `is_bloomberg_url, extract_bloomberg_slug, clean_title_to_slug_title, is_tail_boilerplate, resolve_bloomberg_broadcast_media...`
- [`crawlers/cbsnews_crawler.py`](../crawlers/cbsnews_crawler.py) (31.1 KB): `is_cbsnews_url, crawl_cbsnews`
- [`crawlers/cnbc_crawler.py`](../crawlers/cnbc_crawler.py) (27.9 KB): `is_cnbc_url, crawl_cnbc`
- [`crawlers/coindesk_crawler.py`](../crawlers/coindesk_crawler.py) (32.5 KB): `is_coindesk_url, crawl_coindesk`
- [`crawlers/content_filters.py`](../crawlers/content_filters.py) (15.0 KB): `detect_low_value_roundup_or_promo, is_low_value_roundup_or_promo, is_paywall_or_login_noise, is_truncated_paragraph, has_paywall_or_truncation_noise...`
- [`crawlers/decoder_crawler.py`](../crawlers/decoder_crawler.py) (36.7 KB): `is_decoder_url, crawl_decoder`
- [`crawlers/deepmind_crawler.py`](../crawlers/deepmind_crawler.py) (24.4 KB): `is_deepmind_url, extract_deepmind_slug, clean_deepmind_title, extract_deepmind_author_from_title, clean_deepmind_paragraphs...`
- [`crawlers/forbes_crawler.py`](../crawlers/forbes_crawler.py) (28.2 KB): `is_forbes_url, extract_forbes_slug, clean_forbes_title, resolve_forbes_author_from_url, resolve_forbes_image_and_metadata_from_feeds...`
- [`crawlers/fortune_crawler.py`](../crawlers/fortune_crawler.py) (21.8 KB): `is_fortune_url, fetch_fortune_html, download_and_host_image, crawl_fortune`
- [`crawlers/ft_crawler.py`](../crawlers/ft_crawler.py) (22.7 KB): `is_ft_url, crawl_ft`
- [`crawlers/ifixit_crawler.py`](../crawlers/ifixit_crawler.py) (31.9 KB): `is_ifixit_url, crawl_ifixit`
- [`crawlers/ign_crawler.py`](../crawlers/ign_crawler.py) (44.2 KB): `is_ign_url, extract_ign_article, crawl_ign`
- [`crawlers/mittr_crawler.py`](../crawlers/mittr_crawler.py) (35.7 KB): `is_mittr_url, crawl_mittr`
- [`crawlers/nineto5mac_crawler.py`](../crawlers/nineto5mac_crawler.py) (39.7 KB): `is_nineto5mac_url, crawl_nineto5mac`
- [`crawlers/nypost_crawler.py`](../crawlers/nypost_crawler.py) (30.5 KB): `is_nypost_url, crawl_nypost`
- [`crawlers/nyt_crawler.py`](../crawlers/nyt_crawler.py) (33.9 KB): `is_nyt_url, crawl_nyt`
- [`crawlers/openai_crawler.py`](../crawlers/openai_crawler.py) (53.2 KB): `is_openai_url, crawl_openai`
- [`crawlers/reuters_crawler.py`](../crawlers/reuters_crawler.py) (30.6 KB): `is_reuters_url, crawl_reuters`
- [`crawlers/semafor_crawler.py`](../crawlers/semafor_crawler.py) (27.5 KB): `is_semafor_url, crawl_semafor`
- [`crawlers/siliconangle_crawler.py`](../crawlers/siliconangle_crawler.py) (34.4 KB): `is_siliconangle_url, crawl_siliconangle`
- [`crawlers/techcrunch_crawler.py`](../crawlers/techcrunch_crawler.py) (32.8 KB): `is_techcrunch_url, crawl_techcrunch`
- [`crawlers/techeu_crawler.py`](../crawlers/techeu_crawler.py) (47.6 KB): `is_techeu_url, extract_techeu_slug, clean_techeu_title, extract_techeu_author_from_title, clean_techeu_paragraphs...`
- [`crawlers/techfundingnews_crawler.py`](../crawlers/techfundingnews_crawler.py) (30.1 KB): `is_techfundingnews_url, crawl_techfundingnews`
- [`crawlers/tomshardware_crawler.py`](../crawlers/tomshardware_crawler.py) (32.1 KB): `is_tomshardware_url, crawl_tomshardware`
- [`crawlers/verge_crawler.py`](../crawlers/verge_crawler.py) (22.3 KB): `is_verge_url, fetch_verge_html, crawl_verge`
- [`crawlers/wapo_crawler.py`](../crawlers/wapo_crawler.py) (28.6 KB): `is_wapo_url, crawl_wapo`
- [`crawlers/washsun_crawler.py`](../crawlers/washsun_crawler.py) (15.0 KB): `is_washsun_url, crawl_washsun`
- [`crawlers/wired_crawler.py`](../crawlers/wired_crawler.py) (25.4 KB): `is_wired_url, crawl_wired`
- [`crawlers/wsj_crawler.py`](../crawlers/wsj_crawler.py) (30.9 KB): `is_wsj_url, crawl_wsj`

### 流水线核心调度层 (Core Pipeline & Orchestration)
*系统中央调度、信源分发、推文增量抓取、正文提取与去重清洗管道。*

- [`main.py`](../main.py) (252.3 KB): `generate_sitemap, inject_seo_static_content, generate_daily_briefing, parse_time_for_sort, is_tibo_reset_tweet...`
- [`processor.py`](../processor.py) (119.2 KB): `has_chinglish_seams, strip_chinglish_to_english, normalize_ai_terminology_zh, free_translate_zh, free_translate_en...`
- [`fetcher.py`](../fetcher.py) (198.7 KB): `extract_tech_specs, make_id, is_primarily_english, parse_to_iso, get_smart_cover_url...`
- [`article_extractor.py`](../article_extractor.py) (56.4 KB): `ArticleExtractor, extract_article_substantive`
- [`apify_crawler.py`](../apify_crawler.py) (41.9 KB): `get_apify_tokens, get_apify_token, load_crawler_state, save_crawler_state, format_metric_count...`
- [`config.py`](../config.py) (109.9 KB): `constants: CATEGORIES, SCENARIO_TAGS, PRICING_TAGS, CELEBRITY_PROFILES, SOURCES...`
- [`knowledge_base.py`](../knowledge_base.py) (20.1 KB): `DynamicKnowledgeStore`
- [`translate_fast.py`](../translate_fast.py) (4.6 KB): `is_valid_chinese_content, translate_single_item, ensure_articles_translated, sync_all_json_files`

### 研判精选与头条矩阵 (Curator & Intelligence Highlights)
*Top 3 今日突破、大V思辨矩阵、5W1H 事实提炼、工具融合与中英语言纯度哨兵。*

- [`curator_engine.py`](../curator_engine.py) (54.1 KB): `parse_item_pub_time, curate_news_column, curate_celebrity_column, is_blacklisted_tool, detect_tool_domain...`
- [`topic_cluster.py`](../topic_cluster.py) (68.7 KB): `get_gemini_client, generate_24h_topic_focus, build_topic_focus_html, load_latest_topic_focus`
- [`language_sentinel.py`](../language_sentinel.py) (29.8 KB): `has_cjk, count_chinese_chars, is_pure_chinese_paragraph, translate_and_purify_article, sanitize_item_language...`
- [`tweet_classifier.py`](../tweet_classifier.py) (13.9 KB): `load_tags_cache, save_tags_cache, detect_code_or_prompt, rule_based_classify, enrich_tweet_with_tag...`
- [`tool_fusion.py`](../tool_fusion.py) (21.0 KB): `clean_app_name, normalize_name_fingerprint, extract_repo_fingerprint, extract_apex_domain_fingerprint, extract_tool_fingerprints...`

### 静态发布与 SEO/GEO 引擎 (Static Publishing & Distribution)
*单篇静态落地页编译、首页 SSR 注入、分卷切片、Sitemap 生成与 IndexNow 秒级收录推送。*

- [`content_publisher.py`](../content_publisher.py) (266.8 KB): `format_static_tool_card, format_static_video_card, format_static_prompt_card, format_static_arxiv_card, parse_tweet_time...`
- [`tool_news_publisher.py`](../tool_news_publisher.py) (151.5 KB): `parse_iso_date, sanitize_for_en, escape, build_theme_toggle_html, build_ainr_tags_meta...`
- [`build_flagship_articles.py`](../build_flagship_articles.py) (30.1 KB): `generate_article_page, generate_articles_index, build_all_flagship_pages, main`
- [`seo_geo_engine.py`](../seo_geo_engine.py) (40.5 KB): `atomic_write_text, atomic_write_bytes, sanitize_for_en, xml_escape, parse_iso_or_rfc...`
- [`indexnow_submitter.py`](../indexnow_submitter.py) (6.4 KB): `load_sitemap_urls, load_ledger, save_ledger, submit_urls_to_indexnow, auto_submit_recent_or_all`
- [`fix_seo_titles.py`](../fix_seo_titles.py) (4.0 KB): `clean_title_for_seo, batch_clean_html_files`
- [`generate_bilingual_compliance.py`](../generate_bilingual_compliance.py) (46.1 KB): `build_english_about, build_english_editorial_policy, build_english_contact, build_english_privacy, build_english_terms...`

### 短视频与多模态实战层 (Video & Multimodal Engine)
*YouTube / Bilibili / TikTok 实战视频发现、24-48h 时效切片与提示词库。*

- [`viral_video_engine.py`](../viral_video_engine.py) (116.7 KB): `VideoTimeTuple, get_dynamic_news_hotspots, parse_youtube_views, is_promotional_or_junk, calculate_video_momentum...`
- [`prompts_and_videos.py`](../prompts_and_videos.py) (131.5 KB): `get_curated_actionable_prompts, get_curated_tutorials`

### 前端客户端与单页交互 (Frontend SPA, Theme & Monetization)
*极速弹窗阅读、分卷按需加载、联盟好物光学混合展示、主题/多语言切换与移动端自适应。*

- [`public/js/app.js`](../public/js/app.js) (761.1 KB): `flipPinnedSlide, scheduleNextPinnedFlip, initPinnedSlider, optimizeImageUrl, optimizeAvatarUrl...`
- [`public/js/monetization.js`](../public/js/monetization.js) (365.4 KB): `amzDp, amzSearch, isZhPage, isDarkPage, esc...`
- [`public/js/page_language.js`](../public/js/page_language.js) (23.8 KB): `showToast, updateButtonLabel, ensureChineseConverter, loadTranslateEngine, exec...`
- [`public/js/page_theme.js`](../public/js/page_theme.js) (3.0 KB): `getStoredTheme, resolveIsDark, updateToggleButtons, applyPageTheme, setPageTheme...`
- [`public/js/chinese_converter.js`](../public/js/chinese_converter.js) (30.6 KB): `initMap, toTraditional, toSimplified, convertDomToTraditional, revertDomToSimplified...`
- [`public/m/js/mobile.js`](../public/m/js/mobile.js) (102.9 KB): `updateLanguageState, initTheme, toggleTheme, updateThemeIcon, ensureChineseConverter...`

### 工程运维与自动化工具链 (DevOps, Index & Catalog Tools)
*极速索引同步、免锁安全推送（safe_sync）、Firebase 版本清理、爬虫审计与联盟商品目录构建。*

- [`tools/audit_source_crawlers.py`](../tools/audit_source_crawlers.py) (7.4 KB): `audit_all_crawlers`
- [`tools/build_affiliate_catalog.py`](../tools/build_affiliate_catalog.py) (3.8 KB): `validate_catalog, sync_into_monetization_js`
- [`tools/check_seo_descriptions.py`](../tools/check_seo_descriptions.py) (2.6 KB): `check`
- [`tools/fast_index.py`](../tools/fast_index.py) (62.1 KB): `discover_unregistered_crawlers, discover_rules_and_skills, discover_data_stores, extract_python_symbols, extract_js_symbols...`
- [`tools/fetch_affiliate_images.py`](../tools/fetch_affiliate_images.py) (8.1 KB): `main`
- [`tools/generate_thumbnails.py`](../tools/generate_thumbnails.py) (2.1 KB): `ensure_thumbnails`
- [`tools/prune_firebase_versions.py`](../tools/prune_firebase_versions.py) (6.7 KB): `prune_old_versions`
- [`tools/safe_sync.py`](../tools/safe_sync.py) (3.8 KB): `clean_git_locks, setup_proxy, run_sync`
- [`tools/sync_forbes_data.py`](../tools/sync_forbes_data.py) (4.3 KB): `patch_item, sync_file`
- [`tools/test_fetch_pillars.py`](../tools/test_fetch_pillars.py) (5.8 KB): `test_pillars`
- [`tools/trigger_workflow.py`](../tools/trigger_workflow.py) (1.9 KB): `trigger_dispatch`
- [`tools/update_bloomberg_data.py`](../tools/update_bloomberg_data.py) (1.5 KB): `update_item, update_container`
- [`tools/update_videos_feed.py`](../tools/update_videos_feed.py) (4.3 KB): `main`
- [`tools/verify_seo_fixes.py`](../tools/verify_seo_fixes.py) (2.9 KB): `verify`

### 流水线核心辅助脚本 (Active Pipeline Scripts)
*CI/CD 与日常数据同步调用的榜单更新、工具配图本地化、分卷导出与 IndexNow 推送脚本。*

- [`scripts/update_arena_leaderboard.py`](../scripts/update_arena_leaderboard.py) (11.9 KB): `sync_arena_leaderboard, run_daily_scheduler`
- [`scripts/localize_tool_images.py`](../scripts/localize_tool_images.py) (19.4 KB): `clean_url, is_bad_placeholder, fetch_url_bytes, extract_github_readme_images, make_smart_16_9...`
- [`scripts/export_archive_volumes.py`](../scripts/export_archive_volumes.py) (7.0 KB): `parse_time_for_sort, clean_item_for_volume, export_all_archive_volumes`
- [`scripts/push_indexnow.py`](../scripts/push_indexnow.py) (4.0 KB): `extract_urls_from_sitemap, submit_indexnow, main`
- [`scripts/rebuild_public_data.py`](../scripts/rebuild_public_data.py) (7.2 KB): `clean_archive_item, clean_public_item, parse_time, rebuild`
- [`scripts/purify_language_data.py`](../scripts/purify_language_data.py) (14.7 KB): `translate_en_string, purify_item, process_file, main`
- [`scripts/sync_curated_tools.py`](../scripts/sync_curated_tools.py) (3.0 KB): `main`
- [`scripts/enrich_github_tools.py`](../scripts/enrich_github_tools.py) (13.3 KB): `clean_url, get_mshots_url, extract_gh_owner_repo, fetch_readme, extract_website_from_readme...`
- [`scripts/enrich_tool_media.py`](../scripts/enrich_tool_media.py) (9.2 KB): `clean_url, get_website_screenshot_url, extract_github_readme_images, enrich_tool, main`
- [`scripts/update_prompt_templates.py`](../scripts/update_prompt_templates.py) (9.9 KB): `main`

### 工程规范与数据质量门禁 (Quality Gates & Verification)
*22 项数据质量硬性门禁、视频时效单元测试、27+ 爬虫单测与全工程防回退静态校验。*

- [`tests/test_anthropic_crawler.py`](../tests/test_anthropic_crawler.py) (5.2 KB): `TestAnthropicCrawler`
- [`tests/test_arstechnica_crawler.py`](../tests/test_arstechnica_crawler.py) (4.1 KB): `TestArsTechnicaCrawler`
- [`tests/test_bbc_crawler.py`](../tests/test_bbc_crawler.py) (4.2 KB): `TestBBCCrawler`
- [`tests/test_bloomberg_crawler.py`](../tests/test_bloomberg_crawler.py) (9.1 KB): `TestBloombergCrawler`
- [`tests/test_cbsnews_crawler.py`](../tests/test_cbsnews_crawler.py) (4.4 KB): `TestCBSNewsCrawler`
- [`tests/test_cnbc_crawler.py`](../tests/test_cnbc_crawler.py) (4.3 KB): `TestCnbcCrawler`
- [`tests/test_coindesk_crawler.py`](../tests/test_coindesk_crawler.py) (5.3 KB): `TestCoinDeskCrawler`
- [`tests/test_data_quality_gate.py`](../tests/test_data_quality_gate.py) (51.6 KB): `run_quality_gate_assertions, auto_heal_dataset`
- [`tests/test_decoder_crawler.py`](../tests/test_decoder_crawler.py) (8.2 KB): `TestDecoderCrawler`
- [`tests/test_fortune_crawler.py`](../tests/test_fortune_crawler.py) (6.5 KB): `TestFortuneCrawler`
- [`tests/test_ft_crawler.py`](../tests/test_ft_crawler.py) (4.3 KB): `TestFtCrawler`
- [`tests/test_ifixit_crawler.py`](../tests/test_ifixit_crawler.py) (4.8 KB): `TestIFixitCrawler`
- [`tests/test_ign_crawler.py`](../tests/test_ign_crawler.py) (9.8 KB): `TestIGNCrawler`
- [`tests/test_mittr_crawler.py`](../tests/test_mittr_crawler.py) (8.5 KB): `TestMittrCrawler`
- [`tests/test_nineto5mac_crawler.py`](../tests/test_nineto5mac_crawler.py) (4.7 KB): `TestNineTo5MacCrawler`
- [`tests/test_nypost_crawler.py`](../tests/test_nypost_crawler.py) (3.1 KB): `TestNYPostCrawler`
- [`tests/test_nyt_crawler.py`](../tests/test_nyt_crawler.py) (9.2 KB): `TestNytCrawler`
- [`tests/test_openai_crawler.py`](../tests/test_openai_crawler.py) (6.5 KB): `TestOpenAICrawler`
- [`tests/test_reuters_crawler.py`](../tests/test_reuters_crawler.py) (5.4 KB): `TestReutersCrawler`
- [`tests/test_semafor_crawler.py`](../tests/test_semafor_crawler.py) (2.9 KB): `TestSemaforCrawler`
- [`tests/test_siliconangle_crawler.py`](../tests/test_siliconangle_crawler.py) (2.9 KB): `TestSiliconAngleCrawler`
- [`tests/test_techcrunch_crawler.py`](../tests/test_techcrunch_crawler.py) (4.4 KB): `TestTechCrunchCrawler`
- [`tests/test_techfundingnews_crawler.py`](../tests/test_techfundingnews_crawler.py) (2.7 KB): `TestTechFundingNewsCrawler`
- [`tests/test_tomshardware_crawler.py`](../tests/test_tomshardware_crawler.py) (3.8 KB): `TestTomsHardwareCrawler`
- [`tests/test_verge_crawler.py`](../tests/test_verge_crawler.py) (5.0 KB): `TestVergeCrawler`
- [`tests/test_video_pipeline.py`](../tests/test_video_pipeline.py) (4.9 KB): `TestVideoPipeline`
- [`tests/test_wapo_crawler.py`](../tests/test_wapo_crawler.py) (5.9 KB): `TestWashingtonCrawlers`
- [`tests/test_wired_crawler.py`](../tests/test_wired_crawler.py) (4.8 KB): `TestWiredCrawler`
- [`tests/test_wsj_crawler.py`](../tests/test_wsj_crawler.py) (4.7 KB): `TestWsjCrawler`
- [`tools/verify_code_integrity.py`](../tools/verify_code_integrity.py) (5.9 KB): `scan_anti_patterns, run_unit_tests, main`

### 底层数据存储仓 (Data Stores & Cache Registries)
*后端主库（latest_news.json）、全量归档（master_archive.json）、精选库与信源持久化缓存（仅索引元数据）。*

**核心数据仓与公共分发：**
- **`data/affiliate_products.json`** (`310.8 KB`)
- **`data/apify_crawler_state.json`** (`385.3 KB`)
- **`data/archive_celebrity.json`** (`27.62 MB`)
- **`data/archive_news.json`** (`66.24 MB`)
- **`data/curated_column_highlights.json`** (`36.9 KB`)
- **`data/curated_prompts_library.json`** (`42.2 KB`)
- **`data/curated_workflows_library.json`** (`13.6 KB`)
- **`data/github_stars_history.json`** (`102.4 KB`)
- **`data/indexnow_ledger.json`** (`302.9 KB`)
- **`data/knowledge_graph.json`** (`69.6 KB`)
- **`data/latest_news.json`** (`24.64 MB`)
- **`data/latest_wechat.json`** (`29.3 KB`)
- **`data/master_archive.json`** (`90.44 MB`)
- **`data/processed_news_ledger.json`** (`9.82 MB`)
- **`data/sota_model_registry.json`** (`9.5 KB`)
- **`data/topic_focus.json`** (`18.3 KB`)
- **`public/data/latest_news.json`** (`612.9 KB`)
- **信源独立缓存 (`data/*_cache.json`)**: 共 `27` 个文件，合计 `16.52 MB`（anthropic, arstechnica, bloomberg, cbsnews, chatbot_arena, cnbc, decoder, deepmind, forbes, fortune, ft, mittr, nineto5mac, nypost, nyt, openai, reuters, semafor, siliconangle, techcrunch, techeu, tweet_tags, verge, wapo, washsun, wired, wsj）

---

## 3. 全量权威信源与爬虫路由注册表 (Source Registry — 34 Sources)

| 信源 / 域名 | 解析模块 | 调度入口 | 校验 / 单测 | 守则锚点 |
| :--- | :--- | :--- | :--- | :--- |
| **`bloomberg.com`** (Bloomberg) | [`crawlers/bloomberg_crawler.py`](../crawlers/bloomberg_crawler.py) | `crawl_bloomberg` | `tests/test_bloomberg_crawler.py` | `crawlers/AGENTS.md §5` |
| **`forbes.com`** (Forbes) | [`crawlers/forbes_crawler.py`](../crawlers/forbes_crawler.py) | `crawl_forbes` | `tools/audit_source_crawlers.py` | `crawlers/AGENTS.md §2` |
| **`tech.eu`** (Tech.eu) | [`crawlers/techeu_crawler.py`](../crawlers/techeu_crawler.py) | `crawl_techeu` | `tools/audit_source_crawlers.py` | `crawlers/AGENTS.md §3` |
| **`deepmind.google`** (Google DeepMind / Institute) | [`crawlers/deepmind_crawler.py`](../crawlers/deepmind_crawler.py) | `crawl_deepmind` | `tools/audit_source_crawlers.py` | `crawlers/AGENTS.md §4` |
| **`anthropic.com`** (Anthropic) | [`crawlers/anthropic_crawler.py`](../crawlers/anthropic_crawler.py) | `crawl_anthropic` | `tests/test_anthropic_crawler.py` | `crawlers/AGENTS.md §1` |
| **`openai.com`** (OpenAI) | [`crawlers/openai_crawler.py`](../crawlers/openai_crawler.py) | `crawl_openai` | `tests/test_openai_crawler.py` | `crawlers/AGENTS.md §1` |
| **`reuters.com`** (Reuters) | [`crawlers/reuters_crawler.py`](../crawlers/reuters_crawler.py) | `crawl_reuters` | `tests/test_reuters_crawler.py` | `AGENTS.md §1.1 & crawlers/AGENTS.md §1` |
| **`wsj.com`** (Wall Street Journal) | [`crawlers/wsj_crawler.py`](../crawlers/wsj_crawler.py) | `crawl_wsj` | `tests/test_wsj_crawler.py` | `crawlers/AGENTS.md §1` |
| **`ft.com`** (Financial Times) | [`crawlers/ft_crawler.py`](../crawlers/ft_crawler.py) | `crawl_ft` | `tests/test_ft_crawler.py` | `crawlers/AGENTS.md §1` |
| **`nytimes.com`** (The New York Times) | [`crawlers/nyt_crawler.py`](../crawlers/nyt_crawler.py) | `crawl_nyt` | `tests/test_nyt_crawler.py` | `crawlers/AGENTS.md §1` |
| **`washingtonpost.com`** (The Washington Post) | [`crawlers/wapo_crawler.py`](../crawlers/wapo_crawler.py) | `crawl_wapo` | `tests/test_wapo_crawler.py` | `crawlers/AGENTS.md §1` |
| **`washingtonsun.com`** (The Washington Sun) | [`crawlers/washsun_crawler.py`](../crawlers/washsun_crawler.py) | `crawl_washsun` | `tests/test_wapo_crawler.py` | `crawlers/AGENTS.md §1` |
| **`fortune.com`** (Fortune) | [`crawlers/fortune_crawler.py`](../crawlers/fortune_crawler.py) | `crawl_fortune` | `tests/test_fortune_crawler.py` | `crawlers/AGENTS.md §1` |
| **`cnbc.com`** (CNBC) | [`crawlers/cnbc_crawler.py`](../crawlers/cnbc_crawler.py) | `crawl_cnbc` | `tests/test_cnbc_crawler.py` | `crawlers/AGENTS.md §1` |
| **`bbc.com`** (BBC News) | [`crawlers/bbc_crawler.py`](../crawlers/bbc_crawler.py) | `crawl_bbc` | `tests/test_bbc_crawler.py` | `crawlers/AGENTS.md §1` |
| **`cbsnews.com`** (CBS News) | [`crawlers/cbsnews_crawler.py`](../crawlers/cbsnews_crawler.py) | `crawl_cbsnews` | `tests/test_cbsnews_crawler.py` | `crawlers/AGENTS.md §1` |
| **`nypost.com`** (New York Post) | [`crawlers/nypost_crawler.py`](../crawlers/nypost_crawler.py) | `crawl_nypost` | `tests/test_nypost_crawler.py` | `crawlers/AGENTS.md §1` |
| **`semafor.com`** (Semafor) | [`crawlers/semafor_crawler.py`](../crawlers/semafor_crawler.py) | `crawl_semafor` | `tests/test_semafor_crawler.py` | `crawlers/AGENTS.md §1` |
| **`techcrunch.com`** (TechCrunch) | [`crawlers/techcrunch_crawler.py`](../crawlers/techcrunch_crawler.py) | `crawl_techcrunch` | `tests/test_techcrunch_crawler.py` | `crawlers/AGENTS.md §1` |
| **`theverge.com`** (The Verge) | [`crawlers/verge_crawler.py`](../crawlers/verge_crawler.py) | `crawl_verge` | `tests/test_verge_crawler.py` | `crawlers/AGENTS.md §1` |
| **`wired.com`** (WIRED) | [`crawlers/wired_crawler.py`](../crawlers/wired_crawler.py) | `crawl_wired` | `tests/test_wired_crawler.py` | `crawlers/AGENTS.md §1` |
| **`technologyreview.com`** (MIT Technology Review) | [`crawlers/mittr_crawler.py`](../crawlers/mittr_crawler.py) | `crawl_mittr` | `tests/test_mittr_crawler.py` | `crawlers/AGENTS.md §1` |
| **`the-decoder.com`** (The Decoder) | [`crawlers/decoder_crawler.py`](../crawlers/decoder_crawler.py) | `crawl_decoder` | `tests/test_decoder_crawler.py` | `crawlers/AGENTS.md §1` |
| **`arstechnica.com`** (Ars Technica) | [`crawlers/arstechnica_crawler.py`](../crawlers/arstechnica_crawler.py) | `crawl_arstechnica` | `tests/test_arstechnica_crawler.py` | `crawlers/AGENTS.md §1` |
| **`siliconangle.com`** (SiliconANGLE) | [`crawlers/siliconangle_crawler.py`](../crawlers/siliconangle_crawler.py) | `crawl_siliconangle` | `tests/test_siliconangle_crawler.py` | `crawlers/AGENTS.md §1` |
| **`techfundingnews.com`** (Tech Funding News) | [`crawlers/techfundingnews_crawler.py`](../crawlers/techfundingnews_crawler.py) | `crawl_techfundingnews` | `tests/test_techfundingnews_crawler.py` | `crawlers/AGENTS.md §1` |
| **`coindesk.com`** (CoinDesk) | [`crawlers/coindesk_crawler.py`](../crawlers/coindesk_crawler.py) | `crawl_coindesk` | `tests/test_coindesk_crawler.py` | `crawlers/AGENTS.md §1` |
| **`9to5mac.com`** (9to5Mac) | [`crawlers/nineto5mac_crawler.py`](../crawlers/nineto5mac_crawler.py) | `crawl_nineto5mac` | `tests/test_nineto5mac_crawler.py` | `crawlers/AGENTS.md §1` |
| **`tomshardware.com`** (Tom's Hardware) | [`crawlers/tomshardware_crawler.py`](../crawlers/tomshardware_crawler.py) | `crawl_tomshardware` | `tests/test_tomshardware_crawler.py` | `crawlers/AGENTS.md §1` |
| **`ifixit.com`** (iFixit) | [`crawlers/ifixit_crawler.py`](../crawlers/ifixit_crawler.py) | `crawl_ifixit` | `tests/test_ifixit_crawler.py` | `crawlers/AGENTS.md §1` |
| **`ign.com`** (IGN) | [`crawlers/ign_crawler.py`](../crawlers/ign_crawler.py) | `crawl_ign` | `tests/test_ign_crawler.py` | `crawlers/AGENTS.md §1` |
| **`youtube.com`** (YouTube) | [`viral_video_engine.py`](../viral_video_engine.py) | `fetch_trending_ai_videos` | `tests/test_video_pipeline.py` | `AGENTS.md §3.5 & docs/CODE_INDEX.md (断言 4, 18)` |
| **`x.com`** (X (Twitter)) | [`apify_crawler.py`](../apify_crawler.py) | `fetch_incremental_tweets` | `tests/test_data_quality_gate.py` | `docs/CODE_INDEX.md (断言 5, 10, 11, 12)` |
| **`arxiv.org`** (arXiv) | [`fetcher.py`](../fetcher.py) | `fetch_arxiv_papers` | `tests/test_data_quality_gate.py` | `AGENTS.md §3.5` |

---

## 4. 极速索引检索指令 (Instant CLI Lookup Cheat-Sheet)

```bash
# 1. 符号定位（精确 O(1) + 大小写不敏感与模糊建议，支持函数别名与核心 JS）
python tools/fast_index.py symbol crawl_bloomberg

# 2. 信源路由查询（支持全部 31 爬虫 + YouTube/X/arXiv）
python tools/fast_index.py source bloomberg

# 3. 全局模糊检索（跨规则、技能、信源、文件与符号）
python tools/fast_index.py search modal

# 4. 数据仓分级内存直查（默认优先查轻量热仓，精确 ID 命中即停；加 --all 扫归档仓）
python tools/fast_index.py data b86591fb2c47a91d

# 5. 查看项目作用域规则预算（24 KB 红线）与本地技能
python tools/fast_index.py rules

# 6. 查看架构分层文件与导出符号
python tools/fast_index.py tier frontend

# 7. 校验索引时效、规则预算与爬虫注册表完整性
python tools/fast_index.py --check

# 8. 增量同步 / 全量重建索引
python tools/fast_index.py --sync
python tools/fast_index.py build
```
