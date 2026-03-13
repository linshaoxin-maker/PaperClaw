# Paper Agent v01_source Documentation

**Version:** v01_source
**Status:** Draft
**Last Updated:** 2026-03-12

## Overview

This directory defines **v01 extensions** for Paper Agent focused on:

- **Source**: multi-source collection + source registry/management
- **Profile**: guided interest setup (topics/keywords) and source recommendation

It is designed as an **incremental layer** on top of v01. Whenever possible, this doc set references the base v01 documents instead of restating them.

## Base Documents (v01)

- Requirement (base): `docs/v01/requirement.md`
- Spec (base): `docs/v01/spec.md`
- Design (base): `docs/v01/design.md`

## Documentation Structure

This extension includes five core documents (mirrors v01):

1. **[Requirement](./requirement.md)** - Source/Profile extension requirements, scenarios, use cases
2. **[Feature](./feature.md)** - Feature view derived from design/spec
3. **[Spec](./spec.md)** - CLI contracts + behaviors for Source/Profile + multi-source collect
4. **[Design](./design.md)** - Components/adapters/registry/profile manager + integration with v01 architecture
5. **[MVP](./mvp.md)** - First-release scope for the extension

## Recommended Reading Order

1. `docs/v01/requirement.md` (base)
2. `docs/v01/spec.md` (base)
3. `docs/v01/design.md` (base)
4. `docs/v01_source/requirement.md` (this extension)
5. `docs/v01_source/spec.md`
6. `docs/v01_source/design.md`
7. `docs/v01_source/feature.md`
8. `docs/v01_source/mvp.md`

## Traceability Note

This doc set introduces a separate requirement namespace (e.g., `FR-SRC-xx`, `UC-SRC-xx`, `AC-SRC-xx`, `ADR-SRC-xx`) to avoid collisions with v01 identifiers.
