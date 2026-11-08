# AI Radar 核心架构与符号依赖索引 (Code Symbol & Architecture Index)

> **版本**：v4.2  
> **更新时间**：2026-11-08  
> **适用范围**：AI News Radar 全栈系统（采集、处理、SSR 预渲染、前端客户端渲染、CI 门禁）  
> **核心原则**：**数据契约优先、双轨渲染同构、零静默伪造、硬性门禁阻断回退**

---

## 一、 系统架构分层与数据流向图

```mermaid
flowchart TD
    subgraph DataProducers [1. 数据采集与抓取层 (Producers)]
        A1[apify_crawler.py - Twitter / X]
        A2[viral_video_engine.py - YouTube / TikTok]
        A3[fetcher.py - RSS / Arxiv / TechMeme / ProductHunt]
    end

    subgraph DataProcessors [2. 聚合处理与质检清洗 (Processors & Sentinels)]
        B1[main.py - 编排聚合与持久化]
        B2[curator_engine.py - 深度研判与价值提炼]
        B3[language_sentinel.py - 语言纯度与翻译质检]
        B4[processor.py - 文本清洗与机翻缝隙识别]
    end

    subgraph DataStorage [3. 分级存储体系 (Data Store)]
        C1[(data/latest_news.json - 24h 高精快讯)]
        C2[(data/master_archive.json - 全量历史账本)]
        C3[(public/data/latest_news.json - 前端轻量静态分发)]
    end

    subgraph DualRendering [4. 双轨渲染引擎 (Dual-Track Rendering)]
        D1[content_publisher.py - 服务端/构建时 SSR 静态预渲染]
        D2[public/js/app.js - 浏览器客户端 CSR 动态交互挂载]
    end

    subgraph QualityGates [5. 质量防护与防回退门禁 (Quality Gates)]
        E1[tools/verify_code_integrity.py - 静态反模式扫描与单元回归]
        E2[tests/test_video_pipeline.py - 视频时效解析单元测试]
        E3[tests/test_data_quality_gate.py - 18 项 CI 生产数据硬性断言]
    end

    DataProducers --> DataProcessors
    DataProcessors --> DataStorage
    DataStorage --> DualRendering
    DualRendering -.-> QualityGates
    DataStorage -.-> QualityGates
```

---

## 二、 核心数据模型契约 (Data Contracts)

严禁在任何模块中绕过字段契约，更严禁在抓取失败或缺失字段时使用“静默伪造默认值”（如 `datetime.now()` 或 `diff_hours: 12.0`）。

### 1. 视频实体契约 (`category: "videos"`)

| 字段名 | 类型 | 严格约束与业务定义 |
| :--- | :--- | :--- |
| `id` | `str` | 视频唯一哈希（如 `yt_dQw4w9WgXcQ` 或 md5） |
| `published` | `str` | YouTube / Web 原始展示时间（如 `14h ago`, `1y ago`, `8 months ago`） |
| `raw_published_at` | `str (ISO 8601)` | **真实 UTC 发布时间**。必须由 `parse_relative_time_info()` 严格解析，**严禁直接赋为当前抓取时间 `now()`** |
| `diff_hours` | `float` | 距当前时间的真实发布间隔小时数。若原始为历史视频，值必须 > 48.0 |
| `is_recent_24h` | `bool` | 只有 `diff_hours <= 24.0` 且原始文本非历史标记时才为 `True`，否则必须为 `False` |
| `is_recent_48h` | `bool` | 只有 `diff_hours <= 48.0` 且原始文本非历史标记时才为 `True`，否则必须为 `False` |
| `surge_badge` | `str` | 时效徽标。**历史视频严禁出现 `🔥 24h飙升`**，必须降级为 `实战精讲` 或 `精选教学` |
| `title_zh` | `str` | 中文自然标题。**历史视频严禁出现 `【48h 极客实测】` 前缀**，必须使用 `【实战精讲】` |
| `url` | `str` | 视频直达播放链接 |
| `author` | `str` | 频道主 / 创作者名称 |

### 2. 快讯实体契约 (`category: "news"`)

- 必须包含：`title_en`, `title_zh`, `summary_en`, `summary_zh`, `fact_bullets_en`, `fact_bullets_zh`
- 约束：`fact_bullets_zh` 必须 ≥ 3 条增量事实，严禁万金油套话（“推动相关应用落地”等）；英文页面与 `_en` 字段零中文字符。

### 3. 大V发言实体契约 (`category: "celebrity"`)

- 必须包含：`full_text_en`, `full_text_zh`, `author`, `author_handle`, `url`
- 约束：长推文多段落无损保真（严禁抹平换行符为单行，中英文段落数对齐）。

---

## 三、 跨文件关键符号与调用索引表 (Symbol Cross-Reference)

当修改某一模块时，必须同步检索并验证所有依赖该符号的上下游代码：

| 核心功能 / 业务域 | 生产/计算端 (Producer) | 服务端静态渲染 (SSR) | 客户端动态渲染 (CSR) | 门禁与测试 (CI Gate) |
| :--- | :--- | :--- | :--- | :--- |
| **视频时间解析与时效判断** | `viral_video_engine.py`:<br>`parse_relative_time_info()` | `content_publisher.py`:<br>`format_lead_video_card()` | `public/js/app.js`:<br>`formatVideoTime()` | `tests/test_video_pipeline.py`<br>`tests/test_data_quality_gate.py` (断言 18) |
| **视频标题与前缀隔离** | `viral_video_engine.py`:<br>`sanitize_video_title_zh()` | `content_publisher.py`:<br>`lead_media_2` 注入 | `public/js/app.js`:<br>`renderVideoCard()` | `tests/test_video_pipeline.py`<br>`tests/test_data_quality_gate.py` (断言 4, 18) |
| **中英文纯度与防拼接** | `language_sentinel.py`:<br>`enforce_language_sentinel()` | `content_publisher.py`:<br>`generate_bilingual_pages()` | `public/js/app.js`:<br>`currentLang` 切换 | `tests/test_data_quality_gate.py` (断言 1, 8) |
| **公共数据轻量化分发** | `main.py`:<br>`save_news()` | `content_publisher.py`:<br>读取 `public/data/latest_news.json` | `public/js/app.js`:<br>`fetchLatestNews()` | `tests/test_data_quality_gate.py` (断言 14) |
| **推文多段落高保真** | `apify_crawler.py`:<br>提取原始格式 | `content_publisher.py`:<br>保留 `\n\n` 段落 | `public/js/app.js`:<br>`renderTweetModal()` | `tests/test_data_quality_gate.py` (断言 10, 11) |

---

## 四、 双轨渲染同构守则 (SSR vs CSR)

本项目采用 **SSR 静态化预渲染**（供 SEO 与首屏极速加载）与 **CSR 客户端水合渲染**（供筛选、搜索、页签切换）并行的双轨架构。

> [!WARNING]
> **双轨割裂是引发“奇怪问题”与“修复回退”的最大元凶**！
> 过去多次出现“Python 脚本里修复了时间逻辑，但用户在网页上点击过滤或水合后，`app.js` 仍然跑着旧的假时间算法”，或者“修改了前端 JS 但未重新运行静态发布器，首屏 HTML 依旧是旧假标签”。

### 强制同构规范：
1. **渲染规则对齐**：凡是修改了 `content_publisher.py` 中的卡片生成逻辑，必须在 `public/js/app.js`（以及 `public/zh/js/app.js`）中同步对齐，反之亦然。
2. **禁止静默兜底**：任何一端在无法获取真实时钟差时，统一标为“历史精选/实战”，绝不捏造当前时分。
3. **发布必重编译**：任何数据逻辑变更后，必须执行静态重构并运行质量门禁：
   ```bash
   python content_publisher.py
   python tests/test_data_quality_gate.py
   ```

---

## 五、 代码修改与防回退工程操作规范 (Engineering Change Protocol)

为彻底杜绝“每次修改都会出现奇怪问题”和“修正的问题再次出现”，所有涉及代码修订的操作必须严格执行以下四步：

### 第 1 步：符号影响域检索 (Scope Check)
在修改任何函数或字段前，先在此文档（`docs/CODE_INDEX.md`）检索符号依赖矩阵，明确涉及的所有上游数据产生源和下游渲染消费端。

### 第 2 步：隔离原子修改 (Isolated Atomic Edits)
- 严禁模糊替换或跨文件盲目搜索替换；
- 只针对目标函数与契约字段做精准修改；
- 保留所有非目标代码的注释与原有逻辑。

### 第 3 步：运行全套防回退自动化测试 (Pre-Push Verification)
在提交代码前，必须在本地依次运行：
```powershell
# 1. 静态反模式检查与管线单元测试（毫秒级）
python tools/verify_code_integrity.py

# 2. 生产级 18 项 CI 质量硬门禁
python tests/test_data_quality_gate.py
```
只有当两项命令均输出 `[SUCCESS]` 时，才允许提交 Git。

### 第 4 步：原子化版本提交 (Atomic Commit)
将功能修正与其对应的回归测试用例一同提交，并在 Commit Message 中清晰标明修改动机与影响范围，杜绝无测试保护的裸奔提交。
