# Paper Agent Features

**Title:** Paper Agent Feature View Derived from Design
**Version:** v01
**Status:** Draft
**Owner:** Paper Agent Team
**Last Updated:** 2026-03-10

## Related Documents
- [Requirements](./requirement.md)
- [Specification](./spec.md)
- [Design](./design.md)
- [MVP](./mvp.md)

---

## 1. Purpose

This document is the **feature view derived from the technical design**. It is not an independent product ideation document. Instead, it translates the architecture and components defined in [Design](./design.md) into user-visible and system-visible feature capabilities.

Document relationship in v01:
- **Requirements** define why the system exists and what problems it solves.
- **Specification** defines the required functional behaviors and acceptance criteria.
- **Design** defines the architecture, components, data flow, and technical realization.
- **Feature** extracts the feature-facing view from the design, grouping technical capabilities into coherent product/system features.
- **MVP** selects the subset of those features for the first release.

In other words: **this document goes from design to feature**, not the other way around.

## 2. How to Read This Document

Each feature in this document is mapped from concrete design elements such as services, adapters, managers, storage components, and CLI interfaces. For each feature area, this document answers:
- which design components enable it,
- what capability becomes visible externally,
- what operational value it provides,
- and what boundaries apply in v01.

## 3. Design-to-Feature Mapping Principles

The feature extraction follows these rules:

1. **One feature may span multiple components.**
   For example, daily digest is enabled by collection, filtering, reporting, storage, and delivery components together.

2. **Features are grouped by external capability, not code structure.**
   Users care about “daily digest” more than `DigestGenerator` vs `DeliveryManager`.

3. **The design remains the source of truth for realization.**
   This document summarizes and organizes capabilities; it does not override the design.

4. **The specification remains the source of truth for behavior.**
   Detailed inputs, outputs, flows, and acceptance criteria live in [Specification](./spec.md).

## 4. Feature Extraction from Design

### 4.1 Feature: CLI Command Surface

**Derived from design components:**
- CLI Layer in `design.md`
- `CommandParser`
- `OutputFormatter`
- `ErrorHandler`
- `ProgressIndicator`

**Feature capability:**
Paper Agent exposes a unified command-line interface for collection, filtering, search, reporting, configuration, and export.

**What becomes visible to users:**
- a single entrypoint for all operations,
- human-readable output for interactive use,
- JSON output for automation,
- consistent errors and progress feedback.

**Why this is a feature:**
The CLI is not only an implementation interface; it is the primary product surface for both researchers and automation agents.

**Boundary in v01:**
- CLI-first is mandatory.
- GUI is out of scope.
- Interactive and scriptable usage are both supported.

### 4.2 Feature: Configurable Paper Source Ingestion

**Derived from design components:**
- Collection Service
- `SourceAdapter`
- `ArxivAdapter`
- `ConferenceAdapter`
- `CollectionManager`
- `ConfigManager`
- Storage Layer

**Feature capability:**
The system can ingest papers from configured upstream sources and normalize them into a unified local library.

**What becomes visible to users:**
- source configuration,
- scheduled or manual collection,
- normalized metadata records,
- deduplication across repeated imports.

**Why this is a feature:**
The value is not the adapter pattern itself; the value is that users can rely on one ingestion workflow across multiple paper sources.

**Boundary in v01:**
- arXiv is the primary supported source.
- conference ingestion is designed as an extensible capability.
- manual addition is part of the same ingestion feature family.

### 4.3 Feature: Unified Local Paper Library

**Derived from design components:**
- Storage Layer
- SQLite schema
- paper record model
- collection log
- indexing strategy

**Feature capability:**
All collected papers are stored in a structured local library that can be queried, updated, and reused offline for most read operations.

**What becomes visible to users:**
- persistent paper memory,
- consistent metadata structure,
- topic and relevance annotations stored with papers,
- local-first retrieval behavior.

**Why this is a feature:**
Without this library, collection would be transient and reports/search would not compose into a long-term workflow.

**Boundary in v01:**
- metadata-first, not PDF-first,
- local storage over cloud-first architecture,
- paper records are the central unit of reuse.

### 4.4 Feature: Semantic Relevance Scoring

**Derived from design components:**
- Filtering Service
- `LLMProvider`
- `OpenAIProvider`
- `AnthropicProvider`
- `FilteringManager`
- `PromptBuilder`
- LLM cache in storage

**Feature capability:**
The system can evaluate each collected paper against a configured research-interest profile and produce a relevance signal.

**What becomes visible to users:**
- personalized paper ranking,
- relevant vs non-relevant categorization,
- reusable relevance score for digest and search workflows,
- reduced manual triage effort.

**Why this is a feature:**
This is the core intelligence layer that converts raw paper streams into personalized research value.

**Boundary in v01:**
- scoring is based primarily on title and abstract,
- LLM provider abstraction exists in design,
- caching and batch processing are part of the feature’s operational viability.

### 4.5 Feature: Topic Classification and Research Structuring

**Derived from design components:**
- Filtering Service
- `classify_topics` in `LLMProvider`
- `FilteringManager`
- topic fields in storage

**Feature capability:**
The system can assign topic labels to papers so that downstream browsing, reporting, and library analysis become structured by research area.

**What becomes visible to users:**
- topic-tagged papers,
- better grouping in digests and reports,
- more useful filtering and statistics.

**Why this is a feature:**
This transforms a flat paper list into an organized research corpus.

**Boundary in v01:**
- topic labels are lightweight metadata,
- not a full ontology-management system,
- user override and taxonomy control are secondary concerns relative to automated tagging.

### 4.6 Feature: Daily Digest Generation

**Derived from design components:**
- `WorkflowOrchestrator`
- Filtering Service
- Reporting Service
- `DigestGenerator`
- `ReportFormatter`
- `DeliveryManager`
- Scheduler

**Feature capability:**
The system can compile newly relevant papers into a daily digest artifact for routine researcher review.

**What becomes visible to users:**
- top relevant papers for the day,
- digest summaries and counts,
- ranked outputs that condense collection and filtering results,
- repeatable daily review workflow.

**Why this is a feature:**
The digest is one of the most direct expressions of value from the full pipeline.

**Boundary in v01:**
- generated from collected and filtered papers,
- formatting and delivery may vary,
- file-based output is the baseline delivery mode.

### 4.7 Feature: Topic Report Generation

**Derived from design components:**
- Reporting Service
- `TopicReportGenerator`
- Search Service
- LLMProvider support for clustering/insight extraction
- `ReportFormatter`

**Feature capability:**
The system can generate a deeper synthesized report over a selected topic and time range.

**What becomes visible to users:**
- clustered papers by subtopic,
- key-paper identification,
- extracted trends and insights,
- reusable topic snapshots.

**Why this is a feature:**
It elevates the system from daily paper triage to deeper literature understanding.

**Boundary in v01:**
- report generation depends on the quality of search and topic metadata,
- report depth is configurable in design,
- this is a synthesis feature rather than a raw retrieval feature.

### 4.8 Feature: Library Search and Retrieval

**Derived from design components:**
- Search Service
- `SearchEngine`
- `SearchIndexer`
- Storage Layer
- FTS5 search support
- ranking logic

**Feature capability:**
Users and agents can search the local paper library and retrieve relevant paper records efficiently.

**What becomes visible to users:**
- keyword and semantic-style retrieval,
- ranked search results,
- paper detail lookup,
- library statistics and reusable query workflows.

**Why this is a feature:**
Collection only creates value if prior papers can later be found and reused quickly.

**Boundary in v01:**
- fast local retrieval is central,
- search quality depends on indexing and available metadata,
- deeper semantic retrieval may evolve further in later versions.

### 4.9 Feature: Method-Similarity Paper Discovery

**Derived from design components:**
- `MethodologyExtractor`
- `SearchEngine` (method-similarity search mode)
- `LLMProvider` (methodology extraction)
- Storage Layer (methodology_tags_json)

**Feature capability:**
The system can find papers that use similar methods or techniques, given a paper or a method description as input.

**What becomes visible to users:**
- method-aware paper search,
- methodology tags on papers,
- ranked results by method similarity rather than topic overlap,
- ability to discover cross-domain papers that share the same technique.

**Why this is a feature:**
Researchers often need to find papers using similar approaches regardless of application domain. Topic-based search misses these cross-domain connections.

**Boundary in v01:**
- method extraction is based on title and abstract, not PDF full text,
- methodology tags are lightweight structured metadata,
- method similarity ranking may use LLM-assisted matching.

### 4.10 Feature: Objective-Based Paper Discovery

**Derived from design components:**
- `ObjectiveExtractor`
- `SearchEngine` (objective-based search mode)
- `LLMProvider` (objective extraction)
- Storage Layer (research_objectives_json)

**Feature capability:**
The system can find papers that address similar research objectives or problems, regardless of the methods they use.

**What becomes visible to users:**
- objective-aware paper search,
- research objective tags on papers,
- cross-method results for the same research goal,
- ability to see how different approaches tackle the same problem.

**Why this is a feature:**
When a researcher has a specific problem to solve, they need to see all approaches to that problem, not just papers using the same method. This orthogonal dimension complements method-similarity search.

**Boundary in v01:**
- objective extraction is based on title and abstract,
- objective tags are lightweight structured metadata,
- method and objective are orthogonal dimensions that can be queried independently or combined.

### 4.11 Feature: Literature Survey Generation

**Derived from design components:**
- `SurveyGenerator`
- `MethodologyExtractor`
- `ObjectiveExtractor`
- `SearchEngine`
- `LLMProvider` (taxonomy building, comparative analysis, gap identification)
- `ReportFormatter`
- `DeliveryManager`
- Storage Layer (surveys table)

**Feature capability:**
The system can generate a structured literature survey that goes beyond topic reports by including problem definition, method taxonomy, comparative analysis, research gap identification, and future direction suggestions.

**What becomes visible to users:**
- structured survey artifacts,
- method taxonomy with categorized approaches,
- comparative analysis across methods,
- identified research gaps and opportunities,
- future direction suggestions,
- reusable survey that can be consumed by agents.

**Why this is a feature:**
A survey provides deeper analytical value than a topic report. It helps researchers build systematic understanding of a field, identify what has been done and what remains open, and serves as a starting point for research writing.

**Boundary in v01:**
- survey generation depends on sufficient papers and method diversity in the local library,
- survey depth is higher than topic report but is still an assistive tool, not a publication-ready paper,
- survey is a distinct artifact type that coexists with topic reports.

### 4.12 Feature: Context-Aware Automation Support

**Derived from design components:**
- Search Service
- `ContextExtractor`
- CLI Layer JSON mode
- configuration via files and environment variables
- scriptability conventions

**Feature capability:**
Automation tools can query Paper Agent using code, files, or working-context signals and receive structured machine-readable output.

**What becomes visible to users and agents:**
- `--json` responses,
- context-derived queries,
- predictable automation behavior,
- compatibility with Cursor/Codex-style workflows.

**Why this is a feature:**
This is the bridge between research knowledge and downstream coding or planning systems.

**Boundary in v01:**
- CLI-based automation is primary,
- stable output structure matters more than a broad integration surface,
- file and code context extraction are enablers rather than standalone products.

### 4.10 Feature: Export and Delivery Interfaces

**Derived from design components:**
- `ReportFormatter`
- `DeliveryManager`
- Export Handlers
- `ExportManager`

**Feature capability:**
The system can materialize papers, digests, and reports into external representations suitable for human consumption or downstream tools.

**What becomes visible to users:**
- markdown/html/pdf/text exports,
- file output for persistent use,
- webhook/email style delivery paths where enabled,
- export of paper records to formats such as JSON/CSV/BibTeX.

**Why this is a feature:**
Generated knowledge only becomes useful when it can be consumed outside the internal runtime.

**Boundary in v01:**
- file-based outputs are fundamental,
- richer delivery paths may be staged over time,
- export breadth should not dilute the core collection/filter/search loop.

## 5. Feature Grouping by User Value

The design-derived features can be regrouped into user-facing value bands:

### Band A: Build the library
- Configurable Paper Source Ingestion
- Unified Local Paper Library

### Band B: Make the library intelligent
- Semantic Relevance Scoring
- Topic Classification and Research Structuring
- Method-Similarity Paper Discovery
- Objective-Based Paper Discovery

### Band C: Turn intelligence into outputs
- Daily Digest Generation
- Topic Report Generation
- Literature Survey Generation
- Export and Delivery Interfaces

### Band D: Make it operationally usable
- CLI Command Surface
- Library Search and Retrieval
- Context-Aware Automation Support

## 6. Traceability Back to Design

The following design sections are the primary source for this document:
- Architecture overview and principles in `docs/v01/design.md`
- Component design for CLI, application, collection, filtering, reporting, search, methodology extraction, objective extraction, survey generation, storage, and export
- Data flow sections for collection, search, and report generation
- LLM integration strategy
- automation integration section

This feature view should be read as a **capability projection of the design**, not as a replacement for it.

## 7. Traceability Forward to MVP

The [MVP](./mvp.md) document should select from these design-derived features:
- which ones are required for first release,
- which ones are simplified,
- which ones are deferred,
- and what minimum acceptance bar is needed to preserve end-user value.

## 8. Summary

Paper Agent v01 design implies a coherent feature set centered on seven system outcomes:
- collect papers reliably,
- store them in a reusable local library,
- rank and organize them intelligently (by topic, method, and objective),
- discover related papers through method similarity and objective similarity,
- generate digest/report/survey artifacts,
- synthesize literature surveys with method taxonomy, comparative analysis, and gap identification,
- and expose the entire workflow to humans and automation agents through a CLI-first interface.

The feature document therefore exists to make the design legible as a product/system capability map.

---

**Next Steps:** Use [MVP](./mvp.md) to decide which design-derived features are mandatory for the first release.
