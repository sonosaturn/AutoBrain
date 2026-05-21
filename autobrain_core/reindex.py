import os
import time
import re
from brain import process_file, AI_FOLDER_PATH
from dotenv import load_dotenv

load_dotenv()
VAULT_PATH = os.getenv("VAULT_PATH")

FORMATI_VALIDI = (".md", ".pdf", ".txt", ".docx")

def get_already_processed() -> set[str]:
    processed = set()
    if not os.path.exists(AI_FOLDER_PATH):
        return processed
    for fname in os.listdir(AI_FOLDER_PATH):
        if not fname.endswith(".md"):
            continue
        senza_prefisso = fname[len("Analisi_"):]
        match = re.match(r"(.+?\.\w+?)(?:_\d{3}_.*)?\.md$", senza_prefisso)
        if match:
            processed.add(match.group(1).lower())
    return processed

def reindex_all(force: bool = False) -> None:
    print("🔄 Inizio ri-elaborazione del vault...")
    already_done = set() if force else get_already_processed()
    if already_done:
        print(f"  ⏭️  {len(already_done)} file già processati, verranno saltati.")
        print("      (usa --force per riprocessare tutto)\n")

    processed_count = 0
    skipped_count   = 0

    for root, dirs, files in os.walk(VAULT_PATH):
        if "Z_Cervello_IA" in root or ".obsidian" in root:
            continue

        for file in files:
            if not file.lower().endswith(FORMATI_VALIDI):
                continue
            if not force and file.lower() in already_done:
                skipped_count += 1
                continue

            file_path = os.path.join(root, file)
            try:
                process_file(file_path)
                processed_count += 1
            except Exception as e:
                print(f"  ❌ ERRORE CRITICO su {file}: {e}")
                print("     Salto il file e procedo con il prossimo...")
            time.sleep(1)

    print(f"\n✨ Completato: {processed_count} file processati, {skipped_count} saltati.")

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    force = "--force" in args
    file_specifici = [arg for arg in args if arg != "--force"]

    if file_specifici:
        print(f"🎯 Modalità Target: Riprocesso solo i file specificati...")
        for target in file_specifici:
            trovato = False
            for root, dirs, files in os.walk(VAULT_PATH):
                for file in files:
                    if file == target:
                        file_path = os.path.join(root, file)
                        print(f"  🔍 Trovato: {file_path}")
                        process_file(file_path)
                        trovato = True
            if not trovato:
                print(f"  ❌ File '{target}' non trovato nel vault.")
    else:
        if force:
            print("⚠️ Modalità --force: tutti i file verranno riprocessati.\n")
        reindex_all(force=force)
