import os
import re

VAULT_PATH = os.getenv("VAULT_PATH", r"C:\Users\Lorenzo\Documents\uni vault")

def remove_isolated_wikilinks(vault_path):
    print("🕸️ Avvio rimozione wikilink isolati dal testo Markdown...")
    
    # 1. Contiamo le frequenze di ogni wikilink
    link_counts = {}
    
    for root, _, files in os.walk(vault_path):
        if ".obsidian" in root: continue
        for f in files:
            if f.endswith(".md"):
                try:
                    with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                        content = file.read()
                        matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
                        for m in matches:
                            link = m.strip()
                            if link not in link_counts:
                                link_counts[link] = set()
                            link_counts[link].add(f)
                except: pass
                
    # 2. Identifichiamo i link isolati (citati in 1 solo file) CHE NON HANNO un file fisico
    existing_files = set()
    for root, _, files in os.walk(vault_path):
        for f in files:
            if f.endswith(".md"):
                existing_files.add(f[:-3].lower())

    isolated_links = set()
    for link, sources in link_counts.items():
        if len(sources) == 1 and link.lower() not in existing_files:
            isolated_links.add(link)
            
    print(f"  🔍 Trovati {len(isolated_links)} wikilink isolati (senza file e con 1 sola citazione).")
    
    # 3. Rimuoviamo le parentesi [[ ]] dal testo per questi link
    files_modified = 0
    links_removed = 0
    
    for root, _, files in os.walk(vault_path):
        if ".obsidian" in root: continue
        for f in files:
            if f.endswith(".md"):
                file_path = os.path.join(root, f)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        
                    original_content = content
                    
                    def replace_link(match):
                        full_match = match.group(0) # es: [[Gunrock]] o [[Gunrock|Alias]]
                        link_target = match.group(1).strip()
                        if link_target in isolated_links:
                            nonlocal links_removed
                            links_removed += 1
                            # Restituisce solo il testo, rimuovendo le parentesi
                            # Se c'è un alias [[Target|Alias]], restituisce l'alias
                            if "|" in full_match:
                                return full_match[2:-2].split("|")[1]
                            return link_target
                        return full_match
                        
                    content = re.sub(r"\[\[([^\]]+)\]\]", replace_link, content)
                    
                    if content != original_content:
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(content)
                        files_modified += 1
                except Exception as e:
                    pass
                    
    print(f"  ✅ Rimossi {links_removed} collegamenti da {files_modified} file.")
    print("  ✨ Ora i 'nodi fantasma' spariranno definitivamente dal grafo 3D.")

if __name__ == "__main__":
    remove_isolated_wikilinks(VAULT_PATH)
