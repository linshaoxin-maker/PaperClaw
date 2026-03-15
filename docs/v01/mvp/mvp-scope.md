# Paper Agent MVP

**Title:** Paper Agent Minimum Viable Product Definition
**Version:** v01
**Status:** Draft
**Owner:** Paper Agent Team
**Last Updated:** 2026-03-10

## Related Documents
- [Requirements](./requirement.md)
- [Feature](./feature.md)
- [Specification](./spec.md)
- [Design](./design.md)

---

## 1. MVP Overview

The MVP focuses on delivering core value to AI researchers: automated paper collection, intelligent filtering, and daily digests. The goal is to validate the concept and gather user feedback before building advanced features.

### MVP Goals

1. **Validate Core Value:** Prove that LLM-based filtering saves researchers time
2. **Establish Foundation:** Build solid architecture for future features
3. **Enable Automation:** Provide CLI and JSON output for Cursor/Codex integration
4. **Gather Feedback:** Learn what features users need most

### MVP Timeline

- **Development:** 6-8 weeks
- **Alpha Testing:** 2 weeks
- **Beta Release:** 4 weeks
- **Public Release:** v0.1.0

## 2. MVP Scope

### 2.1 Features Included

#### ✅ Feature Group A: Paper Collection (Simplified)

**A1: arXiv Paper Collection**
- Collect from user-specified arXiv categories
- Daily automated collection
- Basic rate limiting and error handling
- **Simplification:** Start with 5 most popular categories (cs.AI, cs.LG, cs.CL, cs.CV, cs.NE)

**A3: Manual Paper Addition**
- Add papers by arXiv ID only
- **Simplification:** DOI and URL support deferred to v0.2

**Not in MVP:**
- ❌ A2: Conference paper collection (deferred to v0.2)

#### ✅ Feature Group B: Semantic Filtering (Core)

**B1: Interest Profile Configuration**
- Configure topics and keywords via CLI
- Simple YAML configuration file
- **Simplification:** No author preferences in MVP

**B2: LLM-Based Semantic Filtering**
- OpenAI GPT-4 or Anthropic Claude for relevance scoring
- Batch processing for efficiency
- Response caching to reduce costs
- **Simplification:** Single LLM provider (user choice), local models deferred

**B3: Topic Classification**
- Automatic topic tagging
- **Simplification:** Use predefined topic taxonomy (no emergent topics)

#### ✅ Feature Group C: Daily Digest (Core)

**C1: Digest Compilation**
- Generate daily digest with top 10 papers
- Markdown format only
- **Simplification:** Fixed format, no customization

**C2: Digest Delivery**
- Save to local file
- **Simplification:** Email and webhook delivery deferred to v0.2

#### ✅ Feature Group E: Searchable Library (Basic)

**E1: Semantic Search**
- Keyword-based search with SQLite FTS5
- Basic relevance ranking
- **Simplification:** Pure semantic search (embeddings) deferred to v0.2

**E2: Paper Details View**
- Display full paper metadata
- **Simplification:** No related papers feature

**E3: Library Statistics**
- Basic statistics (total papers, by topic, by date)
- **Simplification:** Text output only, no visualizations

#### ✅ Feature Group F: Automation Integration (Core)

**F1: CLI Interface**
- Essential commands only:
  - `paper-agent init` - Initialize configuration
  - `paper-agent config` - Configure interests
  - `paper-agent collect` - Run collection
  - `paper-agent digest` - Generate digest
  - `paper-agent search <query>` - Search library
  - `paper-agent show <id>` - Show paper details
  - `paper-agent stats` - Show statistics

**F2: JSON Output Mode**
- All commands support `--json` flag
- **Simplification:** Basic JSON structure, no pagination

**F4: Configuration Management**
- YAML configuration files
- Environment variables for API keys
- **Simplification:** Single config file, no per-source configuration

**Not in MVP:**
- ❌ F3: Context-aware queries (deferred to v0.2)
- ❌ F5: Batch operations (deferred to v0.2)

### 2.2 Features Deferred

#### 🔄 Deferred to v0.2
- Conference paper collection
- Multiple LLM providers
- Local LLM support
- Context-aware queries for Cursor
- Email and webhook delivery
- Batch operations
- DOI and URL paper addition
- Related papers feature
- Advanced search (embeddings)
- Method-similarity paper discovery (FR-14)
- Objective-based paper discovery (FR-15)

#### 🔄 Deferred to v0.3+
- Topic reports (Feature Group D)
- Literature survey generation (FR-16)
- PDF full-text analysis
- Citation network analysis
- Export to reference managers
- Collaborative features
- Browser extension
- API endpoints (REST/GraphQL)

## 3. MVP Architecture Simplifications

### 3.1 Technology Stack

**Core:**
- Python 3.9+
- Click for CLI
- SQLite for storage
- Requests for HTTP
- OpenAI or Anthropic SDK

**Optional:**
- Rich for terminal output
- PyYAML for configuration
- Schedule for automation

### 3.2 Simplified Components

#### Storage Layer
- Single SQLite database
- No vector embeddings
- Basic FTS5 search only
- Simplified schema (fewer indexes)

#### LLM Integration
- Single provider (user configures OpenAI or Anthropic)
- Simple prompt templates (no few-shot learning)
- Basic caching (in-memory, not persistent)
- No fallback providers

#### Collection Service
- arXiv only (no conferences)
- Single-threaded collection
- Basic error handling (log and continue)
- No retry logic for failed papers

#### Search Service
- Keyword search only (FTS5)
- Simple ranking (TF-IDF)
- No semantic embeddings
- No query expansion

### 3.3 Deployment

**MVP Distribution:**
- PyPI package only
- No standalone binaries
- No Docker image
- Manual installation and setup

## 4. MVP User Flows

### 4.1 First-Time Setup

```bash
# Install
pip install paper-agent

# Initialize
paper-agent init
# Prompts for:
# - LLM provider (OpenAI or Anthropic)
# - API key
# - Data directory

# Configure interests
paper-agent config
# Prompts for:
# - Research topics (free text)
# - Keywords (comma-separated)
# - arXiv categories (select from list)
# - Relevance threshold (1-10)

# Run first collection
paper-agent collect
# Collects papers from last 7 days
# Filters based on interests
# Shows progress and summary
```

### 4.2 Daily Usage

```bash
# View today's digest (auto-generated)
cat ~/.paper-agent/digests/digest-2026-03-10.md

# Search for specific topic
paper-agent search "vision transformers"

# View paper details
paper-agent show <paper-id>

# Check library statistics
paper-agent stats
```

### 4.3 Automation Integration

```bash
# Cursor agent queries papers
paper-agent search "attention mechanisms" --json

# Returns JSON:
{
  "status": "success",
  "count": 15,
  "papers": [
    {
      "id": "uuid",
      "title": "Attention Is All You Need",
      "authors": ["Vaswani et al."],
      "abstract": "...",
      "url": "https://arxiv.org/abs/1706.03762",
      "relevance": 9.5
    }
  ]
}
```

## 5. MVP Acceptance Criteria

### 5.1 Functional Requirements

**Collection:**
- ✅ Collects papers from configured arXiv categories
- ✅ Runs automatically once per day
- ✅ Handles API errors without crashing
- ✅ Deduplicates papers already in library

**Filtering:**
- ✅ Filters papers with >85% precision (relevant papers)
- ✅ Processes 100 papers in <3 minutes
- ✅ Caches LLM responses to reduce costs
- ✅ Assigns topics to papers

**Digest:**
- ✅ Generates digest with 10 most relevant papers
- ✅ Digest includes title, authors, abstract, link, score
- ✅ Digest saved to file automatically
- ✅ Digest is readable and well-formatted

**Search:**
- ✅ Search returns results in <2 seconds for 1000 papers
- ✅ Results ranked by relevance
- ✅ Supports basic filters (date range)

**CLI:**
- ✅ All core commands work correctly
- ✅ Help text available for all commands
- ✅ JSON output mode works for all commands
- ✅ Error messages are clear and actionable

### 5.2 Non-Functional Requirements

**Performance:**
- ✅ CLI commands start in <500ms
- ✅ Search completes in <2 seconds
- ✅ Daily collection completes in <10 minutes

**Reliability:**
- ✅ Automated collection runs without manual intervention
- ✅ Handles network failures gracefully
- ✅ No data loss on crashes

**Usability:**
- ✅ First-time setup takes <10 minutes
- ✅ Configuration is intuitive
- ✅ Error messages help users fix problems

**Cost:**
- ✅ LLM API costs <$5/month for typical usage (50 papers/day)

### 5.3 Quality Gates

**Code Quality:**
- ✅ >70% test coverage
- ✅ All unit tests pass
- ✅ No critical security vulnerabilities
- ✅ Code follows PEP 8 style guide

**Documentation:**
- ✅ README with installation and usage
- ✅ CLI help text for all commands
- ✅ Configuration examples
- ✅ Troubleshooting guide

**Testing:**
- ✅ Manual testing of all user flows
- ✅ Integration tests for core workflows
- ✅ Alpha testing with 5+ users
- ✅ Beta testing with 20+ users

## 6. MVP Risks and Mitigation

### 6.1 Technical Risks

**Risk: LLM API costs too high**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Implement aggressive caching
  - Use cheaper models where possible
  - Set daily budget limits
  - Provide cost estimates to users

**Risk: arXiv API rate limits too restrictive**
- **Impact:** Medium
- **Probability:** Low
- **Mitigation:**
  - Implement client-side rate limiting
  - Spread collection over longer time window
  - Cache paper metadata aggressively

**Risk: Search performance degrades with large libraries**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Optimize SQLite queries
  - Add appropriate indexes
  - Test with 10k+ papers
  - Document performance limits

### 6.2 Product Risks

**Risk: Filtering precision too low (too many irrelevant papers)**
- **Impact:** High
- **Probability:** Medium
- **Mitigation:**
  - Iterate on prompt engineering
  - Allow users to adjust threshold
  - Collect feedback on false positives
  - Implement user feedback loop

**Risk: Users don't find value in daily digests**
- **Impact:** High
- **Probability:** Low
- **Mitigation:**
  - Alpha test with target users
  - Gather feedback on digest format
  - Allow customization of digest size
  - Provide alternative views (weekly, by topic)

**Risk: Automation integration too complex**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Provide clear examples
  - Test with actual Cursor/Codex workflows
  - Simplify JSON output format
  - Create integration guides

### 6.3 Schedule Risks

**Risk: Development takes longer than 8 weeks**
- **Impact:** Medium
- **Probability:** Medium
- **Mitigation:**
  - Prioritize ruthlessly (cut features if needed)
  - Use existing libraries where possible
  - Parallel development of independent components
  - Weekly progress reviews

## 7. Success Metrics

### 7.1 Launch Metrics (First Month)

- **Adoption:** 50+ active users
- **Retention:** 60% weekly active users
- **Engagement:** Average 5 commands per user per week
- **Satisfaction:** >4.0/5.0 user rating

### 7.2 Value Metrics

- **Time Saved:** Users report saving >20 minutes per day
- **Discovery:** Users discover papers they would have missed
- **Precision:** >85% of digest papers rated as relevant
- **Integration:** 20% of users integrate with automation tools

### 7.3 Technical Metrics

- **Performance:** 95% of searches complete in <2 seconds
- **Reliability:** 99% uptime for automated collection
- **Cost:** Average LLM API cost <$5/user/month
- **Quality:** <5 bugs per 100 users per month

## 8. MVP Roadmap

### Phase 1: Foundation (Weeks 1-2)
- Set up project structure
- Implement storage layer (SQLite)
- Implement configuration management
- Basic CLI framework

### Phase 2: Collection (Weeks 3-4)
- Implement arXiv adapter
- Implement collection manager
- Add scheduling for automated collection
- Test with real arXiv data

### Phase 3: Filtering (Weeks 5-6)
- Implement LLM provider (OpenAI/Anthropic)
- Implement filtering manager
- Add topic classification
- Optimize for cost and performance

### Phase 4: Search & Digest (Week 7)
- Implement search engine (FTS5)
- Implement digest generator
- Add CLI commands for search and digest
- Test end-to-end workflows

### Phase 5: Polish & Testing (Week 8)
- Add error handling and logging
- Write documentation
- Comprehensive testing
- Bug fixes and refinements

### Phase 6: Alpha Testing (Weeks 9-10)
- Deploy to 5-10 alpha testers
- Gather feedback
- Fix critical issues
- Iterate on UX

### Phase 7: Beta Release (Weeks 11-14)
- Public beta announcement
- Onboard 20+ beta users
- Monitor usage and errors
- Prepare for v0.1.0 release

## 9. Post-MVP Priorities

Based on user feedback, prioritize for v0.2:

1. **Conference paper collection** - If users request specific conferences
2. **Context-aware queries** - If automation integration is popular
3. **Method-similarity discovery** - Find papers using similar techniques across domains
4. **Objective-based discovery** - Find papers addressing the same research goal regardless of method
5. **Email delivery** - If users want push notifications
6. **Multiple LLM providers** - If cost or availability is an issue
7. **Topic reports** - If users want deeper analysis

Based on user feedback, prioritize for v0.3:

1. **Literature survey generation** - Generate structured surveys with method taxonomy, comparative analysis, research gap identification, and future directions
2. **Advanced search with embeddings** - Semantic retrieval beyond keyword matching

## 10. MVP Constraints

### What We Won't Compromise

- **Quality of filtering:** Must achieve >85% precision
- **Automation integration:** CLI and JSON output must work well
- **Performance:** Search must be fast (<2 seconds)
- **Reliability:** Daily collection must work without intervention

### What We Can Adjust

- **Feature scope:** Can defer features if needed
- **Supported sources:** Can start with fewer arXiv categories
- **Digest format:** Can simplify if needed
- **Configuration options:** Can reduce customization

## 11. Go/No-Go Criteria

### Go Criteria (Ready for Beta)

- ✅ All acceptance criteria met
- ✅ Alpha testers report positive feedback
- ✅ No critical bugs
- ✅ Documentation complete
- ✅ LLM costs within budget
- ✅ Performance targets met

### No-Go Criteria (Need More Work)

- ❌ Filtering precision <80%
- ❌ Critical bugs in core workflows
- ❌ Performance issues (search >5 seconds)
- ❌ LLM costs >$10/user/month
- ❌ Alpha testers don't find value

---

## Summary

The MVP focuses on delivering core value: automated paper collection from arXiv, intelligent LLM-based filtering, and daily digests. By simplifying scope and deferring advanced features, we can validate the concept quickly and gather user feedback to guide future development.

**Key MVP Features:**
- arXiv paper collection
- LLM-based semantic filtering
- Daily digest generation
- Basic search and library management
- CLI with JSON output for automation

**Key Simplifications:**
- arXiv only (no conferences)
- Single LLM provider
- Keyword search only (no embeddings)
- File delivery only (no email/webhooks)
- Basic CLI (no advanced features)
- No method-similarity or objective-based discovery (deferred to v0.2)
- No literature survey generation (deferred to v0.3)

**Success Criteria:**
- >85% filtering precision
- <$5/month LLM costs
- <2 second search performance
- 50+ active users in first month
- Positive user feedback

---

**Implementation:** Ready to begin development following the [Design](./design.md) document.
