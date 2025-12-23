"""Collaboration Service - Real-time collaboration with WebSocket."""
from fastapi import FastAPI
from datetime import datetime
import os
import json
import logging
from dotenv import load_dotenv
import socketio
import redis.asyncio as redis
from typing import Dict, Set

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure based on CORS_ORIGINS env
    logger=True,
    engineio_logger=True
)

# Create FastAPI app
app = FastAPI(
    title="AutoGraph v3 Collaboration Service",
    description="Real-time collaboration service",
    version="1.0.0"
)

# Wrap with Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, app)

# Redis connection for pub/sub
redis_client = None
pubsub = None

# Track active rooms and users
active_rooms: Dict[str, Set[str]] = {}  # room_id -> set of session_ids


async def get_redis():
    """Get Redis connection."""
    global redis_client
    if redis_client is None:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_client = await redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True
        )
    return redis_client


async def publish_to_redis(channel: str, message: dict):
    """Publish message to Redis channel for cross-instance communication."""
    try:
        r = await get_redis()
        await r.publish(channel, json.dumps(message))
        logger.info(f"Published to Redis channel {channel}: {message}")
    except Exception as e:
        logger.error(f"Failed to publish to Redis: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup."""
    logger.info("Starting collaboration service...")
    try:
        r = await get_redis()
        await r.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Redis connection on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Closed Redis connection")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "collaboration-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/broadcast/{room_id}")
async def broadcast_message(room_id: str, message: dict):
    """
    HTTP endpoint to broadcast a message to a room.
    Used by other services (e.g., diagram-service) to send updates.
    """
    try:
        logger.info(f"Broadcasting to room {room_id}: {message}")
        
        # Emit to all clients in the room
        await sio.emit('update', message, room=room_id)
        
        # Also publish to Redis for other service instances
        await publish_to_redis(f"room:{room_id}", message)
        
        return {
            "success": True,
            "room": room_id,
            "message": "Broadcast sent"
        }
    except Exception as e:
        logger.error(f"Failed to broadcast: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    return True


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {sid}")
    
    # Remove from all rooms
    for room_id, members in list(active_rooms.items()):
        if sid in members:
            members.remove(sid)
            if not members:
                del active_rooms[room_id]
            logger.info(f"Removed {sid} from room {room_id}")


@sio.event
async def join_room(sid, data):
    """
    Handle client joining a room.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "username": "User Name"}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        username = data.get('username', 'Anonymous')
        
        if not room_id:
            logger.error(f"No room specified for {sid}")
            return {"success": False, "error": "Room ID required"}
        
        # Join the Socket.IO room
        await sio.enter_room(sid, room_id)
        
        # Track in active rooms
        if room_id not in active_rooms:
            active_rooms[room_id] = set()
        active_rooms[room_id].add(sid)
        
        logger.info(f"Client {sid} ({username}) joined room {room_id}")
        
        # Notify other users in the room
        await sio.emit('user_joined', {
            'user_id': user_id,
            'username': username,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=sid)
        
        return {
            "success": True,
            "room": room_id,
            "members": len(active_rooms[room_id])
        }
    except Exception as e:
        logger.error(f"Failed to join room: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def leave_room(sid, data):
    """
    Handle client leaving a room.
    Expected data: {"room": "file:<file_id>"}
    """
    try:
        room_id = data.get('room')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Leave the Socket.IO room
        await sio.leave_room(sid, room_id)
        
        # Remove from active rooms
        if room_id in active_rooms and sid in active_rooms[room_id]:
            active_rooms[room_id].remove(sid)
            if not active_rooms[room_id]:
                del active_rooms[room_id]
        
        logger.info(f"Client {sid} left room {room_id}")
        
        # Notify other users
        await sio.emit('user_left', {
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to leave room: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def diagram_update(sid, data):
    """
    Handle diagram update from a client.
    Expected data: {"room": "file:<file_id>", "update": {...}}
    """
    try:
        room_id = data.get('room')
        update = data.get('update', {})
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        logger.info(f"Diagram update in room {room_id} from {sid}")
        
        # Broadcast to all other clients in the room
        await sio.emit('update', update, room=room_id, skip_sid=sid)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle diagram update: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def cursor_move(sid, data):
    """
    Handle cursor movement.
    Expected data: {"room": "file:<file_id>", "x": 100, "y": 200, "user_id": "user-id"}
    """
    try:
        room_id = data.get('room')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Broadcast cursor position to all other clients
        await sio.emit('cursor_update', {
            'user_id': data.get('user_id'),
            'x': data.get('x'),
            'y': data.get('y'),
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=sid)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle cursor move: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        socket_app,  # Use socket_app instead of app
        host="0.0.0.0",
        port=int(os.getenv("COLLABORATION_SERVICE_PORT", "8083"))
    )
