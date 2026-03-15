# ADR-001: 选择 MCP 作为 IDE 集成协议

**Status:** Accepted
**Date:** 2026-03-12
**Deciders:** Project Owner

## 问题

Paper Agent 需要与 AI IDE（Claude Code、Cursor）集成，让 AI 助手能调用论文智能工具。需要选择集成方式。

## 选项

### Option A: REST API Server

- Paper Agent 启动 HTTP 服务，IDE 通过 HTTP 调用
- 优势：标准协议，任何客户端可用
- 劣势：需要端口管理、进程守护、跨域处理；CLI 工具启动 HTTP 服务器增加复杂度

### Option B: CLI JSON 调用

- IDE 直接 `exec` paper-agent CLI 命令，解析 JSON 输出
- 优势：零额外架构，直接复用 CLI
- 劣势：每次调用启动新进程，冷启动慢；无状态保持；IDE 需要自己解析 JSON

### Option C: MCP (Model Context Protocol) — ✅ 选中

- Paper Agent 实现 MCP Server，IDE 通过 stdio JSON-RPC 通信
- 优势：Anthropic/Cursor 原生支持；类型化工具定义；支持 Resources 和 Elicitation；一次连接持续通信
- 劣势：协议较新，生态仍在发展

## 决策

选择 **Option C: MCP**。

## 理由

1. Claude Code 和 Cursor 都原生支持 MCP，零额外集成代码
2. MCP 的 Tool/Resource 模型天然适合论文智能工具的 API 形态
3. stdio 传输避免了 HTTP 服务器的端口和进程管理问题
4. MCP Elicitation 为 v02 的 checkbox 多选 UI 提供了原生支持
5. 社区趋势：MCP 正在成为 AI 工具集成的事实标准

## 影响

- 新增 `paper_agent/mcp/` 模块（server.py, tools.py, resources.py）
- CLI 和 MCP 共享核心服务层，MCP 是另一个入口而非替代
- `paper-agent setup` 命令负责为各 IDE 配置 MCP 连接
- 后续新增能力优先暴露为 MCP Tool
