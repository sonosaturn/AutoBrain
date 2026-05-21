import os
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

MODEL_NAME = "gemini-3-flash-preview"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_ai_response(text):
    """Sintetizza la risposta dell'IA per il vault: toglie il codice e riassume il resto."""
    # Cattura riferimenti a file (es: main.py o @project\file.py) e li converte in wikilink
    files_mentioned = re.findall(r'(@?[\w\-\.\\]+\.\w+)', text)
    files_unique = sorted(list(set(files_mentioned)))
    # Puliamo i nomi dei file (togliamo @ se presente) e creiamo wikilink
    wikilinks = [f"[[{f.lstrip('@')}]]" for f in files_unique]
    files_str = f"\n\n**Modificati i seguenti file:** {', '.join(wikilinks)}" if wikilinks else ""
    
    summary_prompt = f"""Riassumi questa risposta dell'IA per l'archiviazione nel Secondo Cervello:
    - Organizza e riassumi il planning e la descrizione delle azioni eseguite in modo denso.
    - RIMUOVI COMPLETAMENTE OGNI BLOCCO DI CODICE (```...```).
    - Usa [[doppie parentesi quadre]] (wikilink) per termini tecnici, linguaggi di programmazione o concetti chiave.
    - Non aggiungere preamboli, vai dritto al riassunto.
    
    TESTO DA RIASSUMERE:
    {text}
    """
    try:
        summary_model = genai.GenerativeModel(MODEL_NAME)
        res = summary_model.generate_content(summary_prompt)
        return res.text.strip() + files_str
    except:
        clean_text = re.sub(r'```.*?```', '[Codice rimosso]', text, flags=re.DOTALL)
        return clean_text[:500] + "..." + files_str

class ConversationLogger:
    def __init__(self, identity="Gemini"):
        self.vault_path = os.getenv("CONVO_VAULT_PATH")
        if not self.vault_path:
            raise ValueError("CONVO_VAULT_PATH non trovata nel file .env")
        
        self.identity = identity
        self.target_folder = os.path.join(self.vault_path, self.identity)
        
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)
            
        self.current_session_file = None
        self._inizializza_sessione()

    def _inizializza_sessione(self):
        data_oggi = datetime.now().strftime("%Y-%m-%d")
        ora_avvio = datetime.now().strftime("%H-%M-%S")
        filename = f"{data_oggi}_{ora_avvio}_Sessione_{self.identity}.md"
        self.current_session_file = os.path.join(self.target_folder, filename)
        
        hub_node = "Gemini CLI" if self.identity == "Gemini" else "Jarvis"

        if not os.path.exists(self.current_session_file):
            with open(self.current_session_file, "w", encoding="utf-8") as f:
                f.write(f"---\n")
                f.write(f"data: {data_oggi}\n")
                f.write(f"ora_inizio: {ora_avvio}\n")
                f.write(f"tipo: sessione_ai\n")
                f.write(f"tags: [{self.identity.lower()}, conversazione, log]\n")
                f.write(f"fonte: [[{hub_node}]]\n")
                f.write(f"---\n\n")
                f.write(f"# Sessione {self.identity} - {data_oggi} ore {ora_avvio}\n\n")

    def log_messaggio(self, ruolo, testo, summarize=False):
        ora = datetime.now().strftime("%H:%M:%S")
        prefix = "👤 **Tu**"
        
        if ruolo == "user":
            prefix = "👤 **Tu**"
        elif ruolo in ["assistant", "jarvis"]:
            prefix = "🤖 **Jarvis**"
            if summarize:
                prefix += " (Riassunto)"
                testo = summarize_ai_response(testo)
        elif ruolo == "gemini_cli" or ruolo == "gemini":
            prefix = "💻 **Gemini CLI**"
            if summarize:
                prefix += " (Riassunto)"
                testo = summarize_ai_response(testo)
        else:
            prefix = f"**{ruolo}**"
        
        with open(self.current_session_file, "a", encoding="utf-8") as f:
            f.write(f"### [{ora}] {prefix}\n")
            f.write(f"{testo}\n\n")
            f.write("---\n\n")

    def log_interazione_completa(self, user_input, assistant_response, summarize=True):
        self.log_messaggio("user", user_input)
        self.log_messaggio("gemini_cli" if self.identity == "Gemini" else "assistant", assistant_response, summarize=summarize)
