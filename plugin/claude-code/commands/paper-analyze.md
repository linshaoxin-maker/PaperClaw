---
description: Generate a structured deep-analysis note for a specific paper
argument-hint: <paper_id or arxiv_id>
allowed-tools: [
  "mcp__plugin_paper-agent_paper-agent__paper_show",
  "mcp__plugin_paper-agent_paper-agent__paper_search",
  "Bash",
  "Read",
  "Write"
]
---

# Paper Analyze

Generate a structured deep-analysis note for a paper.

## Process

1. Parse $ARGUMENTS as `paper_id` (e.g., `2301.12345` or `arxiv:2301.12345`)
2. Call `paper_show(paper_id)` to get full paper details
3. If not found, try `paper_search(query=$ARGUMENTS)` and pick the best match
4. Generate a structured analysis note in Chinese

## Analysis Note Template

```markdown
---
date: "YYYY-MM-DD"
paper_id: "arXiv:XXXX.XXXXX"
title: "论文标题"
authors: "作者列表"
domain: "[领域]"
tags:
  - 论文笔记
  - [领域标签]
quality_score: "[X.X]/10"
status: analyzed
---

# [论文标题]

## 核心信息
| 字段 | 值 |
|------|---|
| arXiv ID | ... |
| 作者 | ... |
| 发布时间 | ... |

## 摘要翻译
[中文翻译]

## 方法概述
### 核心思想
### 方法框架
### 各模块详细说明

## 实验结果
### 主要结果
### 消融实验

## 深度分析
### 研究价值评估
### 方法优势详解
### 局限性分析
### 适用场景

## 与相关论文对比

## 未来工作建议

## 我的笔记
%% 用户可在此添加个人阅读笔记 %%
```

## Image Extraction (Optional)

If the user wants figures from the paper:

```bash
curl -L "https://arxiv.org/e-print/[PAPER_ID]" -o /tmp/paper_analysis/source.tar.gz
mkdir -p /tmp/paper_analysis/extracted
tar -xzf /tmp/paper_analysis/source.tar.gz -C /tmp/paper_analysis/extracted/
# Look for image files in: pics/ figures/ fig/ images/ img/
```
