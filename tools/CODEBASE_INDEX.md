# AI News Radar - 代码库架构与符号极速索引 (Codebase Fast Index)

> **生成时间**: `2026-11-25 10:08:43 UTC` | **收录文件**: `110` 个 | **索引符号**: `1294` 个
> **更新机制**: 由 `tools/fast_index.py` 驱动，在每次代码修改、测试门禁校验与提交前自动增量同步刷新。

---

## 1. 核心架构与功能分层 (Architectural Tiers)

### 信源抓取与解析层 (Dedicated Source Crawlers)
*负责各权威信源（Bloomberg, Forbes, Reuters, DeepMind 等）的定向穿透、授权配图提取与正文清洗。*

- **`crawlers/anthropic_crawler.py`** (28,812 bytes): `is_anthropic_url, _canonical_anthropic_key, _get_proxies, _clean_text, _clean_anthropic_title...`
- **`crawlers/arstechnica_crawler.py`** (31,708 bytes): `is_arstechnica_url, _canonical_ars_key, _get_proxies, _clean_text, _clean_ars_title...`
- **`crawlers/bbc_crawler.py`** (30,352 bytes): `is_bbc_url, _canonical_bbc_key, _get_proxies, _clean_text, _clean_bbc_title...`
- **`crawlers/bloomberg_crawler.py`** (91,521 bytes): `_slug_tokens, _is_generic_bloomberg_title, _has_reuters_contamination, _is_invalid_bloomberg_image, _upgrade_image_url...`
- **`crawlers/cbsnews_crawler.py`** (31,821 bytes): `is_cbsnews_url, _canonical_cbs_key, _get_proxies, _clean_text, _clean_cbs_title...`
- **`crawlers/cnbc_crawler.py`** (28,533 bytes): `is_cnbc_url, _canonical_cnbc_key, _get_proxies, _clean_text, _clean_cnbc_title...`
- **`crawlers/coindesk_crawler.py`** (33,262 bytes): `is_coindesk_url, _canonical_coindesk_key, _get_proxies, _clean_text, _clean_coindesk_title...`
- **`crawlers/decoder_crawler.py`** (37,548 bytes): `is_decoder_url, _canonical_decoder_key, _extract_decoder_slug, _get_proxies, _clean_text...`
- **`crawlers/deepmind_crawler.py`** (25,011 bytes): `is_deepmind_url, extract_deepmind_slug, clean_deepmind_title, extract_deepmind_author_from_title, clean_deepmind_paragraphs...`
- **`crawlers/forbes_crawler.py`** (28,856 bytes): `_get_proxies, _get_from_disk_cache, _save_to_disk_cache, is_forbes_url, extract_forbes_slug...`
- **`crawlers/fortune_crawler.py`** (22,352 bytes): `_get_proxies, _get_from_disk_cache, _save_to_disk_cache, is_fortune_url, fetch_fortune_html...`
- **`crawlers/ft_crawler.py`** (23,292 bytes): `is_ft_url, _canonical_ft_key, _get_proxies, _is_valid_ft_image, _ft_media_stem...`
- **`crawlers/ifixit_crawler.py`** (32,680 bytes): `is_ifixit_url, _canonical_ifixit_key, _get_proxies, _clean_text, _clean_ifixit_title...`
- **`crawlers/ign_crawler.py`** (45,240 bytes): `is_ign_url, _canonical_ign_key, _get_proxies, _clean_text, _clean_ign_title...`
- **`crawlers/mittr_crawler.py`** (36,588 bytes): `is_mittr_url, _canonical_mittr_key, _extract_mittr_post_id, _extract_mittr_slug, _get_proxies...`
- **`crawlers/nineto5mac_crawler.py`** (40,644 bytes): `is_nineto5mac_url, _canonical_n95m_key, _get_proxies, _clean_text, _clean_n95m_title...`
- **`crawlers/nypost_crawler.py`** (31,265 bytes): `is_nypost_url, _canonical_nypost_key, _get_proxies, _clean_text, _clean_nypost_title...`
- **`crawlers/nyt_crawler.py`** (34,702 bytes): `is_nyt_url, _canonical_nyt_key, _get_proxies, _is_valid_nyt_image, _nyt_media_stem...`
- **`crawlers/openai_crawler.py`** (54,509 bytes): `is_openai_url, _canonical_openai_key, _get_proxies, _clean_text, _clean_openai_title...`
- **`crawlers/reuters_crawler.py`** (31,323 bytes): `_get_from_disk_cache, _save_to_disk_cache, is_reuters_url, _is_valid_cover_image, _localize_reuters_image...`
- **`crawlers/semafor_crawler.py`** (28,202 bytes): `is_semafor_url, _canonical_semafor_key, _get_proxies, _clean_text, _clean_semafor_title...`
- **`crawlers/siliconangle_crawler.py`** (35,205 bytes): `is_siliconangle_url, _canonical_sa_key, _extract_sa_slug, _get_proxies, _clean_text...`
- **`crawlers/techcrunch_crawler.py`** (33,575 bytes): `is_techcrunch_url, _canonical_tc_key, _extract_tc_slug, _get_proxies, _clean_text...`
- **`crawlers/techeu_crawler.py`** (48,741 bytes): `is_techeu_url, extract_techeu_slug, clean_techeu_title, extract_techeu_author_from_title, clean_techeu_paragraphs...`
- **`crawlers/techfundingnews_crawler.py`** (30,865 bytes): `is_techfundingnews_url, _canonical_tfn_key, _get_proxies, _clean_text, _clean_tfn_title...`
- **`crawlers/tomshardware_crawler.py`** (32,837 bytes): `is_tomshardware_url, _canonical_toms_key, _get_proxies, _clean_text, _clean_toms_title...`
- **`crawlers/verge_crawler.py`** (22,791 bytes): `is_verge_url, _get_proxies, _is_valid_verge_image, _clean_html_fragment, _clean_verge_title...`
- **`crawlers/wapo_crawler.py`** (29,305 bytes): `is_wapo_url, _canonical_wapo_path, _canonical_wapo_key, _get_proxies, _is_valid_wapo_image...`
- **`crawlers/washsun_crawler.py`** (15,365 bytes): `is_washsun_url, _canonical_key, _get_proxies, _is_valid_washsun_image, _clean_text...`
- **`crawlers/wired_crawler.py`** (25,959 bytes): `is_wired_url, _canonical_wired_key, _get_proxies, _is_valid_wired_image, _wired_media_stem...`
- **`crawlers/wsj_crawler.py`** (31,651 bytes): `is_wsj_url, _get_proxies, _is_valid_wsj_image, _strip_wayback_prefix, _clean_wsj_title...`

### 流水线核心调度层 (Core Pipeline & Orchestration)
*系统中央调度、信源分发、多模态事实提取与去重清洗管道。*

- **`main.py`** (258,343 bytes): `generate_sitemap, inject_seo_static_content, generate_daily_briefing, parse_time_for_sort, is_tibo_reset_tweet...`
- **`processor.py`** (122,048 bytes): `has_chinglish_seams, strip_chinglish_to_english, normalize_ai_terminology_zh, _translate_single_chunk_zh, free_translate_zh...`
- **`fetcher.py`** (196,858 bytes): `extract_tech_specs, make_id, is_primarily_english, parse_to_iso, get_smart_cover_url...`
- **`article_extractor.py`** (57,762 bytes): `ArticleExtractor, extract_article_substantive`
- **`config.py`** (112,496 bytes): `No exported symbols`
- **`knowledge_base.py`** (20,556 bytes): `DynamicKnowledgeStore`

### 研判精选与头条矩阵 (Curator & Intelligence Highlights)
*负责 Top 3 今日核心突破、大V思辨矩阵、5W1H 事实提炼与中英高保真本地化。*

- **`curator_engine.py`** (55,399 bytes): `parse_item_pub_time, curate_news_column, curate_celebrity_column, is_blacklisted_tool, detect_tool_domain...`
- **`topic_cluster.py`** (70,389 bytes): `_get_cached_topic_focus_if_fresh, get_gemini_client, _load_curated_workflows, _match_best_tool_or_workflow, _cluster_topics_with_gemini...`
- **`language_sentinel.py`** (30,509 bytes): `has_cjk, count_chinese_chars, is_pure_chinese_paragraph, translate_and_purify_article, sanitize_item_language...`
- **`tweet_classifier.py`** (14,268 bytes): `load_tags_cache, save_tags_cache, detect_code_or_prompt, rule_based_classify, enrich_tweet_with_tag...`

### 静态发布与 SEO/GEO 引擎 (Static Publishing & Distribution)
*单篇静态落地页编译、首页 SSR 注入、分卷切片、Sitemap 生成与 IndexNow 秒级收录推送。*

- **`content_publisher.py`** (271,976 bytes): `format_static_tool_card, format_static_video_card, format_static_prompt_card, format_static_arxiv_card, parse_tweet_time...`
- **`tool_news_publisher.py`** (154,869 bytes): `parse_iso_date, sanitize_for_en, escape, build_theme_toggle_html, build_ainr_tags_meta...`
- **`build_flagship_articles.py`** (30,871 bytes): `generate_article_page, generate_articles_index, build_all_flagship_pages, main`
- **`seo_geo_engine.py`** (41,421 bytes): `atomic_write_text, atomic_write_bytes, sanitize_for_en, xml_escape, parse_iso_or_rfc...`
- **`indexnow_submitter.py`** (6,599 bytes): `load_sitemap_urls, load_ledger, save_ledger, submit_urls_to_indexnow, auto_submit_recent_or_all`

### 短视频与多模态实战层 (Video & Multimodal Engine)
*YouTube / Bilibili / TikTok 实战视频发现、24-48h 时效切片与去套壳清洗。*

- **`viral_video_engine.py`** (119,453 bytes): `VideoTimeTuple, get_dynamic_news_hotspots, parse_youtube_views, is_promotional_or_junk, calculate_video_momentum...`
- **`prompts_and_videos.py`** (134,608 bytes): `get_curated_actionable_prompts, get_curated_tutorials`

### 前端客户端与单页交互 (Frontend SPA & Mobile App)
*极速弹窗阅读、分卷动态加载、移动端自适应布局与多语言热切换交互。*

- **`public/js/app.js`** (777,388 bytes): `flipPinnedSlide, scheduleNextPinnedFlip, initPinnedSlider, optimizeImageUrl, optimizeAvatarUrl...`
- **`public/m/js/mobile.js`** (105,360 bytes): `updateLanguageState, initTheme, toggleTheme, updateThemeIcon, ensureChineseConverter...`
- **`public/js/monetization.js`** (0 bytes): `No exported symbols`
- **`public/js/chinese_converter.js`** (0 bytes): `No exported symbols`

### 工程规范与数据质量门禁 (Quality Gates & Verification)
*21 项数据质量硬性门禁、视频时效断言与全工程代码规范防回退静态校验。*

- **`tests/test_anthropic_crawler.py`** (5,314 bytes): `TestAnthropicCrawler`
- **`tests/test_arstechnica_crawler.py`** (4,171 bytes): `TestArsTechnicaCrawler`
- **`tests/test_bbc_crawler.py`** (4,260 bytes): `TestBBCCrawler`
- **`tests/test_bloomberg_crawler.py`** (9,302 bytes): `TestBloombergCrawler`
- **`tests/test_cbsnews_crawler.py`** (4,481 bytes): `TestCBSNewsCrawler`
- **`tests/test_cnbc_crawler.py`** (4,370 bytes): `TestCnbcCrawler`
- **`tests/test_coindesk_crawler.py`** (5,404 bytes): `TestCoinDeskCrawler`
- **`tests/test_data_quality_gate.py`** (49,765 bytes): `run_quality_gate_assertions, auto_heal_dataset`
- **`tests/test_decoder_crawler.py`** (8,366 bytes): `TestDecoderCrawler`
- **`tests/test_fortune_crawler.py`** (6,611 bytes): `TestFortuneCrawler`
- **`tests/test_ft_crawler.py`** (4,450 bytes): `TestFtCrawler`
- **`tests/test_ifixit_crawler.py`** (4,916 bytes): `TestIFixitCrawler`
- **`tests/test_ign_crawler.py`** (10,047 bytes): `TestIGNCrawler`
- **`tests/test_mittr_crawler.py`** (8,719 bytes): `TestMittrCrawler`
- **`tests/test_nineto5mac_crawler.py`** (4,830 bytes): `TestNineTo5MacCrawler`
- **`tests/test_nypost_crawler.py`** (3,168 bytes): `TestNYPostCrawler`
- **`tests/test_nyt_crawler.py`** (9,405 bytes): `TestNytCrawler`
- **`tests/test_openai_crawler.py`** (6,618 bytes): `TestOpenAICrawler`
- **`tests/test_reuters_crawler.py`** (5,516 bytes): `TestReutersCrawler`
- **`tests/test_semafor_crawler.py`** (2,951 bytes): `TestSemaforCrawler`
- **`tests/test_siliconangle_crawler.py`** (3,008 bytes): `TestSiliconAngleCrawler`
- **`tests/test_techcrunch_crawler.py`** (4,544 bytes): `TestTechCrunchCrawler`
- **`tests/test_techfundingnews_crawler.py`** (2,723 bytes): `TestTechFundingNewsCrawler`
- **`tests/test_tomshardware_crawler.py`** (3,868 bytes): `TestTomsHardwareCrawler`
- **`tests/test_verge_crawler.py`** (5,110 bytes): `TestVergeCrawler`
- **`tests/test_video_pipeline.py`** (5,016 bytes): `TestVideoPipeline`
- **`tests/test_wapo_crawler.py`** (6,028 bytes): `TestWashingtonCrawlers`
- **`tests/test_wired_crawler.py`** (4,886 bytes): `TestWiredCrawler`
- **`tests/test_wsj_crawler.py`** (4,809 bytes): `TestWsjCrawler`
- **`tools/verify_code_integrity.py`** (5,014 bytes): `scan_anti_patterns, run_unit_tests, main`

### 底层数据存储仓 (Data Stores & Cache Registries)
*公共数据仓（latest_news.json）、全量归档（master_archive.json）与信源独立持久化缓存。*


---

## 2. 权威信源与爬虫路由注册表 (Source Crawler Registry)

| 信源标识 / 域名 | 对应解析模块 | 核心调度入口 | 单元测试文件 | 守则规范锚点 |
| :--- | :--- | :--- | :--- | :--- |
| **`bloomberg.com`** (Bloomberg) | [`crawlers/bloomberg_crawler.py`](crawlers/bloomberg_crawler.py) | `crawl_bloomberg` | `tests/test_bloomberg_crawler.py` | `AGENTS.md Section 12` |
| **`forbes.com`** (Forbes) | [`crawlers/forbes_crawler.py`](crawlers/forbes_crawler.py) | `crawl_forbes` | `tests/test_forbes_crawler.py` | `AGENTS.md Section 9` |
| **`tech.eu`** (Tech.eu) | [`crawlers/techeu_crawler.py`](crawlers/techeu_crawler.py) | `crawl_techeu` | `tests/test_techeu_crawler.py` | `AGENTS.md Section 10` |
| **`deepmind.google`** (Google DeepMind / Institute) | [`crawlers/deepmind_crawler.py`](crawlers/deepmind_crawler.py) | `crawl_deepmind` | `tests/test_deepmind_crawler.py` | `AGENTS.md Section 11` |
| **`the-decoder.com`** (The Decoder) | [`crawlers/decoder_crawler.py`](crawlers/decoder_crawler.py) | `crawl_decoder` | `tests/test_decoder_crawler.py` | `-` |
| **`techcrunch.com`** (TechCrunch) | [`crawlers/techcrunch_crawler.py`](crawlers/techcrunch_crawler.py) | `crawl_techcrunch` | `tests/test_techcrunch_crawler.py` | `-` |
| **`reuters.com`** (Reuters) | [`crawlers/reuters_crawler.py`](crawlers/reuters_crawler.py) | `crawl_reuters` | `tests/test_reuters_crawler.py` | `-` |
| **`arstechnica.com`** (Ars Technica) | [`crawlers/arstechnica_crawler.py`](crawlers/arstechnica_crawler.py) | `crawl_arstechnica` | `tests/test_arstechnica_crawler.py` | `-` |
| **`coindesk.com`** (CoinDesk) | [`crawlers/coindesk_crawler.py`](crawlers/coindesk_crawler.py) | `crawl_coindesk` | `tests/test_coindesk_crawler.py` | `-` |
| **`youtube.com`** (YouTube) | [`viral_video_engine.py`](viral_video_engine.py) | `fetch_trending_ai_videos` | `tests/test_video_pipeline.py` | `AGENTS.md Rule 3.5 & Rule 18` |
| **`twitter.com`** (𝕏 (Twitter)) | [`crawlers/twitter_crawler.py`](crawlers/twitter_crawler.py) | `crawl_twitter` | `-` | `-` |
| **`arxiv.org`** (arXiv) | [`fetcher.py`](fetcher.py) | `fetch_arxiv_papers` | `-` | `-` |

---

## 3. 极速索引检索指令 (Instant CLI Lookup Cheat-Sheet)

AI 模型或开发人员无需全盘慢扫描，可直接在终端秒级查阅任意符号、信源或数据：
```bash
# 1. 秒查符号定位 (函数/类名直达代码行号)
python tools/fast_index.py symbol crawl_bloomberg

# 2. 秒查权威信源 (获取对应爬虫文件、入口函数与规则)
python tools/fast_index.py source bloomberg

# 3. 全局模糊检索 (在毫秒内检索函数名、模块及架构说明)
python tools/fast_index.py search modal

# 4. 数据仓内存直查 (0.05秒查找特定资讯 ID/URL，杜绝无脑 Select-String 假死)
python tools/fast_index.py data b86591fb2c47a91d

# 5. 增量重新构建索引
python tools/fast_index.py build
```
