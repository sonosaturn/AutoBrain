"""
validator.py — Validazione strutturale e retry intelligente per il Secondo Cervello.

Architettura a tre livelli:
  1. Validazione deterministica (zero costo API)
  2. Retry con prompt di correzione chirurgica
  3. Quarantena con log diagnostico per i casi irrecuperabili
"""

import re
import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# STRUTTURA DI UN RISULTATO DI VALIDAZIONE
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self):
        parts = []
        if self.errors:
            parts.append("ERRORI: " + "; ".join(self.errors))
        if self.warnings:
            parts.append("AVVISI: " + "; ".join(self.warnings))
        return " | ".join(parts) if parts else "OK"


# ---------------------------------------------------------------------------
# LIVELLO 1 — VALIDATORE STRUTTURALE (deterministico, senza API)
# ---------------------------------------------------------------------------

# Queste regole mappano esattamente le REGOLE DI ELABORAZIONE del tuo SYSTEM_PROMPT.
# Ogni regola è una funzione che riceve il testo e restituisce un messaggio di errore
# (stringa) se la regola è violata, oppure None se è rispettata.

def _rule_has_h1_title(text: str) -> str | None:
    """Il documento deve iniziare con un titolo H1 (#)."""
    stripped = text.strip()
    if not stripped.startswith("#"):
        # Cerca se esiste almeno un H1 nel testo (potrebbe esserci CoT prima)
        if re.search(r"^#\s+\S", text, re.MULTILINE):
            return "Testo prima del primo titolo H1 (CoT residuo)"
        return "Nessun titolo H1 trovato"
    return None


def _rule_no_cot_markers(text: str) -> str | None:
    """
    Cerca pattern tipici di Chain-of-Thought che non dovrebbero sopravvivere
    al _strip_cot(), ma a volte si nascondono dentro il testo.
    """
    COT_PATTERNS = [
        r"^\s*(okay|ok|alright|bene|perfetto|certo)[,.]?\s*[\w]",  # frasi di apertura conversazionale
        r"^(let me|lasciami|vediamo|analizziamo|procedo)\b",        # intro di ragionamento
        r"<think>",                                                    # tag thinking espliciti
        r"</think>",
        r"^\s*\*\*?(nota|note|avviso|attenzione)\*\*?:",              # meta-note dell'AI
    ]
    for pattern in COT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return f"Possibile CoT residuo: pattern '{pattern[:30]}...'"
    return None


def _rule_code_blocks_closed(text: str) -> str | None:
    """I blocchi di codice ``` devono essere aperti e chiusi correttamente."""
    count = len(re.findall(r"^```", text, re.MULTILINE))
    if count % 2 != 0:
        return f"Blocchi di codice non bilanciati ({count} backtick-fence trovati, deve essere pari)"
    return None


def _rule_has_correlati_section(text: str) -> str | None:
    """Il documento deve terminare con la sezione 'Concetti Correlati:'."""
    if not re.search(r"concetti\s+correlati\s*:", text, re.IGNORECASE):
        return "Sezione 'Concetti Correlati:' mancante"
    return None


def _rule_has_wikilinks(text: str) -> str | None:
    """
    Deve esserci almeno un [[wikilink]].
    Se non ce ne sono affatto, qualcosa è andato storto con la formattazione.
    """
    if not re.search(r"\[\[.+?\]\]", text):
        return "Nessun [[wikilink]] trovato nel documento"
    return None


def _rule_minimum_length(text: str, min_words: int = 80) -> str | None:
    """Output troppo corto è sospetto (risposta troncata o rifiuto silenzioso)."""
    word_count = len(text.split())
    if word_count < min_words:
        return f"Output troppo corto ({word_count} parole, minimo {min_words})"
    return None


def _rule_no_truncation_markers(text: str) -> str | None:
    """
    Alcuni modelli segnalano la troncatura con frasi tipiche.
    """
    TRUNCATION_PATTERNS = [
        r"\.\.\.\s*$",                             # termina con "..."
        r"\[continua\]",
        r"\[troncato\]",
        r"(il testo continua|to be continued)",
        r"(max.{0,20}token|context.{0,20}limit)",
    ]
    last_500 = text[-500:]  # controlla solo la coda
    for pattern in TRUNCATION_PATTERNS:
        if re.search(pattern, last_500, re.IGNORECASE):
            return f"Possibile troncatura rilevata: '{pattern}'"
    return None


# Registro delle regole: (funzione, è_bloccante)
# Le regole bloccanti causano is_valid=False; quelle non bloccanti producono solo warnings.
VALIDATION_RULES: list[tuple] = [
    (_rule_has_h1_title,           True),
    (_rule_no_cot_markers,         True),
    (_rule_code_blocks_closed,     True),
    (_rule_has_correlati_section,  True),
    (_rule_has_wikilinks,          False),   # warning: potrebbe essere legittimamente assente
    (_rule_minimum_length,         True),
    (_rule_no_truncation_markers,  False),   # warning: potrebbe essere stile del modello
]


def validate(text: str) -> ValidationResult:
    """
    Esegue tutte le regole di validazione e restituisce un ValidationResult.
    """
    errors   = []
    warnings = []

    for rule_fn, is_blocking in VALIDATION_RULES:
        msg = rule_fn(text)
        if msg:
            if is_blocking:
                errors.append(msg)
            else:
                warnings.append(msg)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# LIVELLO 2 — PROMPT DI CORREZIONE CHIRURGICA
# ---------------------------------------------------------------------------

def build_correction_prompt(broken_output: str, validation_result: ValidationResult) -> str:
    """
    Costruisce un prompt mirato che descrive esattamente cosa correggere,
    allegando l'output malformato e chiedendo SOLO la riparazione.
    """
    error_list = "\n".join(f"- {e}" for e in validation_result.errors)

    return f"""Il documento Markdown che hai generato contiene i seguenti problemi strutturali che DEVONO essere corretti:

{error_list}

Di seguito trovi l'output malformato. Restituisci ESCLUSIVAMENTE il documento corretto, senza nessuna spiegazione o commento aggiuntivo. Non ri-analizzare il contenuto originale: correggi solo i problemi elencati sopra mantenendo tutto il resto identico.

--- OUTPUT DA CORREGGERE ---
{broken_output}
--- FINE OUTPUT ---"""


# ---------------------------------------------------------------------------
# LIVELLO 3 — QUARANTENA
# ---------------------------------------------------------------------------

QUARANTINE_FOLDER = "_quarantena"


def quarantine(
    original_file_path: str,
    chunk_label: str,
    chunk_text: str,
    broken_output: str,
    validation_result: ValidationResult,
    ai_folder_path: str,
) -> None:
    """
    Salva il chunk problematico in una sottocartella di quarantena con:
    - Il testo del chunk originale
    - L'output malformato prodotto dall'AI
    - Un report diagnostico JSON
    """
    quarantine_path = os.path.join(ai_folder_path, QUARANTINE_FOLDER)
    os.makedirs(quarantine_path, exist_ok=True)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_label = re.sub(r"[\\/:*?\"<>|'\s]", "_", chunk_label)[:50]
    prefix     = f"{timestamp}_{base_label}"

    # 1. Salva il testo originale del chunk
    with open(os.path.join(quarantine_path, f"{prefix}_INPUT.txt"), "w", encoding="utf-8") as f:
        f.write(chunk_text)

    # 2. Salva l'output malformato
    with open(os.path.join(quarantine_path, f"{prefix}_OUTPUT.md"), "w", encoding="utf-8") as f:
        f.write(broken_output or "(output vuoto)")

    # 3. Salva il report diagnostico
    report = {
        "timestamp":        timestamp,
        "source_file":      original_file_path,
        "chunk_label":      chunk_label,
        "chunk_words":      len(chunk_text.split()),
        "errors":           validation_result.errors,
        "warnings":         validation_result.warnings,
    }
    with open(os.path.join(quarantine_path, f"{prefix}_REPORT.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"  🔴 In quarantena: {prefix}_*.* (vedi {QUARANTINE_FOLDER}/)")


# ---------------------------------------------------------------------------
# INTERFACCIA PRINCIPALE — da usare in brain.py
# ---------------------------------------------------------------------------

def validate_and_retry(
    chunk_text: str,
    initial_output: str | None,
    label: str,
    original_file_path: str,
    call_ai_fn,          # passa la funzione call_ai di brain.py
    ai_folder_path: str,
    max_retries: int = 2,
    **kwargs            # argomenti extra per call_ai_fn (es. images)
) -> str | None:
    """
    Orchestratore principale del sistema di validazione.

    Flusso:
      1. Valida l'output iniziale.
      2. Se valido → restituisce subito.
      3. Se invalido → costruisce un prompt di correzione e richiama call_ai_fn.
      4. Ripete fino a max_retries volte.
      5. Se ancora invalido → mette in quarantena e restituisce None.

    Args:
        chunk_text:         Il testo originale del chunk (per la quarantena).
        initial_output:     La risposta grezza dell'AI (può essere None).
        label:              Etichetta leggibile del chunk (per i log).
        original_file_path: Path del file sorgente (per la quarantena).
        call_ai_fn:         Callable con firma call_ai(content, label, **kwargs) → str|None.
        ai_folder_path:     Path della cartella Z_Cervello_IA.
        max_retries:        Numero massimo di tentativi di correzione.
        **kwargs:           Argomenti extra passati a call_ai_fn.

    Returns:
        Il testo validato, oppure None se irrecuperabile.
    """
    current_output = initial_output

    for attempt in range(max_retries + 1):  # tentativo 0 = validazione dell'output iniziale

        # --- Gestione output None ---
        if current_output is None:
            if attempt == max_retries:
                print(f"  ❌ Output None dopo {max_retries} retry su '{label}' → quarantena")
                quarantine(original_file_path, label, chunk_text, "", 
                           ValidationResult(False, ["Output API None"]), ai_folder_path)
                return None
            print(f"  ⚠️  Output None al tentativo {attempt}, riprovo da zero...")
            current_output = call_ai_fn(chunk_text, label, **kwargs)
            time.sleep(10)
            continue

        # --- Validazione ---
        result = validate(current_output)

        if result.warnings:
            print(f"  ⚡ Avvisi (non bloccanti) su '{label}': {'; '.join(result.warnings)}")

        if result.is_valid:
            if attempt > 0:
                print(f"  ✅ Corretto con successo al tentativo {attempt} su '{label}'")
            return current_output

        # --- Output invalido ---
        print(f"  ⚠️  Validazione fallita (tentativo {attempt}/{max_retries}) su '{label}': {result}")

        if attempt == max_retries:
            print(f"  ❌ Irrecuperabile dopo {max_retries} retry → quarantena")
            quarantine(original_file_path, label, chunk_text, current_output, result, ai_folder_path)
            return None

        # --- Costruisci il prompt di correzione e riprova ---
        correction_prompt = build_correction_prompt(current_output, result)
        print(f"  🔧 Invio prompt di correzione chirurgica (tentativo {attempt + 1}/{max_retries})...")
        time.sleep(5)
        # Per la correzione chirurgica NON passiamo le immagini (kwargs), 
        # perché lavoriamo solo sul testo malformato.
        current_output = call_ai_fn(correction_prompt, f"{label} [correzione {attempt + 1}]")

    return None  # non raggiungibile, ma rende mypy felice