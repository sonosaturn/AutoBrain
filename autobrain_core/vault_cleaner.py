import os
import re
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
VAULT_PATH = os.getenv("VAULT_PATH")
AI_FOLDER = "Z_AI_Cerebrum"
CONCEPTS_FOLDER = "_Concepts"
QUARANTINE_FOLDER = "_quarantine"

def clean_vault():
    print(f"🧹 Starting Vault Cleanup in: {VAULT_PATH}")
    
    # 1. Remove .md.md files in Z_AI_Cerebrum and _Concepts
    ai_path = Path(VAULT_PATH) / AI_FOLDER
    concepts_path = Path(VAULT_PATH) / CONCEPTS_FOLDER
    
    for folder_path in [ai_path, concepts_path]:
        if folder_path.exists():
            print(f"🔍 Checking for double extensions in {folder_path.name}...")
            for file in folder_path.glob("*.md.md"):
                print(f"  🗑️ Deleting double extension: {file.name}")
                file.unlink()

    # 2. Move stray .md files from root to _Concepts
    print("🔍 Checking for misplaced .md files in root...")
    for file in Path(VAULT_PATH).glob("*.md"):
        # Don't move if it's a known root file or starting with underscore
        if not file.name.startswith("_"):
            target = concepts_path / file.name
            print(f"  📦 Moving {file.name} to {CONCEPTS_FOLDER}/")
            if target.exists():
                # Merge or delete if empty
                if file.stat().st_size == 0:
                    file.unlink()
                else:
                    shutil.move(str(file), str(target))
            else:
                shutil.move(str(file), str(target))

    # 3. Clean up _quarantine
    quarantine_path = ai_path / QUARANTINE_FOLDER
    if quarantine_path.exists():
        print("🔍 Cleaning up quarantine folder...")
        # Normalize filenames for comparison (lowercase, no spaces, no underscores)
        def normalize(name):
            return re.sub(r"[_\s\-]", "", name.lower())

        processed_files = [normalize(f.name.replace("Analysis_", "").replace(".md", "")) for f in ai_path.glob("Analysis_*.md")]
        
        for file in quarantine_path.iterdir():
            # Match 20260526_011548_FILENAME_INPUT.txt
            match = re.search(r"^\d+_\d+_(.+?)(?:_INPUT|_OUTPUT|_REPORT)", file.name)
            if match:
                original_base_norm = normalize(match.group(1))
                # Check if this normalized base is in our processed set
                if any(original_base_norm in p for p in processed_files) or any(p in original_base_norm for p in processed_files):
                    print(f"  🗑️ Deleting redundant quarantine item: {file.name}")
                    file.unlink()

    # 3. Consolidate _Concepts (e.g., CNN vs CNNs)
    concepts_path = Path(VAULT_PATH) / CONCEPTS_FOLDER
    if concepts_path.exists():
        print("🔍 Consolidating duplicate concepts...")
        concepts = list(concepts_path.glob("*.md"))
        concept_names = {c.stem.lower(): c for c in concepts}
        
        # Identify plural/singular duplicates (simple heuristic)
        for name, path in list(concept_names.items()):
            if name.endswith("s") and name[:-1] in concept_names:
                main_concept = concept_names[name[:-1]]
                print(f"  🔄 Found duplicate concept: '{path.name}' -> '{main_concept.name}'")
                # In Obsidian, we'd ideally merge, but here we'll just delete the plural 
                # if the singular exists, as they are likely auto-generated stubs.
                if path.stat().st_size <= main_concept.stat().st_size:
                    print(f"  🗑️ Deleting plural duplicate: {path.name}")
                    path.unlink()
            
    print("\n✨ Cleanup finished.")

if __name__ == "__main__":
    clean_vault()
