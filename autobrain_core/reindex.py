import os
import time
import re
import logging
from brain import process_file, AI_FOLDER_PATH
from dotenv import load_dotenv

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
VAULT_PATH = os.getenv("VAULT_PATH")

VALID_FORMATS = (".md", ".pdf", ".txt", ".docx")

def get_already_processed() -> set[str]:
    """Retrieves the list of files already analyzed by checking the output folder."""
    processed = set()
    if not os.path.exists(AI_FOLDER_PATH):
        return processed
    for fname in os.listdir(AI_FOLDER_PATH):
        if not fname.endswith(".md"):
            continue
        # Standard prefix is "Analysis_"
        without_prefix = fname[len("Analysis_"):]
        # Regex to handle potential chunking or special naming
        match = re.match(r"(.+?\.\w+?)(?:_\d{3}_.*)?\.md$", without_prefix)
        if match:
            processed.add(match.group(1).lower())
    return processed

def reindex_all(force: bool = False) -> None:
    """Walks through the vault and triggers analysis for new or changed files."""
    print("🔄 Starting vault re-indexing...")
    already_done = set() if force else get_already_processed()
    if already_done:
        print(f"  ⏭️  {len(already_done)} files already processed, skipping.")
        print("      (use --force to reprocess everything)\n")

    processed_count = 0
    skipped_count   = 0

    for root, dirs, files in os.walk(VAULT_PATH):
        # Skip the AI output folder, system folders, and quarantine
        if os.path.basename(AI_FOLDER_PATH) in root or ".obsidian" in root or "_quarantine" in root or "_Concepts" in root:
            continue

        for file in files:
            if not file.lower().endswith(VALID_FORMATS):
                continue
            if not force and file.lower() in already_done:
                skipped_count += 1
                continue

            file_path = os.path.join(root, file)
            try:
                process_file(file_path)
                processed_count += 1
            except Exception as e:
                print(f"  ❌ CRITICAL ERROR on {file}: {e}")
                print("     Skipping file and proceeding...")
            time.sleep(1)

    print(f"\n✨ Completed: {processed_count} files processed, {skipped_count} skipped.")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    force = "--force" in args
    specific_files = [arg for arg in args if arg != "--force"]

    if specific_files:
        print(f"🎯 Target Mode: Reprocessing only specified files...")
        for target in specific_files:
            found = False
            for root, dirs, files in os.walk(VAULT_PATH):
                for file in files:
                    if file == target:
                        file_path = os.path.join(root, file)
                        print(f"  🔍 Found: {file_path}")
                        process_file(file_path)
                        found = True
            if not found:
                print(f"  ❌ File '{target}' not found in vault.")
    else:
        if force:
            print("⚠️ --force Mode: all files will be reprocessed.\n")
        reindex_all(force=force)
