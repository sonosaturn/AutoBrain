import os
import json
import re
import time
from datetime import datetime
from dotenv import load_dotenv

# Importazione locale per la sintesi
try:
    from logger import summarize_ai_response
except ImportError:
    def summarize_ai_response(text): return text

load_dotenv()
CONVO_VAULT_PATH = os.getenv("CONVO_VAULT_PATH")

# Tentativo di trovare il percorso corretto dei log della CLI
possible_paths = [
    os.path.join(os.environ.get("USERPROFILE", ""), ".gemini", "tmp", "desktop", "chats"),
    os.path.join(os.environ.get("USERPROFILE", ""), ".gemini", "tmp", "Lorenzo", "chats"),
    r"C:\Users\Lorenzo\\.gemini\tmp\Lorenzo\chats"
]

CLI_CHATS_PATH = None
for p in possible_paths:
    if os.path.exists(p):
        CLI_CHATS_PATH = p
        break

if not CLI_CHATS_PATH:
    CLI_CHATS_PATH = possible_paths[0] # Fallback

def parse_cli_content(content):
    if isinstance(content, list):
        text = "".join([part.get("text", "") for part in content if "text" in part])
    elif isinstance(content, str):
        text = content
    else:
        return ""

    # Rimuove blocchi di "Content from referenced files" che sporcano il log
    # Questi blocchi iniziano con '--- Content from referenced files ---' e finiscono con '--- End of content ---'
    text = re.sub(r'--- Content from referenced files ---.*?--- End of content ---', 
                  '[Contenuto tecnico rimosso per pulizia]', 
                  text, 
                  flags=re.DOTALL)
    
    # Rimuove anche eventuali blocchi 'Newly Discovered Project Context'
    text = re.sub(r'--- Newly Discovered Project Context ---.*?--- End Project Context ---', 
                  '[Contesto progetto rimosso per pulizia]', 
                  text, 
                  flags=re.DOTALL)

    return text.strip()

def auto_extract_cli_history():
    """Scansiona i log della CLI e li converte in Markdown nel vault."""
    if not CONVO_VAULT_PATH or not os.path.exists(CLI_CHATS_PATH):
        return

    files = [f for f in os.listdir(CLI_CHATS_PATH) if f.endswith(".jsonl")]
    if not files: return

    print(f"🔄 Controllo nuove sessioni CLI in: {CLI_CHATS_PATH}")
    
    for filename in files:
        filepath = os.path.join(CLI_CHATS_PATH, filename)
        
        # Estrazione ID sessione (l'ultima parte dopo l'ultimo trattino prima di .jsonl)
        # Formato tipico: session-2026-05-19T13-02-3559c161.jsonl
        session_id = filename.split('-')[-1].replace(".jsonl", "")
        
        try:
            match = re.search(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})-(\d{2})", filename)
            if match:
                year, month, day, hour, minute = match.groups()
                timestamp = f"{day}-{month}-{year}_{hour}-{minute}"
            else:
                timestamp = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%d-%m-%Y_%H-%M")
        except:
            timestamp = "unknown"

        output_filename = f"Conversazione_CLI_{timestamp}_{session_id[:8]}.md"
        output_path = os.path.join(CONVO_VAULT_PATH, output_filename)

        if os.path.exists(output_path):
            continue

        messages = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    m_type = data.get("type")
                    if m_type in ["user", "gemini"]:
                        content = parse_cli_content(data.get("content", ""))
                        if content.strip():
                            if m_type == "user":
                                role = "👤 Tu"
                                messages.append(f"### {role}\n{content.strip()}")
                            else:
                                role = "🧠 IA (CLI) - Riassunto"
                                summarized = summarize_ai_response(content.strip())
                                messages.append(f"### {role}\n{summarized}")
        except Exception as e:
            print(f"  ⚠️ Errore lettura log {filename}: {e}")
            continue

        if messages:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Sessione Gemini CLI - {timestamp.replace('_', ' ')}\n\n")
                f.write("\n\n".join(messages))
            print(f"  ✅ Nuova sessione CLI sincronizzata: {output_filename}")
