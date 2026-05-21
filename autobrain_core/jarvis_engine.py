import os
import json
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# NOMI MODELLI MANDATORI
VOICE_MODEL = "gemini-3.1-flash-lite"
BRAIN_MODEL = "gemini-3-flash-preview"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------------------------------------------------------------------
# "MANI" - TOOL DI SVILUPPO (Per gli Agenti)
# ---------------------------------------------------------------------------

def scrivi_codice(file_path: str, contenuto: str):
    """Permette all'agente di scrivere o sovrascrivere un file nel progetto."""
    try:
        # Assicura che la directory esista
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(contenuto)
        return f"✅ File {file_path} scritto con successo."
    except Exception as e:
        return f"❌ Errore scrittura file: {e}"

def leggi_codice(file_path: str):
    """Permette all'agente di leggere il contenuto di un file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"❌ Errore lettura file: {e}"

# Tool disponibili per il modello
tools = [scrivi_codice, leggi_codice]

# ---------------------------------------------------------------------------
# CORE AGENTICO (NATIVO)
# ---------------------------------------------------------------------------

def agente_sviluppatore(obiettivo: str):
    """Gestisce un obiettivo di sviluppo usando il modello BRAIN in un loop di ragionamento."""
    print(f"\n👨‍💻 [DEVELOPER AGENT] Inizio task: {BRAIN_MODEL}")
    
    system_instruction = (
        "Sei il Senior Developer di Jarvis. Il tuo obiettivo è analizzare e scrivere codice Python. "
        "Usa i tool 'leggi_codice' per capire il contesto e 'scrivi_codice' per implementare. "
        "Procedi passo dopo passo. Sii conciso e professionale."
    )

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=obiettivo)])]
    
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="scrivi_codice",
                description="Scrive o sovrascrive un file.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "file_path": {"type": "STRING"},
                        "contenuto": {"type": "STRING"}
                    },
                    "required": ["file_path", "contenuto"]
                }
            ),
            types.FunctionDeclaration(
                name="leggi_codice",
                description="Legge un file.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "file_path": {"type": "STRING"}
                    },
                    "required": ["file_path"]
                }
            )
        ])]
    )

    try:
        # Loop di ragionamento (max 5 iterazioni per sicurezza)
        for _ in range(5):
            response = client.models.generate_content(
                model=BRAIN_MODEL,
                contents=contents,
                config=config
            )

            # Aggiungi la risposta al contesto
            contents.append(response.candidates[0].content)
            
            # Controlla se ci sono chiamate a funzione
            tool_results = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    fn_name = part.function_call.name
                    args = part.function_call.args
                    print(f"🛠️ [AZIONE] Eseguo {fn_name}...")
                    
                    if fn_name == "scrivi_codice":
                        result_text = scrivi_codice(**args)
                    elif fn_name == "leggi_codice":
                        result_text = leggi_codice(**args)
                    
                    print(f"📡 [RISULTATO] {result_text[:50]}...")
                    tool_results.append(types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result_text}
                    ))
            
            if not tool_results:
                # Se non ci sono tool call, il task è finito o l'agente ha risposto
                return response.text

            # Aggiungi i risultati dei tool al contesto per il prossimo turno
            contents.append(types.Content(role="tool", parts=tool_results))

        return "⚠️ Timeout: L'agente ha superato il numero massimo di iterazioni."
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Errore Agente: {e}"

if __name__ == "__main__":
    # Test della logica
    # print(agente_sviluppatore("Crea un file test_jarvis.py con un saluto"))
    pass
