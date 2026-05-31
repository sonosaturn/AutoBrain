<!-- gitnexus:start -->
# 🤖 Jarvis-Specific Instructions

## Engineering Standards
- **MANDATORY**: Adhere to the root [[GEMINI.md]] standards.
- **Logging**: Use `logger = logging.getLogger("jarvis.module_name")`. Ensure logs are routed to `logs/jarvis_structured.jsonl`.
- **API**: All frontend-backend communication must include the `X-API-Key` header.
- **GitNexus**: Use `gitnexus_query` to understand the flow before proposing changes to `jarvis_engine.py` or `main.py`.

## Architectural Rules
- Jarvis is an interface. Do not bloat it with heavy data processing logic; delegate that to `autobrain_core`.
- Maintain the WebSocket connection as the single source of truth for the system state (`IDLE`, `LISTENING`, `THINKING`, `SPEAKING`).

> If any GitNexus tool warns the index is stale, run `gitnexus analyze . --index-only` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/jarvis/context` | Codebase overview, check index freshness |
| `gitnexus://repo/jarvis/clusters` | All functional areas |
| `gitnexus://repo/jarvis/processes` | All execution flows |
| `gitnexus://repo/jarvis/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
