# Paper Agent v01_source MVP Scope

**Version:** v01_source
**Status:** Draft
**Last Updated:** 2026-03-12

This document defines the MVP scope for the v01 Source/Profile extension.

Base MVP (v01) is defined in `docs/v01/mvp.md`. This MVP is an **add-on** and focuses on shipping Source/Profile + multi-source collection.

---

## 1. MVP Goals

### MVP-G1: Init decoupled from interests
- `paper-agent init` becomes **LLM-only** infrastructure setup.
- User can finish init without providing topics/keywords/sources.

### MVP-G2: Guided Profile creation
- Provide `paper-agent profile create` to generate and save:
  - `topics`
  - `keywords`
- Show recommended sources and let user enable/disable before saving.

### MVP-G3: Multi-source collection is real (not stubbed)

MVP must implement **actual fetch + parse + store** for all of:

- arXiv
- OpenReview
- DBLP
- ACL Anthology

This is a hard requirement.

### MVP-G4: Source management CLI
- Provide `paper-agent sources ...` commands to list/show/enable/disable sources.

---

## 2. Included Sources (MVP)

### 2.1 Conferences / venues (given by user)

MVP must cover at least the following venue set through appropriate sources:

- NeurIPS
- ICLR
- ICML
- AAAI
- IJCAI
- ACL
- EMNLP
- NAACL

Notes:
- OpenReview mainly covers: NeurIPS / ICLR / ICML.
- DBLP can cover: AAAI / IJCAI (and also many others).
- ACL Anthology covers: ACL / EMNLP / NAACL.

### 2.2 arXiv

- Continue supporting arXiv categories collection.
- Profile recommendation should propose relevant arXiv categories for typical ML/NLP/IR areas.

---

## 3. MVP Deliverables

### 3.1 CLI Deliverables

- `paper-agent init` (LLM-only)
- `paper-agent profile create`
- `paper-agent sources list`
- `paper-agent sources show <id>`
- `paper-agent sources enable <id...>`
- `paper-agent sources disable <id...>`

Optional in MVP:
- `paper-agent sources add` (custom sources, config-only)
- `paper-agent sources config --print/--set`

### 3.2 Data ingest deliverables

- Adapters:
  - `ArxivAdapter`
  - `OpenReviewAdapter`
  - `DBLPAdapter`
  - `ACLAnthologyAdapter`

- Storage:
  - `Paper.source_name` and `Paper.canonical_key` must be correctly populated
  - Deduplication must work across repeated runs per source

### 3.3 Reliability deliverables

- Multi-source collect must be partial-failure tolerant:
  - one source failing does not block other sources
  - CLI output includes per-source error summary

---

## 4. MVP Out of Scope

Explicitly not required for MVP:

- PapersWithCode / Semantic Scholar integration
- Cross-source merge beyond canonical_key (DOI/title fuzzy merge)
- Citation graph exploration
- Full-text PDF download and parsing
- GUI / web UI
- Complex editor integration for config (auto-open editor)
- Advanced scheduling / background daemons

---

## 5. Acceptance Checklist (MVP)

- [ ] A fresh user can run `paper-agent init` without providing topics/keywords/sources.
- [ ] The user can run `paper-agent profile create` to save topics/keywords.
- [ ] The user can list and enable/disable sources via `paper-agent sources ...`.
- [ ] The user can run `paper-agent collect` and it will fetch+store from:
  - [ ] arXiv
  - [ ] OpenReview
  - [ ] DBLP
  - [ ] ACL Anthology
- [ ] A failure in one adapter does not stop others; output includes error summary.
