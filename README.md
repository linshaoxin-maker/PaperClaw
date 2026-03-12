# Paper Agent

CLI-first paper intelligence system for AI researchers.

自动从 arXiv 收集论文，利用 LLM 按你的研究方向过滤评分，生成每日推荐摘要。

## Installation

### 一键安装为系统命令（推荐）

```bash
# clone 后直接跑安装脚本
./install.sh
```

脚本会自动：
1. 检查 Python 3.10+ 环境
2. 安装 pipx（如果没有）
3. 通过 pipx 将 `paper-agent` 安装为全局命令

安装完成后，在任何目录下都可以直接使用 `paper-agent`。

### 开发模式安装

如果你要修改源码，用以下方式安装：

```bash
cd paper_agent

# 方式一：Poetry（推荐）
poetry install
# 之后用 poetry run paper-agent 或 poetry shell 后使用

# 方式二：pip editable install
pip install -e .

```

### 卸载

```bash
pipx uninstall paper-agent
```

## User Journey

### Step 1: 初始化配置

首次使用前必须初始化，设定你的研究方向和 LLM 配置：

```bash
paper-agent init
```

交互式引导你填写：
- **研究方向** — 如 `retrieval-augmented generation, circuit design`
- **关键词** — 更细粒度的过滤词
- **arXiv 分类** — 从哪些分类收集，如 `cs.AI, cs.LG, cs.CL`
- **LLM Provider** — `anthropic` 或 `openai`
- **API Key** — 用于论文过滤和摘要生成
- **Base URL** — 自定义 API 端点（可选，留空使用默认）

配置保存在 `~/.paper-agent/config.yaml`，随时可以重新 `init` 覆盖。

#### 非交互式初始化（适合脚本/自动化）

也可以通过 CLI 参数直接初始化，跳过交互式提示：

```bash
paper-agent init \
  --provider openai \
  --api-key "sk-xxx" \
  --base-url "https://api.custom.com" \
  --topics "RAG, circuit design" \
  --keywords "transformer, attention" \
  --sources "cs.AI, cs.LG"
```

支持的参数：
- `--provider` — LLM 提供商（anthropic/openai）
- `--api-key` — API 密钥
- `--base-url` — 自定义 API 端点（用于代理、Azure OpenAI 等）
- `--model` — 模型名称（留空使用默认）
- `--topics` — 研究方向（逗号分隔）
- `--keywords` — 关键词（逗号分隔）
- `--sources` — arXiv 分类（逗号分隔）

也可以混合使用，例如只提供 API key，其他字段仍然交互式输入：

```bash
paper-agent init --api-key "sk-xxx"
```

### Step 2: 收集论文

从 arXiv 抓取最近的论文，并用 LLM 自动评分过滤：

```bash
paper-agent collect
```

常用选项：
| 选项 | 说明 | 默认值 |
|---|---|---|
| `-d, --days N` | 收集最近 N 天的论文 | 7 |
| `-m, --max N` | 每个分类最多抓取 N 篇 | 200 |
| `--no-filter` | 只收集不过滤（跳过 LLM 评分） | 默认过滤 |

```bash
# 示例：收集最近 3 天，每分类最多 100 篇
paper-agent collect -d 3 -m 100
```

### Step 3: 查看每日推荐

收集完成后，生成今天的论文推荐摘要：

```bash
paper-agent digest
```

会按置信度分为 **High Confidence**（强推荐）和 **Supplemental**（补充参考）两档展示。

```bash
# 查看指定日期的 digest
paper-agent digest --date 2026-03-10
```

### Step 4: 搜索论文

在本地论文库中关键词搜索：

```bash
paper-agent search "retrieval augmented generation"

# 限制返回数量
paper-agent search "transformer" -n 10
```

### Step 5: 查看论文详情

通过论文 ID 查看详细信息（标题、摘要、评分、链接等）：

```bash
paper-agent show <paper-id>
```

### Step 6: 查看统计

总览本地论文库的状态：

```bash
paper-agent stats
```

输出包括：总论文数、高/低置信度数量、未评分数量、热门 topic 排行。

## Interactive Mode (REPL)

直接运行 `paper-agent`（不带子命令）会进入交互式模式：

```bash
paper-agent
```

```
paper> collect -d 3
paper> digest
paper> search transformer
paper> show 1          # 用上一次结果的序号查看详情
paper> stats
paper> help
paper> quit
```

交互模式下 `show` 支持直接用结果列表的序号（如 `show 1` 查看第一篇），不需要手动复制 paper ID。

## JSON Output

所有命令都支持 `--json` 输出，方便脚本集成和自动化：

```bash
paper-agent digest --json
paper-agent search "LLM" --json
paper-agent stats --json
```

## Configuration

查看当前配置：

```bash
paper-agent config
```

API Key 也可以通过环境变量设置（优先级高于配置文件）：

```bash
export PAPER_AGENT_LLM_API_KEY="your-key-here"
```

## Typical Daily Workflow

```bash
# 每天早上跑一次
paper-agent collect -d 1        # 抓昨天的新论文
paper-agent digest              # 看今天的推荐

# 感兴趣的论文深入看
paper-agent show <paper-id>

# 随时搜索历史论文
paper-agent search "topic you care about"
```
