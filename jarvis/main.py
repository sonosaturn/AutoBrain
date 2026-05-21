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
from jarvis_engine import agente_sviluppatore # Import the agent engine
from graph_manager import get_context_for_query
from usage_logger import log_usage
from audio_feedback import play_ping
from logger import ConversationLogger
from vision_module import analyze_screen_context
from jarvis_gui import JarvisGUI

# Shared Client
client = models.client

# Logger
logger = ConversationLogger("Jarvis")

# Wake Words Configuration
WAKE_WORDS = ["jarvis", "wake up", "computer"]
SLEEP_WORDS = ["sleep", "turn off", "rest", "go to bed", "goodbye"]

# Model for "intelligent" responses
BRAIN_MODEL = Config.BRAIN_MODEL

async def answer_with_brain(query_text, mode="summary"):
    """
    Queries the Second Brain.
    """
    context = get_context_for_query(query_text)
    
    if mode == "summary":
        system_instruction = f"""You are Jarvis. Respond based on these notes:
        {context}
        
        RULES:
        1. Make a SUPER DENSE summary (max 20-30 words).
        2. Briefly list key points.
        3. Ask the user which aspect they want to explore further and if they prefer VOICE or TEXT.
        4. Be cordial and professional (Iron Man style).
        """
    else:
        system_instruction = f"""You are Jarvis. Respond based on these notes:
        {context}
        
        RULES:
        1. Provide a detailed but balanced explanation.
        2. Do not be wordy, maintain the user's attention.
        3. If it's a text response, use clean Markdown.
        """

    try:
        response = client.models.generate_content(
            model=BRAIN_MODEL,
            contents=query_text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            )
        )
        
        # Token logging for observability
        usage = response.usage_metadata
        log_usage(BRAIN_MODEL, usage.prompt_token_count, usage.candidates_token_count, task_type="jarvis_query")
        
        return response.text
    except Exception as e:
        print(f"⚠️ Brain-Jarvis Error: {e}")
        return "I am sorry sir, I am having trouble consulting your archives."

def load_vosk_model():
    model_path = os.path.join(os.path.dirname(__file__), "model")
    if not os.path.exists(model_path) or not os.listdir(model_path):
        print("📥 Vosk model not found. Automatic download...")
        import urllib.request
        import zipfile
        import shutil
        url = "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip"
        zip_path = os.path.join(os.path.dirname(__file__), "vosk_model.zip")
        try:
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(os.path.dirname(__file__))
            extracted_dir = os.path.join(os.path.dirname(__file__), "vosk-model-small-it-0.22")
            if os.path.exists(extracted_dir):
                if os.path.exists(model_path):
                    shutil.rmtree(model_path)
                os.rename(extracted_dir, model_path)
            if os.path.exists(zip_path):
                os.remove(zip_path)
            print("✅ Vosk model ready.")
        except Exception as e:
            print(f"❌ Model download error: {e}")
            return None
    return vosk.Model(model_path)

async def listen_and_process():
    model = load_vosk_model()
    if not model:
        print("❌ Could not load voice model. Exiting.")
        return

    rec = vosk.KaldiRecognizer(model, 16000)
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
    stream.start_stream()

    print(f"🚀 Jarvis (Optimized Graph-RAG) listening...")

    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if len(data) == 0: break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            text = result.get("text", "").lower()
            
            if any(word in text for word in WAKE_WORDS):
                print(f"✨ Wake word detected: {text}")
                
                active_session = True
                while active_session:
                    stream.stop_stream()
                    
                    # Show GUI in listening state
                    if gui:
                        gui.set_state("LISTENING")
                        gui.show()
                    
                    recognizer = sr.Recognizer()
                    recognizer.pause_threshold = 2.0 
                    with sr.Microphone() as source:
                        print("🎤 Active listening...")
                        try:
                            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                            user_text = recognizer.recognize_google(audio, language="it-IT")
                            print(f"🗣️ You said: {user_text}")
                            
                            # Sleep Words Control
                            if any(word in user_text.lower() for word in SLEEP_WORDS):
                                print("😴 Sleep command received.")
                                await speak("Certainly, Sir. I am going to rest. Call me if you need anything else.")
                                active_session = False
                                if gui: gui.hide()
                                break

                            # Switch to THINKING state during processing
                            if gui: gui.set_state("THINKING")
                            
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
                                print("👁️ Vision activation...")
                                risposta_finale = await analyze_screen_context(user_text)
                            
                            elif azione == "obiettivo_agente":
                                print(f"👨‍💻 Developer Agent activation for: {parametro}")
                                await speak("Right away, Sir. Activating development protocols and proceeding with the task.")
                                risposta_finale = agente_sviluppatore(parametro)
                            
                            else:
                                risposta_finale = execute_command(comando_json)
                            
                            # Log and Response
                            if risposta_finale.strip().startswith("SILENT|"):
                                risposta_log = risposta_finale.replace("SILENT|", "").strip()
                                logger.log_interazione_completa(user_text, risposta_log, summarize=True)
                                # In continuous mode, return to listening after silent command
                                if gui: gui.set_state("LISTENING")
                            else:
                                logger.log_interazione_completa(user_text, risposta_finale, summarize=True)
                                if gui: gui.set_state("SPEAKING")
                                await speak(risposta_finale)
                                # After speaking, return automatically to listening
                                if gui: gui.set_state("LISTENING")
                                
                        except sr.WaitTimeoutError:
                            print("⏳ Active listening timeout. Returning to standby.")
                            active_session = False
                            if gui: gui.hide()
                        except Exception as e:
                            print(f"⚠️ Active session error: {e}")
                            active_session = False
                            if gui: gui.hide()
                    
                    if active_session:
                        # Small delay to avoid frantic loops
                        await asyncio.sleep(0.5)
                
                stream.start_stream()
                rec.Reset()

if __name__ == "__main__":
    try:
        asyncio.run(listen_and_process())
    except KeyboardInterrupt:
        print("\n👋 Jarvis offline.")
