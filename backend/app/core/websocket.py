from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.video_subscribers: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        for video_id in list(self.video_subscribers.keys()):
            if client_id in self.video_subscribers[video_id]:
                self.video_subscribers[video_id].remove(client_id)
                if not self.video_subscribers[video_id]:
                    del self.video_subscribers[video_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def send_json(self, data: dict, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

    async def broadcast_to_video(self, video_id: str, data: dict):
        if video_id in self.video_subscribers:
            for client_id in self.video_subscribers[video_id]:
                await self.send_json(data, client_id)

    def subscribe_to_video(self, client_id: str, video_id: str):
        if video_id not in self.video_subscribers:
            self.video_subscribers[video_id] = set()
        self.video_subscribers[video_id].add(client_id)

    def unsubscribe_from_video(self, client_id: str, video_id: str):
        if video_id in self.video_subscribers:
            self.video_subscribers[video_id].discard(client_id)
            if not self.video_subscribers[video_id]:
                del self.video_subscribers[video_id]

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                video_id = data.get("video_id")
                if video_id:
                    manager.subscribe_to_video(client_id, video_id)
                    await manager.send_json({
                        "type": "subscribed",
                        "video_id": video_id
                    }, client_id)

            elif data.get("type") == "unsubscribe":
                video_id = data.get("video_id")
                if video_id:
                    manager.unsubscribe_from_video(client_id, video_id)
                    await manager.send_json({
                        "type": "unsubscribed",
                        "video_id": video_id
                    }, client_id)

            elif data.get("type") == "ping":
                await manager.send_json({"type": "pong"}, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)

async def notify_video_progress(video_id: str, status: str, progress: int, message: str = None):
    await manager.broadcast_to_video(video_id, {
        "type": "progress",
        "video_id": video_id,
        "status": status,
        "progress": progress,
        "message": message
    })

async def notify_video_completed(video_id: str, highlights_count: int):
    await manager.broadcast_to_video(video_id, {
        "type": "completed",
        "video_id": video_id,
        "highlights_count": highlights_count
    })

async def notify_video_error(video_id: str, error_message: str):
    await manager.broadcast_to_video(video_id, {
        "type": "error",
        "video_id": video_id,
        "error": error_message
    })