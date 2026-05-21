# 🛰️ Protocollo di Delega (Dispatch Queue)

**MANDATORIO AD OGNI AVVIO:** Controlla la sottocartella `_Dispatch_Queue` all'interno del tuo `CONVO_VAULT_PATH`. 
- Se trovi file con `stato: pendente`, prendili in carico immediatamente.
- Esegui il bug fixing o lo sviluppo richiesto.
- Una volta finito, aggiorna il file Markdown cambiando lo stato in `completato` e aggiungendo il riassunto della soluzione.

---

# 🛠️ Istruzioni Critiche Modelli

**NON USARE ALTRI NOMI.** In ogni chiamata API o configurazione di agenti, usa esclusivamente questi:
- **`gemini-3.1-flash-lite`**: Per task veloci, automazione e interazione vocale.
- **`gemini-3-flash-preview`**: Per analisi profonde, riassunti e ragionamento complesso.

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
