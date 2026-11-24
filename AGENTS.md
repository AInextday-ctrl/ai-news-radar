# AI News Radar - 核心架构与质量工程守则 (Engineering & Quality Gate Rules)

> 本文件为 Antigravity Agent 在本仓库执行任何代码编写、抓取爬虫开发、数据处理或前端维护时的**最高质量准则**。
> 所有开发、自动化流水线与数据生成必须严格遵循以下硬性原则，避免历史偶发缺陷重复出现。

---

## 1. 信源隔离与真品保真原则 (Source Integrity & Anti-Pollution)

1. **零异源通讯社污染**：
   - 严禁将第三方通讯社（如 Reuters）的电讯稿摘要直接拼接到另一家主流媒体（如 Bloomberg）的正文中。
   - 在跨信源兜底事实提取（`fetch_cross_grounding_facts`）中，必须通过正则彻底切除 `By ... (Reuters) -`、`BEIJING (Reuters) -` 等通讯社外电署名前缀。
2. **零悬空截断与原文实录字句忠实 (Zero Truncation & Verbatim Fidelity)**：
   - 正文段落末尾严禁出现 `such as ...`、`including ...`、`and other ...` 或无止境的省略号 `...`。
   - 任何提取到的段落必须为标点完整的独立事实表述。
   - 对于有明确第一现场报道的主流特稿，核心正文段落必须忠实对齐原作者现场采写报道字句，严禁使用粗糙合成段落替代原厂实录。
3. **真实原厂配图与零无关库存图原则 (Authentic Editorial Imagery & Zero False Stock Images)**：
   - 权威财经/技术报道（如联想 AI 服务器财报、GTA VI 彭博社独家深度）严禁被关键词误判或缺省回退打上无关的库存无人机（drone）或机器人坐长椅（Unsplash `photo-1620712943543`）等具象假图。
   - **缺省兜底中性化**：全站默认配图（`default` fallback）必须且仅能使用站点官方中性品牌卡（`og-default.jpg`）或文字排版卡片（`feed-card-editorial`），绝对严禁使用任何具体事物的库存照片充当通用缺省图。
   - **付费墙与风控信源大图穿透**：对于受 PerimeterX 403、Cloudflare 或登录墙拦截的主流信源（如 Bloomberg、WSJ 等），爬虫必须建立二级电讯联合网络检索机制（Syndication Wire Resolvers，如 Techmeme、Bing News RSS 等），主动穿透检索官方 CDN 高清大图（如 `assets.bwbx.io`），并自动下载托管至本地 CDN（`/images/...`），确保重大深度报道具备真实第一现场配图。
4. **零图片注释与邮件推广杂质泄漏 (Zero Leaked Caption & Newsletter Noise)**：
   - 严禁将源站配图注释（Caption，如 `字节跳动联合创始人张一鸣，公司2021年发布的肖像照。`、`View image in fullscreen ... Photograph: ...`）、摄影机构署名（Credit，如 `Photo by ...`、`新华社发`、`视觉中国供图`）当作文章正文段落提取或排版。
   - 严禁将邮件订阅引导语（如 `Get the most important tech news in your inbox each week.`、`每周在您的收件箱中获取最重要的科技新闻。`）泄漏至正文末尾或任何段落中。
   - 所有正文段落必须通过 `clean_article_paragraphs` 自动过滤图片注释与推广尾巴，确保深度报道原文实录纯正无杂质。
5. **信源 URL/Slug 规范化与穿透检索安全守则 (URL Normalization & Safe Search Invariants)**：
   - 外部信源（如 Bloomberg、Reuters 等）URL 路径中若含有前导/尾随特殊连字符（如 `/-grand-theft-auto...`）、特殊符号或多余斜杠，在提取 slug 时必须强制使用 `re.sub(r'^-+|-+$', '', slug)` 彻底过滤。
   - 严禁将带有前导 `-` 的原始 slug 直接拼入外部搜索引擎（如 Google News RSS 的 `site:bloomberg.com "..."`）作为关键词，避免触发搜索引擎的排除运算符（Negative Operator）导致穿透抓取自锁。
   - 所有搜索引擎 Query 构造函数必须具备符号转义与净化层，保证搜索穿透具备高容错性。
6. **零付费墙试读片段与登录诱导泄漏准则 (Zero Paywall Teasers & Login Noise)**：
   - 严禁将任何受付费墙（Paywall / Teaser Wall）截断的残篇片段（如 Bloomberg Law、WSJ 试读版等）直接入库或渲染到前台落地页。
   - 所有段落提取与清洗必须通过 `is_paywall_or_login_noise` 与 `has_paywall_or_truncation_noise` 严格过滤 `Log in to keep reading...`、`Bloomberg Law provides...`、`Sign in to access...`、`彭博法律提供可信的时事报道...`、`登录以继续阅读`、`订阅以解锁` 等提示语。
   - **本地缓存防投毒强校验**：严禁无条件信任本地磁盘缓存（如 `bloomberg_cache.json`）；在从任何持久化缓存加载历史条目时，必须执行 `has_paywall_or_truncation_noise` 校验，一旦检出试读杂质或截断，必须强制废弃该缓存并穿透重新抓取合法全文字句。
7. **电讯穿透语义相关度校验与泛型头像拦截准则 (Semantic Syndication Relevance & Anti-Avatar Invariants)**：
   - **语义相关度强制双向校验**：在通过二级电讯检索网络（Bing News RSS / open syndication）寻找主流受限信源的全文授权镜像时，必须比对候选电讯文章标题与核心摘要的语义关键词重合度（$\ge 35\%$），严禁仅凭单点关键词匹配便将搜索结果中首个抓取成功的无关第三方文章误收为报道全文。
   - **泛型作者头像与占位符严格阻断**：严禁将任何形如 `bwrite-generic-profile`、`author-profile`、`avatar`、`width=44`、`headshot` 等小尺寸作者头像或泛型占位图作为文章封面配图收录或发布。此类图片必须自动丢弃，触发全网穿透检索 1200×800 现场摄影大图，无法检索时仅能回退官方中性品牌卡（`og-default.jpg`）。

---

## 2. 单页看板（SPA）交互与导航原则 (SPA Navigation & Zero 404)

1. **弹窗优先，保持用户阅读上下文**：
   - 在全站各分类页签（`#news`, `#celebrity`, `#tools`, `#videos`, `#prompts`）中，用户点击卡片必须**优先呼出站内极速 AI 分析弹窗**（`openAiNewsModal` / `openToolDetailModal`）。
   - 严禁在切换页签时将卡片点击强制硬重定向至未静态化的单篇落地页，避免打断用户的滚动位置与翻页进度。
2. **全量历史穿透，消除弹窗查找盲区**：
   - `openAiNewsModal` 与 `openToolDetailModal` 的数据检索池必须同时包含 `cachedData`、`_volumeCache`（所有已加载历史分卷）和 `cachedArchiveData`。
   - 确保用户翻到第 20 页、第 50 页的历史资讯时，点击卡片依然能 0ms 秒开深度研判与 5W1H 事实，杜绝“找不到数据直接跳 404”。
3. **404 智能救赎兜底**：
   - [public/404.html](file:///e:/AI/Antigravity/AI%20News/public/404.html) 必须常驻路径捕获脚本。当外部直链访问了未预生成的静态落地页时，自动将用户平滑重定向至看板对应的 `/#news?open={id}`，确保访客永不碰壁。
4. **严谨语义解耦与防假正文冒充 (Strict Microdata Semantics & Anti-Spoofing)**：
   - **后端 Microdata 语义归位**：静态页面发布器（`tool_news_publisher.py`、`content_publisher.py`）中，Schema.org 属性 `itemprop="articleBody"` 必须且仅能声明在真正的正文容器（`<div class="article-body">`）上，绝对严禁标记在要点摘要、引言或列表（`<ul>`/`<ol>`）元素上。
   - **前端提取类型卫语句**：前端弹窗 DOM 降级提取器（`app.js`）在拉取正文时，必须具备严格的容器类型拦截卫语句：若目标元素为纯列表容器（`UL`、`OL`）或内部缺少段落标签（`<p>`），严禁将其作为正文渲染至“深度报道原文实录”，杜绝要点列表倒挂冒充长文正文。

---

## 3. 静态分卷架构与数据轻量化守则 (Static Volume Chunking & Weight Control)

1. **严格坚持分卷按需加载（On-Demand Chunking）**：
   - 历史内容按分类切片为 96 条/卷（`vol_{N}.json`，体积仅 15-20 KB gzip），翻到哪页加载哪卷，严禁回退为单体 6MB 归档大文件拉取。
   - 首页 Page 1 必须使用 `cachedData.grouped[tab]` 秒级直出（0ms 零网络等待）。
2. **公共数据体积红线守门**：
   - `public/data/latest_news.json` 体积必须**严格控制在 850 KB 以内**（CI 断言 14 硬性阻断）。
   - 公共 JSON 中剔除 `article_content_en` 等与 `paragraphs` 重复的冗余大文本，保持轻量高效传输。
3. **服务端静态编译与前端轻量化彻底解耦原则 (Backend Source-of-Truth)**：
   - **严禁数据源倒挂**：服务端静态单篇页面生成脚本（如 `tool_news_publisher.py`、`content_publisher.py`）必须以完整的后端主库（`data/latest_news.json` 与 `master_archive.json`）为第一数据源；严禁将面向浏览器精简后的 `public/data/latest_news.json` 作为静态构建的主输入源。
   - **双轨健壮兜底渲染**：正文排版逻辑必须实施多层回退机制——优先读取完整长文字符串，若字段为空则**必须无缝降级读取 `paragraphs` / `paragraphs_zh` 数组**自动拼接还原全景正文，严禁因单一字段缺失导致有数据却渲染出正文空白的落地页。
4. **全要素持久化原子同步准则 (Atomic Multi-Container & Field Mirror Sync)**：
   - **多容器一致性**：更新或回填资讯条目时，必须保证全量存储容器（`data/latest_news.json` 中的 `items` 与 `grouped[category]`、`data/master_archive.json`、`data/archive_news.json`、`public/data/latest_news.json`、`public/data/archive/news/vol_{N}.json`）同步更新，严禁出现只改 `items` 却遗漏 `grouped` 导致静态发布器拉取旧数据的现象。
   - **镜像字段同步**：段落数组（`paragraphs` / `paragraphs_zh`）与长文字符串（`article_content` / `article_content_zh` / `original_content`）以及首段（`lead_paragraph`）必须保持原子级同步，杜绝因字段间数据脱节导致的渲染内容不一致。
5. **首页与流水线零割裂同步铁律 (Zero-Disconnection Homepage & Pipeline Sync)**：
   - **静态容器无状态幂等替换原则 (Idempotent SSR Container Replacement)**：服务端静态发布器（`content_publisher.py` 等）在向 HTML 模板注入最新内容流（`stream-news`、`stream-videos`、`stream-prompts`、`stream-tools`、`stream-arxiv` 等）时，**严禁使用单次匹配规则（如只匹配 HTML 注释 `<!--.*?-->`）**。所有流容器替换必须使用基于边界锚点的无状态全内容覆盖正则（`r'(<div [^>]*id="stream-..."[^>]*>)([\s\S]*?)(</div>\s*</div>...)'`），确保无论页面之前残留的是初始模板还是历史卡片，后续流水线每次运行均可 100% 覆盖刷新，绝不发生静默失效与内容冻结。
   - **前后端水合时效强校验 (Strict Timestamp Hydration Sync)**：前端 SPA（`app.js`）在首屏复用静态 SSR DOM 时，**必须强制校验版本时间戳**（`ssrUpdated && data.updated_at && ssrUpdated === data.updated_at`）。严禁仅凭页面已有卡片 DOM 就盲目判定数据新鲜并提前 `return`；一旦远程数据版本更新，前端必须强制执行 `renderUI()` 重新水合渲染，保证前台看板与后台抓取永远保持秒级同频。
   - **视觉布局与数据切片刚性耦合 (Visual Layout & Slice Capacity Coupling)**：栅格定高容器（如 `section-col-news` 与 `section-col-arena` 的 `1280px` 对齐）必须与卡片渲染切片数量严格精算匹配。在底部三列板块（落地工具、实战视频、工作流/提示词）中，**严禁使用固定少量切片导致下半区出现发白空洞**。实战视频必须动态回溯 24~48 小时内的优质内容切片取满 4 张横版视频卡（~1180px），紧凑提示词取满 8 张卡，深度工作流取满 3 张卡，确保三列视觉高度严格等高对齐，消除任何视觉断崖。
6. **24 小时极致时效性静态优先与极限 SEO/GEO 架构准则 (24h Static-First & Advanced SEO/GEO Invariants)**：
   - **快讯首屏时间戳绝对倒序**：服务端静态生成器（`content_publisher.py`）向首页快讯流（`stream-news`）注入内容时，必须优先以完整主库（`data/latest_news.json`）为源，严格按 `raw_published_at` 倒序切片，前台优先固化近 1~6 小时内发布的突发资讯，确保访客与爬虫首屏即见最新进展。
   - **Schema.org 强结构化微数据闭环**：静态渲染的每一条快讯 `<article>` 必须显式声明 `itemscope itemtype="https://schema.org/NewsArticle"`，并内置 `<meta itemprop="headline">`、`<meta itemprop="datePublished">` 与 `<meta itemprop="dateModified">`，最大化触发 Google News **QDF (Query Deserves Freshness)** 算法，并为 AI 搜索引擎（Perplexity、Copilot、ChatGPT Search 等）提供结构化时效证明。
   - **Core Web Vitals 零闪烁与首屏 LCP 极速直出**：
     - 首屏英雄多媒体必须在 `<head>` 中动态注入 `<link rel="preload" as="image" href="..." fetchpriority="high">`；
     - 严禁对视频封面等依赖第三方不可靠反代（如 `wsrv.nl`），必须直接使用源站官方 CDN（如 YouTube `i.ytimg.com`）或自托管 CDN，缺省回退中性卡（`/images/og-default.jpg`），严禁库存假图；
     - 所有媒体容器必须显式声明固定宽高比（如 `aspect-video`、`width="480" height="270"`），彻底将累积布局位移消除至零（`CLS = 0`）。
   - **自动化 IndexNow 实时索引推送到端**：静态页面生成完成后，必须同步向 Bing / Microsoft Copilot 的 IndexNow API 批量推送最新变动的公开 URL，达成全网秒级收录。

---

## 4. 前端图片直连与破损自愈 (Direct CDN & Graceful Fallback)

1. **自托管直连，禁用海外代理抖动**：
   - 站内图片一律通过 Firebase CDN 自身域名（`/images/...`）加载，严禁使用 `wsrv.nl` 等第三方海外反代工具，避免因网络抖动或墙体屏蔽导致缩略图大面积变白框。
2. **图片失败容器彻底隐藏**：
   - 所有 `<img>` 标签的 `onerror` 必须保证在图片加载失败时隐藏整个父容器（`this.closest('a')?.style.display='none'`），严禁留下无内容的发白、空置占位框。

---

## 5. 质量门禁一票否决制 (CI Quality Gate Hard Enforcement)

- 任何功能开发与数据变更必须 100% 通过 `python tests/test_data_quality_gate.py` 的所有断言（目前共 22 项硬性断言），任何断言失败均视为不可发布缺陷，自动化部署将自动拦截并回退。

---

## 6. 防回退与爆炸半径控制准则 (Zero Regression & Blast Radius Control —— 杜绝“改一个错一个”)

1. **运行时环境平权与类型注解安全 (Runtime Parity & PEP 563/649)**：
   - 凡修改或新建 Python 代码，模块头部必须强制声明 `from __future__ import annotations`。
   - 所有在类型标注中使用的类型符号（`Any`, `List`, `Dict`, `Optional`, `Tuple`, `Union`, `Iterable`, `Set` 等）必须 100% 显式从 `typing` 导入。
   - 严禁依赖本地高版本 Python（如 3.14）的延迟求值特性，必须确保代码在 CI 生产基准（Python 3.12）下可无错导入。
2. **底层改动必须做干净子进程与全消费者仿真 (Clean Subprocess Dry-Run)**：
   - 任何对 `crawlers/`、`processor.py`、`article_extractor.py` 等公共基础模块的修改，在提交前必须在本地依次执行三级验证：
     1. `python -c "import <修改的模块>"`：验证全新无状态子进程下的导包安全性；
     2. `python tool_news_publisher.py` & `python content_publisher.py`：完整跑通直接调用该模块的下游静态发布链路；
     3. `python tools/verify_code_integrity.py` & `python tests/test_data_quality_gate.py`：双门禁 100% 通过。
3. **流水线入口顶级自愈防御护盾 (Defensive Entrypoint Shielding)**：
   - 所有在 GitHub Actions CI 中被调用的核心 Python 脚本（`main.py`、`content_publisher.py`、`tool_news_publisher.py`、`curator_engine.py` 等），其 `if __name__ == '__main__':` 必须具备顶层 `try...except BaseException` 护盾，打印详细堆栈并实施自愈降级，严禁因偶发非关键报错以 exit code 1 导致整条 24x7 部署流水线中断。
4. **数据存储序列化防污染与体积守恒 (Serialization Invariants)**：
   - 数据文件（`latest_news.json` 等）必须保持既定的序列化紧凑规范（`separators=(',', ':')`），严禁在修改时随意切换格式导致产生数十万行无意义 diff，污染代码审查与历史记录。
5. **海量数据快速索引与零慢扫描铁律 (Fast Indexing & Zero Slow-Scan Invariants)**：
   - 严禁对 `data/` 目录下的海量归档 JSON 文件（如 `master_archive.json`、`archive_news.json` 等 50MB+ 文件）使用 PowerShell `Select-String` 或未加过滤的命令行全文搜索，杜绝单线程全局正则遍历导致进程长时挂起。
   - 数据定位必须优先编写轻量 Python 脚本，基于 `id` 或 `url` 进行内存哈希键值直查（$O(1)$ 秒级响应）。
   - 代码与文本检索必须优先使用多线程索引工具（如 `ripgrep / rg`），并显式排除 `data/*.json` 归档仓或增加 `--max-filesize 5M` 限制。
6. **代码库极速索引与查询优先铁律 (Codebase Fast Index & Query-First Invariants)**：
   - **检索优先原则**：在定位代码实现、函数定义、类结构、信源爬虫入口或前端交互逻辑前，Agent **必须优先使用 `python tools/fast_index.py` 系列指令**（`symbol <name>`、`source <domain>`、`search <kw>`、`data <id>`）或直接查阅 `tools/CODEBASE_INDEX.md` 获取精确行号与映射关系，严禁盲目发起单线程跨目录通配符大范围文本扫描。
   - **自动同步与时效守卫**：索引由 `tools/fast_index.py` 驱动，任何对代码的增删改必须保留或触发其自动增量同步逻辑（通过 `tools/verify_code_integrity.py` 第 3 阶段或 git pre-commit 勾子校验），确保 `tools/codebase_index.json` 与 `tools/CODEBASE_INDEX.md` 永远保持与真实代码 100% 同步。

---

## 7. 系统自主性与防御性归因准则 (Defensive Accountability Invariants)

1. **客观归因，拒绝甩锅外部信源**：
   - 外部媒体网站的付费墙、配图图注（Caption）、摄影署名、动态脚本或非标 URL 格式，均属于公网不可控信源的**客观常态**。
   - 任何“图注混入正文”、“付费墙穿透失败”或“列表冒充长文”，根源均在于系统自身解析规则不严、防御性卫语句缺失或规范化不足，严禁将内部工程缺陷归因于“信源有问题”。
2. **所有偶发缺陷必须通过门禁代码化固锁**：
   - 每解决一个解析或排版异常，必须将对应的防御逻辑同时写入爬虫模块、前端提取器和 `tests/test_data_quality_gate.py` 硬性断言，杜绝口头修补与历史回退。

---

## 8. 模型版本泛化与时效保鲜准则 (Model Version Abstraction & Evergreen Invariants)

1. **零硬编码易碎微版本号**：
   - 现代前沿大模型以周/月为周期高频迭代。在工作流、提示词库、实战指南或前台标签中，凡非官方专属依赖的通用技术方案，**严禁自行捏造或追加具体的模型微版本号**（如 `Claude 3.7 / 3.5 Sonnet`、`GPT-4o`、`DeepSeek-V3` 等易随时间迅速过时的旧代号）。
2. **能力分级抽象与长期通用体系**：
   - 所有模型适配范围必须统一抽象为通用的**技术栈/能力梯队系列**：
     - 编程/Agent 架构类：`主流编程大模型通用 (Claude / GPT / DeepSeek 系列)` / `Universal LLMs (Claude / GPT / DeepSeek)`；
     - 协议与智能体类：`Claude 系列 / 支持 MCP 协议的智能体` / `Agents with MCP Protocol Support`；
     - 本地与开源推理类：`DeepSeek 系列 / 本地开源推理模型` / `Open-Source Reasoning LLMs`；
     - 复杂逻辑与数学推导：`主流长思维链 / 复杂推理大模型` / `Frontier Reasoning LLMs`；
     - 默认通用：`主流大语言模型通用` / `Universal SOTA LLMs`。
3. **跨语言镜像纯正性保障**：
   - 英文版静态渲染与客户端必须对模型适用范围做原生英文化（如 `Universal LLMs`），严禁将带中文的字符直接裁剪导致产生半截括号（如 `(Claude / GPT / DeepSeek`）的破损排版。

---

## 9. 福布斯信源固锁与高保真抓取守则 (Forbes Source Invariants & Contract Lock)

1. **信源契约完全固锁 (Contract Frozen)**：
   - 福布斯信源解析器（`crawlers/forbes_crawler.py`）契约已正式冻结固锁。
   - 凡涉及 `forbes.com` 的抓取与解析，必须统一经由 `crawl_forbes` 与 `is_forbes_url` 调度。
2. **零聚合前缀与真实记者署名**：
   - 严禁聚合平台前缀（如 `Source: ... (Author/Forbes)`）泄漏至标题，必须使用 `clean_forbes_title` 彻底剥离。
   - 记者署名优先从 `/sites/{author_slug}/` 或电讯网络解析，杜绝将作者笼统标记为 `Forbes`。
3. **真实配图本地化托管与零版权锁盒**：
   - 官方配图（`imageio.forbes.com`）由爬虫自动下载并本地化托管至 `/images/forbes_{slug}.jpg`；缺省回退中性品牌卡（`og-default.jpg`），严禁使用无关库存假图。
   - 落地页必须具备 3 段以上实质报道正文（`paragraphs` / `paragraphs_zh`），严禁出现版权锁盒（`Protected by source publisher copyright or login requirements...`）占位符。

---

## 10. 欧洲科技信源固锁与高保真抓取守则 (Tech.eu Source Invariants & Contract Lock)

1. **信源契约完全固锁 (Contract Frozen)**：
   - 欧洲科技信源解析器（`crawlers/techeu_crawler.py`）契约已正式冻结固锁。
   - 凡涉及 `tech.eu` 的抓取与解析，必须统一经由 `crawl_techeu` 与 `is_techeu_url` 调度。
2. **零聚合后缀与真实记者署名**：
   - 严禁聚合平台后缀（如 `(John Reynolds/Tech.eu)`、` - Tech.eu`）泄漏至标题，必须使用 `clean_techeu_title` 彻底剥离。
   - 记者署名优先从 JSON-LD `NewsArticle`（`author.name`）或标题后缀解析（如 `John Reynolds`、`Tamara Djurickovic`、`Cate Lawrence`），杜绝将作者笼统标记为 `Tech.eu`。
3. **真实配图本地化托管与零评论杂质**：
   - 官方高分辨率配图（`cdn.tech.eu/uploads/`）由爬虫自动下载并本地化托管至 `/images/techeu_{slug}.png` 或 `.jpg`；缺省回退中性品牌卡（`og-default.jpg`），严禁使用无关库存假图。
   - 正文段落提取必须通过 `clean_techeu_paragraphs` 自动过滤 `Would you like to write the first comment?` 评论引导语及邮件订阅杂质，确保正文纯净且落地页具备 3 段以上实质报道正文。

---

## 11. 谷歌 DeepMind Institute 信源固锁与高保真抓取守则 (DeepMind Institute Source Invariants & Contract Lock)

1. **信源契约完全固锁 (Contract Frozen)**：
   - 谷歌 DeepMind Institute 解析器（`crawlers/deepmind_crawler.py`）契约已正式冻结固锁。
   - 凡涉及 `institute.deepmind.com` 及 `deepmind.google` 的特稿与深度前瞻博文，必须统一经由 `crawl_deepmind` 与 `is_deepmind_url` 调度。
2. **零聚合语法泄漏与真实科学家署名**：
   - 严禁聚合平台格式（如 Techmeme 前后缀）泄漏至标题，必须使用 `clean_deepmind_title` 彻底净化。
   - 署名优先从 JSON-LD `Article`（`author.name`、`author.jobTitle`）精准解析作者（如 `Tim Genewein`、`Demis Hassabis`、`Shane Legg` 等）及其官方研究职务（如 `Research Scientist at Google DeepMind`），杜绝笼统标记为 `DeepMind`。
3. **真实配图本地化托管与零版权锁盒**：
   - 官方高分辨率学术/视觉大图（`lh3.googleusercontent.com`）由爬虫自动下载并本地化托管至 `/images/deepmind_{slug}.jpg`；缺省回退中性品牌卡（`og-default.jpg`），严禁使用无关库存假图。
   - 落地页必须具备完整前沿特稿全文（`paragraphs` / `paragraphs_zh`），严禁出现版权锁盒（`Protected by source publisher copyright or login requirements...`）占位符。
4. **站点地图主动发现机制 (Sitemap Proactive Discovery)**：
   - 解析器集成 `crawl_deepmind_sitemap`，支持定期巡检 `https://institute.deepmind.com/sitemap.xml` 索引，实现对超级智能（ASI）、AI 伦理与宏观治理深度论文的秒级自主捕获与入库。

---

## 12. 彭博社信源固锁与高保真电讯穿透守则 (Bloomberg Source Invariants & Contract Lock)

1. **信源契约完全固锁 (Contract Frozen)**：
   - 彭博社信源解析器（`crawlers/bloomberg_crawler.py`）契约已正式冻结固锁。
   - 凡涉及 `bloomberg.com` 的抓取与解析，必须统一经由 `crawl_bloomberg` 与 `is_bloomberg_url` 调度。
2. **多源双向字段契约对齐 (Schema Dual-Track Compatibility)**：
   - 在接收第三方文章提取器（如 `ArticleExtractor`）数据时，严禁假设单一图片字段名，必须双向兼容 `ext.get('cover_image') or ext.get('image_url')`，杜绝合法配图被系统静默抛弃。
3. **电讯穿透质量加权评分与防金融爬虫截断 (Syndication Quality Scoring & Anti-Scraper)**：
   - 二级电讯检索网络（Bing News RSS / open syndication）必须显式屏蔽无图、机翻且截断严重的金融股票评级爬虫（`marketscreener.com`、`zonebourse.com`、`streetinsider.com`、`investing.com`、`finviz.com` 等）。
   - 遍历候选结果时，严禁仅凭首个达到 3 段文字的候选即盲目提前 `return`；必须执行多候选综合质量评分（含高清原图 +100 分、权威电讯伙伴 +30 分、含真实记者署名 +20 分），优先收录图文俱全的权威报道。
   - 官方或授权的高清大图（1200×800 / 1200×628）必须通过 `localize_bloomberg_image` 自动下载并自托管至 `/images/bloomberg_{slug}.jpg`，严禁使用无关库存假图。
4. **零图注与社媒推广杂质泄漏 (Zero Leaked Caption & Social Noise)**：
   - 正文段落必须通过 `_clean_paragraph` 强力正则熔断剥离前置图注（如 `... | Bloomberg`）与社交分享引导语（`SHARE/SAVE X Facebook LinkedIn ...`）。
   - 优先从电讯首段或正文中提取现场撰稿记者真实姓名（如 `Saritha Rai`），杜绝笼统标记为 `Bloomberg News`。
5. **全站头条与数据看板全链路字段透传 (Full-Pipeline Cover Image Transit)**：
   - 服务端精选头条引擎（`curator_engine.py`）在组装 `curated_column_highlights.json` 时，必须显式保留并透传资讯的 `cover_image`、`image_url` 与 `author` 字段，严禁在组装顶层卡片数据时遗漏核心视觉资产，导致前台误回退默认品牌卡。

---

## 13. 线上即时交付与纯现金变现工程守则 (Deployment Cadence & Cash Monetization Invariants)

1. **即时推送部署铁律 (Zero-Local-Stagnation & Immediate Push)**：
   - 凡对前端展示、页面模板、脚本（如 `monetization.js`）、配置或外链所作的任何修改，在本地执行测试门禁后，**严禁停留在本地工作区**。
   - 本地验证通过后，必须立即执行 `git commit` 并 `git push origin main` 触发 CI/CD 自动部署至生产环境（Firebase Hosting CDN）。
   - 严禁“本地改完即宣告完成”；所有面向用户的改动必须以“生产环境已触发部署 / 已上线”为真正完成判定标准。

2. **纯真金白银现金变现准则 (Strict Cash Monetization & Zero-Coupon Invariant)**：
   - 接入任何商业赞助、广告联盟或分销推广时，**必须且仅能选择支持直接现金结算与提现（银行卡、Wise ACH、支付宝、PayPal 等）的正规返佣或广告联盟**。
   - 绝对严禁接入任何形式的「代金券」、「折扣券」、「积分」或「平台内 Token」等非现金返利计划，杜绝用站点的真实商业流量换取无法提现的虚幻额度。

3. **多品类聚合与防机器人拒审准则 (Anti-Bot Rejection & Multi-Product Aggregation)**：
   - 严禁孤立单打独斗推销单一小众产品，优先依托聚合联盟（如 PartnerStack 内部大市场）或全自动展示轮播网（如 Adsterra Native）实现产品矩阵覆盖；
   - 严禁向用户推荐对新站、独立站或 `.xyz` 域名存在黑盒机器秒拒风控的平台（如 Impact 等），避免浪费用户审核时间与信任成本。

---

## 14. 云端定时流水线防回退与免锁极速同步守则 (Continuous Deployment Anti-Regression & Safe Sync Invariants)

1. **构建器底层自愈固锁 (Idempotent Generator Invariant Guard)**：
   - 核心静态页面生成脚本（`content_publisher.py`、`tool_news_publisher.py`）必须具备底层自愈防御卫语句。
   - 无论是本地手动编译还是云端 GitHub Actions 定时机器人自动触发，脚本在向任何 HTML 输出 `<head>` 前，**必须强制校验 Monetag 广告标签（`zone=12339176`）与站长所有权验证元数据（`meta name="monetag"`）**。
   - 若检测到缺失，构建器必须自动强行注入，绝对杜绝因旧模板编译导致关键变现标签被冲刷回滚。

2. **本地改动原子置顶与免锁同步 (Atomic Local-Precedence & Stale Lock Elimination)**：
   - 本地与云端主分支同步严禁依赖容易死锁的手动命令，必须统一由 `python tools/safe_sync.py` 调度执行：
     1. **锁文件彻底免疫**：同步前自动强制清除 `.git/*.lock`、`shallow.lock` 与 `maintenance.lock` 僵尸锁；
     2. **本地代理强绑定**：强制路由至 `127.0.0.1:7890`，杜绝因直连 GitHub 丢包挂起；
     3. **本地改动绝对置顶**：拉取云端提交时必须采用 `git pull --rebase -X ours origin main`，永远以本地人工改动的模板与代码为最高优先级，杜绝被云端机器人的新闻更新代码冲散。

3. **云端定时流水线零冲刷门禁 (Zero-Regression CI Quality Gate Hard Lock)**：
   - `tests/test_data_quality_gate.py` 必须常驻 **断言 22（Monetag 全端常驻门禁）**，覆盖核验 PC 英文、PC 中文、移动端英文、移动端中文等所有核心入口。
   - 任何构建产物若丢失变现标签或验证元数据，CI 必须一票否决并强行中断发布，阻断残次版本流入生产 CDN。

4. **双端时效对齐与现场抓包复核 (Live Endpoint Grounding & Zero Blind Trust)**：
   - 严禁“本地终端打印部署成功即宣布完成”。
   - 所有涉及广告验证、第三方审核（如 Monetag、Google AdSense）或关键栏目布局变更，完成部署后 Agent **必须通过 Python 发起真实生产域名请求（`https://ainewsradar.xyz` 与 `https://ai-radar-news.web.app`）现场抓包**。
   - 必须确认返回 HTTP 200 且 100% 包含目标特征字符串后，方可向用户交付完成。



