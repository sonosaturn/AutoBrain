import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configurazione Vault
VAULTS = {
    "UNI_VAULT": {
        "path": os.getenv("VAULT_PATH"),
        "concept_folder": "_Concetti"
    },
    "CONVO_VAULT": {
        "path": os.getenv("CONVO_VAULT_PATH"),
        "concept_folder": "_Concetti"
    }
}

def get_wikilink_frequencies(vault_path):
    """Conta quante volte ogni [[wikilink]] viene citato in file diversi."""
    link_counts = {} # { "NomeLink": set(["file1.md", "file2.md"]) }
    existing_files = set()
    
    # 1. Mappiamo tutti i file esistenti (escludendo la cartella _Concetti)
    for root, _, files in os.walk(vault_path):
        if "_Concetti" in root: continue
        for f in files:
            if f.endswith(".md"):
                existing_files.add(f[:-3].lower())
                
    # 2. Scansioniamo i file per contare le citazioni
    for root, dirs, files in os.walk(vault_path):
        if ".obsidian" in root or "_Concetti" in root:
            continue
            
        for f in files:
            if f.endswith(".md"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
                        for m in matches:
                            link = m.strip()
                            if link.lower() not in existing_files:
                                if link not in link_counts:
                                    link_counts[link] = set()
                                link_counts[link].add(f)
                except: pass
                    
    return link_counts

def materialize(vault_name, config):
    path = config["path"]
    concept_dir = os.path.join(path, config["concept_folder"])
    
    if not path or not os.path.exists(path):
        print(f"❌ Path non valida per {vault_name}")
        return

    print(f"🧠 Ottimizzazione nodi per: {vault_name}")
    os.makedirs(concept_dir, exist_ok=True)
    
    link_frequencies = get_wikilink_frequencies(path)
    
    # Filtriamo: solo i link citati in almeno 2 file diversi
    links_to_keep = {link for link, sources in link_frequencies.items() if len(sources) >= 2}
    
    print(f"  🔍 Trovati {len(link_frequencies)} link unici.")
    print(f"  🎯 {len(links_to_keep)} di questi sono 'ponti' (citati in 2+ file).")
    
    # 1. Pulizia: Rimuoviamo i file in _Concetti che non sono più necessari
    cleaned_count = 0
    for f in os.listdir(concept_dir):
        if f.endswith(".md"):
            name_no_ext = f[:-3]
            if name_no_ext not in links_to_keep:
                try:
                    os.remove(os.path.join(concept_dir, f))
                    cleaned_count += 1
                except: pass
    
    # 2. Creazione: Materializziamo solo i ponti
    created_count = 0
    for link in links_to_keep:
        safe_name = re.sub(r'[\\/*?:"<>|]', "", link)
        file_path = os.path.join(concept_dir, f"{safe_name}.md")
        
        if not os.path.exists(file_path):
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"---\ntipo: concetto\nautomatico: true\n---\n\n# {link}\n\nQuesto nodo è un 'Ponte' in quanto citato in più documenti.")
                created_count += 1
            except: pass
                
    print(f"  🧹 Rimosse {cleaned_count} vecchie definizioni isolate.")
    print(f"  ✅ Creati {created_count} nuovi nodi ponte.")

def main():
    for name, config in VAULTS.items():
        materialize(name, config)
    print("\n✨ Operazione completata. Ricarica il Grafo 3D per vedere i collegamenti!")

if __name__ == "__main__":
    main()
