<h1 align="center">PaperClaw</h1>

<p align="center">
  <strong>Your AI-powered research copilot.</strong><br>
  Collect, filter, search, analyze, compare, and survey academic papers — from the terminal or directly inside your IDE.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &nbsp;|&nbsp;
  <a href="#features">Features</a> &nbsp;|&nbsp;
  <a href="#ide-integration">IDE Integration</a> &nbsp;|&nbsp;
  <a href="#mcp-tools">MCP Tools</a> &nbsp;|&nbsp;
  <a href="#contributing">Contributing</a>
</p>

---

## Why PaperClaw?

Keeping up with research papers is exhausting. Every day, hundreds of new papers appear on arXiv, and manually checking, filtering, and organizing them wastes hours of productive research time.

**PaperClaw automates the boring parts**, so you can focus on what matters — reading and building.

- **Multi-source collection** — arXiv + DBLP + Semantic Scholar, parallel fetching, deduplication
- **LLM-powered filtering** — Scores every paper against your research interests using OpenAI or Anthropic
- **Daily digest** — One command for today's personalized recommendations, ranked by relevance
- **IDE-native via MCP** — Works inside Cursor and Claude Code as a first-class AI tool; search and analyze papers without leaving your editor
- **6 interactive research workflows** — Daily reading, deep dive, literature survey, citation exploration, paper triage, trend insights
- **Local-first** — SQLite database + plain markdown workspace; your data never leaves your machine
- **Workspace** — Reading lists, notes, paper groups, citation traces — all as plain markdown in `.paper-agent/`

## Quick Start

### Install

```bash
# Option 1: pipx (recommended, installs globally)
pipx install paper-agent

# Option 2: from source
git clone https://github.com/linshaoxin-maker/PaperClaw.git
cd PaperClaw
./install.sh
```

### Initialize

```bash
paper-agent init
```

The interactive wizard will ask for:
- **LLM provider** — `openai` or `anthropic`
- **API key** — for paper filtering and summarization
- **Research topics** — e.g. `retrieval-augmented generation, circuit design`
- **Keywords** — fine-grained filters like `transformer, GNN`
- **arXiv categories** — e.g. `cs.AI, cs.LG, cs.CL`

Config is saved to `~/.paper-agent/config.yaml`. Re-run `init` anytime to update.

<details>
<summary><strong>Non-interactive init (for scripts & CI)</strong></summary>

```bash
paper-agent init \
  --provider openai \
  --api-key "sk-xxx" \
  --base-url "https://api.custom.com" \
  --topics "RAG, circuit design" \
  --keywords "transformer, attention" \
  --sources "cs.AI, cs.LG"
```

You can also mix: `paper-agent init --api-key "sk-xxx"` sets the key and prompts for the rest interactively.

</details>

### Daily workflow

```bash
paper-agent collect -d 1      # Fetch yesterday's papers, LLM scores them
paper-agent digest             # View today's personalized recommendations
paper-agent show <paper-id>    # Dive into a specific paper
paper-agent search "GNN"       # Search your local library anytime
```

That's it. You're set up.

## Features

### CLI Commands

| Command | Description |
|---------|-------------|
| `paper-agent init` | Interactive setup (LLM provider, research topics, arXiv categories) |
| `paper-agent collect` | Fetch papers from arXiv + DBLP + Semantic Scholar with LLM scoring |
| `paper-agent digest` | Generate daily paper recommendations |
| `paper-agent search <query>` | Full-text search across your local paper library |
| `paper-agent show <paper-id>` | View paper details (abstract, score, links) |
| `paper-agent stats` | Library overview (total papers, score distribution, top topics) |
| `paper-agent config` | View current configuration |
| `paper-agent setup <ide>` | One-command IDE integration (see [IDE Integration](#ide-integration)) |

#### Collect options

| Flag | Description | Default |
|------|-------------|---------|
| `-d, --days N` | Fetch papers from the last N days | 7 |
| `-m, --max N` | Max papers per arXiv category | 200 |
| `--no-filter` | Collect only, skip LLM scoring | off |

### Interactive REPL

Run `paper-agent` without arguments to enter interactive mode:

```
paper> collect -d 3
paper> digest
paper> search transformer
paper> show 1            # Use result index directly, no need to copy IDs
paper> stats
paper> quit
```

### JSON Output

All commands support `--json` for scripting and automation:

```bash
paper-agent digest --json
paper-agent search "LLM" --json
paper-agent stats --json
```

## IDE Integration

PaperClaw integrates with AI coding tools via [MCP (Model Context Protocol)](https://modelcontextprotocol.io/), turning your IDE into a research workstation. Search, analyze, and manage papers without switching windows.

### Cursor

```bash
paper-agent setup cursor

# Or install globally (available in all projects)
paper-agent setup cursor --scope global
```

Restart Cursor, then talk to Agent:

```
You: start my day
You: search papers about transformer placement
You: analyze paper 2301.12345
```

### Claude Code

```bash
paper-agent setup claude-code

# Or register MCP server globally
paper-agent setup claude-code --scope global
```

Start `claude` in the project directory. Slash commands are ready:

| Command | What it does |
|---------|-------------|
| `/start-my-day` | Collect today's papers + generate personalized digest |
| `/paper-search <query>` | Search local + online (arXiv, Semantic Scholar) |
| `/paper-analyze <id>` | Deep dive: structured analysis note saved to workspace |
| `/paper-compare <ids>` | Side-by-side method/result comparison table |
| `/paper-survey <topic>` | Generate a literature survey + BibTeX export |
| `/paper-download <ids>` | Batch download PDFs |
| `/paper-triage` | Batch evaluate & triage papers by relevance |
| `/paper-insight <topic>` | Research trend analysis & gap identification |
| `/paper-setup` | Conversational research profile configuration |

Or just use natural language: *"find me papers about LoRA fine-tuning for hardware design"*

### Research Workspace

After running `setup`, a `.paper-agent/` workspace is created in your project:

```
.paper-agent/
├── README.md              ← Auto-updated research dashboard
├── research-journal.md    ← AI-maintained activity log
├── reading-list.md        ← Reading queue (grouped by status)
├── collections/           ← Named paper groups
├── notes/                 ← Per-paper analysis notes
└── citation-traces/       ← Citation graph explorations
```

Everything is plain markdown — open, edit, and version-control with your project.

### Interactive Workflow Skills

Skills are pre-orchestrated research workflows. The AI interacts with you at key decision points and produces structured deliverables.

| Skill | Trigger | Deliverable |
|-------|---------|-------------|
| **Daily Reading** | "start my day" | Daily digest with scoring + reading list updates |
| **Deep Dive** | "analyze this paper" | Structured analysis note (motivation, method, results, limitations) |
| **Literature Survey** | "survey", "what work exists on X" | Survey report + BibTeX bibliography |
| **Citation Explore** | "citations", "who cited this" | Bidirectional citation graph report |
| **Paper Triage** | "which are worth reading" | Triage decision table with recommendations |
| **Research Insight** | "trends", "what's emerging" | Trend analysis + research gap identification |

## MCP Tools

For IDE plugin developers and advanced users, here's the full MCP tool reference:

<details>
<summary><strong>Search & Discovery</strong></summary>

| Tool | Description |
|------|-------------|
| `paper_search(query, diverse)` | Local FTS5 search; `diverse=True` auto-expands keywords |
| `paper_search_batch(queries)` | Multi-direction batch search, results grouped by query |
| `paper_search_online(query, sources)` | Online search via arXiv + Semantic Scholar |

</details>

<details>
<summary><strong>Collection & Management</strong></summary>

| Tool | Description |
|------|-------------|
| `paper_collect(days)` | arXiv + DBLP + Semantic Scholar parallel collection with progress |
| `paper_survey_collect(keywords, venues)` | Multi-year retrospective collection for literature surveys |

</details>

<details>
<summary><strong>Analysis & Comparison</strong></summary>

| Tool | Description |
|------|-------------|
| `paper_show(paper_id)` | Single paper details |
| `paper_batch_show(paper_ids, detail)` | Batch view (compact by default, `detail=True` for full) |
| `paper_compare(paper_ids, aspects)` | Structured comparison data |

</details>

<details>
<summary><strong>Workspace</strong></summary>

| Tool | Description |
|------|-------------|
| `paper_workspace_status()` | Dashboard: reading progress, groups, notes, activity |
| `paper_workspace_context()` | Research context summary for session restoration |
| `paper_reading_status(paper_ids, status)` | Set status: `to_read` / `reading` / `read` / `important` |
| `paper_reading_stats()` | Reading progress statistics |
| `paper_note_add(paper_id, content)` | Add notes (user or AI-generated), synced to `notes/{id}.md` |
| `paper_note_show(paper_id)` | View all notes for a paper |
| `paper_group_create(name, description)` | Create named paper group |
| `paper_group_add(name, paper_ids)` | Add papers to a group |
| `paper_group_show(name)` | View group contents |
| `paper_group_list()` | List all groups with paper counts |
| `paper_citations(paper_id, direction)` | Query citation relationships via Semantic Scholar |

</details>

<details>
<summary><strong>Export & Download</strong></summary>

| Tool | Description |
|------|-------------|
| `paper_find_and_download(title)` | Find by title across S2 + arXiv, auto-import + download PDF |
| `paper_download(paper_ids)` | Batch PDF download |
| `paper_export(paper_ids, format)` | Export as BibTeX / Markdown / JSON |

</details>

## Architecture

```
paper_agent/
├── cli/              # Typer-based CLI + interactive REPL
├── mcp/              # MCP server (stdio transport, used by IDEs)
├── services/         # Application services
│   ├── search_engine         # FTS5 local + online search
│   ├── source_collector      # Multi-source paper fetching
│   ├── collection_manager    # Collection orchestration
│   ├── filtering_manager     # LLM-based relevance scoring
│   ├── digest_generator      # Daily recommendation generation
│   ├── citation_service      # Citation graph traversal
│   ├── profile_manager       # Research profile management
│   └── workspace_manager     # Workspace file sync
├── domain/           # Domain models, policies, value objects
├── infra/            # Infrastructure adapters
│   ├── sources/      # arXiv, DBLP, Semantic Scholar, OpenReview, ACL Anthology
│   ├── storage/      # SQLite with FTS5
│   └── llm/          # OpenAI & Anthropic adapters
├── contracts/        # Shared interfaces
├── export/           # BibTeX, Markdown, JSON exporters
└── app/              # Application bootstrap & DI
```

**Data sources**: arXiv API, DBLP API, Semantic Scholar API, OpenReview API, ACL Anthology

**Storage**: SQLite with FTS5 full-text search, stored at `~/.paper-agent/papers.db`

**LLM providers**: OpenAI-compatible (including Azure, local proxies) and Anthropic

## Configuration

View current config:

```bash
paper-agent config
```

API key can also be set via environment variable (takes precedence over config file):

```bash
export PAPER_AGENT_LLM_API_KEY="your-key-here"
```

All config is stored in `~/.paper-agent/config.yaml`.

## Development

```bash
git clone https://github.com/linshaoxin-maker/PaperClaw.git
cd PaperClaw

# Install with dev dependencies
poetry install

# Run
poetry run paper-agent

# Run MCP server directly
poetry run paper-agent-mcp

# Tests
poetry run pytest

# Lint
poetry run ruff check .
poetry run mypy paper_agent/
```

Requires Python 3.10+.

## Uninstall

```bash
pipx uninstall paper-agent
```

To remove all local data: `rm -rf ~/.paper-agent`

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
