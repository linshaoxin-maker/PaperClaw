# Paper Agent v02 — 用户旅程

**Phase:** Phase 0
**Status:** Draft
**Last Updated:** 2026-03-14

---

## 旅程总览

v02 用户旅程围绕 **Workspace** 展开。核心变化：每次交互不再"聊完即逝"，而是自动沉淀到 `.paper-agent/` 目录中的 markdown 文件。

```
Day 0: 初始化 Workspace
         ↓
Day 1+: 每日循环
  ┌─ /start-my-day ─────────────────────────────────────┐
  │  收集论文 → 推荐 → 标记待读 → journal 记录          │
  └──────────────────────────────────────────────────────┘
         ↓
  ┌─ 阅读 & 笔记 ──────────────────────────────────────┐
  │  从 reading-list 选论文 → 阅读 → 标记状态            │
  │  → 写笔记 → notes/ 自动保存                         │
  └──────────────────────────────────────────────────────┘
         ↓
  ┌─ 分组 & 引用链 ─────────────────────────────────────┐
  │  创建 collection → 添加论文 → 追踪引用链             │
  │  → collections/ 和 citation-traces/ 自动更新         │
  └──────────────────────────────────────────────────────┘
         ↓
  ┌─ 综述 & 导出 ──────────────────────────────────────┐
  │  基于 collection 写 survey → 导出 BibTeX             │
  │  → 所有操作记录到 journal                            │
  └──────────────────────────────────────────────────────┘
```

---

## 旅程 1：Workspace 初始化

Workspace 在运行 `paper-agent setup cursor/claude-code` 时自动创建，无需额外操作：

```
$ paper-agent setup claude-code
✅ MCP → .mcp.json
✅ Commands → .claude/commands
✅ Workspace → .paper-agent/
```

如果用户跳过了 setup，MCP 工具在首次使用时会静默自动创建 workspace。

用户可以随时查看 workspace 仪表盘：

```
You: 看看我的研究全貌

Claude: [调用 paper_workspace_status()]

        📊 Research Dashboard

        **阅读进度**
        | 待读 | 阅读中 | 已读 | 重要 |
        |------|--------|------|------|
        | 5    | 1      | 3    | 2    |

        **论文分组** (1 个)
        - rl-placement-papers (5 篇)

        仪表盘已更新 → .paper-agent/README.md
```

### 情感曲线
- 触点：首次接触 workspace 概念
- 情感：好奇（"这些文件是干什么的？"）→ 理解（看到仪表盘）→ 安心（"随时能打开看"）
- 痛点：无——初始化由 setup 自动完成

---

## 旅程 2：每日阅读流程（阅读状态管理）

```
You: /start-my-day

Claude: [调用 paper_collect(days=1)]
        [调用 paper_digest()]

        📋 今日推荐 5 篇高置信论文：
        1. RL-Placer: Deep RL for...  — 9.2
        2. GNN-Driven Routing...      — 8.7
        ...

        [自动更新 research-journal.md: "09:15 — 每日收集: 47 篇新增, 5 篇推荐"]

        要把哪些加入阅读队列？

You: 1 和 2 加到待读

Claude: [调用 paper_reading_status(
            paper_ids=["2603.04567", "2603.04321"],
            status="to_read"
        )]

        ✅ 已添加到阅读队列。

        [自动更新 reading-list.md: To Read +2]
        [自动更新 research-journal.md: "09:16 — 标记待读: RL-Placer, GNN-Routing"]

        你当前的阅读队列：
        🔴 To Read: 5 篇
        🟡 Reading: 1 篇
        🟢 Read: 3 篇

You: 开始看 RL-Placer

Claude: [调用 paper_reading_status("2603.04567", status="reading")]
        [调用 paper_show("2603.04567")]

        📄 RL-Placer: Deep RL for Chip Macro Placement
        ...

        [自动更新 reading-list.md: 从 To Read 移到 Reading]

You: 看完了，方法很不错但只在小规模上验证了

Claude: [调用 paper_reading_status("2603.04567", status="read")]
        [调用 paper_note_add("2603.04567",
            content="方法很不错但只在小规模上验证了"
        )]

        ✅ 已标记为已读，笔记已保存到 .paper-agent/notes/2603.04567.md

        [自动更新 reading-list.md: 从 Reading 移到 Read]
        [自动更新 notes/2603.04567.md: 新建笔记文件]
        [自动更新 research-journal.md: "09:30 — 读完 RL-Placer, 笔记: 方法不错但规模有限"]
```

### 情感曲线
- 触点：每日推荐 → 加入队列 → 阅读 → 标记完成 → 写笔记
- 情感：高效（"不用记住自己看了哪些"）→ 满足（"打开文件就看到进度"）
- 痛点：如果状态更新有延迟会困惑

---

## 旅程 3：引用链探索

```
You: 这篇 RL-Placer 引用了什么重要的工作？

Claude: [调用 paper_citations("2603.04567", direction="references")]

        RL-Placer 引用了 42 篇论文，其中高相关的：

        📚 关键引用（按相关度排序）：
        1. DREAMPlace (2019) — 解析 placement 基线
        2. Google's RL for Chip Design (2021) — RL placement 开创性工作
        3. ChipFormer (2025) — SAC + Transformer
        4. MaskPlace (2024) — DQN + 离散动作空间
        ...

        [自动创建/更新 citation-traces/rl-placement.md]

        要继续追踪哪篇的引用链？还是看谁引用了 RL-Placer？

You: 看看谁引用了 Google's RL for Chip Design

Claude: [调用 paper_citations("nature2021.chip", direction="citations")]

        被引用 387 次！高相关的后续工作：

        📚 后续工作：
        1. RL-Placer (2026) — 改进奖励函数
        2. DeepPlace (2024) — 端到端方法
        3. GraphPlace (2025) — GNN 状态表示
        ...

        [自动更新 citation-traces/rl-placement.md: 添加第二层引用]
        [自动更新 research-journal.md: "10:00 — 引用链探索: RL placement 方向"]

        引用链已保存到 .paper-agent/citation-traces/rl-placement.md
        你可以随时打开这个文件查看完整的引用关系。
```

### 情感曲线
- 触点：从一篇论文出发 → 追踪引用 → 发现关键工作 → 保存引用链
- 情感：发现（"原来这篇是从 Google 那篇发展来的"）→ 掌控（"引用链都记录下来了"）
- 痛点：引用数量太多时需要过滤策略

---

## 旅程 4：论文分组 & 基于集合的综述

```
You: 创建一个 "RL Placement" 的论文集合

Claude: [调用 paper_group_create("rl-placement",
            description="Survey on RL-based placement methods"
        )]

        ✅ 分组已创建：.paper-agent/collections/rl-placement.md

You: 把刚才引用链里的那几篇加进去

Claude: [调用 paper_group_add("rl-placement",
            paper_ids=["2603.04567", "nature2021.chip",
                       "2501.05678", "2401.09012", "2504.03456"]
        )]

        ✅ 已添加 5 篇到 "RL Placement" 分组。

        [自动更新 collections/rl-placement.md]
        [自动更新 collections/_index.md]

You: 基于这个集合写个 survey

Claude: [读取 .paper-agent/collections/rl-placement.md 获取论文列表]
        [调用 paper_batch_show(IDs)]

        正在基于 "RL Placement" 集合的 5 篇论文生成综述...

        ---
        # Reinforcement Learning for Chip Placement: A Survey
        ...
        ---

        [自动更新 research-journal.md: "14:00 — 基于 rl-placement 集合生成综述"]
```

### 情感曲线
- 触点：创建集合 → 添加论文 → 基于集合做分析/综述
- 情感：有序（"终于能分类管理了"）→ 高效（"直接基于集合写 survey"）
- 痛点：手动逐篇添加繁琐——需要支持批量添加

---

## 旅程 5：跨会话上下文恢复

```
=== 新的一天，打开 Claude Code ===

You: 继续昨天的 RL placement survey

Claude: [读取 .paper-agent/research-journal.md]
        [读取 .paper-agent/collections/rl-placement.md]

        我看到你昨天在做 RL Placement 方向的综述：
        - 集合 "rl-placement" 有 5 篇论文
        - 昨天生成了综述草稿
        - 你还标记了 3 篇待读论文

        要继续哪个？
        a) 扩充集合（搜索更多论文加入）
        b) 修改综述草稿
        c) 继续阅读队列里的论文

You: 先搜点新论文加进去

Claude: [调用 paper_search_online("RL chip placement", sources=["arxiv", "s2"])]
        ...
```

### 情感曲线
- 触点：新会话开始 → AI 自动恢复上下文
- 情感：惊喜（"它还记得我昨天在干什么！"）→ 信任（"不用重复说了"）
- 痛点：如果 journal 太大导致恢复变慢

---

## 旅程 6：直接编辑 Workspace 文件

```
（研究员直接在 IDE 打开 .paper-agent/reading-list.md，手动修改状态）

You: 我刚才手动把几篇论文从 To Read 改成 Read 了，帮我同步一下

Claude: [调用 paper_workspace_sync()]

        检测到 reading-list.md 有手动修改：
        - 2603.04567: to_read → read（已同步到数据库）
        - 2501.05678: to_read → read（已同步到数据库）

        ✅ Workspace ↔ 数据库已同步。
```

---

## 旅程 7：按标题精确查找 + 下载

```
You: 帮我找一下 "Attention Is All You Need" 这篇论文

Claude: [调用 paper_find_and_download(title="Attention Is All You Need")]

        ✅ 找到了！

        **Attention Is All You Need**
        - Authors: Ashish Vaswani, Noam Shazeer, et al.
        - Source: Semantic Scholar → arXiv:1706.03762
        - 已保存到本地库

        📥 PDF 已下载：papers/1706.03762_Attention_Is_All_You_Need.pdf

        要深入分析这篇吗？
```

### 情感曲线
- 触点：用户知道标题但不知道 arXiv ID → 直接给标题 → 全自动
- 情感：懒得查（"我就知道名字"）→ 惊喜（"直接就找到并下载了"）→ 信赖
- 痛点：标题不精确时可能匹配失败，需要提示用 `paper_search_online`

---

## 错误恢复

| 错误场景 | 用户看到什么 | 恢复路径 |
|---------|------------|---------|
| Workspace 目录被删 | AI 检测到目录不存在 | MCP 工具自动 auto-init 重建 |
| journal 文件损坏 | AI 读取失败 | 通过 `rebuild_all()` 从数据库重建 |
| reading-list 与数据库不一致 | AI 检测到差异 | MCP 工具自动从 DB 重新生成文件 |
| 笔记文件被意外删除 | 数据库中笔记仍在 | 从数据库重建 notes/ 目录 |
| S2 API 调用失败 | 引用链查询超时 | 重试 + 降级提示"稍后再试" |

---

## 每日场景时间线

```
08:00  /start-my-day
       → 三源并行采集 → 推荐 5 篇 → 标记 2 篇待读
       → journal 自动记录, reading-list 自动更新

08:15  "开始看第一篇"
       → 状态变为 reading → 展示详情 → 阅读

08:40  "看完了，方法不错但数据集太小"
       → 状态变为 read → 笔记保存到 notes/
       → journal 记录

09:00  "这篇引用了什么重要工作？"
       → 引用链追踪 → citation-traces/ 更新

09:30  "把这些整理成一个集合"
       → 创建 collection → 批量添加
       → collections/ 更新

14:00  "基于这个集合做 survey"
       → 读取 collection → paper_batch_show → 生成综述
       → journal 记录

15:00  "帮我找一下 DREAMPlace 那篇论文，下载一下"
       → paper_find_and_download("DREAMPlace...") → S2 匹配 → 入库 + PDF 下载

=== 次日 ===

08:00  "继续昨天的工作"
       → AI 读取 journal + collections → 恢复上下文
       → "你昨天在做 RL Placement 综述，要继续吗？"
```
