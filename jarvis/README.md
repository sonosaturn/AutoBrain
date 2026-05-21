# Jarvis - Assistente Vocale IA

Jarvis è un assistente vocale per Windows che ascolta una "wake word" e esegue comandi di sistema tramite intelligenza artificiale.

## Funzionalità
- **Attivazione vocale:** Sempre in ascolto per "Jarvis" o "Porcupine".
- **Comandi:**
  - "Apri Brave e cerca [query]"
  - "Riproduci [artista/canzone] su Spotify"
  - "Cerca [video] su YouTube"
  - "Apri [applicazione]"
- **Feedback Vocale:** Risponde usando voci neurali di alta qualità.

## Installazione

1. **Ottieni la chiave Picovoice:**
   - Vai su [console.picovoice.ai](https://console.picovoice.ai/)
   - Crea un account gratuito.
   - Copia la tua **Access Key**.
   - Inseriscila nel file `.env` alla voce `PICOVOICE_ACCESS_KEY`.

2. **Configura OpenRouter:**
   - Assicurati che `OPENROUTER_API_KEY` sia presente nel file `.env`.

3. **Configura l'avvio automatico:**
   - Esegui `python setup_autostart.py` per fare in modo che Jarvis si avvii ad ogni accensione del PC.

## Struttura
- `main.py`: Core dell'applicazione.
- `intent_parser.py`: Analisi IA del linguaggio naturale.
- `executor.py`: Esecuzione fisica dei comandi su Windows.
- `tts.py`: Sintesi vocale.
- `setup_autostart.py`: Utility per l'avvio al boot.
