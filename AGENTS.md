# AI News Radar - 核心架构与质量工程守则 (Root Project Rules)

> 本文件为 Antigravity Agent 在本仓库的**全局最高质量准则**（严格控制在 24 KB 规则上限内，确保零截断完整加载）。
> 专有信源爬虫契约与前端细则已按 Antigravity 层级作用域拆分为目录规则：`crawlers/AGENTS.md` 与 `public/AGENTS.md`（见 §10 路由表）。

---

## 1. 信源隔离与真品保真原则 (Source Integrity & Anti-Pollution)

1. **零异源通讯社污染**：严禁将第三方通讯社（如 Reuters）电讯稿摘要拼接到另一主流媒体（如 Bloomberg）正文中；跨信源兜底（`fetch_cross_grounding_facts`）必须正则切除 `By ... (Reuters) -`、`BEIJING (Reuters) -` 等署名前缀。
2. **零悬空截断与原厂实录忠实**：正文段落末尾严禁出现 `such as ...`、`including ...`、`and other ...` 或悬空省略号 `...`；段落须标点完整；主流特稿必须忠实保留第一现场原文字句，严禁用粗糙合成段落替代。
3. **真实原厂配图与零无关库存假图**：权威报道严禁误配无人机或机器人坐长椅（Unsplash `photo-1620712943543`）等具象库存假图；默认缺省回退仅能使用官方中性品牌卡（`/images/og-default.jpg`）或纯排版卡（`feed-card-editorial`）。付费墙/风控信源（Bloomberg、WSJ 等）须经二级电讯网络穿透提取高清原图并本地托管至 `/images/...`。
4. **零图片注释与邮件推广杂质**：严禁将配图注释（Caption）、摄影机构署名（`Photo by ...`、`新华社发`、`视觉中国供图`）及邮件订阅尾巴（`Get the most important tech news...` 等）混入正文，须经 `clean_article_paragraphs` 净化。
5. **URL/Slug 规范化与检索安全**：提取 URL slug 必须先 `re.sub(r'^-+|-+$', '', slug)` 剔除首尾连字符与特殊符号；严禁将带前导 `-` 的原始 slug 拼入搜索引擎查询（防触发负向排除符自锁）。
6. **零付费墙试读与缓存防投毒**：严禁入库/渲染试读残篇与登录诱导语（`Log in to keep reading`、`Bloomberg Law provides`、`Sign in to access`、`登录以继续阅读`、`订阅以解锁` 等），统一经 `is_paywall_or_login_noise` / `has_paywall_or_truncation_noise` 过滤；从任何本地磁盘缓存加载历史条目时必须复检，命中杂质即强制废弃重抓。
7. **电讯语义校验与禁泛型头像**：二级电讯穿透必须双向比对标题与核心摘要关键词重合度（≥ 35%），杜绝单点关键词误抓无关文章；严禁收录 `bwrite-generic-profile`、`author-profile`、`avatar`、`width=44`、`headshot` 等小尺寸头像/占位图，无高清原图时仅回退 `/images/og-default.jpg`。
8. **社媒长推文无损补全与防切片截断**：RSS/Syndication 抓取的 X/Twitter 正文若落入 110–295 字符或含断尾特征/`t.co/` 链接，视为潜在截断，必须经 FxTwitter API（带重试、自动探测代理 `127.0.0.1:7890`、并发 `≤ 6`）或 Apify `noteTweet` 补全完整正文，并在补全后立即重算 `evaluate_dynamic_pinned_status`；`language_sentinel.py` 处理原文参考字段严禁使用 `[:300]`、`[:400]` 等硬切片。

---

## 2. 单页看板（SPA）交互与语义防伪 (SPA Navigation & Microdata)

1. **弹窗优先**：各分类页签（`#news`、`#celebrity`、`#tools`、`#videos`、`#prompts`）点击卡片须优先呼出站内 AI 分析弹窗（`openAiNewsModal` / `openToolDetailModal`），严禁强制硬跳转打断翻页与滚动上下文。
2. **三池历史穿透**：弹窗检索池必须同时覆盖 `cachedData`、`_volumeCache`（已加载分卷）与 `cachedArchiveData`，确保深层历史翻页 0ms 秒开、零 404。
3. **404 智能救赎**：`public/404.html` 必须常驻路径捕获脚本，将未静态化单篇直链平滑重定向至 `/#news?open={id}`。
4. **Microdata 语义归位与防假正文**：`tool_news_publisher.py` / `content_publisher.py` 中 `itemprop="articleBody"` 仅能声明于正文容器 `<div class="article-body">`，严禁标在摘要或 `<ul>/<ol>` 列表上；`public/js/app.js` 降级提取器须拦截纯列表或无 `<p>` 容器，防止要点列表冒充深度正文。

---

## 3. 静态分卷架构、双轨同构与 SEO/GEO (Chunking, Sync & SEO)

1. **按需分卷加载**：历史内容按分类切片 96 条/卷（`vol_{N}.json`），按页加载，严禁回退为单体大归档拉取；Page 1 须由 `cachedData.grouped[tab]` 0ms 直出。
2. **公共数据体积红线**：`public/data/latest_news.json` 必须严格 ≤ 850 KB（CI 断言 14 阻断），剔除与 `paragraphs` 重复的 `article_content_en` 等冗余字段。
3. **后端主库第一源与双轨兜底**：服务端静态编译（`tool_news_publisher.py`、`content_publisher.py`）必须以完整后端主库（`data/latest_news.json`、`data/master_archive.json`）为第一数据源，严禁倒挂读取前端精简版 `public/data/latest_news.json`；正文渲染须优先读完整长文，为空时无缝降级拼接 `paragraphs` / `paragraphs_zh`。
4. **全容器原子同步与前端精简库显式重建**：`language_sentinel.py` 与 `content_publisher.py` 不会自动将 `data/latest_news.json` 的改动派生覆盖 `public/data/latest_news.json`。凡更新或回填条目，必须先按 `id` 去重并同步刷新 `data/latest_news.json`（含 `items`、`grouped[cat]`、`viral_ticker_tweets`）、`data/master_archive.json`、`data/archive_news.json` 与 `vol_{N}.json`，**显式重建精简版 `public/data/latest_news.json`（≤ 850 KB）**，再同步保持 `paragraphs`/`paragraphs_zh`、`article_content`/`article_content_zh`/`original_content`、`lead_paragraph` 一致后执行哨兵与静态发布器。
5. **首页零割裂与双轨同构**：
   - **幂等 SSR 容器替换**：`content_publisher.py` 注入 `stream-news/videos/prompts/tools/arxiv` 严禁依赖一次性注释占位符，须使用基于边界锚点的无状态全覆盖替换。
   - **水合时间戳强校验**：`public/js/app.js` 复用 SSR DOM 前必须校验 `ssrUpdated && data.updated_at && ssrUpdated === data.updated_at`，版本变更立即强制 `renderUI()`。
   - **底部三列等高切片**：栅格定高容器须与卡片数量耦合——实战视频回溯 24–48h 取满 4 张、紧凑提示词取满 8 张、深度工作流取满 3 张，消除底部留白断崖。
6. **24h 时效优先与 SEO/GEO 闭环**：
   - 快讯流严格按 `raw_published_at` 倒序固化近 1–6h 突发资讯；每条快讯 `<article>` 声明 `itemscope itemtype="https://schema.org/NewsArticle"` 及 `headline`/`datePublished`/`dateModified`。
   - 首屏英雄图 `<head>` 动态注入 `preload` + `fetchpriority="high"`；媒体容器显式声明宽高比实现 `CLS = 0`；静态发布后同步推送 IndexNow。

---

## 4. 前端图片直连与破损自愈 (Direct CDN & Fallback)

1. **自托管直连，禁用海外反代 (Rule 4.1)**：站内图片统一经 Firebase CDN 自身路径（`/images/...`）或源站官方 CDN（如 `i.ytimg.com`）直连，严禁使用 `wsrv.nl` 等不稳定第三方代理。
2. **破损容器彻底隐藏**：所有 `<img>` 的 `onerror` 必须在加载失败时隐藏父容器（`this.closest('a')?.style.display='none'`），绝不留空置白框。

---

## 5. 质量门禁一票否决制 (CI Quality Gate)

- 任何代码与数据变更必须 100% 通过 `python tools/verify_code_integrity.py` 与 `python tests/test_data_quality_gate.py`（共 22 项硬性断言）；任一失败即视为不可发布缺陷。

---

## 6. 防回退、类型安全与极速检索 (Zero Regression & Fast Index)

1. **Python 3.12 运行时平权 (PEP 563/649)**：凡新建/修改 `.py` 文件，头部必须声明 `from __future__ import annotations`，且所有类型标注符号（`Any`, `List`, `Dict`, `Optional`, `Tuple`, `Union`, `Iterable`, `Set` 等）须 100% 从 `typing` 显式导入，严禁依赖本地 Python 3.14 延迟求值特性。
2. **底层改动三级验证**：修改 `crawlers/`、`processor.py`、`article_extractor.py` 等公共模块后必须依次执行：
   1. `python -c "import <模块>"`（干净子进程导包校验）；
   2. `python tool_news_publisher.py` & `python content_publisher.py`（下游发布链路实跑）；
   3. `python tools/verify_code_integrity.py` & `python tests/test_data_quality_gate.py`（双门禁全绿）。
3. **CI 入口顶级自愈护盾**：CI 核心脚本（`main.py`、`content_publisher.py`、`tool_news_publisher.py`、`curator_engine.py`）的 `__main__` 须具备顶层 `try...except BaseException` 护盾，输出完整堆栈并降级自愈。
4. **紧凑序列化守恒**：`latest_news.json` 等核心数据文件保持 `separators=(',', ':')` 紧凑格式，严禁无故切换缩进制造海量无意义 diff。
5. **禁慢扫描海量 JSON**：严禁对 `data/*.json`（50MB+ 归档仓）运行 PowerShell `Select-String` 或无过滤全文扫描；数据查询必须用 `python tools/fast_index.py data <id>` 或轻量 Python 内存哈希查表；代码检索优先 `rg` 并排除 `data/*.json`。
6. **极速索引优先与自动同步**：定位函数、类、信源爬虫或前端逻辑前，**必须优先使用 `python tools/fast_index.py`**（`symbol` / `source` / `search` / `data` / `rules` / `tier`）或查阅 `tools/CODEBASE_INDEX.md`；索引通过 `tools/verify_code_integrity.py` 及 `.git/hooks/pre-commit` 自动同步，严禁过期漂移。

---

## 7. 防御性归因与门禁固锁 (Defensive Accountability)

1. **拒绝甩锅外部信源**：付费墙、图注、署名、非标 URL 属公网常态；任何解析/排版泄漏一律归因为内部解析与卫语句缺失。
2. **缺陷代码化固锁**：每修复一类异常，须同步将防御逻辑固化进爬虫/前端解析器及 `tests/test_data_quality_gate.py` 或 `tools/verify_code_integrity.py`，杜绝回归。

---

## 8. 模型版本泛化与跨语言纯正性 (Evergreen Model Abstraction)

1. **零硬编码易碎微版本号**：工作流、提示词库、指南与通用标签中，非官方专属依赖严禁硬编码易过时微版本号（如 `Claude 3.7/3.5 Sonnet`、`GPT-4o`、`DeepSeek-V3`）。
2. **能力梯队通用映射**：
   - 编程/Agent：`主流编程大模型通用 (Claude / GPT / DeepSeek 系列)` / `Universal LLMs (Claude / GPT / DeepSeek)`
   - 协议/智能体：`Claude 系列 / 支持 MCP 协议的智能体` / `Agents with MCP Protocol Support`
   - 本地/开源推理：`DeepSeek 系列 / 本地开源推理模型` / `Open-Source Reasoning LLMs`
   - 复杂逻辑推导：`主流长思维链 / 复杂推理大模型` / `Frontier Reasoning LLMs`
   - 默认通用：`主流大语言模型通用` / `Universal SOTA LLMs`
3. **英文镜像纯正性**：英文静态页与客户端须采用原生英文能力描述，严禁截断中文导致破损半截括号。

---

## 9. 线上即时交付、纯现金变现与资产防回退 (Deployment, Cash & Asset Guard)

1. **即时推送交付铁律**：凡修改前端、模板、`monetization.js`、配置或外链，本地门禁通过后严禁停留在工作区，必须立即同步推送 `origin main` 触发生产部署，以“生产环境已生效”为完成标准。
2. **纯现金变现与多品类聚合**：仅接入支持直接现金提现（银行卡、Wise ACH、支付宝、PayPal 等）的返佣/广告联盟，**绝对严禁**代金券/积分/站内 Token；优先依托聚合联盟或自动展示网络覆盖多品类，严禁推荐对新站/`.xyz` 域名存在黑盒机器秒拒的平台（如 Impact）。
3. **零 Monetag 与核心静态资产固锁**：全站彻底下线并阻断 Monetag 广告/跳转/弹窗；`content_publisher.py` 与 `tool_news_publisher.py` 严禁输出任何 Monetag 标签；确保版本化核心样式/脚本（如 `/css/style-v735.min.css`、`/js/app-v746.min.js`）完整存在并受 `tests/test_data_quality_gate.py` **断言 22** 强校验。
4. **免锁本地置顶同步 (`tools/safe_sync.py`)**：严禁依赖易死锁的手动 git 拉推命令，统一由 `python tools/safe_sync.py` 执行——自动清除 `.git/*.lock` / `shallow.lock` / `maintenance.lock`，绑定本地代理 `127.0.0.1:7890`；采用 `git pull --rebase -X theirs origin main`（注：`git rebase` 语义下 `-X theirs` 保留本地提交、`-X ours` 才是上游分支），非 rebase 合并兜底再使用 `--no-rebase -X ours`。关键数据同步推送后，须立即以 `git show HEAD:public/data/latest_news.json` 复核目标字段未在冲突中被远端覆盖。
5. **双生产域名现场抓包复核**：涉及前端样式、脚本或关键布局变更部署后，严禁仅凭终端日志宣告完成，必须通过 Python 实测抓取 `https://ainewsradar.xyz` 与 `https://ai-radar-news.web.app`，确认 HTTP 200、核心资产可访问且渲染正常后再交付。

---

## 10. 作用域规则、技能与索引路由表 (Scoped Rules, Skills & Index Map)

| 作用范围 | 文件路径 | 用途与触发场景 |
| :--- | :--- | :--- |
| **信源爬虫作用域规则** | `crawlers/AGENTS.md` | 31 个隔离爬虫契约，含 Forbes / Tech.eu / DeepMind / Bloomberg 固锁守则与审计命令 |
| **前端与静态页作用域规则** | `public/AGENTS.md` | SPA/移动端双轨同构、弹窗三池穿透、正文卫语句、CDN 直连与变现/主题防回退 |
| **极速索引技能** | `.agents/skills/codebase-fast-index/SKILL.md` | `tools/fast_index.py` CLI 检索指南（符号/信源/模糊/数据/规则/层级查询） |
| **联盟展示与主题技能** | `.agents/skills/affiliate-ui-and-theming/SKILL.md` | `monetization.js`、`page_theme.js`、光学混合商品卡与 Light/Dark/Auto 同步规范 |
| **部署与缓存排障技能** | `.agents/skills/firebase-deploy-and-cache/SKILL.md` | Firebase Hosting 429 配额清理、CDN 缓存分层与静态资产失效排查 |
| **自动化符号与文件索引** | `tools/CODEBASE_INDEX.md` + `tools/codebase_index.json` | AST 全量符号、31 信源注册表、数据仓与工具脚本索引（自动增量同步） |
| **架构与数据契约索引** | `docs/CODE_INDEX.md` | 系统数据流图、实体字段契约、跨文件 SSR/CSR 符号依赖矩阵 |
