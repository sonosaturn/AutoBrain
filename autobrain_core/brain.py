import fitz       # PyMuPDF for PDFs
import docx        # python-docx for Word files
import os
import time
import logging
import sys
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.genai import types

# Modular Import Logic
try:
    from core_utils import Config, models
    from sync_manager import auto_extract_cli_history
    from graph_manager import build_knowledge_graph
    from validator import validate_and_retry
    from usage_logger import log_usage
except ImportError:
    # Fallback for transition phase
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_utils import Config, models
    from sync_manager import auto_extract_cli_history
    from graph_manager import build_knowledge_graph
    from validator import validate_and_retry
    from usage_logger import log_usage

VAULT_PATH = Config.VAULT_PATH

# Initialize Google GenAI Client (Shared)
client = models.client

AI_FOLDER_NAME = "Z_AI_Cerebrum"
AI_FOLDER_PATH = os.path.join(VAULT_PATH, AI_FOLDER_NAME)
os.makedirs(AI_FOLDER_PATH, exist_ok=True)

# MODEL CONFIGURATION
# NOTE: gemini-3.5-flash has a strict daily quota (e.g. 20 req/day) on some free tiers.
# If reindexing many files, consider switching MODEL_FAST to Config.VOICE_MODEL.
MODEL_QUALITY = Config.VOICE_MODEL
MODEL_FAST    = Config.BRAIN_MODEL
DESCRIBE_IMAGES = True
FAST_MODEL_THRESHOLD = 8_000

# ---------------------------------------------------------------------------
# TEXT AND IMAGE EXTRACTION (GOOGLE NATIVE)
# ---------------------------------------------------------------------------

CODE_FONTS = ("courier", "mono", "code", "consolas", "jetbrains",
              "inconsolata", "firacode", "sourcecodepro", "lucidaconsole")

def extract_page_with_code(page) -> str:
    """Extracts text by detecting monospace fonts for code blocks."""
    blocks = page.get_text("dict")["blocks"]
    result = ""
    in_code = False

    for block in blocks:
        for line in block.get("lines", []):
            line_text = ""
            line_is_code = False
            for span in line.get("spans", []):
                font = span.get("font", "").lower()
                text = span.get("text", "")
                if any(f in font for f in CODE_FONTS):
                    line_is_code = True
                line_text += text + " "

            if line_is_code and not in_code:
                result += "\n```\n"
                in_code = True
            elif not line_is_code and in_code:
                result += "```\n"
                in_code = False
            result += line_text.rstrip() + "\n"

    if in_code: result += "```\n"
    return result

def extract_images_as_blobs(page) -> list:
    """Extracts images as types.Part for the Google SDK."""
    images = []
    doc = page.parent
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.alpha or pix.colorspace not in (fitz.csRGB, fitz.csGRAY):
                pix = fitz.Pixmap(fitz.csRGB, pix)
            if pix.width < 100 or pix.height < 100: continue
            
            img_bytes = pix.tobytes("png")
            # Correct format for google.genai SDK
            images.append(types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
        except: continue
    return images

# ---------------------------------------------------------------------------
# ANALYSIS CORE
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are the Second Brain Analyzer.
Your task is to transform documents into structured Markdown notes for Obsidian.

STRICT RULES:
1. ALWAYS respond in ITALIAN (to match the user's primary study language).
2. Use [[wikilinks]] for technical terms (use English for standard terms).
3. Start with an H1 title (#).
4. Always end with a '## Related Concepts' section containing wikilinks.
5. If images are present, describe them and integrate the analysis into the text naturally.
6. Do NOT include ANY preamble. Start immediately with #.
"""

def get_pdf_chunks(doc):
    """
    Groups PDF pages into logical chunks based on TOC or fixed page counts.
    Returns a list of (label, start_page, end_page).
    """
    toc = doc.get_toc()
    total_pages = len(doc)
    chunks = []

    if toc:
        # Filter for top-level entries and cleanup
        entries = [e for e in toc if e[0] == 1]
        
        # If there are many entries (like slides), group them
        MAX_CHUNKS_PER_FILE = 15
        if len(entries) > MAX_CHUNKS_PER_FILE:
            # Group every N entries
            group_size = (len(entries) // MAX_CHUNKS_PER_FILE) + 1
            for i in range(0, len(entries), group_size):
                group = entries[i : i + group_size]
                start = group[0][2] - 1 # 0-indexed
                end = entries[i + group_size][2] - 1 if i + group_size < len(entries) else total_pages
                
                label = group[0][1]
                # Clean label for filename
                label = re.sub(r'[\\/:*?"<>|]', "", label).strip()
                chunks.append((label, start, end))
        else:
            # Standard TOC chunking
            for i, entry in enumerate(entries):
                start = entry[2] - 1
                end = entries[i+1][2] - 1 if i+1 < len(entries) else total_pages
                label = re.sub(r'[\\/:*?"<>|]', "", entry[1]).strip()
                chunks.append((label, start, end))
    
    # Fallback or too few chunks
    if not chunks or (len(chunks) == 1 and total_pages > 20):
        # Page-based split (every 10 pages)
        PAGE_STEP = 10
        for i in range(0, total_pages, PAGE_STEP):
            start = i
            end = min(i + PAGE_STEP, total_pages)
            label = f"Parte { (i // PAGE_STEP) + 1}"
            chunks.append((label, start, end))
            
    return chunks

def call_ai_native(content: str, label: str, images: list = None) -> str:
    """Sends text and images to Gemini using the native SDK."""
    word_count = len(content.split())
    # Choose model: Flash for images or long text, Pro for the rest.
    model_name = MODEL_FAST if word_count > FAST_MODEL_THRESHOLD or images else MODEL_QUALITY
    
    logging.info(f"🤖 AI Engine ({model_name}) -> '{label}'")
    
    # Prepare multimodal content
    prompt_parts = [content]
    if images:
        prompt_parts.extend(images)
    
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt_parts,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "temperature": 0.1
            }
        )
        try:
            usage = response.usage_metadata
            if usage:
                log_usage(model_name, usage.prompt_token_count, usage.candidates_token_count, task_type="analysis")
        except:
            pass
        return response.text
    except Exception as e:
        logging.error(f"❌ Gemini API Error: {e}")
        return None

def process_file(file_path: str):
    """Processes a single file by extracting data and invoking the AI."""
    logging.info(f"🧠 Processing file: {os.path.basename(file_path)}")
    ext = file_path.lower().split(".")[-1]
    
    try:
        if ext == "pdf":
            doc = fitz.open(file_path)
            chunks = get_pdf_chunks(doc)
            
            for i, (label, start, end) in enumerate(chunks):
                chunk_text = ""
                chunk_images = []
                chunk_id = f"{i+1:03}"
                full_label = f"{os.path.basename(file_path)}_{chunk_id}_{label}"
                
                logging.info(f"📄 Processing chunk {chunk_id}: {label} (pages {start+1}-{end})")
                
                for page_num in range(start, end):
                    page = doc[page_num]
                    chunk_text += extract_page_with_code(page)
                    if DESCRIBE_IMAGES:
                        chunk_images.extend(extract_images_as_blobs(page))

                if not chunk_text.strip() and not chunk_images:
                    continue

                # AI call with validation and retry
                output = call_ai_native(chunk_text, full_label, images=chunk_images[:15])
                
                valid_output = validate_and_retry(
                    chunk_text=chunk_text,
                    initial_output=output,
                    label=full_label,
                    original_file_path=file_path,
                    call_ai_fn=lambda c, l: call_ai_native(c, l, images=chunk_images[:15]),
                    ai_folder_path=AI_FOLDER_PATH
                )
                
                if valid_output:
                    out_name = f"Analysis_{full_label}.md"
                    with open(os.path.join(AI_FOLDER_PATH, out_name), "w", encoding="utf-8") as f:
                        f.write(f"---\nsource: [[{os.path.basename(file_path)}]]\n---\n\n{valid_output}")
                    logging.info(f"✅ Chunk saved: {out_name}")

        elif ext in ("md", "txt", "docx"):
            full_text = ""
            if ext in ("md", "txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    full_text = f.read()
            else: # docx
                doc = docx.Document(file_path)
                full_text = "\n".join(p.text for p in doc.paragraphs)

            if not full_text.strip():
                return

            # AI call with validation and retry
            output = call_ai_native(full_text, os.path.basename(file_path))
            
            valid_output = validate_and_retry(
                chunk_text=full_text,
                initial_output=output,
                label=os.path.basename(file_path),
                original_file_path=file_path,
                call_ai_fn=lambda c, l: call_ai_native(c, l),
                ai_folder_path=AI_FOLDER_PATH
            )
            
            if valid_output:
                out_name = f"Analysis_{os.path.basename(file_path)}.md"
                with open(os.path.join(AI_FOLDER_PATH, out_name), "w", encoding="utf-8") as f:
                    f.write(f"---\nsource: [[{os.path.basename(file_path)}]]\n---\n\n{valid_output}")
                logging.info(f"✅ Analysis saved: {out_name}")

    except Exception as e:
        logging.error(f"❌ Error during processing of {file_path}: {e}")

# Debounce
last_processed = {}

class VaultHandler(FileSystemEventHandler):
    """Event handler for folder monitoring."""
    def on_modified(self, event):
        if event.is_directory: return
        if event.src_path.lower().endswith((".pdf", ".md", ".txt", ".docx")):
            if AI_FOLDER_NAME in event.src_path: return
            
            now = time.time()
            if event.src_path in last_processed and (now - last_processed[event.src_path]) < 5:
                return
            last_processed[event.src_path] = now
            
            logging.info(f"🔍 Modification detected on: {os.path.basename(event.src_path)}")
            time.sleep(2) # Pause to allow writing to finish
            process_file(event.src_path)

def maintenance_task():
    """Checks project status and environment consistency."""
    try:
        # We no longer perform automatic 'pip freeze' to avoid polluting the requirements.txt
        # with every package installed in the local environment.
        # Dependency management should be intentional.
        logging.info("📝 Maintenance check completed (Auto-freeze disabled for portability).")
    except Exception as e:
        logging.error(f"⚠️ Error during maintenance: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"🚀 Brain Engine 3.0 (Super-Build) active on {VAULT_PATH}")
    
    # Run initial maintenance check
    maintenance_task()

    # 1. Initial CLI and Graph sync
    auto_extract_cli_history()
    build_knowledge_graph()
    
    event_handler = VaultHandler()
    observer = Observer()
    observer.schedule(event_handler, VAULT_PATH, recursive=True)
    observer.start()
    
    last_cli_check = time.time()
    last_maintenance = time.time()
    try:
        while True: 
            time.sleep(1)
            now = time.time()
            # Period check every 5 minutes
            if now - last_cli_check > 300:
                auto_extract_cli_history()
                build_knowledge_graph()
                last_cli_check = now
            
            # Maintenance (requirements) every hour
            if now - last_maintenance > 3600:
                maintenance_task()
                last_maintenance = now
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
