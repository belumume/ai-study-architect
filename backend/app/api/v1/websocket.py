"""WebSocket endpoints for real-time updates"""

import json
import logging
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_ws
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected websockets
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

manager = ConnectionManager()

@router.websocket("/ws/status")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time status updates"""
    user = None
    try:
        # Authenticate user from token
        if token:
            user = await get_current_user_ws(token, db)
            if user:
                await manager.connect(websocket, str(user.id))
                
                # Send initial connection success
                await websocket.send_json({
                    "type": "connection",
                    "status": "connected",
                    "message": "Connected to status updates"
                })
                
                # Keep connection alive
                while True:
                    # Wait for any message from client (ping/pong)
                    data = await websocket.receive_text()
                    if data == "ping":
                        await websocket.send_text("pong")
            else:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        else:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            
    except WebSocketDisconnect:
        if user:
            manager.disconnect(websocket, str(user.id))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if user:
            manager.disconnect(websocket, str(user.id))

# Export manager for use in other modules
websocket_manager = manager