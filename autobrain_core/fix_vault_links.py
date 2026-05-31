import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
CONVO_VAULT_PATH = os.getenv("CONVO_VAULT_PATH")

def fix_file(file_path, identity):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    changed = False
    hub_node = "Gemini CLI" if identity == "Gemini" else "Jarvis"
    
    # 1. Aggiunge 'fonte' se manca nel frontmatter
    if "fonte:" not in content and content.startswith("---"):
        # Trova il secondo ---
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            new_frontmatter = frontmatter.rstrip() + f"\nfonte: [[{hub_node}]]\n"
            content = f"---{new_frontmatter}---{parts[2]}"
            changed = True

    # 2. Converte riferimenti a file @path/to/file.py in [[path/to/file.py]]
    # Cerchiamo pattern che sembrano file e non sono già wikilink
    def replace_file(match):
        file_ref = match.group(1).lstrip("@")
        # Se è già dentro [[ ]], non facciamo nulla (regex negativa non banale qui, facciamo check manuale)
        return f"[[{file_ref}]]"

    # Regex migliorata: cattura solo i file che iniziano esplicitamente con @ (aggiunto dalla CLI)
    # oppure cattura file locali senza slash (es. script.py). Include i due punti per i dischi (es. C:\).
    # Esclude esplicitamente url http.
    new_content = re.sub(r'(?<!\[\[)(@(?:[A-Za-z]:)?[\w\-\.\/\\:]+\.[a-zA-Z0-9]+)(?<!\]\])', replace_file, content)
    
    if new_content != content:
        content = new_content
        changed = True

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def main():
    if not CONVO_VAULT_PATH:
        print("CONVO_VAULT_PATH non definita.")
        return

    folders = ["Gemini", "Jarvis"]
    total_fixed = 0

    for folder in folders:
        target = os.path.join(CONVO_VAULT_PATH, folder)
        if not os.path.exists(target): continue
        
        print(f"🛠️  Elaborazione cartella: {folder}")
        for file in os.listdir(target):
            if file.endswith(".md") and file != f"{folder}.md":
                if fix_file(os.path.join(target, file), folder):
                    print(f"  ✅ Link aggiunti a: {file}")
                    total_fixed += 1

    print(f"\n✨ Finito! Aggiornati {total_fixed} file.")

if __name__ == "__main__":
    main()
