import os
import json
import networkx as nx
from pathlib import Path
from graphify import extract, build, export, cluster
from dotenv import load_dotenv

load_dotenv()
# Nota: VAULT_PATH e CONVO_VAULT_PATH sono stringhe nel .env
VAULT_PATH = os.getenv("VAULT_PATH")
CONVO_VAULT_PATH = os.getenv("CONVO_VAULT_PATH")
GRAPH_OUTPUT_PATH = "graph.json"

def build_knowledge_graph():
    """Costruisce il Knowledge Graph dai vault."""
    print("🕸️ Inizio costruzione del Knowledge Graph...")
    
    roots = []
    if VAULT_PATH: roots.append(Path(VAULT_PATH))
    if CONVO_VAULT_PATH: roots.append(Path(CONVO_VAULT_PATH))
    
    all_files = []
    for root in roots:
        all_files.extend(extract.collect_files(root))
    
    if not all_files:
        print("  ⚠️ Nessun file trovato per il grafo.")
        return None

    print(f"  🔍 Analisi di {len(all_files)} file...")
    
    try:
        extractions = extract.extract(all_files)
        G = build.build([extractions])
        communities = cluster.cluster(G)
        export.to_json(G, communities, GRAPH_OUTPUT_PATH)
        
        print(f"  ✅ Grafo generato: {len(G.nodes)} nodi, {len(G.edges)} archi.")
        return G
    except Exception as e:
        print(f"  ❌ Errore durante la generazione del grafo: {e}")
        return None

def get_context_for_query(query_text, max_files=10):
    """
    Usa il grafo per trovare i file più rilevanti e ritorna il loro contenuto.
    """
    if not os.path.exists(GRAPH_OUTPUT_PATH):
        return "Nessuna conoscenza trovata (grafo non esistente)."
    
    try:
        with open(GRAPH_OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        nodes = data.get("nodes", [])
        
        # 1. Trova nodi che corrispondono alla query
        matched_files = set()
        query_words = query_text.lower().split()
        
        for node in nodes:
            label = node.get("label", "").lower()
            if any(word in label for word in query_words):
                source = node.get("source_file")
                if source:
                    # Normalizziamo il path
                    matched_files.add(source)
        
        if not matched_files:
            return "Nessun appunto rilevante trovato nel grafo per questa query."

        # 2. Carica il contenuto dei file (limitando il numero)
        context = ""
        count = 0
        
        # Priorità ai file che hanno più match o sono più centrali? 
        # Per ora usiamo i primi trovati.
        for rel_path in matched_files:
            if count >= max_files: break
            
            # Dobbiamo ricostruire il path assoluto. 
            # Il source_file nel JSON di Graphify è relativo alla root passata.
            # Ma qui potrebbe essere un mix. Proviamo a cercarlo.
            full_path = None
            for root in [VAULT_PATH, CONVO_VAULT_PATH]:
                if not root: continue
                temp_path = os.path.join(root, rel_path)
                if os.path.exists(temp_path):
                    full_path = temp_path
                    break
            
            if not full_path and os.path.exists(rel_path):
                full_path = rel_path

            if full_path and os.path.isfile(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        context += f"\n\n--- DOCUMENTO: {rel_path} ---\n"
                        context += f.read()
                    count += 1
                except: pass

        return context
    except Exception as e:
        return f"Errore durante il recupero del contesto dal grafo: {e}"

if __name__ == "__main__":
    build_knowledge_graph()
