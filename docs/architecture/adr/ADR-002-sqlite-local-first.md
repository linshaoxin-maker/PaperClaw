# ADR-002: 选择 SQLite 本地优先存储

**Status:** Accepted
**Date:** 2026-03-10
**Deciders:** Project Owner

## 问题

Paper Agent 需要持久化论文元数据、评分、标签等数据。需要选择存储方案。

## 选项

### Option A: PostgreSQL / MySQL

- 优势：成熟、功能完整、支持并发
- 劣势：需要独立数据库进程；CLI 工具场景过重；增加安装复杂度

### Option B: JSON 文件

- 优势：零依赖，最简单
- 劣势：无索引，大数据集检索慢；无事务；全文搜索需自己实现

### Option C: SQLite + FTS5 — ✅ 选中

- 优势：零进程依赖（嵌入式）；内置 FTS5 全文搜索；单文件部署；Python 标准库支持
- 劣势：不支持并发写入；单机限制

## 决策

选择 **Option C: SQLite + FTS5**。

## 理由

1. CLI 工具的用户预期是「装完即用」，不应要求数据库服务
2. FTS5 提供了足够的全文检索能力，满足 `paper_search` 的性能要求（<1s for 10k papers）
3. 单文件数据库便于备份、迁移、调试
4. Python `sqlite3` 模块零额外依赖
5. 论文库规模（千~万级）在 SQLite 性能范围内

## 影响

- `papers.db` 单文件存储在 `~/.paper-agent/`
- FTS5 虚拟表用于搜索索引
- 不支持多进程并发写入（CLI 场景下不需要）
- 大规模场景（10 万+论文）可能需要重新评估
