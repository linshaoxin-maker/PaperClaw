# Paper Agent v01_source Feature Doc

**Version:** v01_source
**Status:** Draft
**Last Updated:** 2026-03-12

[Note] This document derives capabilities from `docs/v01_source/spec.md` and `docs/v01_source/design.md`, and references the base v01 feature set in `docs/v01/feature.md`.

---

## 1. Feature Overview

v01_source introduces four externally visible capability groups:

1. **Profile** (interest onboarding + iteration)
2. **Sources** (source registry + management)
3. **Multi-source Collect** (arXiv + OpenReview + DBLP + ACL Anthology)
4. **Config** (command-driven configuration for profile/sources)

---

## 2. Feature Groups

### 2.1 Profile

#### F-SRC-PRO-01 Profile create (guided)
- What: guided creation of topics/keywords with multiple entry points
- Why: reduce init burden and improve interest signal quality
- Primary commands:
  - `paper-agent profile create`
- Maps to requirements:
  - FR-SRC-02
- Maps to design components:
  - `ProfileManager`

#### F-SRC-PRO-02 Profile-driven source recommendation
- What: recommend a set of sources based on chosen template/topics
- Primary surface:
  - final step of `profile create`
- Maps to requirements:
  - FR-SRC-04
- Design:
  - `SourceRegistry.recommend(profile)`

---

### 2.2 Sources

#### F-SRC-SRC-01 Source registry (built-in + custom)
- What: list/show built-in sources and custom user-defined ones
- Primary commands:
  - `paper-agent sources list`
  - `paper-agent sources show <id>`
  - `paper-agent sources add`
- Requirement mapping:
  - FR-SRC-03, FR-SRC-06
- Design mapping:
  - `SourceRegistry`

#### F-SRC-SRC-02 Enable/disable sources
- What: persistently enable/disable sources
- Primary commands:
  - `paper-agent sources enable <id...>`
  - `paper-agent sources disable <id...>`
- Requirement mapping:
  - FR-SRC-06
- Design mapping:
  - user override layer for SourceRegistry

---

### 2.3 Multi-source Collect

#### F-SRC-COL-01 Collect from arXiv
- What: collect and store papers from arXiv categories
- Adapter:
  - `ArxivAdapter`
- Requirement mapping:
  - FR-SRC-05

#### F-SRC-COL-02 Collect from OpenReview
- What: collect and store papers from OpenReview venues
- Adapter:
  - `OpenReviewAdapter`
- Requirement mapping:
  - FR-SRC-05

#### F-SRC-COL-03 Collect from DBLP
- What: collect and store papers from DBLP venue keys
- Adapter:
  - `DBLPAdapter`
- Requirement mapping:
  - FR-SRC-05

#### F-SRC-COL-04 Collect from ACL Anthology
- What: collect and store papers from ACL Anthology venues
- Adapter:
  - `ACLAnthologyAdapter`
- Requirement mapping:
  - FR-SRC-05

#### F-SRC-COL-05 Deduplication by canonical_key
- What: prevent duplicates across repeated runs and sources
- Implementation anchor:
  - `Paper.canonical_key` + SQLite unique constraint
- Requirement mapping:
  - FR-SRC-05

#### F-SRC-COL-06 Partial failure and recovery
- What: one source failure does not abort others; structured error summary
- Requirement mapping:
  - FR-SRC-08

---

### 2.4 Config

#### F-SRC-CFG-01 LLM-only init
- What: init only requires LLM fields; profile fills interest and sources
- Commands:
  - `paper-agent init`
  - `paper-agent profile create`
- Requirement mapping:
  - FR-SRC-01

#### F-SRC-CFG-02 Command-driven configuration
- What: allow setting profile/sources through CLI (avoid manual YAML edits)
- Commands:
  - `paper-agent config ...` (extension / alias)
  - `paper-agent sources config`
- Requirement mapping:
  - FR-SRC-07

---

## 3. MVP Feature Scope Pointer

See `docs/v01_source/mvp.md` for the committed first-release scope.
