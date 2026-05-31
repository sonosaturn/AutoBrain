# 🚀 Engineering Standards 2026 (AutoBrain)

Tutte le operazioni di implementazione, refactoring e manutenzione eseguite dalla Gemini CLI o dagli agenti interni di Jarvis devono aderire a questi standard.

## 1. 🚫 No "Vibe Coding" (Anti-Fragilità)
- **Logging Strutturato**: MAI usare `print()`. Utilizzare esclusivamente `import logging` e il setup centralizzato in `core_utils.logging_setup`.
- **Osservabilità**: Ogni nuovo modulo deve generare log in formato JSON (`.jsonl`) per permettere il debug post-mortem senza dover aggiungere log a posteriori.
- **Livelli di Log**: Usare `DEBUG` per dettagli tecnici, `INFO` per flussi normali, `WARNING` per retry/sovraccarico API, `ERROR` per eccezioni gestite, `CRITICAL` per crash di sistema.

## 2. 🛡️ Security & API Hardening
- **Protezione Endpoint**: Ogni nuovo endpoint API (FastAPI) deve implementare la validazione `X-API-Key` tramite `core_utils.Config.JARVIS_API_KEY`.
- **CORS Policy**: Non usare mai `allow_origins=["*"]`. Limitare sempre agli host locali autorizzati (es. `http://localhost:5173`).
- **Gestione Segreti**: Non hardcodare mai chiavi o percorsi. Usa `core_utils.Config` che legge dal file `.env`.

## 3. 🕸️ Architectural Integrity (GitNexus)
- **Impact Analysis**: Prima di modificare qualsiasi funzione, classe o metodo esistente, è OBBLIGATORIO eseguire `gitnexus impact <symbol>` per valutare il "raggio d'azione" (blast radius).
- **Hub & Spoke**: Mantenere il disaccoppiamento tra Jarvis e il Brain Core. Jarvis comunica con il Brain tramite API o interfacce definite, mai importando logica interna "privata".

## 4. 🧪 Validazione e Testing
- **Syntax Check**: Ogni codice Python generato deve essere validato sintatticamente (es. tramite `py_compile`) prima di sovrascrivere file esistenti.
- **Backup**: Effettuare sempre un backup `.bak` dei file critici prima di una sovrascrittura massiva.
