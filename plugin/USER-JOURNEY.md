# Paper Agent in Claude Code — 完整使用指南

在 Claude Code 中使用 paper-agent 的详细旅程。从安装配置到 8 个 slash 命令的完整交互示例。

---

## 前置条件

在 Claude Code 中使用 paper-agent 之前，需要在终端完成两步准备（约 3 分钟）：

```bash
# 1. 安装 paper-agent
pipx install paper-agent

# 2. 初始化 LLM（因为要输入 API Key，必须在终端）
paper-agent init
#   LLM Provider: openai
#   API Key: sk-xxxxx
#   Base URL: (留空)
#   ✅ 初始化完成！
```

之后所有操作都可以在 Claude Code 中完成，不需要再回终端。

---

## 连接到 Claude Code

在你的研究项目目录中运行：

```bash
cd ~/my-research-project
paper-agent setup claude-code
```

会生成以下文件：

```
my-research-project/
├── .mcp.json                      ← MCP 服务器配置
├── CLAUDE.md                      ← 告诉 AI 可用的工具
└── .claude/
    └── commands/
        ├── start-my-day.md        ← /start-my-day
        ├── paper-search.md        ← /paper-search
        ├── paper-analyze.md       ← /paper-analyze
        ├── paper-collect.md       ← /paper-collect
        ├── paper-setup.md         ← /paper-setup
        ├── paper-compare.md       ← /paper-compare
        ├── paper-survey.md        ← /paper-survey
        └── paper-download.md      ← /paper-download
```

现在启动 Claude Code：

```bash
claude
```

Claude Code 读取 `.mcp.json`，自动启动 `paper-agent-mcp` 后端。你就可以开始用了。

---

## 第一次使用：配置研究方向

### `/paper-setup` — 对话式配置

```
You: /paper-setup

Claude: 你好！我来帮你配置 paper-agent 的研究方向。
        先看看你有没有已有的配置...

        [调用 paper_profile()]

        你还没有设置研究方向。我先看看有哪些预设模板：

        [调用 paper_templates_list()]

        有几个可选的研究模板：

        1. **ai-hardware** — AI for Hardware Design
           包含: EDA, circuit design, high-level synthesis, logic synthesis
        2. **nlp** — Natural Language Processing
           包含: language modeling, text generation, RAG
        3. **cv** — Computer Vision
           包含: image recognition, object detection, segmentation
        4. **ml-theory** — Machine Learning Theory
           包含: optimization, generalization, statistical learning

        你的研究方向跟哪个比较接近？或者直接告诉我你在做什么研究，
        我帮你定制。

You: 我做 EDA 方向的，主要关注用 AI 做电路设计，特别是 placement 和 routing

Claude: 明白！我基于 ai-hardware 模板，再结合你的具体方向来配置：

        **Topics（研究主题）：**
        - circuit design, EDA, chip placement, routing
        - high-level synthesis, logic synthesis
        - physical design, floorplanning

        **Keywords（搜索关键词）：**
        - transformer, GNN, reinforcement learning
        - netlist, timing optimization, HPWL
        - macro placement, global routing

        [调用 paper_sources_list()]

        推荐启用以下论文源：

        **arXiv 分类**（每日预印本）：
        - **arxiv:cs.AR** — Hardware Architecture（核心）
        - **arxiv:cs.AI** — Artificial Intelligence
        - **arxiv:cs.LG** — Machine Learning

        **会议**（通过 DBLP + Semantic Scholar 采集）：
        - **conf:DAC** — Design Automation Conference
        - **conf:ICCAD** — International Conference on CAD
        - **conf:DATE** — Design, Automation & Test in Europe

        这样配置可以吗？需要调整吗？

You: 可以，再加一个 cs.PL

Claude: 好的。

        [调用 paper_profile_update(
            topics=["circuit design", "EDA", "chip placement", "routing",
                    "high-level synthesis", "logic synthesis",
                    "physical design", "floorplanning"],
            keywords=["transformer", "GNN", "reinforcement learning",
                      "netlist", "timing optimization", "HPWL",
                      "macro placement", "global routing"]
        )]

        [调用 paper_sources_enable(
            source_ids=["arxiv:cs.AR", "arxiv:cs.AI", "arxiv:cs.LG", "arxiv:cs.PL",
                        "conf:DAC", "conf:ICCAD", "conf:DATE"]
        )]

        ✅ 研究方向已保存！已启用 4 个 arXiv 分类 + 3 个会议源。
        收集时会从 arXiv + DBLP + Semantic Scholar 三源并行采集。

        要不要现在就收集一周的论文试试看效果？

You: 好

Claude: [调用 paper_collect(days=7)]

        开始采集: arXiv(4) + DBLP(5) + S2(关键词) 并行 ...
          arXiv: 抓取分类 cs.AR ...
          arXiv: cs.AR 完成, 89 篇
          arXiv: 抓取分类 cs.AI ...
          DBLP: 抓取 DAC (conf/dac) ...
          S2: 搜索 2 组关键词, venue 过滤=["DAC","ICCAD","DATE"] ...
          S2: 查询 [1/2] "chip placement routing EDA" ...
          ✓ dblp: 156 篇
          ✓ arxiv: 210 篇
          ✓ semantic_scholar: 87 篇
          去重后: 340 篇唯一论文
          完成: 312 新增, 28 重复

        ✅ 收集完成！

        - 收集论文：340 篇（arXiv 210 + DBLP 156 + S2 87，去重后 340）
        - 新增：312 篇
        - 重复跳过：28 篇
        - LLM 评分：312 篇已完成

        要看看今天的推荐吗？输入 /start-my-day 或者直接告诉我。

        💡 **提示**: 初始化 Workspace 后，你的阅读进度、笔记、论文分组
        都会以 markdown 文件的形式保存在 `.paper-agent/` 目录，打开文件夹就能看到。

You: 先初始化一下 workspace

Claude: [调用 paper_workspace_init()]

        ✅ Workspace 初始化完成！

        创建了以下文件：
        ```
        .paper-agent/
        ├── research-journal.md     ← 研究日志（AI 的记忆）
        ├── reading-list.md         ← 阅读队列
        ├── collections/            ← 论文分组
        │   └── _index.md
        ├── notes/                  ← 论文笔记
        └── citation-traces/        ← 引用链记录
        ```

        之后每次操作都会自动更新这些文件。看看推荐吗？

You: 看看

Claude: [调用 paper_digest()]

        📋 **今日论文推荐 — 2026-03-13**

        ## 高置信推荐（6 篇）

        ### 1. [[RL-Placer: Deep RL for Chip Macro Placement]]
        - **评分**: 9.2/10
        - **作者**: Zhang et al. (PKU)
        - **核心贡献**: 提出新的 RL 框架做 macro placement，在 ISPD 上比
          传统方法快 3.2×
        - → 跟你的 "placement + RL" 方向高度匹配

        ### 2. [[GNN-Driven Routing Optimization]]
        - **评分**: 8.7/10
        - **作者**: Li et al. (UCSD)
        - **核心贡献**: 用 GNN 预测 routing congestion，减少 DRC 违规 45%

        ...（共 6 篇）

        ## 补充参考（12 篇）
        ...

        需要深入看哪篇？告诉我序号或标题。
```

---

## 8 个 Slash 命令详解

### 1. `/start-my-day` — 每日开工

每天早上用一次。先恢复上下文（你昨天在干什么），再收集新论文。

```
You: /start-my-day

Claude: 先看看你最近在研究什么...

        [调用 paper_workspace_context()]

        📋 **上下文恢复**
        - 昨天搜索了 "RL placement" 相关论文（12 篇）
        - 标记了 3 篇为"待读"，1 篇为"重要"
        - 分组 "rl-placement" 有 7 篇论文
        - 阅读进度：待读 5 | 阅读中 2 | 已读 8 | 重要 3

        正在收集今日论文...

        [调用 paper_collect(days=1)]

        开始采集: arXiv(4) + DBLP(5) + S2(关键词) 并行 ...
          ...
        收集完成：47 篇新论文（三源去重），已完成 LLM 评分。

        [调用 paper_digest()]

        📋 **今日论文推荐 — 2026-03-14**

        ## 今日概览

        今日推荐的 5 篇论文主要聚焦于 **电路布局优化** 和 **HLS 自动化**。

        ## 高置信推荐（5 篇）

        ### 1. [[Transformer-Based Placement Engine]]
        - **作者**: Wang et al.
        - **评分**: 9.1/10
        - **链接**: [arXiv](https://arxiv.org/abs/2603.04567)
        - **一句话总结**: 首次将 vision transformer 引入 chip placement

        ### 2. [[Diffusion Models for VLSI Floorplanning]]
        - **作者**: Chen et al.
        - **评分**: 8.5/10
        - **链接**: [arXiv](https://arxiv.org/abs/2603.04321)
        - **一句话总结**: 用 diffusion model 生成 floorplan 方案

        ...

        ## 阅读建议

        建议先阅读第 1 篇了解 transformer 在 placement 中的新应用，
        再关注第 2 篇的 diffusion 方法——这两种生成式方法的对比很有价值。

        需要深入分析哪篇？

You: 第 1 篇展开

Claude: [调用 paper_show("arxiv:2603.04567")]

        📄 **Transformer-Based Placement Engine**

        | 字段 | 值 |
        |------|---|
        | arXiv ID | 2603.04567 |
        | 作者 | Wang, Li, Zhang (Tsinghua) |
        | 日期 | 2026-03-12 |
        | 分类 | cs.AR, cs.AI |
        | 评分 | 9.1/10 |

        **摘要翻译**
        > 本文提出一种基于 Vision Transformer 的芯片布局引擎。通过将
        > netlist 表示为图像化的 2D 特征图，利用 self-attention 机制
        > 捕捉宏单元间的全局依赖关系...

        **评分理由**
        与你的 "chip placement + transformer" 方向高度匹配，方法新颖且
        实验充分。

        要深入分析这篇吗？我可以生成一份结构化笔记。

You: 好的，帮我分析

Claude: (进入 paper-analyze 流程，见下方)
```

---

### 2. `/paper-search <query>` — 搜索论文

在本地论文库中搜索。支持关键词自动扩展和智能建议。

```
You: /paper-search attention mechanism for EDA

Claude: [调用 paper_search("attention mechanism for EDA")]

        找到 8 篇相关论文：

        1. **AttentionPlacer: Cross-Attention for Chip Layout** — 评分 8.9/10
           首次将 cross-attention 应用于 macro placement

        2. **Self-Attention in Logic Synthesis** — 评分 7.4/10
           用 self-attention 优化逻辑综合流程

        3. **Multi-Head Attention for Timing Analysis** — 评分 8.1/10
           attention 机制预测时序违规

        4. **Transformer-EDA: A Survey** — 评分 8.6/10
           EDA 领域 transformer 应用综述

        ...

        需要查看某篇的详细信息吗？告诉我编号。

You: 看看第 4 篇

Claude: [调用 paper_show("arxiv:2501.07890")]

        📄 **Transformer-EDA: A Comprehensive Survey**
        ...
```

**结果少时自动提示建议：**

```
You: /paper-search GNN placement

Claude: [调用 paper_search("GNN placement")]

        找到 3 篇相关论文：
        ...

        💡 本地只找到 3 篇结果。可以尝试多样性搜索，自动扩展关键词:
           graph neural network placement
           → paper-agent search "GNN placement" --diverse

        🌐 本地结果较少(3 篇)。可以尝试在线搜索从 arXiv + Semantic Scholar
           实时获取更多结果（包括会议论文）。

You: 在线搜一下

Claude: [调用 paper_search_online("GNN placement")]

        在线搜索完成（arXiv + Semantic Scholar 并行）：
        - arXiv: 25 篇
        - Semantic Scholar: 18 篇（含 DAC、ICCAD 会议论文）
        去重后共 38 篇，已保存到本地库。
        ...
```

**多方向批量搜索：**

```
You: 帮我搜一下这四个方向的论文：episodic memory, memory architecture,
     long-term memory, memory management

Claude: [调用 paper_search_batch(
            queries=["episodic memory agent",
                     "memory architecture agent",
                     "long-term memory LLM",
                     "memory management context"],
            limit_per_query=20,
            diverse=True
        )]

        四个方向共找到 72 篇论文：
        - episodic memory agent: 20 篇
        - memory architecture agent: 19 篇
        - long-term memory LLM: 18 篇
        - memory management context: 15 篇

        要基于这些写综述吗？还是选几篇对比？
```

**自然语言也可以，不一定要用 slash 命令：**

```
You: 有没有用 GNN 做 routing 的论文？

Claude: 我帮你搜搜看。

        [调用 paper_search("GNN routing", diverse=True)]
        （自动扩展: "graph neural network routing"）

        找到 8 篇相关论文：
        ...
```

---

### 3. `/paper-analyze <paper_id>` — 深度分析

生成结构化分析笔记。

```
You: /paper-analyze 2603.04567

Claude: [调用 paper_show("arxiv:2603.04567")]

        我来生成这篇论文的深度分析：

        ---

        ## Transformer-Based Placement Engine — 深度分析

        ### 核心信息

        | 字段 | 值 |
        |------|---|
        | arXiv ID | 2603.04567 |
        | 作者 | Wang, Li, Zhang (Tsinghua) |
        | 发布时间 | 2026-03-12 |
        | 评分 | 9.1/10 |

        ### 摘要翻译

        本文提出一种基于 Vision Transformer 的芯片布局引擎。通过将
        netlist 表示为图像化的 2D 特征图，利用 self-attention 机制
        捕捉宏单元间的全局依赖关系，实现端到端的 placement 优化。

        ### 方法概述

        **核心思想**
        将 chip placement 问题转化为图像到图像的预测任务。

        **方法框架**
        1. 输入：netlist → 2D feature map（每个 cell 占一个 patch）
        2. 编码器：ViT encoder 提取全局 cell 间关系
        3. 解码器：预测每个 cell 的最优坐标

        **关键设计**
        - Position encoding 编码 cell 的物理约束
        - Cross-attention 层融合 timing 信息

        ### 实验结果

        | Benchmark | HPWL 改进 | 运行时间 | 对比方法 |
        |-----------|----------|---------|---------|
        | ISPD-2015 | -15.3%   | 2.1h    | DREAMPlace |
        | ICCAD-2019| -12.7%   | 3.4h    | ePlace |

        ### 深度分析

        **优势**
        - 全局感受野，避免传统方法的局部最优
        - 端到端训练，无需手工特征工程

        **局限**
        - 计算开销大（ViT 的 O(n²) 复杂度）
        - 仅验证了 macro placement，standard cell 未涉及

        **适用场景**
        适合中等规模（< 10K macros）的 placement 问题

        ---

        分析完成。要保存笔记吗？

You: 保存一下

Claude: [调用 paper_note_add(
            paper_id="arxiv:2603.04567",
            content="(上述完整分析内容)",
            source="ai_analysis"
        )]

        ✅ 笔记已保存！
        - 数据库记录：note_id = abc123
        - 文件同步：`.paper-agent/notes/e3f2a1b9c0d4.md`
        - 研究日志已更新

        打开 `.paper-agent/notes/` 就能看到。要继续分析其他论文吗？

You: 顺便标记为"阅读中"

Claude: [调用 paper_reading_status(
            paper_ids=["arxiv:2603.04567"],
            status="reading"
        )]

        ✅ 已标记为"阅读中"。
        阅读进度：待读 5 | **阅读中 3** | 已读 8 | 重要 3
        reading-list.md 已更新。
```

---

### 4. `/paper-collect [days]` — 收集论文

从 arXiv + DBLP + Semantic Scholar 三源并行采集，带实时进度日志。
（`/start-my-day` 已包含此步骤，通常不需要单独用。）

```
You: /paper-collect 14

Claude: 正在收集最近 14 天的论文...

        [调用 paper_collect(days=14)]

        开始采集: arXiv(4) + DBLP(5) + S2(关键词) 并行 ...
          arXiv: 抓取分类 cs.AR ...
          arXiv: cs.AR 完成, 203 篇
          DBLP: 抓取 DAC (conf/dac) ...
          DBLP: 抓取 ICCAD (conf/iccad) ...
          S2: 搜索 2 组关键词 ...
          ✓ arxiv: 478 篇
          ✓ dblp: 312 篇
          ✓ semantic_scholar: 197 篇
          去重后: 892 篇唯一论文
          完成: 645 新增, 247 重复

        ## 收集完成

        - 收集论文：892 篇（三源去重）
        - 新增论文：645 篇
        - 重复跳过：247 篇
        - LLM 评分：645 篇

        [调用 paper_stats()]

        ## 库概览

        - 总计：2,139 篇
        - 高置信：287 篇
        - 待评分：0 篇
        - 来源：arXiv (1,203), DBLP (645), S2 (291)
        - 热门方向：cs.AI (563), cs.LG (421), cs.AR (312)

        要看 digest 吗？

You: 看看

Claude: [调用 paper_digest()]
        ...
```

---

### 5. `/paper-setup` — 配置研究方向

见上方「第一次使用」的完整示例。也可以随时用来更新方向：

```
You: /paper-setup

Claude: [调用 paper_profile()]

        你当前的研究方向：

        **Topics**: circuit design, EDA, chip placement, routing, ...
        **Keywords**: transformer, GNN, reinforcement learning, ...
        **Sources**: cs.AR, cs.AI, cs.LG, cs.PL

        需要修改什么吗？

You: 最近在关注 diffusion model，帮我加上

Claude: 好的，我帮你加上 diffusion model 相关的关键词：

        新增 Keywords:
        - diffusion model
        - denoising diffusion
        - score-based generative model

        Topics 也加上：
        - generative models for EDA

        [调用 paper_profile_update(
            topics=[...现有..., "generative models for EDA"],
            keywords=[...现有..., "diffusion model", "denoising diffusion",
                      "score-based generative model"]
        )]

        ✅ 已更新！下次收集时会用新的关键词评分。
        要现在重新收集看看效果吗？
```

---

### 6. `/paper-compare` — 多篇对比（v02）

横向比较多篇论文的方法、结果、适用场景。

```
You: /paper-compare

Claude: 你想对比哪些论文？
        可以给我 arXiv ID 列表，或者告诉我一个主题，我帮你找。

You: 对比一下 RL 做 placement 的几篇论文

Claude: 我先搜一下：

        [调用 paper_search("reinforcement learning placement")]

        找到 7 篇相关论文：
        1. RL-Placer (2026) — 评分 9.2
        2. ChipFormer (2025) — 评分 8.8
        3. MaskPlace (2024) — 评分 8.3
        4. DeepPlace (2024) — 评分 7.9
        5. GraphPlace (2025) — 评分 8.1
        6. PRNet (2023) — 评分 7.5
        7. PlaceRL (2024) — 评分 7.2

        你想对比哪几篇？可以告诉我编号。

You: 1, 2, 3, 5

Claude: 你想从哪些维度对比？
        a) 方法架构
        b) 实验结果 (benchmark)
        c) 适用场景
        d) 全部

You: a 和 b

Claude: [调用 paper_compare(
            paper_ids=["arxiv:2602.01234", "arxiv:2501.05678",
                       "arxiv:2401.09012", "arxiv:2504.03456"],
            aspects=["methodology", "results"]
        )]

        ## RL Placement 方法对比

        ### 方法架构

        | 论文 | RL 算法 | 状态表示 | 动作空间 | 奖励函数 |
        |------|---------|---------|---------|---------|
        | RL-Placer | PPO | Graph embedding | 连续坐标 | HPWL + congestion |
        | ChipFormer | SAC | Transformer encoding | 网格位置 | HPWL + timing |
        | MaskPlace | DQN + mask | CNN feature map | 候选位置集 | HPWL |
        | GraphPlace | A2C | GNN embedding | 连续坐标 | 加权 HPWL |

        ### 实验结果

        | 论文 | Benchmark | HPWL 改进 | 运行时间 | vs. 基线 |
        |------|-----------|----------|---------|---------|
        | RL-Placer | ISPD-2015 | -15.3% | 2.1h | DREAMPlace |
        | ChipFormer | MMS | -11.8% | 1.5h | ePlace |
        | MaskPlace | ISPD-2015 | -8.4% | 4.2h | DREAMPlace |
        | GraphPlace | ICCAD-2019 | -10.1% | 2.8h | RePlAce |

        ### 分析总结

        - **最佳 HPWL**: RL-Placer 效果最好，得益于 PPO 的稳定训练 +
          graph embedding 的全局视野
        - **最快速度**: ChipFormer 因为用了 SAC 的离策略学习，
          sample efficiency 最高
        - **Trade-off**: MaskPlace 的离散动作空间简化了问题，但限制了精度
        - **建议**: 如果你追求精度用 RL-Placer 框架，追求速度用 ChipFormer

        要保存这个对比表格吗？或者基于这些写 survey？

You: 保存到 notes/rl-placement-comparison.md

Claude: [写入文件]
        ✅ 已保存到 `notes/rl-placement-comparison.md`

You: 顺便导出这几篇的 BibTeX

Claude: [调用 paper_export(paper_ids, format="bibtex")]

        导出到哪个文件？

You: refs/placement.bib

Claude: [写入文件]
        ✅ 已导出 4 条 BibTeX 到 `refs/placement.bib`
```

---

### 7. `/paper-survey <topic>` — 生成文献综述（v02）

从搜索到综述的全流程。支持单方向和多方向综述。

**单方向综述：**

```
You: /paper-survey Reinforcement Learning for Chip Placement

Claude: 我来帮你生成这个方向的文献综述。

        首先分析关键词：
        - 主要: reinforcement learning, chip placement
        - 扩展: macro placement, VLSI, floorplanning, optimization
        - 相关: deep RL, policy gradient, graph neural network

        这些关键词覆盖够吗？

You: 加上 simulated annealing 作为传统方法的对比

Claude: 好的。先搜本地库：

        [调用 paper_search("RL chip placement", diverse=True)]
        （自动扩展: "reinforcement learning chip placement"）

        本地找到 12 篇。要从在线源补充搜索吗？
        （在线搜索覆盖 arXiv + Semantic Scholar，包括会议论文）

You: 搜一下

Claude: [调用 paper_search_online(
            "reinforcement learning chip placement optimization"
        )]

        在线搜索完成（arXiv + Semantic Scholar 并行）：
        - arXiv: 18 篇
        - Semantic Scholar: 15 篇（含 DAC, ICCAD 会议论文）
        合并去重后共 34 篇候选。

        以下是候选列表（按相关度排序）：

        | # | 标题 | 年份 | 评分 | 来源 |
        |---|------|------|------|------|
        | 1 | RL-Placer: Deep RL for... | 2026 | 9.2 | 本地 |
        | 2 | ChipFormer: Transformer... | 2025 | 8.8 | 本地 |
        | 3 | A Survey of ML for EDA... | 2025 | 8.5 | arXiv |
        | 4 | Placement by SA+DL... | 2025 | 8.1 | S2/DAC |
        | ... | | | | |

        你想把哪些纳入 survey？可以告诉我编号，或者"全选"。

You: 选前 15 篇吧

Claude: 好的，15 篇确认。Survey 要包含哪些章节？

        a) Background & Motivation
        b) 方法分类与对比
        c) 实验结果汇总
        d) Open Problems & Future Directions
        e) 全部

You: 全部

Claude: 正在获取这 15 篇论文的详细信息...

        [调用 paper_batch_show(15 篇 IDs)]
        （使用 compact 格式，精简摘要 + 核心信息）

        生成 survey 草稿中...

        ---

        # Reinforcement Learning for Chip Placement: A Survey

        ## 1. 引言与背景

        芯片布局（chip placement）是 VLSI 物理设计中的核心问题。传统方法
        如模拟退火（simulated annealing）和解析方法（analytical placement）
        已有数十年研究...近年来，深度强化学习的引入为这一问题带来了新思路。

        本文综述了 2023-2026 年间 15 篇代表性工作...

        ## 2. 方法分类

        ### 2.1 基于 Policy Gradient 的方法
        ...

        ### 2.2 基于 Value-Based RL 的方法
        ...

        ### 2.3 混合方法（RL + 传统优化）
        ...

        ## 3. 方法对比

        | 论文 | 方法类别 | 状态表示 | 核心创新 | HPWL 改进 |
        |------|---------|---------|---------|----------|
        | ... | ... | ... | ... | ... |

        ## 4. 实验对比

        ...

        ## 5. 研究空白与未来方向

        1. **可扩展性**：现有方法大多在 < 10K macros 的规模上验证
        2. **迁移学习**：跨设计的策略迁移仍是挑战
        3. **timing-aware**：多数方法仅优化 HPWL，未考虑时序约束
        ...

        ## 参考文献

        [1] Zhang et al., "RL-Placer: ..." arXiv:2602.01234
        [2] ...

        ---

        Survey 草稿完成（约 4000 字）。看看需要修改哪里？

You: Background 部分太短了，加一些传统方法的发展历程

Claude: 好的，我来补充传统 placement 方法的背景：

        (补充 simulated annealing 的经典工作、analytical placement
         的代表方法如 ePlace/DREAMPlace 的演进...)

        修改完成。还需要调整其他地方吗？

You: 可以了，保存吧

Claude: 保存到哪个文件？

You: survey/rl-placement-survey.md

Claude: [写入文件]

        ✅ 已保存到 `survey/rl-placement-survey.md`

        要导出这 15 篇的 BibTeX 吗？

You: 好

Claude: [调用 paper_export(15 篇 IDs, format="bibtex")]

        导出到 `survey/rl-placement-refs.bib` 可以吗？

You: 行

Claude: [写入文件]

        ✅ 已导出 15 条 BibTeX 到 `survey/rl-placement-refs.bib`

        全部完成！文件列表：
        - `survey/rl-placement-survey.md` — 综述全文
        - `survey/rl-placement-refs.bib` — BibTeX 引用
```

---

**多方向综述（如 4 个方向同时出综述）：**

```
You: 这四个方向上的论文分别选 20 篇分析一下，输出一个综述：
     episodic memory, memory architecture, long-term memory, memory management

Claude: 好的，我先用批量搜索一次搞定四个方向：

        [调用 paper_search_batch(
            queries=["episodic memory agent",
                     "memory architecture LLM",
                     "long-term memory agent",
                     "memory management context"],
            limit_per_query=20,
            diverse=True
        )]

        四个方向共找到 72 篇论文：
        - episodic memory agent: 20 篇
        - memory architecture LLM: 19 篇
        - long-term memory agent: 18 篇
        - memory management context: 15 篇

        本地结果略少，要在线补充搜索吗？

You: 搜一下

Claude: [调用 paper_search_online("episodic memory agent", sources=["arxiv", "s2"])]
        [调用 paper_search_online("memory architecture LLM agent", sources=["arxiv", "s2"])]
        ...

        在线补充后每个方向均达到 20+ 篇，总计 82 篇。

        正在获取论文详情...

        [调用 paper_batch_show(82 篇 IDs)]

        正在生成综述...

        ---

        # LLM Agent Memory Systems: A Multi-Perspective Survey

        ## 1. 引言

        大语言模型 Agent 的记忆系统是当前 AI 研究的热点...

        ## 2. Episodic Memory
        ...

        ## 3. Memory Architecture
        ...

        ## 4. Long-Term Memory
        ...

        ## 5. Memory Management
        ...

        ## 6. 交叉分析与对比
        ...

        ## 7. 未来方向
        ...

        ---

        综述草稿完成（约 6000 字）。需要修改哪里？
```

> **注意**：多方向综述使用 `paper_search_batch` 一次搜多个方向，
> 而不是反复调用 `paper_search`。这样更快、更可靠、不会因为某个查询
> 报错而中断整个流程。

---

### 8. `/paper-download <paper_id>` — 批量下载 PDF（v02）

一次可以下载多篇 PDF，传入多个 ID 即可。

```
You: /paper-download 2602.01234

Claude: [调用 paper_download(paper_ids=["arxiv:2602.01234"])]

        ✅ 已下载：
        - papers/2602.01234_RL-Placer.pdf (2.3 MB)

        要阅读这篇吗？

You: 帮我把刚才 survey 里的 15 篇全下载了

Claude: [调用 paper_download(paper_ids=[15 篇 IDs])]

        批量下载结果：
        ✅ papers/2602.01234_RL-Placer.pdf — 已存在，跳过
        ✅ papers/2501.05678_ChipFormer.pdf — 2.1 MB
        ✅ papers/2401.09012_MaskPlace.pdf — 1.8 MB
        ✅ papers/2504.03456_GraphPlace.pdf — 2.5 MB
        ✅ papers/2503.07890_ML-EDA-Survey.pdf — 3.2 MB
        ...（共 15 篇）
        ❌ papers/2402.xxxxx_xxx.pdf — 无 arXiv 源，跳过

        14/15 篇下载成功。要读哪篇？
```

---

## Workspace 功能

v02 引入 **Workspace Layer**——`.paper-agent/` 目录下的一组 markdown 文件，
作为你和 AI 之间的"共享工作记忆"。所有操作自动记录，打开文件夹就能看到全貌。

### 阅读状态管理

```
You: 把今天推荐的前 3 篇标记为"待读"

Claude: [调用 paper_reading_status(
            paper_ids=["e3f2a1b9c0d4", "a1b2c3d4e5f6", "f7e8d9c0b1a2"],
            status="to_read"
        )]

        ✅ 3 篇已标记为"待读"。
        - RL-Placer: Deep RL for Chip Macro Placement
        - GNN-Driven Routing Optimization
        - Transformer-Based Placement Engine

        阅读进度：**待读 8** | 阅读中 2 | 已读 8 | 重要 3
        reading-list.md 已更新。

You: 看看阅读进度

Claude: [调用 paper_reading_stats()]

        📊 **阅读进度**

        | 状态 | 数量 | 最近论文 |
        |------|------|---------|
        | 重要 | 3 | RL-Placer, ChipFormer, MaskPlace |
        | 阅读中 | 2 | Transformer-Based Placement, AttentionPlacer |
        | 待读 | 8 | GNN-Driven Routing, ... |
        | 已读 | 8 | ... |

        要看哪个类别的详细列表？

You: 那篇 RL-Placer 我读完了，标记一下

Claude: [调用 paper_reading_status(
            paper_ids=["e3f2a1b9c0d4"],
            status="read"
        )]

        ✅ RL-Placer 已标记为"已读"。待读 8 | 阅读中 2 | **已读 9** | 重要 3
```

### 论文分组

```
You: 创建一个 "rl-placement" 分组，把 RL 相关的论文放进去

Claude: [调用 paper_group_create(
            name="rl-placement",
            description="RL-based chip placement methods"
        )]

        ✅ 分组 "rl-placement" 已创建。
        文件：`.paper-agent/collections/rl-placement.md`

        要加哪些论文进去？

You: 把之前对比的那 4 篇加进去

Claude: [调用 paper_group_add(
            name="rl-placement",
            paper_ids=["e3f2a1b9c0d4", "a1b2c3d4e5f6",
                       "f7e8d9c0b1a2", "b3c4d5e6f7a8"]
        )]

        ✅ 4 篇已添加到分组 "rl-placement"（共 4 篇）。
        collections/rl-placement.md 已更新。

You: 看看有哪些分组

Claude: [调用 paper_group_list()]

        📂 **论文分组**

        | 分组名 | 描述 | 论文数 |
        |--------|------|--------|
        | rl-placement | RL-based chip placement methods | 4 |
        | timing-opt | Timing optimization papers | 6 |

        要查看某个分组的详情？
```

### 引用链追踪

```
You: 看看 RL-Placer 这篇论文引用了什么，被谁引用了

Claude: [调用 paper_citations(
            paper_id="e3f2a1b9c0d4",
            direction="both",
            limit=15,
            trace_name="rl-placement-chain"
        )]

        🔗 **RL-Placer 引用关系**

        ### 引用的论文（backward, 15 篇）
        1. Google's Chip Placement with RL (Nature 2021) — 开创性工作
        2. DREAMPlace: Deep Learning Toolkit for VLSI Placement
        3. ...

        ### 被引用（forward, 8 篇）
        1. ChipFormer: Transferable Chip Placement (ICML 2023)
        2. MaskPlace: Fast Chip Placement via RL (NeurIPS 2022)
        3. ...

        新发现的论文已自动保存到本地库（23 篇新增）。
        引用链记录：`.paper-agent/citation-traces/rl-placement-chain.md`

        要深入看某篇吗？或者继续追踪某篇的引用？

You: 追踪一下 Google 那篇

Claude: [调用 paper_citations(
            paper_id="(Google 论文 ID)",
            direction="references",
            limit=10,
            trace_name="rl-placement-chain"
        )]

        Google Chip Placement 引用了 10 篇关键论文：
        ...

        引用链追踪已追加到 `citation-traces/rl-placement-chain.md`。
```

### 跨会话上下文恢复

每次新会话开始时，AI 自动读取 workspace 文件恢复上下文：

```
（新会话开始）

You: 我昨天在看什么来着？

Claude: [调用 paper_workspace_context()]

        📋 **你最近的研究活动**

        **昨天 (3/13)**
        - 09:30 搜索了 "RL placement" 论文 (12 篇)
        - 10:15 深度分析了 RL-Placer
        - 14:00 对比了 4 篇 RL placement 论文
        - 15:30 查了 RL-Placer 的引用链 (23 篇新增)
        - 16:00 创建分组 "rl-placement" (4 篇)

        **阅读进度**
        - 待读 8 | 阅读中 2 | 已读 9 | 重要 3

        **活跃分组**
        - rl-placement (4 篇)
        - timing-opt (6 篇)

        **引用链**
        - rl-placement-chain

        要继续昨天的工作吗？

You: 继续看引用链
```

---

## 自然语言交互

除了 slash 命令，你也可以用自然语言。Claude Code 会自动识别论文相关意图并调用 MCP 工具。

### 写代码时查论文

```
You: 我在实现一个 attention-based placement engine，有没有相关论文？

Claude: 我帮你搜搜看。

        [调用 paper_search("attention placement engine circuit")]

        找到 6 篇相关论文：

        | # | 标题 | 评分 |
        |---|------|------|
        | 1 | AttentionPlacer: Cross-Attention for... | 8.9 |
        | 2 | Self-Attention in VLSI Layout | 7.4 |
        | 3 | DREAMPlace 4.0: Attention-Enhanced... | 8.1 |
        | ... | | |

        第 1 篇和你的方向最接近。要看详细分析吗？

You: 第 1 篇展开

Claude: [调用 paper_show("arxiv:2601.03421")]

        📄 **AttentionPlacer: Cross-Attention for Chip Placement**
        ...

        与你代码的关联：
        你当前实现的 attention-based placement engine 可以参考
        他们的 cross-attention 设计（Section 3.2），特别是
        position encoding 的处理方式。

You: 帮我把核心方法记到 notes/attention-placement.md

Claude: [写入文件]
        ✅ 已保存到 `notes/attention-placement.md`
```

### 随时调整方向

```
You: 最近项目转向做 timing optimization 了，帮我更新一下

Claude: [调用 paper_profile()]

        当前 Profile 里没有 timing 相关的关键词。我帮你加上：

        新增 Topics:
        - timing optimization, static timing analysis

        新增 Keywords:
        - slack, critical path, setup/hold violation

        [调用 paper_profile_update(...)]

        ✅ 已更新。下次 /start-my-day 就会推荐 timing 相关的论文了。
```

### 中途切换任务

```
You: 对了，我之前看过一篇 LoRA 做 EDA 的论文，帮我找找

Claude: [调用 paper_search("LoRA EDA fine-tuning")]

        本地库找到 2 篇：
        1. LoRA-EDA: Parameter-Efficient Fine-Tuning for... — 7.8
        2. Efficient LLM Adaptation for Circuit Design — 8.2

        本地只有 2 篇。要从 arXiv 在线搜一下补充吗？

You: 搜一下

Claude: [调用 paper_search_online("LoRA fine-tuning EDA circuit design")]

        在线搜索完成（arXiv + Semantic Scholar 并行）：
        - arXiv: 5 篇（预印本）
        - S2: 4 篇（含 DAC'25 会议论文）
        去重后共 8 篇新论文，已自动加入本地库。
        合并后共 10 篇：
        ...
```

---

## 完整工作日场景

以下是一个研究员的典型工作日：

```
08:00  /start-my-day
       → workspace_context 恢复昨日上下文
       → 三源并行采集 47 篇新论文 → 推荐 5 篇高置信

08:10  "第 2 篇不错，标记待读；第 1 篇很重要"
       → paper_reading_status → reading-list.md 更新

08:15  /paper-analyze 2603.04567
       → 深度分析 → paper_note_add 保存笔记
       → .paper-agent/notes/ 自动更新

10:30  （写代码中）"这个 GNN aggregation 有论文讲过吗？"
       → paper_search(diverse=True) → 扩展搜索 → 找到 8 篇

11:00  "看看这篇引用了什么"
       → paper_citations → 引用链 → citation-traces/ 更新

14:00  /paper-compare
       → 选 4 篇 RL placement 论文 → 对比方法和结果
       → paper_group_create("rl-placement") → 创建分组

15:00  /paper-survey AI for Chip Placement
       → paper_search_batch 多方向搜索
       → paper_search_online (arXiv + S2 并行) 在线补充
       → paper_batch_show (compact) 获取详情
       → 生成综述 → 修改 → 保存

16:30  "导出今天看过的论文 BibTeX"
       → paper_export → refs.bib

17:00  "帮我把 survey 里的 15 篇 PDF 全下载了"
       → paper_download(15 篇 IDs) → papers/ 目录

-- 次日 --

08:00  /start-my-day
       → "昨天你分析了 RL-Placer，对比了 4 篇，创建了分组..."
       → 无缝恢复上下文
```

---

## 交互设计原则

paper-agent 在 Claude Code 中的每次交互都遵循同一个循环：

```
研究员发起（自然语言 / slash 命令）
    ↓
Claude Code 理解意图 → 确认/澄清
    ↓
调用 MCP tool(s) → 获取数据
    ↓
格式化呈现（中文、表格、wikilink）
    ↓
追问下一步（保存？继续？切换？）
    ↓
研究员反馈 → 循环
```

Claude Code 在每个环节：
- **记忆**：每次操作自动写入 research-journal.md，新会话自动恢复上下文
- **理解**：把模糊的描述转化为精确的查询
- **确认**：不确定时主动追问
- **建议**：结果少时自动建议 diverse 搜索或在线搜索
- **批量**：多方向任务用 `paper_search_batch` 一次搞定，不逐个调用
- **呈现**：compact 格式精简输出，避免信息过载
- **持久化**：笔记、分组、引用链自动保存为 markdown 文件，人可读
- **引导**：每步结束后建议下一步
- **修改**：结果不满意时支持迭代

---

## 故障排查

### MCP 连接失败

```
You: /start-my-day
Claude: ❌ 无法连接到 paper-agent MCP server
```

检查：
1. `paper-agent-mcp` 是否已安装：`which paper-agent-mcp`
2. `.mcp.json` 是否存在：`ls .mcp.json`
3. 重新配置：`paper-agent setup claude-code`

### 论文库为空

```
Claude: 库中没有论文。先收集一些？
```

确认已初始化 profile：
- 输入 `/paper-setup` 配置研究方向
- 然后 `/start-my-day` 收集

### API Key 失效

```
Claude: LLM 评分失败：API key invalid
```

在终端重新配置：`paper-agent init`

---

## 与 CLI 的对比

| 场景 | CLI（终端） | Claude Code |
|------|-----------|-------------|
| 查论文 | `paper-agent search "query"` | "帮我查 xxx 论文" |
| 关键词扩展 | `search "query" --diverse` | AI 自动建议 diverse 搜索 |
| 在线搜索 | 不支持 | `paper_search_online`（arXiv + S2 并行） |
| 每日推荐 | `collect -d 1 && digest`（两步） | `/start-my-day`（一步 + 上下文恢复） |
| 多源采集 | `collect`（arXiv + DBLP + S2 并行） | `/paper-collect`（同上 + 进度日志） |
| 分析论文 | `show <id>`（看原始数据） | `/paper-analyze`（结构化中文笔记） |
| 保存笔记 | 自己复制粘贴 | `paper_note_add`（自动保存到 DB + 文件） |
| 阅读状态 | 不支持 | `paper_reading_status`（待读/阅读中/已读/重要） |
| 论文分组 | 不支持 | `paper_group_create/add`（分组 + 文件同步） |
| 引用链 | 不支持 | `paper_citations`（S2 API + 自动入库 + 文件记录） |
| 跨会话记忆 | 不支持 | `paper_workspace_context`（自动恢复上下文） |
| 多篇对比 | 不支持 | `/paper-compare`（对比表格 + 分析） |
| 批量搜索 | 不支持 | `paper_search_batch`（N 个方向一次搞定） |
| 写综述 | 不支持 | `/paper-survey`（全流程引导） |
| 批量下载 | 不支持 | `/paper-download`（一次传多个 ID） |
| 上下文 | 需要在终端和 IDE 间切换 | AI 知道你在写什么代码 |
| 研究全貌 | 只能通过命令查 | 打开 `.paper-agent/` 目录即见 |
| 语言 | 英文命令 + 英文输出 | 自然语言输入 + 中文输出 |
