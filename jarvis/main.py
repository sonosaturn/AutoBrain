import os
import json
import pyaudio
import vosk
import speech_recognition as sr
import asyncio
import threading
import sys
import time
from datetime import datetime

# Modular Import Logic
try:
    from core_utils import Config, models
except ImportError:
    # Fallback for transition phase
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_utils import Config, models

from intent_parser import parse_intent
from executor import execute_command
from tts import speak
from jarvis_engine import agente_sviluppatore
from graph_manager import get_context_for_query
from usage_logger import log_usage
from audio_feedback import play_ping
from logger import ConversationLogger
from vision_module import analyze_screen_context
from api import app, jarvis_state
import uvicorn
from window_manager import focus_jarvis_window

# Shared Client
client = models.client
from core_utils.logging_setup import setup_logging
# Logger di sistema
logger = setup_logging("jarvis")
# Logger delle conversazioni (Markdown)
conv_logger = ConversationLogger("Jarvis")
# shared state contains the active model
BRAIN_MODEL = jarvis_state.active_model
# Config
WAKE_WORDS = ["jarvis", "wake up", "computer"]
SLEEP_WORDS = ["sleep", "turn off", "rest", "go to bed", "goodbye"]

async def run_server():
    # Use port 8008 to avoid common conflicts with port 8000
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8008, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def load_vosk_model():
    model_path = os.path.join(os.path.dirname(__file__), "model")
    if not os.path.exists(model_path) or not os.listdir(model_path):
        return None
    return vosk.Model(model_path)

CHATS_DIR = os.path.join(os.path.dirname(__file__), "chats")

GEM_PROMPTS = {
    "default": "You are Jarvis, a highly advanced AI assistant. Be professional, concise, and helpful.",
    "university_tutor": """You are the 'University Tutor' Gem. 
Your expertise is based on the university notes in the Knowledge Graph.
RULES:
1. When answering, adopt the tone of a brilliant professor who simplifies complex concepts.
2. Use pedagogical examples related to the context of the notes.
3. If the user asks about a specific topic, correlate it with other related topics in the notes.
4. Encourage deep reasoning rather than just providing the answer.
5. Always cite which 'Lezione' or 'Documento' you are referring to."""
}

async def answer_with_brain(query_text, mode="summary", gem="default", chat_history=[]):
    # If using the Tutor Gem, restrict search to the university notes vault only
    vault_to_search = VAULT_PATH if gem == "university_tutor" else None
    context = get_context_for_query(query_text, vault_filter=vault_to_search)
    
    gem_instruction = GEM_PROMPTS.get(gem, GEM_PROMPTS["default"])
    
    if mode == "summary":
        system_instruction = f"{gem_instruction}\n\nCONTEXT FROM NOTES:\n{context}\n\nRULES:\n1. DENSE summary (max 30 words).\n2. Cordial and professional."
    else:
        system_instruction = f"{gem_instruction}\n\nCONTEXT FROM NOTES:\n{context}\n\nRULES:\n1. Detailed but balanced.\n2. Use clean Markdown."

    # Build history for Gemini
    contents = []
    for msg in chat_history[-5:]: # Last 5 messages for context
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": query_text}]})

    max_retries = 5
    for i in range(max_retries):
        try:
            from google.genai import types
            loop = asyncio.get_event_loop()
            active_model = jarvis_state.active_model
            response = await loop.run_in_executor(None, lambda: client.models.generate_content(
                model=active_model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            ))
            usage = response.usage_metadata
            log_usage(active_model, usage.prompt_token_count, usage.candidates_token_count, task_type=f"jarvis_{gem}")
            return response.text
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg) and i < max_retries - 1:
                wait_time = (2 ** i) * 5 + random.random()
                logger.warning(f"Brain-Jarvis sovraccarico (429/503). Prossimo tentativo tra {wait_time:.1f}s (tentativo {i+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
                continue
            
            logger.error(f"Brain-Jarvis Error: {e}")
            return "I am sorry sir, I am having trouble consulting your archives."

async def process_user_request(user_text, is_voice=True, gem="default", chat_id=None):
    """Common logic for processing commands from voice or text."""
    await jarvis_state.set_state("THINKING")
    
    # Load chat history if available
    chat_history = []
    if chat_id:
        chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(chat_file):
            try:
                with open(chat_file, "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
                    chat_history = chat_data.get("messages", [])
                    # Inherit gem from chat if not specified
                    if gem == "default" and chat_data.get("gem"):
                        gem = chat_data.get("gem")
            except Exception as e:
                logger.error(f"Error loading chat history: {e}")

    loop = asyncio.get_event_loop()
    # parse_intent is a blocking API call, must run in executor
    comando_json = await loop.run_in_executor(None, parse_intent, user_text)
    azione = comando_json.get("azione")
    parametro = comando_json.get("parametro", "")
    
    risposta_finale = ""
    if azione == "messaggio":
        mode = "detailed" if any(k in user_text.lower() for k in ["elaborate", "tell me more", "details", "spiegami"]) else "summary"
        # answer_with_brain now handles context and history internally
        risposta_finale = await answer_with_brain(parametro if parametro else user_text, mode=mode, gem=gem, chat_history=chat_history)
    elif azione == "mostra_testo":
        testo_dettagliato = await answer_with_brain(parametro if parametro else user_text, mode="detailed", gem=gem, chat_history=chat_history)
        comando_json["parametro"] = testo_dettagliato
        # execute_command creates the file and returns a status message
        esecuzione_status = await loop.run_in_executor(None, execute_command, comando_json)
        # We want the chat response to be the actual explanation, not just "I opened the file"
        risposta_finale = f"{esecuzione_status}\n\nEcco una sintesi di quanto richiesto:\n\n{testo_dettagliato}"
    else:
        risposta_finale = await loop.run_in_executor(None, execute_command, comando_json)
    
    # Save to chat history if chat_id exists
    if chat_id:
        timestamp = datetime.now().isoformat()
        chat_history.append({"role": "user", "content": user_text, "timestamp": timestamp})
        chat_history.append({"role": "jarvis", "content": risposta_finale, "timestamp": timestamp})
        
        try:
            chat_file = os.path.join(CHATS_DIR, f"{chat_id}.json")
            if os.path.exists(chat_file):
                with open(chat_file, "r", encoding="utf-8") as f:
                    chat_data = json.load(f)
            else:
                chat_data = {"id": chat_id, "gem": gem}

            chat_data["messages"] = chat_history
            chat_data["updated_at"] = timestamp
            chat_data["gem"] = gem
            
            # Auto-title if it's the first message or generic title
            if len(chat_history) <= 2 or chat_data.get("title") == "New Conversation":
                chat_data["title"] = user_text[:40] + "..." if len(user_text) > 40 else user_text
                
            with open(chat_file, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving chat history: {e}")

    if risposta_finale.strip().startswith("SILENT|"):
        risposta_log = risposta_finale.replace("SILENT|", "").strip()
        conv_logger.log_interazione_completa(user_text, risposta_log, summarize=True)
        await jarvis_state.set_state("IDLE")
        return risposta_log
    else:
        conv_logger.log_interazione_completa(user_text, risposta_finale, summarize=True)
        if is_voice:
            await jarvis_state.set_state("SPEAKING")
            await speak(risposta_finale)
        await jarvis_state.set_state("IDLE")
        return risposta_finale

async def handle_text_commands():
    """Monitor the command queue for dict-based input from the Web UI."""
    while True:
        request = await jarvis_state.command_queue.get()
        if request:
            command = request.get("command")
            chat_id = request.get("chat_id")
            gem = request.get("gem", "default")
            
            await jarvis_state.broadcast({"type": "USER_MESSAGE", "data": command})
            response = await process_user_request(command, is_voice=False, gem=gem, chat_id=chat_id)
            await jarvis_state.broadcast({"type": "JARVIS_RESPONSE", "data": response})
        jarvis_state.command_queue.task_done()

async def listen_and_process():
    model = load_vosk_model()
    if not model:
        logger.error("Could not load voice model.")
        return

    rec = vosk.KaldiRecognizer(model, 16000)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    logger.info("Jarvis (Optimized Graph-RAG) listening...")

    while True:
        # Use run_in_executor to avoid blocking the event loop with stream.read
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, stream.read, 4000, False)
        
        if len(data) == 0: break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            
            if any(word in text for word in WAKE_WORDS):
                logger.info(f"Wake word detected: {text}")
                focus_jarvis_window()
                await jarvis_state.notify_wake_word(text)
                
                active_session = True
                while active_session:
                    stream.stop_stream()
                    await jarvis_state.set_state("LISTENING")
                    
                    recognizer = sr.Recognizer()
                    recognizer.pause_threshold = 2.0 
                    with sr.Microphone() as source:
                        logger.info("Active listening...")
                        try:
                            # recognizer.listen is blocking, run in executor
                            audio = await loop.run_in_executor(None, lambda: recognizer.listen(source, timeout=10, phrase_time_limit=15))
                            user_text = await loop.run_in_executor(None, recognizer.recognize_google, audio, "it-IT")
                            logger.info(f"You said: {user_text}")
                            
                            if any(word in user_text.lower() for word in SLEEP_WORDS):
                                await jarvis_state.set_state("SPEAKING")
                                await speak("Certainly, Sir. I am going to rest. Call me if you need anything else.")
                                active_session = False
                                await jarvis_state.set_state("IDLE")
                                break

                            response = await process_user_request(user_text, is_voice=True)
                            await jarvis_state.broadcast({"type": "JARVIS_RESPONSE", "data": response})
                            await jarvis_state.set_state("LISTENING")
                                
                        except sr.WaitTimeoutError:
                            active_session = False
                            await jarvis_state.set_state("IDLE")
                        except Exception as e:
                            logger.error(f"Error during voice recognition: {e}")
                            active_session = False
                            await jarvis_state.set_state("IDLE")
                    
                    if active_session:
                        await asyncio.sleep(0.5)
                
                stream.start_stream()
                rec.Reset()

if __name__ == "__main__":
    async def main():
        # Start server, command handler and listener concurrently
        await asyncio.gather(
            run_server(),
            handle_text_commands(),
            listen_and_process()
        )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Jarvis offline.")
