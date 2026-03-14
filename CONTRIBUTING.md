# Contributing to PaperClaw

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/linshaoxin-maker/PaperClaw.git
cd PaperClaw
poetry install
```

Requires Python 3.10+.

## Running Locally

```bash
# CLI
poetry run paper-agent

# MCP server
poetry run paper-agent-mcp

# Tests
poetry run pytest

# Lint
poetry run ruff check .

# Type check
poetry run mypy paper_agent/
```

## Making Changes

1. Fork the repo and create a feature branch from `main`
2. Make your changes
3. Add tests for new functionality
4. Run `ruff check .` and `mypy paper_agent/` — fix any issues
5. Run `pytest` — make sure all tests pass
6. Submit a pull request

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for all function signatures
- Lint with [Ruff](https://docs.astral.sh/ruff/) (config in `pyproject.toml`)
- Type check with [mypy](https://mypy-lang.org/)
- Keep line length under 100 characters

## Project Structure

```
paper_agent/
├── cli/          # CLI commands (Typer)
├── mcp/          # MCP server for IDE integration
├── services/     # Application logic
├── domain/       # Domain models & policies
├── infra/        # External adapters (APIs, storage, LLM)
├── contracts/    # Shared interfaces
├── export/       # Output formatters (BibTeX, JSON, Markdown)
└── app/          # Bootstrap & dependency injection
```

## Reporting Issues

- Use GitHub Issues
- Include: Python version, OS, steps to reproduce, expected vs actual behavior
- For paper source issues (arXiv/DBLP/S2), include the query or paper ID

## Adding a New Paper Source

Paper sources live in `paper_agent/infra/sources/`. To add a new source:

1. Create a new adapter inheriting from `BaseAdapter`
2. Register it in `source_registry.py`
3. Add tests in `tests/`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
