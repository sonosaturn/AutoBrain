"""
validator.py — Structural validation and intelligent retry system for the Second Brain.

Three-level architecture:
  1. Deterministic validation (zero API cost)
  2. Retry with surgical correction prompt
  3. Quarantine with diagnostic log for unrecoverable cases
"""

import re
import os
import json
import time
from datetime import datetime
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# VALIDATION RESULT STRUCTURE
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self):
        parts = []
        if self.errors:
            parts.append("ERRORS: " + "; ".join(self.errors))
        if self.warnings:
            parts.append("WARNINGS: " + "; ".join(self.warnings))
        return " | ".join(parts) if parts else "OK"


# ---------------------------------------------------------------------------
# LEVEL 1 — STRUCTURAL VALIDATOR (deterministic, no API)
# ---------------------------------------------------------------------------

# These rules map exactly to the processing rules in your SYSTEM_PROMPT.
# Each rule is a function that receives the text and returns an error message
# (string) if the rule is violated, or None if it is respected.

def _rule_has_h1_title(text: str) -> str | None:
    """The document must start with an H1 title (#)."""
    stripped = text.strip()
    if not stripped.startswith("#"):
        # Check if at least one H1 exists in the text (there might be residue CoT before)
        if re.search(r"^#\s+\S", text, re.MULTILINE):
            return "Text before the first H1 title (residue CoT)"
        return "No H1 title found"
    return None


def _rule_no_cot_markers(text: str) -> str | None:
    """
    Looks for typical Chain-of-Thought patterns that shouldn't survive
    _strip_cot(), but sometimes hide within the text.
    """
    COT_PATTERNS = [
        r"^\s*(okay|ok|alright|bene|perfetto|certo)[,.]?\s*[\w]",  # conversational opening phrases
        r"^(let me|lasciami|vediamo|analizziamo|procedo)\b",        # reasoning intro
        r"<think>",                                                    # explicit thinking tags
        r"</think>",
        r"^\s*\*\*?(nota|note|avviso|attention)\*\*?:",              # AI meta-notes
    ]
    for pattern in COT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return f"Possible residue CoT: pattern '{pattern[:30]}...'"
    return None


def _rule_code_blocks_closed(text: str) -> str | None:
    """The code blocks ``` must be properly opened and closed."""
    count = len(re.findall(r"^```", text, re.MULTILINE))
    if count % 2 != 0:
        return f"Unbalanced code blocks ({count} backtick-fences found, must be even)"
    return None


def _rule_has_correlati_section(text: str) -> str | None:
    """The document must end with the 'Related Concepts' section."""
    if not re.search(r"related\s+concepts\b", text, re.IGNORECASE):
        return "Missing 'Related Concepts' section"
    return None


def _rule_has_wikilinks(text: str) -> str | None:
    """
    There must be at least one [[wikilink]].
    If there are none at all, something went wrong with the formatting.
    """
    if not re.search(r"\[\[.+?\]\]", text):
        return "No [[wikilinks]] found in the document"
    return None


def _rule_minimum_length(text: str, min_words: int = 80) -> str | None:
    """Output too short is suspicious (truncated response or silent refusal)."""
    word_count = len(text.split())
    if word_count < min_words:
        return f"Output too short ({word_count} words, minimum {min_words})"
    return None


def _rule_no_truncation_markers(text: str) -> str | None:
    """
    Some models signal truncation with typical phrases.
    """
    TRUNCATION_PATTERNS = [
        r"\.\.\.\s*$",                             # ends with "..."
        r"\[continued\]",
        r"\[truncated\]",
        r"(the text continues|to be continued)",
        r"(max.{0,20}token|context.{0,20}limit)",
    ]
    last_500 = text[-500:]  # only check the tail
    for pattern in TRUNCATION_PATTERNS:
        if re.search(pattern, last_500, re.IGNORECASE):
            return f"Possible truncation detected: '{pattern}'"
    return None


# Rule Registry: (function, is_blocking)
# Blocking rules cause is_valid=False; non-blocking rules only produce warnings.
VALIDATION_RULES: list[tuple] = [
    (_rule_has_h1_title,           True),
    (_rule_no_cot_markers,         True),
    (_rule_code_blocks_closed,     True),
    (_rule_has_correlati_section,  True),
    (_rule_has_wikilinks,          False),   # warning: could be legitimately absent
    (_rule_minimum_length,         True),
    (_rule_no_truncation_markers,  False),   # warning: could be model style
]


def validate(text: str) -> ValidationResult:
    """
    Executes all validation rules and returns a ValidationResult.
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
# LEVEL 2 — SURGICAL CORRECTION PROMPT
# ---------------------------------------------------------------------------

def build_correction_prompt(broken_output: str, validation_result: ValidationResult) -> str:
    """
    Builds a targeted prompt that describes exactly what to fix,
    attaching the malformed output and asking ONLY for the repair.
    """
    error_list = "\n".join(f"- {e}" for e in validation_result.errors)

    return f"""The Markdown document you generated contains the following structural problems that MUST be corrected:

{error_list}

Below is the malformed output. Return EXCLUSIVELY the corrected document, without any additional explanation or comment. Do not re-analyze the original content: only fix the issues listed above keeping everything else identical.

--- OUTPUT TO CORRECT ---
{broken_output}
--- END OUTPUT ---"""


# ---------------------------------------------------------------------------
# LEVEL 3 — QUARANTINE
# ---------------------------------------------------------------------------

QUARANTINE_FOLDER = "_quarantine"


def quarantine(
    original_file_path: str,
    chunk_label: str,
    chunk_text: str,
    broken_output: str,
    validation_result: ValidationResult,
    ai_folder_path: str,
) -> None:
    """
    Saves the problematic chunk in a quarantine subfolder with:
    - The original chunk text
    - The malformed output produced by the AI
    - A JSON diagnostic report
    """
    quarantine_path = os.path.join(ai_folder_path, QUARANTINE_FOLDER)
    os.makedirs(quarantine_path, exist_ok=True)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_label = re.sub(r"[\\/:*?\"<>|'\s]", "_", chunk_label)[:50]
    prefix     = f"{timestamp}_{base_label}"

    # 1. Save original chunk text
    with open(os.path.join(quarantine_path, f"{prefix}_INPUT.txt"), "w", encoding="utf-8") as f:
        f.write(chunk_text)

    # 2. Save malformed output
    with open(os.path.join(quarantine_path, f"{prefix}_OUTPUT.md"), "w", encoding="utf-8") as f:
        f.write(broken_output or "(empty output)")

    # 3. Save diagnostic report
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

    print(f"  🔴 Quarantined: {prefix}_*.* (see {QUARANTINE_FOLDER}/)")


# ---------------------------------------------------------------------------
# MAIN INTERFACE — to be used in brain.py
# ---------------------------------------------------------------------------

def validate_and_retry(
    chunk_text: str,
    initial_output: str | None,
    label: str,
    original_file_path: str,
    call_ai_fn,          # pass brain.py's call_ai function
    ai_folder_path: str,
    max_retries: int = 2,
    **kwargs            # extra arguments for call_ai_fn (e.g. images)
) -> str | None:
    """
    Main orchestrator of the validation system.

    Flow:
      1. Validates the initial output.
      2. If valid → returns immediately.
      3. If invalid → builds a correction prompt and calls call_ai_fn.
      4. Repeats up to max_retries times.
      5. If still invalid → puts in quarantine and returns None.

    Args:
        chunk_text:         Original chunk text (for quarantine).
        initial_output:     Raw AI response (can be None).
        label:              Readable chunk label (for logs).
        original_file_path: Source file path (for quarantine).
        call_ai_fn:         Callable with signature call_ai(content, label, **kwargs) → str|None.
        ai_folder_path:     Path of the Z_AI_Cerebrum folder.
        max_retries:        Maximum number of correction attempts.
        **kwargs:           Extra arguments passed to call_ai_fn.

    Returns:
        The validated text, or None if unrecoverable.
    """
    current_output = initial_output

    for attempt in range(max_retries + 1):  # attempt 0 = validation of initial output

        # --- Handle None output ---
        if current_output is None:
            if attempt == max_retries:
                print(f"  ❌ Output None after {max_retries} retries on '{label}' → quarantine")
                quarantine(original_file_path, label, chunk_text, "", 
                           ValidationResult(False, ["API Output None"]), ai_folder_path)
                return None
            print(f"  ⚠️  Output None at attempt {attempt}, retrying from scratch...")
            current_output = call_ai_fn(chunk_text, label, **kwargs)
            time.sleep(10)
            continue

        # --- Validation ---
        result = validate(current_output)

        if result.warnings:
            print(f"  ⚡ Warnings (non-blocking) on '{label}': {'; '.join(result.warnings)}")

        if result.is_valid:
            if attempt > 0:
                print(f"  ✅ Successfully corrected at attempt {attempt} on '{label}'")
            return current_output

        # --- Invalid output ---
        print(f"  ⚠️  Validation failed (attempt {attempt}/{max_retries}) on '{label}': {result}")

        if attempt == max_retries:
            print(f"  ❌ Unrecoverable after {max_retries} retries → quarantine")
            quarantine(original_file_path, label, chunk_text, current_output, result, ai_folder_path)
            return None

        # --- Build correction prompt and retry ---
        correction_prompt = build_correction_prompt(current_output, result)
        print(f"  🔧 Sending surgical correction prompt (attempt {attempt + 1}/{max_retries})...")
        time.sleep(5)
        # For surgical correction we do NOT pass images (kwargs),
        # because we are only working on the malformed text.
        current_output = call_ai_fn(correction_prompt, f"{label} [correction {attempt + 1}]")

    return None
