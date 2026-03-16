# Paper Agent — 领域术语表

**Phase:** Phase 0
**Last Updated:** 2026-03-13

---

## 产品与架构术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **Paper Agent** | 面向 AI 研究员的论文智能助手系统，CLI + MCP Server 架构 | 项目名称 |
| **paper-agent** | CLI 命令行工具，用户直接交互的入口 | `paper-agent collect` / `paper-agent search` |
| **paper-agent-mcp** | MCP Server 进程，通过 stdio 协议为 AI IDE 提供工具调用 | `paper-agent-mcp` 启动命令 |
| **MCP** | Model Context Protocol，AI 客户端与工具服务器之间的标准化协议 | Anthropic 定义，Claude Code / Cursor 支持 |
| **MCP Tool** | MCP 协议中可被 AI 调用的函数，如 `paper_search`、`paper_collect` | 数据层对交互层的能力暴露 |
| **MCP Resource** | MCP 协议中可被 AI 读取的数据端点，如 `paper://digest/today` | 只读数据获取 |
| **MCP Elicitation** | MCP 协议中服务端向客户端请求用户输入的机制（文本、选择、checkbox） | v02 用于多篇论文选择 |
| **交互层** | Claude Code / Cursor 等 AI IDE，负责理解意图、格式化、引导对话 | 用户直接交互的界面 |
| **数据层** | paper-agent-mcp 及其底层服务，负责收集、存储、检索、评分 | MCP 工具背后的能力 |

## 论文工作流术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **Digest** | 系统生成的论文推荐摘要，包含评分最高的论文列表 | 默认 daily intake 入口 |
| **Paper Library** | 本地 SQLite 数据库，存储所有收集的论文元数据 | `~/.paper-agent/papers.db` |
| **Collection** | 从 arXiv 等来源抓取论文元数据并存入本地库的过程 | `paper-agent collect` / `paper_collect` |
| **Relevance Scoring** | 使用 LLM 对论文进行相关性评分（1-10），基于用户 Profile | 高分进入 Digest |
| **Topic Tagging** | LLM 为论文自动生成 topic/tag 分类标签 | 用于 Digest 分组和搜索过滤 |
| **Paper Detail** | 单篇论文的详细信息视图（元数据 + 摘要 + 评分 + 关联） | `paper_show` |
| **Topic Report** | 围绕某主题生成的中等深度结构化报告 | v01 规划，FR-11 |
| **Survey** | 围绕主题生成的文献综述，深度高于 Topic Report | v02 规划，FR-16 |

## 配置术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **Profile** | 研究兴趣画像，包含 topics、keywords、启用的 sources | 决定 Digest 推荐方向 |
| **Source** | 论文来源，如 arXiv 分类 (`cs.AI`)、会议 (`NeurIPS`) | Source Registry 管理 |
| **Source Registry** | 所有可用论文来源的注册表，含名称、分类、启用状态 | `sources.yaml` |
| **Template** | 预定义的研究方向模板，快速配置 Profile | `paper_templates_list` |

## IDE 集成术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **Claude Code** | Anthropic 开发的 AI 编程助手，支持 MCP 集成 | 主要交互界面 |
| **Cursor** | AI 驱动的代码编辑器，支持 MCP 集成 | 辅助交互界面 |
| **Slash Command** | Claude Code 中以 `/` 开头的自定义命令，如 `/start-my-day` | `.claude/commands/` 目录 |
| **Skill** | Cursor 中的 AI 能力增强配置，含指令和参考模板 | `.cursor/skills/` 目录 |
| **Rule** | Cursor 中的 AI 行为规则，触发特定模式时自动激活 | `.cursor/rules/` 目录 |

## 技术术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **FTS5** | SQLite 全文搜索扩展，用于论文库检索 | Search 基础层 |
| **arXiv** | 学术预印本服务器，论文的主要来源 | `arxiv.org` |
| **Semantic Scholar** | 学术搜索引擎，提供论文元数据和引用网络 API | v02+ 联网搜索 |
| **BibTeX** | 学术引用格式，用于 LaTeX 文档 | v02 导出功能 |
| **pipx** | Python 应用独立安装工具，用于全局安装 paper-agent | 安装方式 |
| **Poetry** | Python 依赖管理和打包工具 | 开发环境 |
| **Typer** | Python CLI 框架，用于构建 paper-agent 命令行 | CLI 层 |

## Workspace 术语 (v02)

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **Workspace** | `.paper-agent/` 目录下的一组 markdown 文件，作为研究员和 AI 的共享工作记忆 | v02 核心概念 |
| **Workspace Layer** | 架构层：位于交互层和数据层之间，负责持久化人可读的研究状态 | 三层架构 |
| **Research Journal** | `research-journal.md`，记录研究操作日志（搜索、阅读、分析等），AI 用于恢复上下文 | 最近 50 条，自动归档 |
| **Reading List** | `reading-list.md`，按状态（to-read/reading/read/important）管理论文阅读队列 | 双向同步：MCP 工具 ↔ 手动编辑 |
| **Collection** | `collections/{name}.md`，命名的论文分组，含用途描述和论文列表 | 类似 Zotero Collections |
| **Paper Note** | `notes/{paper-id}.md`，单篇论文的笔记（用户手写 + AI 生成分析） | 每篇论文一个文件 |
| **Citation Trace** | `citation-traces/{topic}.md`，引用链探索记录（forward + backward citations） | 基于 S2 API |
| **Reading Status** | 论文阅读状态：`to_read` → `reading` → `read` → `important` | Paper model 新增字段 |
| **Context Recovery** | AI 在新会话开始时读取 journal + reading-list 恢复上下文 | 跨会话记忆 |
| **Workspace Sync** | Workspace 文件与数据库之间的双向同步操作 | 容错机制 |

## v04-experience 术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **能力可达性 (Discoverability)** | 用户能否通过自然语言意图触达系统已有的工具能力 | v04 核心问题：70% 工具不可见 |
| **Skill 层** | SKILL.md 文件定义的工作流，指导 AI IDE 在各 Phase 调用哪些 MCP 工具 | 位于交互层，是用户触达工具能力的桥梁 |
| **条件分支** | Skill 中根据前置条件（如"论文是否已有 PDF"）决定调用不同工具链的逻辑 | v04 新增，v03 Skill 无此能力 |
| **数据预填充** | 报告模板中的动态字段由工具返回的结构化数据填充，而非 AI 自由推断 | 提升报告质量一致性 |
| **Batch Scoring** | 将逐篇 LLM 评分改为一次 prompt 评多篇，降低延迟和成本 | FilteringManager 优化 |
| **Title 预过滤** | 在 LLM scoring 前用 profile keywords 快速排除明显不相关的论文 | 减少 LLM API 调用量 |
| **Feedback 闭环** | 用户的偏好反馈（paper_feedback）反向影响推荐和评分权重 | v04 建立，v03 只记录不影响 |
| **PaperProfile** | 从论文中提取的结构化元数据：task, method_family, datasets, baselines, metrics 等 | paper_extract 产出，paper_compare_table 消费 |

## 版本术语

| 术语 | 定义 | 上下文 |
|------|------|--------|
| **v01** | 基础版本 + 多源扩展：CLI + MCP + arXiv/DBLP/S2 + 多篇智能 | 已实现 |
| **v02** | Workspace Layer 版本：阅读管理 + 笔记 + 分组 + 引用链 + 跨会话记忆 | 已实现 |
| **v03** | 能力下沉版本：多步 AI 链下沉为单步原子工具 (quick_scan, auto_triage, citation_trace, morning_brief, trend_data) | 已实现 |
| **v04-experience** | 能力上浮 + 体验打磨：Skill 层升级、输出质量提升、性能优化、反馈闭环 | 当前版本 |

---

**更新规则**：新增术语在首次出现的文档中添加此表条目。跨团队有歧义的术语必须收录。
