---
name: codebase-fast-index
description: Fast codebase, scoped-rules, and data store indexing for AI News Radar. Use when locating functions, classes, source crawlers, frontend UI modals, project AGENTS.md rules, or querying items in massive data files without slow scans.
---

# Codebase Fast Index & Retrieval Guide

本技能指导 Agent 在 AI News Radar 仓库中使用 `tools/fast_index.py` 实现毫秒级符号定位、34 信源路由查询、项目规则预算检查及数据仓直查。

## 常用极速检索指令

### 1. 查找函数、类、别名或核心 JS 定义 (Symbol Lookup, <10ms)
```bash
python tools/fast_index.py symbol <symbol_name>
```
- 示例：`python tools/fast_index.py symbol crawl_bloomberg` 或 `python tools/fast_index.py symbol openAiNewsModal`
- 特性：O(1) 精确匹配；未命中时自动降级大小写不敏感匹配并输出模糊候选；支持 Python 函数别名（如 `crawl_anthropic`、`crawl_ign`）与核心前端 JS（`app.js`、`monetization.js`、`page_theme.js`、`page_language.js`、`chinese_converter.js`、`mobile.js`）。

### 2. 查找信源爬虫路由与守则锚点 (Source Registry, <5ms)
```bash
python tools/fast_index.py source <domain_or_name>
```
- 覆盖全部 31 个 `crawlers/*_crawler.py` 隔离爬虫 + YouTube / X (Twitter) / arXiv（共 34 个信源）。
- 输出：爬虫路径、调度入口、验证单测、本地缓存文件状态、对应 `AGENTS.md` / `crawlers/AGENTS.md` 锚点及功能特性。

### 3. 全局模糊关键词检索 (Search, <20ms)
```bash
python tools/fast_index.py search <keyword>
```
- 跨项目规则（`AGENTS.md`）、本地技能（`.agents/skills/`）、信源注册表、文件路径与代码符号统一检索。

### 4. 海量数据仓分级内存直查 (Tiered Data Lookup)
```bash
# 默认优先查热仓（curated_column_highlights / public & data latest_news），精确 ID 命中即停；未命中自动回退归档仓
python tools/fast_index.py data <id_or_keyword>

# 强制全量扫描含 archive_news.json 与 master_archive.json
python tools/fast_index.py data <id_or_keyword> --all
```

### 5. 查看项目作用域规则预算与架构分层
```bash
# 查看所有 AGENTS.md 规则体积（24,000 B 截断红线）与本地技能清单
python tools/fast_index.py rules

# 查看架构分层（crawlers / core / curation / publishing / videos / frontend / tools / pipeline_scripts / quality_gates / data_stores）
python tools/fast_index.py tier [tier_name]
```

### 6. 校验与同步索引
```bash
# 校验规则 24 KB 预算、爬虫注册表完整度与索引时效（CI / 门禁集成）
python tools/fast_index.py --check

# 增量同步（代码、规则或技能变更时自动重建）
python tools/fast_index.py --sync

# 全量重新构建 tools/codebase_index.json 与 tools/CODEBASE_INDEX.md
python tools/fast_index.py build
```

## 相关架构索引与作用域规则
- 全局守则：`AGENTS.md`（目录级补充：`crawlers/AGENTS.md`、`public/AGENTS.md`）
- 自动化符号与信源清单：`tools/CODEBASE_INDEX.md`
- 系统数据流、实体契约与跨文件 SSR/CSR 符号矩阵：`docs/CODE_INDEX.md`
