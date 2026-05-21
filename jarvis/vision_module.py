import os
import mss
import mss.tools
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime

basedir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(basedir, ".env"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3-flash-preview"

def capture_all_screens():
    """Cattura uno screenshot per ogni monitor connesso."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = []
    
    try:
        with mss.mss() as sct:
            # monitors[0] è l'intero desktop virtuale.
            # monitors[1:] sono i singoli monitor fisici.
            for i, monitor in enumerate(sct.monitors[1:], 1):
                temp_path = os.path.join(basedir, f"screenshot_monitor{i}_{timestamp}.png")
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=temp_path)
                paths.append(temp_path)
    except Exception as e:
        print(f"⚠️ Errore cattura schermi: {e}")
        
    return paths

async def analyze_screen_context(prompt_text):
    """
    Cattura tutti gli schermi e chiede a Gemini di analizzarli.
    """
    image_paths = capture_all_screens()
    
    if not image_paths:
        return "Signore, non sono riuscito a rilevare alcun monitor attivo o i sensori sono bloccati."
    
    loaded_images = []
    try:
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        
        # Prepariamo il contenuto multimodale
        instruction = f"""Sei gli occhi di Jarvis. Lorenzo ha una configurazione multi-monitor ({len(image_paths)} schermi).
Ti sto inviando le immagini dei singoli monitor. 

RICHIESTA DI LORENZO: "{prompt_text}"

Analizza il contenuto globale degli schermi e rispondi in modo conciso e professionale. 
Indica chiaramente su quale monitor (1, 2, ecc.) vedi ciò che descrivi, se pertinente.
"""
        contents = [instruction]
        
        # Carichiamo le immagini in memoria
        for path in image_paths:
            loaded_images.append(Image.open(path))
        
        contents.extend(loaded_images)
        
        # Chiamata asincrona a Gemini
        response = await model.generate_content_async(contents)
        
        return response.text
        
    except Exception as e:
        return f"Signore, ho avuto un problema tecnico con la visione multi-monitor: {e}"
        
    finally:
        # Pulizia rigorosa dei file e della memoria
        for img in loaded_images:
            try:
                img.close()
            except:
                pass
                
        for path in image_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

if __name__ == "__main__":
    # Test rapido
    import asyncio
    async def test():
        print(f"🖥️ Rilevati {len(capture_all_screens())} monitor.")
        # print(await analyze_screen_context("Cosa vedi sui miei schermi?"))
    asyncio.run(test())
