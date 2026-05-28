import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configurazione Vault
VAULTS = {
    "UNI_VAULT": {
        "path": os.getenv("VAULT_PATH"),
        "concept_folder": "_Concepts"
    },
    "CONVO_VAULT": {
        "path": os.getenv("CONVO_VAULT_PATH"),
        "concept_folder": "_Concepts"
    }
}

def get_wikilink_frequencies(vault_path, concept_folder):
    """Conta quante volte ogni [[wikilink]] viene citato in file diversi."""
    link_counts = {} # { "NomeLink": set(["file1.md", "file2.md"]) }
    existing_files = set()
    
    # 1. Mappiamo tutti i file esistenti (escludendo la cartella dei concetti)
    for root, _, files in os.walk(vault_path):
        if concept_folder in root: continue
        for f in files:
            if f.endswith(".md"):
                existing_files.add(f[:-3].lower())
                
    # 2. Scansioniamo i file per contare le citazioni
    for root, dirs, files in os.walk(vault_path):
        if ".obsidian" in root or concept_folder in root:
            continue
            
        for f in files:
            if f.endswith(".md"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
                        for m in matches:
                            link = m.strip()
                            # Normalizziamo il link rimuovendo estensioni comuni
                            link_clean = link
                            if link_clean.lower().endswith(".md"): link_clean = link_clean[:-3]
                            if link_clean.lower().endswith(".pdf"): link_clean = link_clean[:-4]
                            
                            if link_clean.lower() not in existing_files:
                                if link_clean not in link_counts:
                                    link_counts[link_clean] = set()
                                link_counts[link_clean].add(f)
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
    
    link_frequencies = get_wikilink_frequencies(path, config["concept_folder"])
    
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
    
    # 2. Creazione/Aggiornamento: Materializziamo solo i ponti
    processed_count = 0
    for link in links_to_keep:
        safe_name = re.sub(r'[\\/*?:"<>|]', "", link)
        file_path = os.path.join(concept_dir, f"{safe_name}.md")
        
        # Recuperiamo le fonti (i padri)
        sources = sorted(list(link_frequencies[link]))
        backlinks_md = "\n".join([f"- [[{s}]]" for s in sources])

        content = f"""---
tipo: concetto
automatico: true
fonti_count: {len(sources)}
---

# {link}

Questo nodo è un **Ponte** che collega diversi documenti della base di conoscenza.

## 🔗 Menzionato in:
{backlinks_md}
"""
        
        try:
            # Scriviamo sempre (sovrascrivendo) per aggiornare i backlinks
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            processed_count += 1
        except Exception as e:
            print(f"  ❌ Errore nella scrittura di {safe_name}: {e}")
                
    print(f"  🧹 Rimosse {cleaned_count} vecchie definizioni isolate.")
    print(f"  ✅ Processati {processed_count} nodi ponte con relativi backlinks.")

def main():
    for name, config in VAULTS.items():
        materialize(name, config)
    print("\n✨ Operazione completata. Ricarica il Grafo 3D per vedere i collegamenti!")

if __name__ == "__main__":
    main()
