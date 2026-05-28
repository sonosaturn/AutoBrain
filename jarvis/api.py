from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json

app = FastAPI()

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CommandRequest(BaseModel):
    command: str

# Global state to share with main.py
class JarvisState:
    def __init__(self):
        self.state = "IDLE"
        self.connected_clients = set()
        self.command_queue = asyncio.Queue()

    async def set_state(self, new_state: str):
        self.state = new_state
        await self.broadcast({"type": "STATE_UPDATE", "data": new_state})

    async def broadcast(self, message: dict):
        if not self.connected_clients:
            return
        
        # Create a list of tasks for broadcasting to all clients
        tasks = [client.send_json(message) for client in self.connected_clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def notify_wake_word(self, text: str):
        await self.broadcast({"type": "WAKE_WORD_DETECTED", "data": text})

jarvis_state = JarvisState()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    jarvis_state.connected_clients.add(websocket)
    # Send initial state
    await websocket.send_json({"type": "STATE_UPDATE", "data": jarvis_state.state})
    try:
        while True:
            # We don't expect much from the client via WS for now, 
            # but we need to keep the connection alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        jarvis_state.connected_clients.remove(websocket)

@app.post("/api/command")
async def receive_command(request: CommandRequest):
    # Put the command into the queue for main.py to process
    await jarvis_state.command_queue.put(request.command)
    return {"status": "queued"}

@app.get("/api/status")
async def get_status():
    return {"state": jarvis_state.state}
