# ADR-003: 交互层与数据层的职责分工

**Status:** Accepted
**Date:** 2026-03-13
**Deciders:** Project Owner

## 问题

Paper Agent 通过 MCP 与 AI IDE 集成后，需要明确哪些能力由 paper-agent 实现，哪些由 Claude Code/Cursor（交互层）承担。

## 选项

### Option A: paper-agent 全栈化

- paper-agent 负责搜索意图分析、关键词扩展、中文翻译、笔记生成等
- 优势：自包含
- 劣势：重复 AI IDE 已有能力；增加 paper-agent 复杂度和 LLM 成本

### Option B: paper-agent 纯数据 + AI IDE 纯交互 — ✅ 选中

- paper-agent 只管数据层（收集、存储、检索、评分、Profile）
- AI IDE 管交互层（理解意图、确认、格式化、分析、合成、写文件、引导下一步）
- 优势：各自发挥优势；paper-agent 保持轻量
- 劣势：依赖 AI IDE 的能力质量

### Option C: 混合模式

- paper-agent 内置部分智能（如关键词扩展），AI IDE 补充其余
- 优势：灵活
- 劣势：职责边界模糊，维护成本高

## 决策

选择 **Option B: 数据层 + 交互层分离**。

## 理由

1. AI IDE（Claude Code）本身就是强大的 LLM，搜索意图分析、翻译、笔记生成都是其核心能力
2. paper-agent 专注数据管理可以保持代码简洁、低 LLM 成本
3. MCP 协议天然支持这种分工：Tool 返回 JSON，AI IDE 负责呈现和交互
4. 避免在 paper-agent 中重复实现 AI IDE 已有的能力

## 影响

- paper-agent MCP Tools 只返回 JSON 数据，不做格式化
- 搜索意图分析、关键词扩展等不在 paper-agent 范围内
- Claude Code commands (slash commands) 和 skills 承担交互编排
- 每个环节的交互设计（追问、确认、引导下一步）由 AI IDE 侧的 commands/skills 定义
- 文档 `docs/paper-agent-overview.md` 记录了完整的 10 环节交互设计
