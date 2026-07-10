# SkillMesh PRD-lite

## Product definition

SkillMesh is a graph-powered Skill OS for Codex and AI agents. It manages skills as durable assets, ranks skills against live context, and learns from execution outcomes over time.

## Problem statement

The ecosystem already has partial tools for local skill management, graph visualization, marketplace browsing, and run inspection. What is still missing is a single product loop that connects these jobs end to end:

1. discover local and remote skills
2. explain what each skill does and depends on
3. install or enable the right skill quickly
4. recommend the right skill for the current thread or repo
5. execute or bridge into execution
6. observe what actually happened
7. improve future recommendation quality

Without the final three steps, a product is only a browser or installer. Without the first three, it is only a thin recommendation panel.

## Target users

Primary users:

- Codex users with growing local and remote skill catalogs
 - teams that maintain shared skill bundles or internal marketplaces
 - advanced individual users who want repeatable task routing across repos

Secondary users:

- plugin and marketplace maintainers
 - reviewers or platform owners who need policy, trust, and dependency visibility

## Core loop

`discover -> understand -> install -> recommend -> execute -> observe -> improve`

## Information architecture

The first release should expose six primary views:

1. `Recommend`
   - current workspace summary
   - prompt and repo signals
   - ranked skill suggestions
   - recommendation reasons and confidence

2. `Library`
   - all indexed skills
   - filters for source, status, trust, and platform
   - version and dependency overview

3. `Graph`
   - nodes for skill, tool, MCP, plugin, workspace, and flow template
   - edges for requires, recommends, used_in, and triggered_by
   - missing dependency and conflict highlighting

4. `Flow`
   - reusable multi-step templates
   - preflight checks
   - fallback paths

5. `Runs`
   - recent executions
   - success, warning, and failure outcomes
   - user feedback and recommendation quality

6. `Sources`
   - local, GitHub, marketplace, and plugin sources
   - trust and sync policy
   - install targets and permissions

## Scope by phase

### P0

The minimum differentiated loop:

 - local and remote source indexing
 - skill inventory and detail surface
 - dependency graph
 - prompt and repo-aware recommendation
 - install or enable actions with dependency validation
 - run history with basic feedback states

### P1

The next product layer:

 - flow template authoring
 - workspace presets and collections
 - version updates and rollback
 - richer recommendation explanation
 - analytics dashboards

### P2

Longer-term defensibility:

 - learning from historical threads and runs
 - team approval and governance workflows
 - skill lint and validator pipelines
 - marketplace publish flows
 - auto-discovered composable flows

## Architecture split

SkillMesh should be split across two product surfaces:

 - Codex-facing plugin: thread-local context gathering, recommendation injection, execution bridge
 - global app: source management, graph views, bulk configuration, analytics, publish workflows

That boundary keeps the thread experience fast while preserving a richer administrative and analytical surface outside the thread.

## Technical direction

Recommended stack for the first implementation:

 - UI shell: React + TypeScript
 - desktop wrapper: Tauri when native packaging becomes necessary
 - persistence: SQLite
 - search: SQLite FTS
 - graph rendering: relationship tables plus front-end rendering
 - ranking: explicit rules first, embeddings later

## Success criteria for the first real milestone

The first milestone is successful when a user can:

1. point SkillMesh at one or more skill sources
2. browse the resulting inventory
3. inspect a selected skill and its dependencies
4. see a ranked recommendation for the current workspace context
5. understand why that recommendation appeared
6. record whether the recommendation helped

Once those six are real, the product stops being a concept deck and becomes a usable operating surface.
