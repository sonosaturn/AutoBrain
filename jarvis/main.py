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
# Logger
logger = ConversationLogger("Jarvis")
# Models
BRAIN_MODEL = Config.BRAIN_MODEL
# Config
WAKE_WORDS = ["jarvis", "wake up", "computer"]
SLEEP_WORDS = ["sleep", "turn off", "rest", "go to bed", "goodbye"]

async def run_server():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def answer_with_brain(query_text, mode="summary"):
    context = get_context_for_query(query_text)
    if mode == "summary":
        system_instruction = f"You are Jarvis. Respond based on these notes:\n{context}\n\nRULES:\n1. Make a SUPER DENSE summary (max 20-30 words).\n2. Briefly list key points.\n3. Ask the user which aspect they want to explore further and if they prefer VOICE or TEXT.\n4. Be cordial and professional (Iron Man style)."
    else:
        system_instruction = f"You are Jarvis. Respond based on these notes:\n{context}\n\nRULES:\n1. Provide a detailed but balanced explanation.\n2. Do not be wordy, maintain the user's attention.\n3. If it's a text response, use clean Markdown."

    try:
        from google.genai import types
        response = client.models.generate_content(
            model=BRAIN_MODEL,
            contents=query_text,
            config=types.GenerateContentConfig(system_instruction=system_instruction)
        )
        usage = response.usage_metadata
        log_usage(BRAIN_MODEL, usage.prompt_token_count, usage.candidates_token_count, task_type="jarvis_query")
        return response.text
    except Exception as e:
        print(f"⚠️ Brain-Jarvis Error: {e}")
        return "I am sorry sir, I am having trouble consulting your archives."

def load_vosk_model():
    model_path = os.path.join(os.path.dirname(__file__), "model")
    if not os.path.exists(model_path) or not os.listdir(model_path):
        return None
    return vosk.Model(model_path)

async def process_user_request(user_text, is_voice=True):
    """Common logic for processing commands from voice or text."""
    await jarvis_state.set_state("THINKING")
    print(f"🤖 Processing: {user_text}")
    
    comando_json = parse_intent(user_text)
    azione = comando_json.get("azione")
    parametro = comando_json.get("parametro", "")
    
    risposta_finale = ""
    if azione == "messaggio":
        deep_keywords = ["elaborate", "tell me more", "details", "explain better", "by voice"]
        if any(k in user_text.lower() for k in deep_keywords):
            risposta_finale = await answer_with_brain(parametro, mode="detailed")
        else:
            risposta_finale = await answer_with_brain(parametro, mode="summary")
    elif azione == "mostra_testo":
        testo_dettagliato = await answer_with_brain(parametro, mode="detailed")
        comando_json["parametro"] = testo_dettagliato
        risposta_finale = execute_command(comando_json)
    elif azione == "analizza_schermo":
        risposta_finale = await analyze_screen_context(user_text)
    elif azione == "obiettivo_agente":
        if is_voice: await speak("Right away, Sir. Activating development protocols.")
        risposta_finale = agente_sviluppatore(parametro)
    else:
        risposta_finale = execute_command(comando_json)
    
    if risposta_finale.strip().startswith("SILENT|"):
        risposta_log = risposta_finale.replace("SILENT|", "").strip()
        logger.log_interazione_completa(user_text, risposta_log, summarize=True)
        await jarvis_state.set_state("IDLE")
        return risposta_log
    else:
        logger.log_interazione_completa(user_text, risposta_finale, summarize=True)
        if is_voice:
            await jarvis_state.set_state("SPEAKING")
            await speak(risposta_finale)
        await jarvis_state.set_state("IDLE")
        return risposta_finale

async def handle_text_commands():
    """Monitor the command queue for text input from the Web UI."""
    while True:
        command = await jarvis_state.command_queue.get()
        if command:
            # We broadcast the user's text to the UI as well (to show in chat)
            await jarvis_state.broadcast({"type": "USER_MESSAGE", "data": command})
            response = await process_user_request(command, is_voice=False)
            await jarvis_state.broadcast({"type": "JARVIS_RESPONSE", "data": response})
        jarvis_state.command_queue.task_done()

async def listen_and_process():
    model = load_vosk_model()
    if not model:
        print("❌ Could not load voice model.")
        return

    rec = vosk.KaldiRecognizer(model, 16000)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print(f"🚀 Jarvis (Optimized Graph-RAG) listening...")

    while True:
        # Use run_in_executor to avoid blocking the event loop with stream.read
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, stream.read, 4000, False)
        
        if len(data) == 0: break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            
            if any(word in text for word in WAKE_WORDS):
                print(f"✨ Wake word detected: {text}")
                focus_jarvis_window()
                await jarvis_state.notify_wake_word(text)
                
                active_session = True
                while active_session:
                    stream.stop_stream()
                    await jarvis_state.set_state("LISTENING")
                    
                    recognizer = sr.Recognizer()
                    recognizer.pause_threshold = 2.0 
                    with sr.Microphone() as source:
                        print("🎤 Active listening...")
                        try:
                            # recognizer.listen is blocking, run in executor
                            audio = await loop.run_in_executor(None, lambda: recognizer.listen(source, timeout=10, phrase_time_limit=15))
                            user_text = await loop.run_in_executor(None, recognizer.recognize_google, audio, "it-IT")
                            print(f"🗣️ You said: {user_text}")
                            
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
                            print(f"⚠️ Error: {e}")
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
        print("\n👋 Jarvis offline.")
