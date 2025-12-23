"""Collaboration Service - Real-time collaboration with WebSocket."""
from fastapi import FastAPI, HTTPException, Header
from datetime import datetime, timedelta
import os
import json
import logging
from dotenv import load_dotenv
import socketio
import redis.asyncio as redis
from typing import Dict, Set, Optional, List
import jwt
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "autograph-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# User colors for cursor presence (8 distinct colors)
USER_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A",
    "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2"
]


class PresenceStatus(str, Enum):
    ONLINE = "online"
    AWAY = "away"
    OFFLINE = "offline"


@dataclass
class UserPresence:
    """Track user presence information."""
    user_id: str
    username: str
    email: str
    color: str
    status: PresenceStatus
    cursor_x: float = 0
    cursor_y: float = 0
    last_active: datetime = None
    selected_elements: List[str] = None
    active_element: Optional[str] = None
    is_typing: bool = False
    
    def __post_init__(self):
        if self.last_active is None:
            self.last_active = datetime.utcnow()
        if self.selected_elements is None:
            self.selected_elements = []


@dataclass
class ActivityEvent:
    """Activity feed event."""
    event_id: str
    user_id: str
    username: str
    action: str
    target: Optional[str]
    timestamp: datetime
    
    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


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
    description="Real-time collaboration service with presence, cursors, and activity tracking",
    version="1.0.0"
)

# Wrap with Socket.IO ASGI app
socket_app = socketio.ASGIApp(sio, app)

# Redis connection for pub/sub
redis_client = None
pubsub = None

# Track active rooms and users
active_rooms: Dict[str, Set[str]] = {}  # room_id -> set of session_ids
room_users: Dict[str, Dict[str, UserPresence]] = {}  # room_id -> {user_id: UserPresence}
session_user_map: Dict[str, str] = {}  # sid -> user_id
session_room_map: Dict[str, str] = {}  # sid -> room_id
activity_feeds: Dict[str, List[ActivityEvent]] = {}  # room_id -> list of events (max 100)
next_color_index: int = 0


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return None


def assign_user_color() -> str:
    """Assign a color to a new user (rotating through predefined colors)."""
    global next_color_index
    color = USER_COLORS[next_color_index % len(USER_COLORS)]
    next_color_index += 1
    return color


def add_activity_event(room_id: str, user_id: str, username: str, action: str, target: Optional[str] = None):
    """Add an event to the activity feed."""
    if room_id not in activity_feeds:
        activity_feeds[room_id] = []
    
    event = ActivityEvent(
        event_id=f"{room_id}_{len(activity_feeds[room_id])}",
        user_id=user_id,
        username=username,
        action=action,
        target=target,
        timestamp=datetime.utcnow()
    )
    
    activity_feeds[room_id].append(event)
    
    # Keep only last 100 events
    if len(activity_feeds[room_id]) > 100:
        activity_feeds[room_id] = activity_feeds[room_id][-100:]
    
    return event


async def update_user_presence(room_id: str, user_id: str, **updates):
    """Update user presence information."""
    if room_id in room_users and user_id in room_users[room_id]:
        presence = room_users[room_id][user_id]
        for key, value in updates.items():
            if hasattr(presence, key):
                setattr(presence, key, value)
        presence.last_active = datetime.utcnow()
        return presence
    return None


async def check_away_users():
    """Background task to mark users as away after 5 minutes of inactivity."""
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            now = datetime.utcnow()
            
            for room_id, users in room_users.items():
                for user_id, presence in users.items():
                    if presence.status == PresenceStatus.ONLINE:
                        time_inactive = (now - presence.last_active).total_seconds()
                        if time_inactive > 300:  # 5 minutes
                            presence.status = PresenceStatus.AWAY
                            await sio.emit('presence_update', {
                                'user_id': user_id,
                                'status': PresenceStatus.AWAY,
                                'last_active': presence.last_active.isoformat()
                            }, room=room_id)
        except Exception as e:
            logger.error(f"Error in check_away_users: {e}")


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
        
        # Start background task for checking away users
        asyncio.create_task(check_away_users())
        logger.info("Started presence monitoring task")
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


@app.get("/rooms/{room_id}/users")
async def get_room_users(room_id: str):
    """Get all users currently in a room with their presence information."""
    try:
        if room_id not in room_users:
            return {
                "room": room_id,
                "users": [],
                "count": 0
            }
        
        users_list = []
        for user_id, presence in room_users[room_id].items():
            users_list.append({
                "user_id": presence.user_id,
                "username": presence.username,
                "email": presence.email,
                "color": presence.color,
                "status": presence.status.value,
                "last_active": presence.last_active.isoformat(),
                "cursor": {"x": presence.cursor_x, "y": presence.cursor_y},
                "selected_elements": presence.selected_elements,
                "active_element": presence.active_element,
                "is_typing": presence.is_typing
            })
        
        return {
            "room": room_id,
            "users": users_list,
            "count": len(users_list)
        }
    except Exception as e:
        logger.error(f"Failed to get room users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms/{room_id}/activity")
async def get_room_activity(room_id: str, limit: int = 50):
    """Get activity feed for a room."""
    try:
        if room_id not in activity_feeds:
            return {
                "room": room_id,
                "events": [],
                "count": 0
            }
        
        events = activity_feeds[room_id][-limit:]
        return {
            "room": room_id,
            "events": [event.to_dict() for event in events],
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Failed to get activity feed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms")
async def list_active_rooms():
    """List all active rooms with user counts."""
    try:
        rooms = []
        for room_id, sessions in active_rooms.items():
            user_count = len(room_users.get(room_id, {}))
            rooms.append({
                "room_id": room_id,
                "sessions": len(sessions),
                "users": user_count
            })
        
        return {
            "rooms": rooms,
            "total": len(rooms)
        }
    except Exception as e:
        logger.error(f"Failed to list rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection with JWT authentication."""
    try:
        # Extract token from auth data
        token = None
        if auth and isinstance(auth, dict):
            token = auth.get('token')
        
        # Try to get token from query params if not in auth
        if not token and 'QUERY_STRING' in environ:
            query = environ['QUERY_STRING']
            if 'token=' in query:
                token = query.split('token=')[1].split('&')[0]
        
        # Verify JWT token
        if token:
            payload = verify_jwt_token(token)
            if payload:
                logger.info(f"Client {sid} authenticated as user {payload.get('user_id')}")
                # Store user info in session
                await sio.save_session(sid, {
                    'user_id': payload.get('user_id'),
                    'username': payload.get('username', 'Anonymous'),
                    'email': payload.get('email', '')
                })
                return True
            else:
                logger.error(f"Client {sid} failed authentication")
                return False
        else:
            logger.warning(f"Client {sid} connecting without authentication")
            # Allow connection but mark as anonymous
            await sio.save_session(sid, {
                'user_id': f'anonymous_{sid[:8]}',
                'username': 'Anonymous',
                'email': ''
            })
            return True
            
    except Exception as e:
        logger.error(f"Error during connection: {e}")
        return False


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    try:
        logger.info(f"Client disconnected: {sid}")
        
        # Get user and room info
        user_id = session_user_map.get(sid)
        room_id = session_room_map.get(sid)
        
        # Remove from all rooms
        for room_id in list(active_rooms.keys()):
            if sid in active_rooms[room_id]:
                active_rooms[room_id].remove(sid)
                if not active_rooms[room_id]:
                    del active_rooms[room_id]
                
                # Update presence and notify
                if room_id in room_users and user_id in room_users[room_id]:
                    presence = room_users[room_id][user_id]
                    presence.status = PresenceStatus.OFFLINE
                    
                    # Notify other users
                    await sio.emit('user_left', {
                        'user_id': user_id,
                        'username': presence.username,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=room_id)
                    
                    # Remove from room users after delay (in case of reconnect)
                    await asyncio.sleep(30)
                    if room_id in room_users and user_id in room_users[room_id]:
                        if room_users[room_id][user_id].status == PresenceStatus.OFFLINE:
                            del room_users[room_id][user_id]
                            if not room_users[room_id]:
                                del room_users[room_id]
                
                logger.info(f"Removed {sid} from room {room_id}")
        
        # Clean up mappings
        if sid in session_user_map:
            del session_user_map[sid]
        if sid in session_room_map:
            del session_room_map[sid]
            
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")


@sio.event
async def join_room(sid, data):
    """
    Handle client joining a room.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "username": "User Name"}
    """
    try:
        # Get session data
        session = await sio.get_session(sid)
        user_id = data.get('user_id') or session.get('user_id')
        username = data.get('username') or session.get('username', 'Anonymous')
        email = session.get('email', '')
        
        room_id = data.get('room')
        
        if not room_id:
            logger.error(f"No room specified for {sid}")
            return {"success": False, "error": "Room ID required"}
        
        # Join the Socket.IO room
        await sio.enter_room(sid, room_id)
        
        # Track in active rooms
        if room_id not in active_rooms:
            active_rooms[room_id] = set()
        active_rooms[room_id].add(sid)
        
        # Track session mappings
        session_user_map[sid] = user_id
        session_room_map[sid] = room_id
        
        # Create or update user presence
        if room_id not in room_users:
            room_users[room_id] = {}
        
        if user_id not in room_users[room_id]:
            # Assign color to new user
            color = assign_user_color()
            presence = UserPresence(
                user_id=user_id,
                username=username,
                email=email,
                color=color,
                status=PresenceStatus.ONLINE
            )
            room_users[room_id][user_id] = presence
        else:
            # User reconnecting - update status
            presence = room_users[room_id][user_id]
            presence.status = PresenceStatus.ONLINE
            presence.last_active = datetime.utcnow()
        
        logger.info(f"Client {sid} ({username}) joined room {room_id}")
        
        # Get all current users in the room
        current_users = []
        for uid, pres in room_users[room_id].items():
            current_users.append({
                "user_id": pres.user_id,
                "username": pres.username,
                "email": pres.email,
                "color": pres.color,
                "status": pres.status.value,
                "cursor": {"x": pres.cursor_x, "y": pres.cursor_y},
                "selected_elements": pres.selected_elements,
                "active_element": pres.active_element,
                "is_typing": pres.is_typing
            })
        
        # Notify other users in the room
        await sio.emit('user_joined', {
            'user_id': user_id,
            'username': username,
            'color': presence.color,
            'timestamp': datetime.utcnow().isoformat()
        }, room=room_id, skip_sid=sid)
        
        # Add activity event
        event = add_activity_event(room_id, user_id, username, "joined", None)
        await sio.emit('activity', event.to_dict(), room=room_id)
        
        return {
            "success": True,
            "room": room_id,
            "user_id": user_id,
            "color": presence.color,
            "members": len(active_rooms[room_id]),
            "users": current_users
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
    Handle cursor movement with color-coded presence.
    Expected data: {"room": "file:<file_id>", "x": 100, "y": 200, "user_id": "user-id"}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            cursor_x=data.get('x', 0),
            cursor_y=data.get('y', 0)
        )
        
        if presence:
            # Broadcast cursor position with color to all other clients
            await sio.emit('cursor_update', {
                'user_id': user_id,
                'username': presence.username,
                'color': presence.color,
                'x': data.get('x'),
                'y': data.get('y'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id, skip_sid=sid)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle cursor move: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def selection_change(sid, data):
    """
    Handle selection change.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "selected_elements": ["id1", "id2"]}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        selected_elements = data.get('selected_elements', [])
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            selected_elements=selected_elements
        )
        
        if presence:
            # Broadcast selection to all other clients
            await sio.emit('selection_update', {
                'user_id': user_id,
                'username': presence.username,
                'color': presence.color,
                'selected_elements': selected_elements,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id, skip_sid=sid)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle selection change: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def element_edit(sid, data):
    """
    Handle when a user starts/stops editing an element.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "element_id": "id" or null}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        element_id = data.get('element_id')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            active_element=element_id
        )
        
        if presence:
            # Broadcast active element to all other clients
            await sio.emit('element_active', {
                'user_id': user_id,
                'username': presence.username,
                'color': presence.color,
                'element_id': element_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id, skip_sid=sid)
            
            # Add activity event if starting edit
            if element_id:
                event = add_activity_event(room_id, user_id, presence.username, "editing", element_id)
                await sio.emit('activity', event.to_dict(), room=room_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle element edit: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def typing_status(sid, data):
    """
    Handle typing indicator.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "is_typing": true/false}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        is_typing = data.get('is_typing', False)
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            is_typing=is_typing
        )
        
        if presence:
            # Broadcast typing status to all other clients
            await sio.emit('typing_update', {
                'user_id': user_id,
                'username': presence.username,
                'is_typing': is_typing,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id, skip_sid=sid)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle typing status: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def presence_update(sid, data):
    """
    Handle presence status update.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "status": "online/away/offline"}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        status = data.get('status', 'online')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            status=PresenceStatus(status)
        )
        
        if presence:
            # Broadcast presence to all clients
            await sio.emit('presence_update', {
                'user_id': user_id,
                'username': presence.username,
                'status': status,
                'last_active': presence.last_active.isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle presence update: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def shape_created(sid, data):
    """
    Handle shape creation event for activity feed.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "shape_type": "rectangle", "shape_id": "id"}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        shape_type = data.get('shape_type', 'shape')
        shape_id = data.get('shape_id')
        
        if not room_id or not user_id:
            return {"success": False, "error": "Room ID and User ID required"}
        
        # Get username
        username = "Unknown"
        if room_id in room_users and user_id in room_users[room_id]:
            username = room_users[room_id][user_id].username
        
        # Add activity event
        event = add_activity_event(room_id, user_id, username, f"created {shape_type}", shape_id)
        await sio.emit('activity', event.to_dict(), room=room_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle shape created: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def shape_deleted(sid, data):
    """
    Handle shape deletion event for activity feed.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "shape_count": 1}
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        shape_count = data.get('shape_count', 1)
        
        if not room_id or not user_id:
            return {"success": False, "error": "Room ID and User ID required"}
        
        # Get username
        username = "Unknown"
        if room_id in room_users and user_id in room_users[room_id]:
            username = room_users[room_id][user_id].username
        
        # Add activity event
        action = f"deleted {shape_count} shape{'s' if shape_count > 1 else ''}"
        event = add_activity_event(room_id, user_id, username, action, None)
        await sio.emit('activity', event.to_dict(), room=room_id)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle shape deleted: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        socket_app,  # Use socket_app instead of app
        host="0.0.0.0",
        port=int(os.getenv("COLLABORATION_SERVICE_PORT", "8083"))
    )
