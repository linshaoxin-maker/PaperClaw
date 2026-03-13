# Paper Agent Plugin

这个目录包含 paper-agent 的 **IDE 插件分发物料**，用于通过 marketplace 分发给其他用户。

> **普通用户不需要手动操作这个目录。** 请使用 `paper-agent setup` 命令一键配置。

## 快速开始（推荐方式）

```bash
# Cursor 用户
paper-agent setup cursor

# Claude Code 用户
paper-agent setup claude-code
```

详见 [README - IDE Integration](../README.md#ide-integration)。

## 目录结构

```
plugin/
├── README.md                        ← 你在这里
├── install.sh                       ← 全局安装脚本（旧版，建议用 setup 命令代替）
└── claude-code/                     ← Claude Code plugin 物料
    ├── .claude-plugin/
    │   └── plugin.json              ← 插件清单
    ├── .mcp.json                    ← MCP 服务器配置模板
    ├── commands/                    ← Slash 命令定义
    │   ├── start-my-day.md
    │   ├── paper-search.md
    │   ├── paper-analyze.md
    │   └── paper-collect.md
    └── skills/
        └── paper-intelligence/
            ├── SKILL.md
            └── references/
                └── analysis-template.md
```

## 这个目录 vs `paper-agent setup`

| | `paper-agent setup` | `plugin/` 目录 |
|---|---|---|
| **用途** | 终端用户一键配置 IDE | 开发者维护插件分发物料 |
| **方式** | 自动写入配置文件 | 手动或通过 marketplace 安装 |
| **推荐** | ✅ 推荐所有用户使用 | 仅 marketplace 发布需要 |

## Claude Code Marketplace 发布

如需通过 marketplace 分发，可将此 repo 作为 marketplace 源：

```bash
# 其他用户在 Claude Code 中运行：
/plugin marketplace add linshaoxin-maker/paper_agent
/plugin install paper-agent@linshaoxin-maker-paper_agent
```

## Cursor Marketplace 发布

Cursor 插件需要 `.cursor-plugin/plugin.json` 格式，可在 [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish) 提交。
