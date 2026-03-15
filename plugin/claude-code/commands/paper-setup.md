---
description: Set up research profile through conversation — determine research interests and configure sources
allowed-tools: [
  "mcp__paper-agent__paper_profile",
  "mcp__paper-agent__paper_profile_update",
  "mcp__paper-agent__paper_templates_list",
  "mcp__paper-agent__paper_sources_list",
  "mcp__paper-agent__paper_sources_enable",
  "mcp__paper-agent__paper_collect",
  "mcp__paper-agent__paper_health"
]
---

# Paper Setup

Guide the user through creating their research profile via conversation.

## Process

1. Call `paper_profile()` to check if a profile already exists
2. If profile exists, show current topics/keywords and ask if user wants to update
3. Ask the user about their research interests in a natural conversation:
   - What are your research areas?
   - What techniques or methods do you focus on?
4. Optionally call `paper_templates_list()` to show available templates
   - If a template matches, use its topics/keywords as a starting point
5. Extract topics and keywords from the conversation
6. Call `paper_sources_list()` to show available arXiv categories
7. Recommend relevant sources based on the user's interests
8. Call `paper_profile_update(topics, keywords, enable_sources)` to save
9. Ask if the user wants to do an initial collection:
   - If yes, call `paper_collect(days=7)`

## Conversation Style

- Use Chinese for all communication
- Be conversational, not a form to fill out
- Suggest topics/keywords proactively based on what the user describes
- Explain what sources are and why they matter
