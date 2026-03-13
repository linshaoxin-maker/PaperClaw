# Paper Agent 用户旅程与错误恢复

**Version:** v01
**Status:** Draft
**Last Updated:** 2026-03-12

## 文档说明

本文档描述 Paper Agent 的完整用户旅程，包括：
- 正常使用路径（Happy Path）
- 常见错误场景与恢复策略
- 不同用户角色的典型工作流

## 目标用户角色

### 角色 1：Individual AI Researcher
- **目标**：持续跟踪研究方向，快速获取高价值论文
- **使用频率**：每日查看 digest，按需搜索
- **技术水平**：熟悉命令行，了解基本配置

### 角色 2：Research Engineer
- **目标**：在实现、复现、benchmark 阶段快速获取论文上下文
- **使用频率**：按需搜索，频繁查看 paper detail
- **技术水平**：熟练使用 CLI 和自动化工具

### 角色 3：PhD Student / Early Researcher
- **目标**：建立 topic understanding，维护本地知识积累
- **使用频率**：每日 digest + 定期 topic exploration
- **技术水平**：基本命令行能力

### 角色 4：Automation Agent
- **目标**：程序化获取研究上下文，支持编码和规划任务
- **使用频率**：按需调用，要求稳定 JSON 输出
- **技术水平**：通过 CLI + JSON 接口集成

---

## 命令与输出件速查（v01）

本节集中说明 Paper Agent 当前版本（v01）已实现的命令、常用参数与主要输出件，便于科研工作流脚本化/自动化。

### `--config` 参数（配置文件路径）

当前版本中，`--config` **需要写在子命令后**（或用于进入 REPL 时指定配置）。

- 进入 REPL 并指定配置：
  - `paper-agent --config ~/.paper-agent-test/config.yaml`
- 子命令指定配置：
  - `paper-agent digest --config ~/.paper-agent-test/config.yaml`

### 主要命令与参数（按真实实现）

#### 1) `paper-agent init`

初始化/覆盖“基础设施配置”（LLM provider / API key / model 等）。

- `--provider <anthropic|openai>`：LLM Provider
- `--api-key <key>`：API Key（也可用环境变量 `PAPER_AGENT_LLM_API_KEY` 提供）
- `--base-url <url>`：自定义 Base URL
- `--model <name>`：模型名（留空使用 provider 默认）
- `--config <path>`：配置文件路径

> 说明：当前版本 `init` 不再配置 topics/keywords/sources；这些由 `paper-agent profile create` 负责。

#### 2) `paper-agent profile create`

创建/更新科研兴趣 profile（topics/keywords），并可按模板推荐并启用 sources。

- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

交互入口：
- `template`：从内置 research area 模板选择（模板来自内置 `sources.yaml`）
- `manual`：手动输入 `topics/keywords`

#### 3) `paper-agent sources ...`

管理论文来源（sources）。

- `paper-agent sources list [--json] [--config <path>]`
- `paper-agent sources show <source_id> [--json] [--config <path>]`
- `paper-agent sources enable <source_id>... [--config <path>]`
- `paper-agent sources disable <source_id>... [--config <path>]`
- `paper-agent sources config [--print] [--json] [--config <path>]`

#### 4) `paper-agent collect`

从已启用的 sources 收集论文，并可选用 LLM 打分过滤。

- `-d, --days <int>`：回溯最近 N 天（默认 7）
- `-m, --max <int>`：每个分类最多抓取 N 篇（默认 200）
- `--filter / --no-filter`：是否执行 LLM 过滤（默认 `--filter`）
- `--debug`：显示更详细抓取日志（排查网络/0 篇问题；会打印 `[collect:debug] ...`）
- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

#### 5) `paper-agent digest`

生成/查看某天的 digest。

- `--date YYYY-MM-DD`：指定日期（不传则为当天）
- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

#### 6) `paper-agent search "<query>"`

在本地库中检索论文。

- `-n, --limit <int>`：返回条数（默认 20）
- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

#### 7) `paper-agent show <paper_id>`

查看论文详情。

- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

#### 8) `paper-agent stats`

查看本地库统计。

- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

#### 9) `paper-agent config`

查看当前配置。

- `--show-secrets`：显示完整 API key（默认遮罩）
- `--json`：JSON 输出（成功时）
- `--config <path>`：配置文件路径

### JSON 输出与错误处理说明

- `--json` 目前只覆盖“成功输出”。发生错误时，会打印形如 `Error: <message>` 的文本到 stderr；并不会返回结构化 JSON 错误对象。
- `init` 当前不支持 `--json`。

### 交互模式（REPL）说明

直接运行 `paper-agent`（不带子命令）会进入交互模式：

- 优势：无需重复输入 `paper-agent` 前缀；支持 `show 1` 按上一轮结果序号查看。
- `search` 有别名 `s`；未知命令会被当作搜索关键词处理。
- 注意：交互模式的 `collect` 当前仅支持 `-d/-m/--no-filter`，不支持 `--debug/--json`。

### 输出件（Artifacts）与落盘位置

科研用户通常需要“可复现/可追溯”的输出件，v01 主要包括：

1. **本地论文库（SQLite）**
   - 默认路径：`~/.paper-agent/library.db`
   - 用途：本地检索/统计/digest 生成。

2. **Digest Markdown 文件**
   - 默认路径：`~/.paper-agent/artifacts/digests/digest-YYYY-MM-DD.md`
   - 用途：便于沉淀到 Obsidian/Notion/个人知识库，或作为周报素材。

3. **Sources 覆盖文件（可选）**
   - 路径：`~/.paper-agent/sources.yaml`
   - 用途：覆盖 sources 的 enabled 状态/配置；可用 `paper-agent sources config --print` 查看。

4. **JSON 输出（适合脚本/Agent）**
   - `collect/digest/search/show/stats/config/profile create/sources list/sources show/sources config` 支持 `--json`

---

## 核心用户旅程

### Journey 1: 首次使用 - 从安装到第一份 Digest

**目标**：用户完成安装、初始化，并成功获得第一份有价值的 digest

#### 步骤流程

```
安装 → 初始化（基础设施） → 创建 Profile → 首次收集 → 查看 Digest
```

#### 详细步骤

**Step 1.1: 安装系统**

```bash
# 克隆仓库
git clone <repo-url>
cd paper_agent

# 一键安装（推荐）
./install.sh
```

**预期结果**：
- `paper-agent` 命令全局可用
- Python 3.10+ 环境检查通过
- pipx 安装完成

**Step 1.2: 初始化配置（基础设施）**

```bash
paper-agent init
```

**交互流程**：
1. 选择 LLM Provider（`anthropic` 或 `openai`）
2. 输入 API Key（可选：使用环境变量 `PAPER_AGENT_LLM_API_KEY`）
3. 可选：自定义 Base URL 和 Model

**预期结果**：
- 配置保存到 `~/.paper-agent/config.yaml`
- 本地数据库初始化完成（默认：`~/.paper-agent/library.db`）
- 提示：下一步运行 `paper-agent profile create` 完成研究兴趣与 sources 配置

**Step 1.3: 创建研究 Profile（研究兴趣与 sources）**

```bash
paper-agent profile create
```

**交互流程**：
1. 选择入口：`template`（推荐）或 `manual`
2. 生成/编辑 topics 与 keywords
3. 选择启用的 sources（可留空，仅保存 topics/keywords；sources 可后续用 `paper-agent sources enable/disable` 调整）

**预期结果**：
- `topics/keywords/sources` 写入 `~/.paper-agent/config.yaml`
- profile 标记为完成（`profile_completed: true`）
- 提示：`运行 paper-agent collect 开始收集论文`

**Step 1.4: 首次收集论文**

```bash
paper-agent collect -d 7
```

**系统行为**：
1. 从已启用的 sources 收集最近 7 天的论文（v01 默认包含 arXiv 类 sources）
2. 自动执行 LLM 过滤和评分（可用 `--no-filter` 关闭）
3. 显示收集统计：总数、新增、重复

**预期结果**：
- 收集统计输出类似：`收集完成: N 篇论文 (X 新增, Y 重复)`
- 若新增论文且启用过滤：提示 `过滤完成: M 篇论文已评分`
- 若收集到 0 篇：提示使用 `paper-agent collect --debug` 查看抓取日志

**Step 1.5: 查看首份 Digest**

```bash
paper-agent digest
```

**预期结果**：
- 显示当日 digest
- **High Confidence** 区：5-20 篇高相关论文
- **Supplemental** 区：补充候选论文
- 每篇论文显示：标题、作者、发布日期、相关性评分、推荐理由

**成功标准**：
- 用户认为 High Confidence 区的论文确实与研究方向相关
- 用户理解如何进入下一步（查看详情、搜索、调整配置）

---

### Journey 2: 日常使用 - 每日论文监控

**目标**：用户建立稳定的每日论文 intake 习惯

#### 典型工作流

```
每日收集 → 查看 Digest → 深入感兴趣论文 → 搜索相关主题
```

#### 详细步骤

**Step 2.1: 每日收集（可自动化）**

```bash
# 手动执行
paper-agent collect -d 1

# 或配置 cron job（注意替换 paper-agent 的实际安装路径）
0 8 * * * /usr/local/bin/paper-agent collect -d 1
```

**Step 2.2: 查看 Digest**

```bash
paper-agent digest
```

**用户决策点**：
- 高置信论文中有感兴趣的 → 进入 Step 2.3
- 想了解某个主题 → 进入 Step 2.4
- 今日无感兴趣内容 → 结束，明日再看

**Step 2.3: 查看论文详情**

```bash
paper-agent show <paper-id>
```

**显示内容**：
- 完整标题和作者
- 摘要
- arXiv ID 和链接
- 发布日期
- 相关性评分和推荐理由
- Topic 标签
- PDF 链接

**用户后续动作**：
- 打开 PDF 阅读
- 复制引用信息
- 搜索相关论文

**Step 2.4: 搜索相关主题**

```bash
paper-agent search "transformer architecture"
```

**预期结果**：
- 返回本地库中匹配的论文列表
- 当前版本默认按文本匹配的 FTS rank 排序（更接近“搜索相关性”，不等同于 relevance_score 排序）
- 可进一步查看详情

---

### Journey 3: 深度研究 - Topic 探索与整理

**目标**：围绕特定主题进行系统性文献梳理

#### 步骤流程

```
确定研究主题 → 搜索相关论文 → 查看统计 → 导出整理
```

#### 详细步骤

**Step 3.1: 主题搜索**

```bash
paper-agent search "retrieval augmented generation" -n 50
```

**Step 3.2: 查看库统计**

```bash
paper-agent stats
```

**显示内容**：
- 总论文数
- 高/低置信度分布
- 未评分论文数
- Top 10 热门 topics

**用户洞察**：
- 了解本地库的覆盖范围
- 发现新的研究方向
- 评估是否需要扩大收集范围

**Step 3.3: 批量查看与整理**

```bash
# JSON 输出便于脚本处理
paper-agent search "RAG" --json > rag_papers.json

# 查看配置确认覆盖范围
paper-agent config
```

---

### Journey 4: IDE 集成 — 在 Cursor / Claude Code 中使用

**目标**：在日常编码环境中直接使用论文智能功能，无需切换到终端

#### 前置条件

Journey 1 已完成（init + profile + 首次 collect），且 `paper-agent-mcp` 可用。

#### 步骤流程

```
完成 CLI 初始化 → 运行 setup 命令 → 重启 IDE → 日常使用
```

#### 详细步骤

**Step 4.1: 选择你的 IDE 并运行 setup**

```bash
# 在你的研究项目目录中运行（不是 paper-agent 源码目录）
cd ~/my-research-project

# Cursor 用户
paper-agent setup cursor

# Claude Code 用户
paper-agent setup claude-code
```

**系统行为（Cursor）**：
1. 自动检测 `paper-agent-mcp` 的路径
2. 写入 `.cursor/mcp.json` — MCP 服务器配置
3. 写入 `.cursor/skills/paper-agent/SKILL.md` — Agent 技能定义
4. 写入 `.cursor/rules/paper-agent.mdc` — 自动触发规则

**系统行为（Claude Code）**：
1. 自动检测 `paper-agent-mcp` 的路径
2. 写入 `.mcp.json` — MCP 服务器配置
3. 写入 `.claude/commands/` — 8 个 slash 命令
4. 写入 `CLAUDE.md` — 项目上下文指令

**Step 4.2: 重启 IDE**

- Cursor: Cmd+Shift+P → "Reload Window" 或完全重启
- Claude Code: 重新运行 `claude`

**Step 4.3: 验证集成生效**

| 操作 | Cursor | Claude Code |
|------|--------|-------------|
| 每日推荐 | 在 chat 中说 "start my day" | 输入 `/start-my-day` |
| 搜索论文 | 说 "搜索论文 transformer" | 说 "搜索论文 transformer" |
| 分析论文 | 说 "分析论文 2301.12345" | 输入 `/paper-analyze 2301.12345` |
| 收集论文 | 说 "收集最近 3 天的论文" | 输入 `/paper-collect 3` |
| 配置方向 | 说 "配置研究方向" | 输入 `/paper-setup` |
| 多篇对比 | 说 "对比这几篇论文" | 输入 `/paper-compare` |
| 文献综述 | 说 "写个 survey" | 输入 `/paper-survey <topic>` |
| 下载 PDF | 说 "下载这篇论文" | 输入 `/paper-download <id>` |

**预期结果**：
- Agent 自动调用 paper-agent MCP 工具
- 返回中文论文分析和推荐
- 无需手动切换到终端

#### Scope 选择

| Scope | 命令 | 效果 |
|-------|------|------|
| **project**（默认） | `paper-agent setup cursor` | 仅当前项目可用，配置随项目走 |
| **global** | `paper-agent setup cursor --scope global` | 所有项目可用，配置在 `~/.cursor/` |

建议：先用 project scope 在一个项目里试用，确认没问题再全局安装。

---

### Journey 5: Agent 自动化 — JSON 输出与脚本集成

**目标**：将 Paper Agent 集成到自动化脚本和 CI 工作流中

#### 集成场景

**场景 A：编码时查找相关论文**

```bash
paper-agent search "attention mechanism implementation" --json
```

**场景 B：获取每日推荐用于规划**

```bash
paper-agent digest --json
```

**场景 C：查看特定论文详情**

```bash
paper-agent show arxiv:2301.12345 --json
```

**关键特性**：
- 关键命令支持 `--json`（如 `collect/digest/search/show/stats/config/profile create/sources list` 等）
- 输出结构尽量稳定，便于解析
- 注意：出错时当前仍以 stderr 文本输出为主（形如 `Error: ...`），不会返回结构化 JSON 错误对象

---

## 错误场景与恢复策略

### 错误类型 1: 初始化失败

#### 场景 1.1: 未安装 Python 3.10+

**错误表现**（示例）：
```
Error: Python 3.10+ required
```

**恢复步骤**：
1. 安装或升级 Python：`brew install python@3.10`（macOS）
2. 重新运行 `./install.sh`

#### 场景 1.2: 未完成 Profile（缺少 topics/sources）

**错误表现**（示例，实际 message 以 `Error: ...` 形式显示）：
- `Error: 缺少 topics（研究方向）`
- `Error: 缺少 sources（论文来源）`

**恢复步骤**：
1. 运行 `paper-agent profile create` 完成研究兴趣与 sources 配置
2. 再次执行 `paper-agent collect`

#### 场景 1.3: 配置文件损坏 / YAML 解析失败

**错误表现**：
- 通常表现为 `Error: <yaml parser error ...>`（由 YAML 解析器返回具体信息）

**恢复步骤**：
1. 备份现有配置：`cp ~/.paper-agent/config.yaml ~/.paper-agent/config.yaml.bak`
2. 重新初始化：`paper-agent init`
3. 重新创建 profile：`paper-agent profile create`

---

### 错误类型 2: 收集失败

#### 场景 2.1: 网络连接失败 / arXiv 请求异常

**错误表现**：
- 通常表现为 `Error: <network error ...>` 或收集结果为 0 篇（具体错误信息由底层 HTTP/YAML 库返回）。

**恢复步骤**：
1. 检查网络连接
2. 检查是否需要代理配置
3. 使用 debug 模式查看请求细节：`paper-agent collect --debug`
4. 稍后重试：`paper-agent collect -d 7`

#### 场景 2.2: arXiv 限流/返回非 200（可能导致 0 篇）

**错误表现**：
- 可能不会显示明确的“Rate limit exceeded”错误文本，而是表现为收集到 0 篇，或在 `--debug` 日志里看到非 200 状态码。

**恢复步骤**：
1. 稍后重试
2. 减少单次收集数量：`paper-agent collect -d 3 -m 100`
3. 分批收集不同分类/来源

#### 场景 2.3: LLM 调用失败（过滤阶段）

**错误表现**：
- 通常表现为 `Error: <provider error ...>`（由 LLM SDK 返回具体信息）。

**恢复步骤**：
1. 检查 API key / 余额 / 限流状态
2. 先收集不过滤：`paper-agent collect --no-filter`
3. 修复后重新执行带过滤的收集

#### 场景 2.4: 收集到 0 篇论文

**错误表现**：
```
收集完成: 0 篇论文 (0 新增, 0 重复)
提示: 未获取到任何论文。可使用 paper-agent collect --debug 查看完整抓取日志。
```

**可能原因**：
- 时间范围内该分类无新论文
- sources 未启用/配置不完整（例如未运行 `paper-agent profile create`，或 sources 被 disable）
- 网络问题导致部分请求失败

**恢复步骤**：
1. 使用 debug 模式查看详情：`paper-agent collect --debug`
2. 扩大时间范围：`paper-agent collect -d 14`
3. 检查当前 sources 是否为空：`paper-agent config`；必要时运行 `paper-agent sources list` 查看启用状态
4. 调整 sources：运行 `paper-agent profile create`（重新选择/启用 sources），或使用 `paper-agent sources enable/disable`

---

### 错误类型 3: Digest 生成失败

#### 场景 3.1: 本地库为空

**错误表现**：
```
Error: 当前本地论文库为空。请先执行 paper-agent collect。
```

**恢复步骤**：
1. 执行收集：`paper-agent collect -d 7`
2. 再次生成 digest：`paper-agent digest`

#### 场景 3.2: 所有论文都是低相关性

**错误表现**：
```
Digest — 2026-03-12
Library: 150 | Filtered: 150
今日高置信结果较少，已提供补充候选供参考。
```

**可能原因**：
- 研究方向配置与收集的论文不匹配
- 关键词过于严格

**恢复步骤**：
1. 检查配置：`paper-agent config`
2. 调整研究方向和关键词：`paper-agent profile create`
3. 调整 sources（增加覆盖范围或切换模板）：`paper-agent sources enable/disable` 或重新运行 `paper-agent profile create`
4. 重新收集：`paper-agent collect -d 7`

#### 场景 3.3: 指定日期的 digest 结果为空 / 候选较少

**错误表现**：
- 不一定报错；可能显示 `今日无候选论文。` 或仅有 Supplemental。

**恢复步骤**：
1. 不指定日期生成当日 digest：`paper-agent digest`
2. 扩大收集范围并重新收集：`paper-agent collect -d 14`
3. 调整 profile（topics/keywords）与 sources：`paper-agent profile create` / `paper-agent sources enable/disable`

---

### 错误类型 4: 搜索失败

#### 场景 4.1: 本地库为空

**错误表现**：
```
Error: 当前本地论文库为空。请先执行 paper-agent collect。
```

**恢复步骤**：
1. 执行收集：`paper-agent collect -d 7`
2. 再次搜索

#### 场景 4.2: 无匹配结果

**错误表现**：
```
未找到匹配论文。
```

**可能原因**：
- 搜索词过于具体
- 本地库覆盖范围不足

**恢复步骤**：
1. 使用更通用的搜索词
2. 检查库统计：`paper-agent stats`
3. 扩大收集范围：调整配置并重新收集

---

### 错误类型 5: 论文详情查看失败

#### 场景 5.1: 论文 ID 不存在

**错误表现**：
```
Error: 未找到论文: arxiv:9999.99999
```

**恢复步骤**：
1. 检查 ID 格式是否正确
2. 搜索论文标题：`paper-agent search "paper title"`
3. 从搜索结果中获取正确的 ID

#### 场景 5.2: 论文数据不完整

**错误表现**：
- 显示论文但缺少某些字段（如摘要、评分）

**可能原因**：
- 收集时数据不完整
- 过滤未完成

**恢复步骤**：
1. 重新收集该论文：`paper-agent collect -d 30`（扩大范围）
2. 如果是评分缺失，重新执行带过滤的收集

---

### 错误类型 6: 配置问题

#### 场景 6.1: 配置文件权限错误

**错误表现**：
```
Error: Permission denied: ~/.paper-agent/config.yaml
```

**恢复步骤**：
1. 修复权限：`chmod 600 ~/.paper-agent/config.yaml`
2. 检查目录权限：`chmod 700 ~/.paper-agent`

#### 场景 6.2: 数据库文件损坏

**错误表现**（示例）：
- `Error: <sqlite error ...>`（SQLite 异常文本；具体内容依实际损坏情况而定）

**恢复步骤**：
1. 备份数据库：`cp ~/.paper-agent/library.db ~/.paper-agent/library.db.bak`
2. 尝试修复（SQLite）：`sqlite3 ~/.paper-agent/library.db "PRAGMA integrity_check;"`
3. 如果无法修复，删除并重新初始化：
   ```bash
   rm ~/.paper-agent/library.db
   paper-agent init
   paper-agent profile create
   paper-agent collect -d 30
   ```

---

## 交互模式使用

### 进入交互模式

```bash
paper-agent
```

### 交互模式命令

```
paper> collect -d 3
paper> digest
paper> search transformer
paper> show 1          # 使用结果序号
paper> stats
paper> help
paper> quit
```

### 交互模式优势

- 无需重复输入 `paper-agent` 前缀
- `show` 命令支持结果序号（如 `show 1` 查看第一篇）
- `search` 支持别名 `s`；未知命令会被当作搜索关键词
- 更快的迭代探索

---

## 最佳实践

### 实践 1: 建立每日习惯

```bash
# 每天早上执行
paper-agent collect -d 1
paper-agent digest
```

### 实践 2: 定期扩展库

```bash
# 每周执行一次，扩大覆盖范围
paper-agent collect -d 7 -m 300
```

### 实践 3: 使用 JSON 输出进行自动化

```bash
# 导出数据用于分析
paper-agent digest --json > digest_$(date +%Y%m%d).json
paper-agent stats --json > stats.json
```

### 实践 4: 配置环境变量

```bash
# 在 ~/.zshrc 或 ~/.bashrc 中
export PAPER_AGENT_LLM_API_KEY="your-key-here"
```

### 实践 5: 备份配置和数据

```bash
# 定期备份
cp -r ~/.paper-agent ~/.paper-agent.backup
```

---

## 用户旅程总结（v01，Claude Code 为主）

### Day 0 — 安装与连接（终端，5 分钟）
1. `pipx install paper-agent` → `paper-agent init` → `paper-agent setup claude-code`
2. 成功标准：Claude Code 中 MCP 连接成功，`/paper-setup` 可用

### Day 1 — 首次使用（Claude Code）
1. `/paper-setup` 对话配研究方向 → `/start-my-day` 收集 + 推荐
2. 成功标准：获得第一份有价值的 digest

### Day 2-7 — 日常使用（Claude Code）
1. 每日 `/start-my-day` → 搜索论文 → 查看详情 → 分析笔记
2. 成功标准：论文 intake 成为日常习惯

### Day 8+ — 多篇智能使用（v02，Claude Code）
1. 搜索 → `/paper-compare` 多篇对比 → `/paper-survey` 生成综述
2. `/paper-download` 下载 PDF → `paper_export` 导出 BibTeX
3. `paper_search_online` 实时搜索 arXiv 补充本地库
4. profile/sources 调整 → JSON 导出
5. 成功标准：Paper Agent 融入研究工作流，支持多篇对比和综述

---

## 下一步

- 查看 [Paper Agent Overview](../paper-agent-overview.md) 了解完整产品视图和 v02 规划
- 查看 [开发者旅程](./developer-journey.md) 了解如何扩展和定制系统
- 查看 [Feature](./feature.md) 了解完整功能列表
- 查看 [Spec](./spec.md) 了解详细功能规格
