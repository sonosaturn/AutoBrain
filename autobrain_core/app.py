"""
app.py — Interfaccia web per il Secondo Cervello (Graph-RAG Edition)
"""

import os
import json
import threading
import webbrowser
import sys
from datetime import datetime
from flask import Flask, render_template, request, Response, stream_with_context

# Modular Import Logic
try:
    from core_utils import Config, models
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core_utils import Config, models

# Moduli locali
from graph_manager import get_context_for_query

VAULT_PATH = Config.VAULT_PATH
CONVO_VAULT_PATH = Config.CONVO_VAULT_PATH

client = models.client
MODEL_NAME = Config.BRAIN_MODEL
CONV_VAULT_PATH = CONVO_VAULT_PATH 
os.makedirs(CONV_VAULT_PATH, exist_ok=True)

app = Flask(__name__)

conversation_history = []

def build_system_prompt(user_query: str) -> str:
    """Costruisce il prompt recuperando solo i dati rilevanti dal grafo."""
    context = get_context_for_query(user_query)
    
    return f"""Sei l'interfaccia del Secondo Cervello di Lorenzo.
Rispondi basandoti sui miei appunti forniti qui sotto (estratti dal mio Knowledge Graph).
Se la risposta non è presente negli appunti, dillo chiaramente.
Cita sempre il nome del documento da cui proviene l'informazione.
Rispondi sempre in italiano in modo chiaro, strutturato e dettagliato.

BASE DI CONOSCENZA RILEVANTE:
{context}"""


def save_conversation():
    """Salva la cronologia corrente in un file Markdown nel vault conversazioni."""
    if not conversation_history:
        return

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"Conversazione_Web_{timestamp}.md"
    filepath = os.path.join(CONV_VAULT_PATH, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Conversazione Secondo Cervello - {timestamp.replace('_', ' ')}\n\n")
        for msg in conversation_history:
            role = "👤 Tu" if msg["role"] == "user" else "🧠 IA"
            f.write(f"### {role}\n{msg['content']}\n\n")

    print(f"💾 Conversazione salvata: {filename}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return Response("", status=400)

    conversation_history.append({"role": "user", "content": user_message})
    
    # Prepara il modello Gemini con il contesto dinamico estratto dal grafo
    system_instruction = build_system_prompt(user_message)
    
    # Prepara la cronologia per il nuovo SDK (formato Contents)
    history_contents = []
    for msg in conversation_history[:-1]:
        role = "user" if msg["role"] == "user" else "model"
        history_contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    def generate():
        full_reply = ""
        try:
            # Nuovo SDK: client.models.generate_content (oppure start_chat)
            # Per semplicità in questo refactoring usiamo generate_content con history
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_message,
                config={
                    "system_instruction": system_instruction,
                    # history non è un parametro diretto di generate_content nel nuovo SDK
                    # bisogna passarla nei contents. Per semplicità usiamo un prompt concatenato o refactor chat
                }
            )
            # Refactoring completo per supportare streaming con il nuovo SDK
            # (Nota: Il nuovo SDK google-genai ha una sintassi diversa per lo streaming)
            for chunk in client.models.generate_content_stream(
                model=MODEL_NAME,
                contents=user_message,
                config={"system_instruction": system_instruction}
            ):
                text = chunk.text
                full_reply += text
                yield f"data: {json.dumps({'token': text})}\n\n"

            conversation_history.append({"role": "assistant", "content": full_reply})
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/clear", methods=["POST"])
def clear():
    save_conversation()
    conversation_history.clear()
    return {"status": "ok"}


def open_browser():
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    print("🧠 Secondo Cervello (Graph-RAG) avviato → http://localhost:5000")
    try:
        app.run(debug=False, port=5000)
    finally:
        save_conversation()
