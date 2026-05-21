import asyncio
import edge_tts
import pygame
import os
import tempfile
import re

# Inizializza pygame per la riproduzione audio
pygame.mixer.init()

def clean_text_for_speech(text: str) -> str:
    """
    Pulisce il testo per la lettura vocale: rimuove URL, asterischi e altri simboli.
    """
    # Rimuovi blocchi di codice markdown
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    # Rimuovi URL
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Rimuovi asterischi (grassetto/corsivo markdown)
    text = text.replace('*', '')
    # Rimuovi cancelletti (titoli markdown)
    text = text.replace('#', '')
    # Rimuovi backtick (codice inline)
    text = text.replace('`', '')
    # Rimuovi link markdown [testo](url) mantenendo solo il testo
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    
    # Riduci spazi multipli e pulisci bordi
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def speak(text: str):
    """
    Trasforma il testo in voce usando Edge TTS e lo riproduce.
    """
    cleaned_text = clean_text_for_speech(text)
    if not cleaned_text:
        print("🔈 Jarvis: (Niente da dire a voce)")
        return

    print(f"🎙️ Jarvis: {cleaned_text}")
    
    # Scegli una voce italiana di alta qualità
    voice = "it-IT-DiegoNeural" 
    
    # Crea un file temporaneo per l'audio
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        output_path = tmp_file.name
    
    try:
        communicate = edge_tts.Communicate(cleaned_text, voice)
        await communicate.save(output_path)
        
        # Riproduci l'audio
        pygame.mixer.music.load(output_path)
        pygame.mixer.music.play()
        
        # Attendi la fine della riproduzione
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
            
        pygame.mixer.music.unload()
    finally:
        # Pulisci il file temporaneo
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

if __name__ == "__main__":
    asyncio.run(speak("Sistema pronto. Sono ai tuoi ordini."))
