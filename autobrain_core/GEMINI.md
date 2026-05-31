# 🧠 Brain Core Instructions

## Engineering Standards
- **MANDATORY**: Adhere to the root [[GEMINI.md]] standards.
- **Disaccoppiamento**: Il Core non deve conoscere l'esistenza dell'interfaccia di Jarvis. Espone solo API e metodi di gestione del grafo e dei documenti.
- **Performance**: Ogni modifica al Knowledge Graph deve essere preceduta da un'analisi di impatto sulle performance di indicizzazione.
- **AI Folder**: `Z_AI_Cerebrum` (contains all AI-generated analysis).
- **Quarantine**: `_quarantine` (inside the AI folder).
- **Source PDFs**: `_PDF_Sources` (for raw document input).
- **Analysis Section**: `## Related Concepts` (at the end of every analysis note).
- **Analysis Prefix**: `Analysis_` (for generated filenames).

---

# 🧠 Architectural Integrity (GitNexus)

**MANDATORY:** For every modification that is not a trivial bug fix, you MUST use GitNexus to preserve the "Hub & Spoke" structure of the project.

- **Before modifying a symbol:** Run `gitnexus_impact` to evaluate the "blast radius". If the risk is HIGH (many dependencies), ask the user for confirmation.
- **To understand flows:** Use `gitnexus_query` to visualize how data flows between modules before adding new logic.
- **Post-Modification:** Verify that new links do not create circular couplings between modules (e.g., Jarvis must not depend directly on Brain's internal logic, but go through defined APIs).

---

# 🛰️ Delegation Protocol (Dispatch Queue)

**MANDATORY AT EVERY START:** Check the `_Dispatch_Queue` subfolder inside your `CONVO_VAULT_PATH`. 
- If you find files with `status: pending`, take them on immediately.
- Perform the requested bug fixing or development.
- Once finished, update the Markdown file by changing the status to `completed` and adding a summary of the solution.

---

# 🛠️ Critical Model Instructions

DO NOT USE OTHER NAMES. In every API call or agent configuration, use exclusively these:
- **`gemini-3.1-flash-lite`**: For fast tasks, automation, and voice interaction.
- **`gemini-3.5-flash`**: For analysis, summaries, and complex reasoning (current standard).
- **`gemini-3-flash-preview`**: Legacy support for deep analysis if needed.

---

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **secondo_cervello_ai** (274 symbols, 363 relationships, 14 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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
| `gitnexus://repo/secondo_cervello_ai/context` | Codebase overview, check index freshness |
| `gitnexus://repo/secondo_cervello_ai/clusters` | All functional areas |
| `gitnexus://repo/secondo_cervello_ai/processes` | All execution flows |
| `gitnexus://repo/secondo_cervello_ai/process/{name}` | Step-by-step execution trace |

<!-- gitnexus:end -->
