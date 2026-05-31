from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from core_utils import Config

# Inizializza il logger per l'API
logger = logging.getLogger("jarvis.api")

app = FastAPI(title="Jarvis API", version="2.0.0")

# Security: API Key
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == Config.JARVIS_API_KEY:
        return api_key
    logger.warning(f"Tentativo di accesso non autorizzato con API Key errata.")
    raise HTTPException(status_code=403, detail="Could not validate credentials")

# Tighten CORS: Allow only the local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHATS_DIR = os.path.join(os.path.dirname(__file__), "chats")
os.makedirs(CHATS_DIR, exist_ok=True)

class Message(BaseModel):
    role: str
    content: str
    timestamp: str

class Chat(BaseModel):
    id: str
    title: str
    gem: str = "default"
    messages: List[Message] = []
    updated_at: str

class CommandRequest(BaseModel):
    command: str
    chat_id: Optional[str] = None
    gem: Optional[str] = "default"

class ConfigUpdate(BaseModel):
    active_model: str

# Global state to share with main.py
class JarvisState:
    def __init__(self):
        self.state = "IDLE"
        self.connected_clients = set()
        self.command_queue = asyncio.Queue()
        self.active_gem = "default"
        self.active_model = self.load_model_config()

    def load_model_config(self):
        try:
            with open("config.json", "r") as f:
                return json.load(f).get("active_model", "gemini-3-flash-preview")
        except:
            return "gemini-3-flash-preview"

    async def set_state(self, new_state: str):
        self.state = new_state
        await self.broadcast({"type": "STATE_UPDATE", "data": new_state})

    async def broadcast(self, message: dict):
        if not self.connected_clients:
            return
        
        clients = list(self.connected_clients)
        tasks = [client.send_json(message) for client in clients]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for client, result in zip(clients, results):
            if isinstance(result, Exception):
                if client in self.connected_clients:
                    self.connected_clients.remove(client)

    async def notify_wake_word(self, text: str):
        await self.broadcast({"type": "WAKE_WORD_DETECTED", "data": text})

jarvis_state = JarvisState()

@app.get("/api/chats", dependencies=[Depends(get_api_key)])
async def list_chats():
    chats = []
    for filename in os.listdir(CHATS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(CHATS_DIR, filename), "r", encoding="utf-8") as f:
                chats.append(json.load(f))
    chats.sort(key=lambda x: x["updated_at"], reverse=True)
    return chats

@app.get("/api/chats/{chat_id}", dependencies=[Depends(get_api_key)])
async def get_chat(chat_id: str):
    file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Chat not found")

@app.post("/api/chats", dependencies=[Depends(get_api_key)])
async def create_chat(chat_data: dict):
    chat_id = str(uuid.uuid4())
    new_chat = {
        "id": chat_id,
        "title": chat_data.get("title", "New Conversation"),
        "gem": chat_data.get("gem", "default"),
        "messages": [],
        "updated_at": datetime.now().isoformat()
    }
    with open(os.path.join(CHATS_DIR, f"{chat_id}.json"), "w", encoding="utf-8") as f:
        json.dump(new_chat, f)
    return new_chat

@app.delete("/api/chats/{chat_id}", dependencies=[Depends(get_api_key)])
async def delete_chat(chat_id: str):
    file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Chat not found")

@app.post("/api/command", dependencies=[Depends(get_api_key)])
async def receive_command(request: CommandRequest):
    await jarvis_state.command_queue.put({
        "command": request.command,
        "chat_id": request.chat_id,
        "gem": request.gem
    })
    return {"status": "queued"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Nota: L'autenticazione via API Key header non è standard per i WebSocket.
    # Spesso si usa un query parameter o un messaggio iniziale.
    # Per semplicità ora lo lasciamo così, ma registriamo la connessione.
    await websocket.accept()
    jarvis_state.connected_clients.add(websocket)
    logger.info(f"Nuovo client WebSocket connesso.")
    try:
        await websocket.send_json({"type": "STATE_UPDATE", "data": jarvis_state.state})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"Client WebSocket disconnesso.")
    except Exception as e:
        logger.error(f"Errore WebSocket: {e}")
    finally:
        if websocket in jarvis_state.connected_clients:
            jarvis_state.connected_clients.remove(websocket)

from usage_logger import get_model_usage_stats

@app.get("/api/config", dependencies=[Depends(get_api_key)])
async def get_config():
    return {
        "active_model": jarvis_state.active_model,
        "usage": get_model_usage_stats()
    }

@app.post("/api/config", dependencies=[Depends(get_api_key)])
async def update_config(config: ConfigUpdate):
    jarvis_state.active_model = config.active_model
    with open("config.json", "w") as f:
        json.dump({"active_model": config.active_model}, f)
    return {"status": "success"}
