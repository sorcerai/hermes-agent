# Engineering Handoff: AXI Token Optimization, Tiered Browser Routing & Sandbox Infrastructure

**Date**: 2026-09-06  
**Author**: Antigravity Pair-Programming Agent  
**Status**: In-Flight Work 100% Implemented, Tested, Deployed, and Pushed to `origin/main`

---

## 1. Executive Summary

This session executed a major capability upgrade across two core repositories:
1. **`hermes-agent`**: Implemented **AXI Phase 2** (zero-dependency TOON serializer, content-first CLI output formatting, Did-You-Mean typo correction), saving **-94.9% web tokens** and **-71.5% CLI tokens**. Authored comprehensive architecture documentation and compiled the interactive **Archify** infrastructure diagram.
2. **`agent-computer`**: Developed and deployed **Tiered Browser Routing** via `reach_smart_browse` (version 0.3.0). Implemented a sub-100ms fast path via `obscura` with automatic escalation to headed Chromium in the `reach-lab` microVM for anti-bot barriers (Cloudflare Turnstile, 403, React hydration). Fixed CDP connection timeout and tab bloat in `docker.rs`. Rebuilt and deployed the live `reach` daemon on the microVM (`PID 55011`).

All code changes are pushed to `origin/main` on both GitHub remotes with clean working trees. All beads and Reverie knowledge bases have been synchronized.

---

## 2. Repository Inventory & Git SHAs

| Repository | Path | Head Commit | Description | Remote Status |
|:---|:---|:---:|:---|:---:|
| **`hermes-agent`** | `/Users/ahpramesi/repos/hermes-agent` | [`4b3e89f047`](https://github.com/sorcerai/hermes-agent/commit/4b3e89f047) | docs: add tiered browser routing spec & Archify map | Up to date with `origin/main` |
| | | [`49c02d0855`](https://github.com/sorcerai/hermes-agent/commit/49c02d0855) | feat(cli): AXI Phase 2 TOON formatting & suggestions | Up to date with `origin/main` |
| **`agent-computer`** | `/Users/ahpramesi/repos/agent-computer` | [`42d3808`](https://github.com/sorcerai/agent-computer/commit/42d3808) | feat(hermes): reach_smart_browse tiered routing & CDP fix | Up to date with `origin/main` |
| | | [`57a3d11`](https://github.com/sorcerai/agent-computer/commit/57a3d11) | docs(mcp): document AXI Phase 1 MCP parameters | Up to date with `origin/main` |
| | | [`8487703`](https://github.com/sorcerai/agent-computer/commit/8487703) | feat(reach-cli): implement AXI Phase 1 query filtering | Up to date with `origin/main` |
| | | [`2b9d872`](https://github.com/sorcerai/agent-computer/commit/2b9d872) | feat(reach-cli): implement AXI Phase 0 compact serialization | Up to date with `origin/main` |
| **`archify`** | `/Users/ahpramesi/repos/archify` | `main` | Graph compiler & interactive renderer | Clean local clone |

---

## 3. Live MicroVM & Sandbox Runtime Architecture

```
[macOS Host]                                  [OrbStack "reach-lab" MicroVM (192.168.139.232)]
Hermes Agent / CLI -------------------------> Reach Rust Daemon (Port 4200, PID 55011)
  - reach-agent-computer plugin                  - Host Header Guard: 127.0.0.1:4200
  - reach_smart_browse tool                      - ProfileBroker (Screen leases)
       |                                             |
       |-- Tier 1: Obscura (sub-100ms local)         |-- Docker Sandbox Container ("agent-computer")
       |                                                   - Xvfb :99 (1280x720)
       |-- Tier 2: MicroVM Headed Chrome <-----------------  - Openbox Window Manager
       |                                                   - Headed Chromium (Persistent Profile)
       |-- Tier 3: Human Takeover (noVNC) <----------------  - x11vnc (:5900) + websockify (:6080)
```

### Critical Environment Invariants:
1. **DNS Rebinding Protection**:
   - The Reach daemon strictly checks `Host` headers and rejects any request where `Host` is not `127.0.0.1:4200` or `localhost:4200`.
   - When calling Reach across the network bridge (`192.168.139.232:4200`), requests **must** include `Host: 127.0.0.1:4200`. This is baked into [`_http_request`](file:///Users/ahpramesi/repos/agent-computer/integrations/hermes/plugins/reach-agent-computer/__init__.py#L72-L93).
2. **Profile Leases**:
   - Screen leases are keyed by Hermes profile name (`get_owner()`).
   - Leased in `on_session_start`, released in `on_session_finalize`.
   - Any tool named `mcp__reach__*` or in `PLUGIN_TOOLS` is automatically routed to the session's leased screen via `pre_tool_call`.
3. **Live noVNC Stream**:
   - URL: `http://192.168.139.232:6080/vnc.html?autoconnect=1&resize=remote`
   - Use `auth_handoff` to trigger human takeover whenever logins or complex captchas occur.

---

## 4. Key Deliverables & Files

### AXI Phase 2 in Hermes Agent
- [`hermes_cli/axi_formatter.py`](file:///Users/ahpramesi/repos/hermes-agent/hermes_cli/axi_formatter.py): Zero-dependency TOON serializer, content-first table/JSON formatter, and Levenshtein-based Did-You-Mean suggestion engine.
- [`hermes_cli/cli_repl_mixin.py`](file:///Users/ahpramesi/repos/hermes-agent/hermes_cli/cli_repl_mixin.py#L42-L68): Integrated Did-You-Mean suggestion interceptor for unknown slash commands.
- [`tests/hermes_cli/test_axi_cli_formatting.py`](file:///Users/ahpramesi/repos/hermes-agent/tests/hermes_cli/test_axi_cli_formatting.py): 12 unit tests verifying token formatting and suggestions.

### Tiered Browser Routing in Agent Computer
- [`integrations/hermes/plugins/reach-agent-computer/__init__.py`](file:///Users/ahpramesi/repos/agent-computer/integrations/hermes/plugins/reach-agent-computer/__init__.py): Added `reach_smart_browse` tool with anti-bot classifier, Obscura fast path, and Reach headed Chrome escalation.
- [`integrations/hermes/plugins/reach-agent-computer/plugin.yaml`](file:///Users/ahpramesi/repos/agent-computer/integrations/hermes/plugins/reach-agent-computer/plugin.yaml): Bumped version to `0.3.0` and registered tool.
- [`integrations/hermes/plugins/reach-agent-computer/test_plugin.py`](file:///Users/ahpramesi/repos/agent-computer/integrations/hermes/plugins/reach-agent-computer/test_plugin.py): 11 unit tests covering fast-path hits, anti-bot fallbacks, and forced-headed mode.
- [`crates/reach-cli/src/docker.rs`](file:///Users/ahpramesi/repos/agent-computer/crates/reach-cli/src/docker.rs): Playwright CDP connect timeout increased to 3000ms with backoff, plus automatic pruning of stale `about:blank` tabs.

### Documentation & Diagrams
- [`docs/TIERED_BROWSER_ROUTING.md`](file:///Users/ahpramesi/repos/hermes-agent/docs/TIERED_BROWSER_ROUTING.md): Complete architecture specification and empirical benchmarks.
- [`docs/infrastructure.html`](file:///Users/ahpramesi/repos/hermes-agent/docs/infrastructure.html): Self-contained interactive Archify visualization.
- [`docs/infrastructure.architecture.json`](file:///Users/ahpramesi/repos/hermes-agent/docs/infrastructure.architecture.json): Archify graph source model.
- [`scratch/infrastructure_diagram.png`](file:///Users/ahpramesi/.gemini/antigravity-cli/brain/30fb058f-2909-4a9e-887b-87ee4b5c075e/scratch/infrastructure_diagram.png): High-resolution rendered system diagram.

---

## 5. Empirical Benchmark Summary

### Latency Comparison
- **Hacker News (Clean)**: Obscura **65.2 ms** vs Reach MicroVM 1,484.4 ms (**22.7x speedup**).
- **Wikipedia Nobel Prize (Large DOM)**: Obscura **112.4 ms** vs Reach MicroVM 1,890.1 ms (**16.8x speedup**).
- **Cloudflare Turnstile Demo**: 340.2 ms probe $\rightarrow$ clean escalation to Reach MicroVM.

### Token Economy (AXI Phase 2)
- **Web DOM / Page Content**: **-94.9% token overhead** (from ~8,850 tokens down to 454 tokens).
- **CLI Output Formatting**: **-26.5% to -71.5% token reduction**.
- **Typo Recovery Overhead**: **-94.7% token reduction** (from 566 tokens down to 30 tokens).

---

## 6. How to Verify & Run Tests

```bash
# 1. Test reach-agent-computer plugin
cd /Users/ahpramesi/repos/agent-computer
python3 integrations/hermes/plugins/reach-agent-computer/test_plugin.py

# 2. Test hermes-agent AXI formatting suite
cd /Users/ahpramesi/repos/hermes-agent
scripts/run_tests.sh tests/hermes_cli/test_axi_cli_formatting.py

# 3. Live end-to-end browse test against reach-lab
cd /Users/ahpramesi/repos/agent-computer
python3 -c "
import sys; sys.path.insert(0, 'integrations/hermes/plugins/reach-agent-computer')
import __init__ as p
res = p.reach_smart_browse('https://news.ycombinator.com', api_url='http://192.168.139.232:4200')
print('Tier 1:', res.get('tier'), res.get('latency_ms'), 'ms')
res2 = p.reach_smart_browse('https://news.ycombinator.com', api_url='http://192.168.139.232:4200', force_headed=True)
print('Tier 2:', res2.get('tier'), res2.get('latency_ms'), 'ms')
"

# 4. Check microVM service status
orb -m reach-lab bash -c "systemctl --user status reach-serve.service --no-pager"
```

---

## 7. Knowledge Base Keys (Beads & Reverie)

### Reverie Memories (`reveried client get <id>`)
- **ID 82453** (`hermes-agent`, topic: `integration/tiered-browser-routing-and-axi`): AXI Phase 1-2 & Tiered Browser Routing implementation and benchmark summary.
- **ID 82454** (`agent-computer`, topic: `project/agent-computer-status`): Agent Computer v0.3.0 deployment, CDP resilience, and live microVM state.

### Beads Memories (`bd remember <key>`)
- `reach-dns-rebinding-host-header`: Reach daemon requires `Host: 127.0.0.1:4200` to prevent DNS rebinding across network bridges.
- `tiered-browser-rotation-architecture`: Three-tier escalation model (Obscura sub-100ms $\rightarrow$ Reach microVM headed Chrome $\rightarrow$ Human Takeover via noVNC :6080).
- `handoff-axi-tiered-browser-sep2026`: Handoff marker noting all commits pushed and daemons active.

---

## 8. Immediate Next Steps / Roadmap for Next Agent

1. **AXI Phase 3 (Delta AXTree & Grounding)**:
   - Implement DOM diffing to send only mutated nodes between interactive turns instead of full trees.
   - Map visual bounding boxes from viewport screenshots into AXI `@eN` references.
2. **Autonomous Routine Workflows**:
   - Write scheduled routine scripts executing on the `agent-computer` sandbox that output to `/workspace/reports/`.
3. **Hermes Core v1.1 Milestone**:
   - `hermes-agent-44a.6`: Publish `hermes:session_stall` on the plugin event bus from `_notify_session_stall`.
