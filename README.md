# InkFrame

InkFrame is an AI-assisted novel-to-screenplay converter. It turns Chinese or English prose into an editable structured screenplay draft, with source references, confidence scores, inferred-content markers, and intermediate JSON files for debugging.

## Product Goal

Help fiction authors move from a novel manuscript to a screenplay draft faster. The tool does not try to be the final authority on adaptation choices; it creates a traceable first pass that authors can inspect, edit, and export.

## MVP Scope

- File-backed FastAPI pipeline.
- React + TypeScript web editor.
- Mock LLM provider for local development and tests.
- Stage outputs stored as JSON/YAML contracts.
- Left/right source and screenplay editor.
- Character table, relationship graph, scene timeline, validation log, and YAML export.

## Documentation

- [PRD.md](./PRD.md): product requirements, architecture decisions, API contract, storage contract, and issue split strategy.
- [theme.css](./theme.css): design tokens and base utility classes.
- [.agents/DESIGN_GUIDE.md](./.agents/DESIGN_GUIDE.md): UI implementation guidance.

## Current Status

This repository currently contains the product and design documentation only. Implementation should start from the schema and file storage contract described in the PRD.
