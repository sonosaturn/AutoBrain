import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# Nuovo client SDK
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.1-flash-lite"

SYSTEM_PROMPT = """You are Jarvis, Lorenzo's advanced voice assistant.
You are connected to his "Second Brain" (Knowledge Graph).

YOUR TASK:
Translate the user's phrase into a JSON command.

SUPPORTED ACTIONS:
- apri_browser: Open websites, web searches, or online services (e.g., YouTube, Google, ChatGPT, Netflix, Amazon).
- cerca_youtube: Specific video search on YouTube.
- riproduci_spotify: Music or playlists on Spotify.
- apri_app: Open LOCAL software (e.g., Word, Calculator, Notepad, Brave, Chrome, Obsidian).
- mostra_testo: Read information from the Second Brain.
- analizza_schermo: Questions about what's on screen or visual interaction.
- obiettivo_agente: For DEVELOPMENT requests, feature creation, code modifications, or complex automation tasks (e.g., "create an interface", "add email function", "refactor code for X").
- messaggio: For oral questions, trivia, or general conversation.

CRITICAL RULES:
1. YouTube, Netflix, ChatGPT, Google are WEBSITES, so use "apri_browser". NEVER use "apri_app" for these.
2. If the user asks to create, modify, or add features to the system, ALWAYS use "obiettivo_agente".
3. If the user says "open youtube", the correct command is {"azione": "apri_browser", "parametro": "https://www.youtube.com"}.
4. Use "cerca_youtube" if the intent is to search for a specific video.
5. Use "apri_app" ONLY if you are sure it is an installed program (.exe). When in doubt, use "apri_browser".
6. Respond ONLY with the JSON.
"""

"""

def parse_intent(text: str) -> dict:
    """
    Invia il testo a Gemini e riceve il comando JSON usando il nuovo SDK.
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json"
            )
        )
        
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Errore parsing intento: {e}")
        return {"azione": "messaggio", "parametro": "Scusa, non ho capito il comando."}

if __name__ == "__main__":
    print(parse_intent("riproduci i Queen su spotify"))
