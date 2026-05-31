import os
import json
import networkx as nx
import math
from pathlib import Path
from graphify import extract, build, export, cluster
from dotenv import load_dotenv

load_dotenv()
# Percorso radice del progetto
PROJECT_ROOT = Path(__file__).parent.parent
VAULT_PATH = os.getenv("VAULT_PATH")
CONVO_VAULT_PATH = os.getenv("CONVO_VAULT_PATH")
GRAPH_OUTPUT_PATH = str(PROJECT_ROOT / "graph.json")

def build_knowledge_graph():
    """Costruisce il Knowledge Graph dai vault."""
    print("🕸️ Inizio costruzione del Knowledge Graph...")
    
    roots = []
    if VAULT_PATH: roots.append(Path(VAULT_PATH))
    if CONVO_VAULT_PATH: roots.append(Path(CONVO_VAULT_PATH))
    
    all_files = []
    for root in roots:
        if root.exists():
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
    Usa il grafo per trovare i file più rilevanti applicando il 
    Link-Density Weighted Retrieval (LDWR).
    """
    if not os.path.exists(GRAPH_OUTPUT_PATH):
        return "Nessuna conoscenza trovata (grafo non esistente)."
    
    try:
        with open(GRAPH_OUTPUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        nodes = data.get("nodes", [])
        links = data.get("links", [])
        
        # 1. Calcolo Link Density (Centralità di grado)
        # Contiamo quanti archi entrano o escono da ogni nodo
        degree_map = {}
        for link in links:
            s, t = link.get("source"), link.get("target")
            degree_map[s] = degree_map.get(s, 0) + 1
            degree_map[t] = degree_map.get(t, 0) + 1

        # 2. Scoring dei nodi basato su Query Match + LDWR
        scored_files = {} # { "path": score }
        query_words = [w.lower() for w in query_text.lower().split() if len(w) > 2]
        
        for node in nodes:
            label = node.get("label", "").lower()
            source = node.get("source_file")
            if not source: continue
            
            # Calcolo match semantico (molto semplificato)
            match_count = sum(1 for word in query_words if word in label)
            
            if match_count > 0:
                # LDWR Boost: Boost = log(Degree + 1)
                # Più il nodo è connesso, più è considerato un "Knowledge Hub"
                degree = degree_map.get(node.get("id"), 0)
                ldwr_boost = math.log1p(degree)
                
                final_score = match_count * (1 + ldwr_boost)
                
                if source not in scored_files or final_score > scored_files[source]:
                    scored_files[source] = final_score
        
        if not scored_files:
            return "Nessun appunto rilevante trovato nel grafo per questa query."

        # 3. Ordinamento per score decrescente
        sorted_files = sorted(scored_files.items(), key=lambda x: x[1], reverse=True)
        
        # 4. Carica il contenuto dei file (limitando il numero)
        context = ""
        count = 0
        
        for rel_path, score in sorted_files:
            if count >= max_files: break
            
            full_path = None
            # Tenta di trovare il file nelle varie root, considerando anche le sottocartelle
            # tipiche come 'Jarvis' per il Convo Vault
            for root in [VAULT_PATH, CONVO_VAULT_PATH]:
                if not root: continue
                
                # Check 1: Root diretta
                p1 = os.path.join(root, rel_path)
                # Check 2: Sottocartella Jarvis (comune nel progetto)
                p2 = os.path.join(root, "Jarvis", rel_path)
                # Check 3: Sottocartella Gemini (comune nel progetto)
                p3 = os.path.join(root, "Gemini", rel_path)
                
                for p in [p1, p2, p3]:
                    if os.path.exists(p) and os.path.isfile(p):
                        full_path = p
                        break
                if full_path: break
            
            if not full_path and os.path.exists(rel_path):
                full_path = rel_path

            if full_path:
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        context += f"\n\n--- DOCUMENTO: {rel_path} (Relevance Score: {score:.2f}) ---\n"
                        context += f.read()
                    count += 1
                except: pass

        return context
    except Exception as e:
        return f"Errore durante il recupero del contesto dal grafo: {e}"

if __name__ == "__main__":
    build_knowledge_graph()
