# Paper Analysis Note Template

Use this template when generating deep analysis notes for papers.

## Frontmatter

```yaml
---
date: "YYYY-MM-DD"
paper_id: "arXiv:XXXX.XXXXX"
title: "论文标题"
authors: "Author1, Author2, ..."
domain: "[领域]"
tags:
  - 论文笔记
  - [领域标签]
quality_score: "[X.X]/10"
status: analyzed
---
```

## Note Structure

```markdown
# [论文标题]

## 核心信息

| 字段 | 值 |
|------|---|
| arXiv ID | XXXX.XXXXX |
| 作者 | Author List |
| 机构 | Affiliations |
| 发布时间 | YYYY-MM-DD |
| 链接 | https://arxiv.org/abs/XXXX.XXXXX |

## 摘要翻译

[Translate abstract to Chinese, preserve technical terms]

## 要点提炼

1. [Key point 1]
2. [Key point 2]
3. [Key point 3]

## 研究背景与动机

[Why this problem matters, what gap it fills]

## 方法概述

### 核心思想
[One-paragraph core idea]

### 方法框架
[Overall architecture description]

### 各模块详细说明
[Module-by-module breakdown]

## 实验结果

### 主要结果
[Key quantitative results with comparison to baselines]

### 消融实验
[Ablation study findings]

## 深度分析

### 研究价值评估
| 维度 | 评分 | 说明 |
|------|------|------|
| 创新性 | X/10 | ... |
| 实用性 | X/10 | ... |
| 可复现性 | X/10 | ... |
| 影响力 | X/10 | ... |

### 方法优势详解
[Detailed strengths]

### 局限性分析
[Honest limitations]

### 适用场景
[Where this method works best]

## 与相关论文对比

| 方法 | 优势 | 不足 |
|------|------|------|
| 本文方法 | ... | ... |
| 方法A | ... | ... |
| 方法B | ... | ... |

## 未来工作建议

1. [Direction 1]
2. [Direction 2]

## 我的笔记

%% 用户可在此添加个人阅读笔记 %%
```

## Image Extraction

When extracting figures from arXiv source:

1. Download source: `curl -L "https://arxiv.org/e-print/[ID]" -o source.tar.gz`
2. Extract: `tar -xzf source.tar.gz -C extracted/`
3. Search for image directories: `pics/`, `figures/`, `fig/`, `images/`, `img/`
4. Common formats: `.pdf`, `.png`, `.jpg`, `.eps`
5. Generate image index listing all found figures with captions
