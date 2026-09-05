# ARCH.md — Construction blueprint

> **For builder agents.** Short by design: negatives (forbidden edges/patterns)
> don't rot; positive specs do. Inject into agent context at session start. A
> change that breaks one of these is DRIFT, not a fix — stop and update this
> file (with a reason + beads issue) first.

## What this is (2-line positive anchor)

Hermes is a personal AI agent running across CLI, messaging gateways, TUI, and Electron desktop.
It learns across sessions (memory + skills), delegates to subagents, and drives real environments.

## Negative invariants (forbidden — breaking one is drift, not a fix)

1. Never mutate system-prompt state, swap toolsets, or invalidate per-conversation prompt caching mid-conversation (the single exception is context compression).
2. The core is a narrow waist; capability lives at the edges. Never add new core tools when a CLI command + skill, service-gated tool (`check_fn`), or plugin suffices.
3. Surface capability is a property of the SESSION, never of the process env (`HERMES_DESKTOP=1` means backend spawned by app, not that a GUI is attached).
4. Never break strict role alternation (never two same-role messages in a row; never inject synthetic user messages mid-turn-loop).
5. Never hardcode `~/.hermes` — use `get_hermes_home()` for code paths and `display_hermes_home()` for user-facing output.
6. Never introduce `HERMES_*` environment variables for non-secret behavioral configuration; behavioral settings belong in `config.yaml`.
7. Never infer process identity from arbitrary argv substrings; use canonical matchers (`looks_like_gateway_command_line`, derived flag sets).
8. Third-party vendor products/SaaS connectors must never land in core `plugins/`; ship as standalone external plugins.

## When this file is wrong

If a task genuinely requires breaking an invariant, update THIS file first (with
a beads issue + reason), then change the code. A silent violation is the exact
late-caught drift this file exists to prevent.
