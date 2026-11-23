---
name: codebase-fast-index
description: Fast codebase and data store indexing for AI News Radar. Use when locating functions, classes, source crawlers, frontend UI modals, or querying items in massive data files without slow scans.
---

# Codebase Fast Index & Retrieval Guide

本技能指导 Agent 在 AI News Radar 仓库中如何使用 `tools/fast_index.py` 实现毫秒级符号定位、信源路由查询及数据直查。

## 常用极速检索指令

### 1. 查找函数或类定义 (Symbol Lookup, <10ms)
```bash
python tools/fast_index.py symbol <symbol_name>
```
- 示例：`python tools/fast_index.py symbol crawl_bloomberg`
- 输出：返回文件路径、精确行号及文档摘要。

### 2. 查找信源爬虫路由与规则 (Source Crawler Registry, <5ms)
```bash
python tools/fast_index.py source <domain_or_name>
```
- 示例：`python tools/fast_index.py source bloomberg` 或 `python tools/fast_index.py source techcrunch`
- 输出：爬虫文件、入口函数、单元测试文件、对应 `AGENTS.md` 规则节及功能特性。

### 3. 全局模糊关键词检索 (Search, <20ms)
```bash
python tools/fast_index.py search <keyword>
```
- 示例：`python tools/fast_index.py search modal` 或 `python tools/fast_index.py search filter`
- 输出：匹配的信源、文件及符号列表。

### 4. 海量数据仓内存直查 (Data Store Lookup, <0.05s)
```bash
python tools/fast_index.py data <id_or_keyword>
```
- 示例：`python tools/fast_index.py data b86591fb2c47a91d`
- 输出：秒级在 `latest_news.json`、`curated_column_highlights.json`、`master_archive.json` 中查找对应项，避免正则扫盘卡死。

### 5. 校验与更新索引
```bash
# 增量同步 (文件更新时自动触发)
python tools/fast_index.py --sync

# 全量重新构建
python tools/fast_index.py build
```
