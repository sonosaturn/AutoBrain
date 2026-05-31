import os
import json
import logging
import time
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Inizializza il logger per questo modulo
logger = logging.getLogger("jarvis.intent_parser")

basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Nuovo client SDK
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_model():
    """Recupera il modello attivo dallo stato globale o dal file di config."""
    try:
        from api import jarvis_state
        return jarvis_state.active_model
    except:
        try:
            with open("config.json", "r") as f:
                return json.load(f).get("active_model", "gemini-3-flash-preview")
        except:
            return "gemini-3-flash-preview"

SYSTEM_PROMPT = """Sei Jarvis, l'assistente vocale avanzato di Lorenzo.
Sei connesso al suo "Secondo Cervello" (Knowledge Graph).

IL TUO COMPITO:
Traduci la frase dell'utente in un comando JSON.

AZIONI SUPPORTATE:
- apri_browser: Apri siti web, ricerche web o servizi online (es. YouTube, Google, ChatGPT, Netflix, Amazon).
- cerca_youtube: Ricerca specifica di un video su YouTube.
- riproduci_spotify: Musica o playlist su Spotify.
- apri_app: Apri software LOCALI (es. Word, Calcolatrice, Blocco note, Brave, Chrome, Obsidian).
- mostra_testo: Da usare SOLO se l'utente chiede esplicitamente di "mostrare un file", "aprire un documento" o "creare una nota" con le informazioni. NON usare per spiegazioni orali o scritte in chat.
- analizza_schermo: Domande su cosa c'è a video o interazione visiva.
- obiettivo_agente: Per richieste di SVILUPPO, creazione di feature, modifiche al codice o task di automazione complessi (es. "crea un'interfaccia", "aggiungi funzione email", "rifattorizza il codice per X").
- messaggio: Per domande, spiegazioni, curiosità o conversazione generale. USA QUESTA se l'utente chiede di "spiegare", "raccontare" o "cercare informazioni" senza chiedere esplicitamente un file.

REGOLE CRITICHE:
1. YouTube, Netflix, ChatGPT, Google sono SITI WEB, quindi usa "apri_browser". NON usare MAI "apri_app" per questi.
2. Se l'utente chiede di creare, modificare o aggiungere funzionalità al sistema, usa SEMPRE "obiettivo_agente".
3. Se l'utente dice "apri youtube", il comando corretto è {"azione": "apri_browser", "parametro": "https://www.youtube.com"}.
4. Se l'utente chiede "spiegami X", usa "messaggio". Se dice "fammi un file su X", usa "mostra_testo".
5. Usa "apri_app" SOLO se sei sicuro sia un programma installato (.exe). Nel dubbio, usa "apri_browser".
6. Rispondi SOLO con il JSON.
"""

def parse_intent(text: str) -> dict:
    """
    Invia il testo a Gemini e riceve il comando JSON usando il nuovo SDK.
    Include logica di retry per gestire errori di quota (429).
    """
    max_retries = 5
    current_model = get_model()
    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=current_model,
                contents=text,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg) and i < max_retries - 1:
                wait_time = (2 ** i) * 5 + random.random()
                logger.warning(f"Gemini sovraccarico (429/503). Prossimo tentativo tra {wait_time:.1f}s (tentativo {i+1}/{max_retries})...")
                time.sleep(wait_time)
                continue
            
            logger.error(f"Errore parsing intento: {e}")
            break

    return {"azione": "messaggio", "parametro": "Scusa, non ho capito il comando."}

if __name__ == "__main__":
    # In un ambiente di test standalone, configuriamo un logger di base
    logging.basicConfig(level=logging.INFO)
    print(parse_intent("riproduci i Queen su spotify"))
