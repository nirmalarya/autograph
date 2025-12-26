"""Collaboration Service - Real-time collaboration with WebSocket."""
from fastapi import FastAPI, HTTPException, Header
from datetime import datetime, timedelta
import os
import json
import logging
import traceback
from dotenv import load_dotenv
import socketio
import redis.asyncio as redis
from typing import Dict, Set, Optional, List
import jwt
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio

load_dotenv()

# Configure structured logging
class StructuredLogger:
    """Structured logger with JSON output for distributed tracing."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)

        # Set log level from environment variable (default: INFO)
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)

        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log(self, level: str, message: str, correlation_id: str = None, **kwargs):
        """Log structured message with correlation ID."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level.upper(),
            "message": message,
            "correlation_id": correlation_id,
            **kwargs
        }

        # Use appropriate logging method based on level
        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(json.dumps(log_data))
        elif level_upper == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level_upper == "ERROR":
            self.logger.error(json.dumps(log_data))
        else:  # INFO or any other level
            self.logger.info(json.dumps(log_data))

    def debug(self, message: str, correlation_id: str = None, **kwargs):
        self.log("debug", message, correlation_id, **kwargs)

    def info(self, message: str, correlation_id: str = None, **kwargs):
        self.log("info", message, correlation_id, **kwargs)

    def error(self, message: str, correlation_id: str = None, exc: Exception = None, **kwargs):
        """Log error message with optional exception and stack trace."""
        if exc is not None:
            kwargs['error_type'] = type(exc).__name__
            kwargs['error_message'] = str(exc)
            kwargs['stack_trace'] = traceback.format_exc()
        self.log("error", message, correlation_id, **kwargs)

    def warning(self, message: str, correlation_id: str = None, **kwargs):
        self.log("warning", message, correlation_id, **kwargs)

logger = StructuredLogger("collaboration-service")

# JWT Configuration
# IMPORTANT: Must match auth-service JWT_SECRET for token verification
# Updated: 2025-12-25 to fix signature verification issue
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
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


class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"


class ConnectionQuality(str, Enum):
    EXCELLENT = "excellent"  # < 50ms latency
    GOOD = "good"           # 50-150ms
    FAIR = "fair"           # 150-300ms
    POOR = "poor"           # > 300ms


@dataclass
class UserPresence:
    """Track user presence information."""
    user_id: str
    username: str
    email: str
    color: str
    status: PresenceStatus
    role: UserRole = UserRole.EDITOR
    cursor_x: float = 0
    cursor_y: float = 0
    last_active: datetime = None
    last_heartbeat: datetime = None
    selected_elements: List[str] = None
    active_element: Optional[str] = None
    is_typing: bool = False
    connection_quality: ConnectionQuality = ConnectionQuality.GOOD
    latency_ms: float = 0
    
    def __post_init__(self):
        if self.last_active is None:
            self.last_active = datetime.utcnow()
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()
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

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mount Socket.IO on the app instead of wrapping
# This allows both Socket.IO and HTTP routes to coexist
app.mount("/socket.io", socketio.ASGIApp(sio))

# Export app as socket_app for compatibility with startup.py
socket_app = app

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


async def redis_subscriber_task():
    """
    Background task to subscribe to Redis pub/sub channels.
    Listens for messages from other service instances and broadcasts to local clients.
    Feature #397: Redis pub/sub for cross-server broadcasting
    """
    global redis_client

    logger.info("Starting Redis subscriber task...")

    while True:
        try:
            # Create a new Redis connection for pub/sub
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))

            pubsub_client = await redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )

            # Create pub/sub instance
            pubsub = pubsub_client.pubsub()

            # Subscribe to pattern for all room channels
            await pubsub.psubscribe("room:*")
            logger.info("Subscribed to Redis pattern: room:*")

            # Listen for messages
            async for message in pubsub.listen():
                try:
                    if message['type'] == 'pmessage':
                        channel = message['channel']
                        data = message['data']

                        # Extract room_id from channel (format: "room:{room_id}")
                        room_id = channel.split(":", 1)[1] if ":" in channel else None

                        if not room_id:
                            continue

                        # Parse message
                        try:
                            msg_data = json.loads(data)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse Redis message: {data}")
                            continue

                        logger.info(f"Received Redis message for room {room_id}: {msg_data}")

                        # Broadcast to all local WebSocket clients in this room
                        # This allows messages from other server instances to reach clients on this server
                        await sio.emit('update', msg_data, room=room_id)
                        logger.info(f"Broadcasted Redis message to local clients in room {room_id}")

                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
                    continue

        except Exception as e:
            logger.error(f"Redis subscriber error: {e}")
            logger.info("Reconnecting to Redis in 5 seconds...")
            await asyncio.sleep(5)


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

        # Start Redis subscriber task for cross-server broadcasting (Feature #397)
        asyncio.create_task(redis_subscriber_task())
        logger.info("Started Redis subscriber task for cross-server broadcasting")
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
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "username": "User Name", "role": "viewer|editor|admin"}
    """
    try:
        # Get session data
        session = await sio.get_session(sid)
        user_id = data.get('user_id') or session.get('user_id')
        username = data.get('username') or session.get('username', 'Anonymous')
        email = session.get('email', '')
        role_str = data.get('role', 'editor')
        
        # Validate and set role
        try:
            user_role = UserRole(role_str)
        except ValueError:
            user_role = UserRole.EDITOR
        
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
                status=PresenceStatus.ONLINE,
                role=user_role
            )
            room_users[room_id][user_id] = presence
        else:
            # User reconnecting - update status
            presence = room_users[room_id][user_id]
            presence.status = PresenceStatus.ONLINE
            presence.last_active = datetime.utcnow()
            presence.role = user_role  # Update role
        
        logger.info(f"Client {sid} ({username}) joined room {room_id} as {user_role.value}")
        
        # Get all current users in the room
        current_users = []
        for uid, pres in room_users[room_id].items():
            current_users.append({
                "user_id": pres.user_id,
                "username": pres.username,
                "email": pres.email,
                "color": pres.color,
                "status": pres.status.value,
                "role": pres.role.value,
                "cursor": {"x": pres.cursor_x, "y": pres.cursor_y},
                "selected_elements": pres.selected_elements,
                "active_element": pres.active_element,
                "is_typing": pres.is_typing,
                "connection_quality": pres.connection_quality.value,
                "last_active": pres.last_active.isoformat() if pres.last_active else None
            })
        
        # Notify other users in the room
        await sio.emit('user_joined', {
            'user_id': user_id,
            'username': username,
            'color': presence.color,
            'role': user_role.value,
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
            "role": user_role.value,
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


@sio.event
async def comment_added(sid, data):
    """
    Handle comment added event for activity feed.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "username": "User Name", "comment_id": "id", "element_id": "id"}
    Feature #400: Activity feed - comment added
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        username = data.get('username', 'Anonymous')
        comment_id = data.get('comment_id')
        element_id = data.get('element_id')

        if not room_id or not user_id:
            return {"success": False, "error": "Room ID and User ID required"}

        # Add activity event
        target = f"element:{element_id}" if element_id else None
        event = add_activity_event(room_id, user_id, username, "added comment", target)

        # Broadcast to room
        await sio.emit('activity', event.to_dict(), room=room_id)

        logger.info(f"User {username} added comment in room {room_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to handle comment added: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def heartbeat(sid, data):
    """
    Handle presence heartbeat to maintain connection and detect quality.
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "timestamp": ms}
    Feature #416: Presence heartbeat
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        client_timestamp = data.get('timestamp', 0)
        
        if not room_id or not user_id:
            return {"success": False, "error": "Room ID and User ID required"}
        
        # Calculate latency
        server_time = datetime.utcnow().timestamp() * 1000
        latency = server_time - client_timestamp if client_timestamp > 0 else 0
        
        # Determine connection quality
        if latency < 50:
            quality = ConnectionQuality.EXCELLENT
        elif latency < 150:
            quality = ConnectionQuality.GOOD
        elif latency < 300:
            quality = ConnectionQuality.FAIR
        else:
            quality = ConnectionQuality.POOR
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            last_heartbeat=datetime.utcnow(),
            latency_ms=latency,
            connection_quality=quality
        )
        
        return {
            "success": True,
            "latency": latency,
            "quality": quality,
            "server_time": server_time
        }
    except Exception as e:
        logger.error(f"Failed to handle heartbeat: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def set_role(sid, data):
    """
    Set user role in room (viewer, editor, admin).
    Expected data: {"room": "file:<file_id>", "user_id": "user-id", "role": "viewer|editor|admin"}
    Features #417-418: Collaborative permissions
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        role = data.get('role', 'editor')
        
        if not room_id or not user_id:
            return {"success": False, "error": "Room ID and User ID required"}
        
        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            return {"success": False, "error": f"Invalid role: {role}"}
        
        # Update presence
        presence = await update_user_presence(
            room_id, user_id,
            role=user_role
        )
        
        if presence:
            # Notify others of role change
            await sio.emit('role_update', {
                'user_id': user_id,
                'username': presence.username,
                'role': role,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room_id)
        
        return {"success": True, "role": role}
    except Exception as e:
        logger.error(f"Failed to set role: {e}")
        return {"success": False, "error": str(e)}


@sio.event
async def delta_update(sid, data):
    """
    Handle delta updates (only changed properties) for bandwidth optimization.
    Expected data: {"room": "file:<file_id>", "delta": {"element_id": {...changes...}}}
    Feature #419: Bandwidth optimization - delta updates
    """
    try:
        room_id = data.get('room')
        delta = data.get('delta', {})
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        logger.info(f"Delta update in room {room_id}: {len(delta)} elements changed")
        
        # Broadcast delta to all other clients in the room
        await sio.emit('delta_update', delta, room=room_id, skip_sid=sid)
        
        return {"success": True, "elements_updated": len(delta)}
    except Exception as e:
        logger.error(f"Failed to handle delta update: {e}")
        return {"success": False, "error": str(e)}


# Track cursor update timestamps for throttling
cursor_update_throttle: Dict[str, float] = {}  # sid -> last_update_time
CURSOR_THROTTLE_MS = 50  # 50ms throttle (20 updates/sec max)


@sio.event
async def cursor_move_throttled(sid, data):
    """
    Handle cursor movement with throttling to reduce bandwidth.
    Expected data: {"room": "file:<file_id>", "x": 100, "y": 200, "user_id": "user-id"}
    Feature #420: Bandwidth optimization - throttle cursor updates
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        
        if not room_id:
            return {"success": False, "error": "Room ID required"}
        
        # Check throttle
        current_time = datetime.utcnow().timestamp() * 1000
        last_update = cursor_update_throttle.get(sid, 0)
        
        if current_time - last_update < CURSOR_THROTTLE_MS:
            # Too soon, skip this update
            return {"success": True, "throttled": True}
        
        # Update throttle timestamp
        cursor_update_throttle[sid] = current_time
        
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
        
        return {"success": True, "throttled": False}
    except Exception as e:
        logger.error(f"Failed to handle throttled cursor move: {e}")
        return {"success": False, "error": str(e)}


@app.get("/rooms/{room_id}/connection-quality")
async def get_room_connection_quality(room_id: str):
    """
    Get connection quality for all users in a room.
    Feature #423: Connection quality indicator
    """
    try:
        if room_id not in room_users:
            return {
                "room": room_id,
                "users": [],
                "count": 0
            }
        
        quality_info = []
        for user_id, presence in room_users[room_id].items():
            quality_info.append({
                "user_id": presence.user_id,
                "username": presence.username,
                "quality": presence.connection_quality.value,
                "latency_ms": presence.latency_ms,
                "last_heartbeat": presence.last_heartbeat.isoformat()
            })
        
        return {
            "room": room_id,
            "users": quality_info,
            "count": len(quality_info)
        }
    except Exception as e:
        logger.error(f"Failed to get connection quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Offline queue storage (in-memory for now, could be Redis)
offline_queues: Dict[str, List[dict]] = {}  # user_id -> list of queued operations


# Operational Transform state tracking
# Track the last known state of each element for OT conflict resolution
element_states: Dict[str, Dict[str, any]] = {}  # room_id -> {element_id: state}
operation_history: Dict[str, List[dict]] = {}  # room_id -> list of operations


@dataclass
class Operation:
    """Represents a single operation on an element."""
    operation_id: str
    user_id: str
    element_id: str
    operation_type: str  # 'move', 'resize', 'style', 'delete', 'create'
    old_value: any
    new_value: any
    timestamp: datetime
    transformed: bool = False

    def to_dict(self):
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }


def transform_operations(op1: Operation, op2: Operation) -> tuple:
    """
    Operational Transform: Transform two concurrent operations.

    Returns (op1', op2') where:
    - op1' is op1 transformed against op2
    - op2' is op2 transformed against op1

    This implements a simple OT algorithm for concurrent edits.
    """
    # If operations are on different elements, no transformation needed
    if op1.element_id != op2.element_id:
        return op1, op2

    # Same element - need to resolve conflict
    logger.info(f"OT: Transforming concurrent operations on element {op1.element_id}")
    logger.info(f"  Op1: {op1.operation_type} by {op1.user_id} at {op1.timestamp}")
    logger.info(f"  Op2: {op2.operation_type} by {op2.user_id} at {op2.timestamp}")

    # Strategy: Last-write-wins based on timestamp (with tie-breaker by user_id)
    # In production, more sophisticated OT algorithms could be used

    if op1.timestamp < op2.timestamp:
        # op2 wins - op1 is superseded
        logger.info(f"OT: Op2 wins (later timestamp)")
        op1.transformed = True
        op2.transformed = True
        return op2, op2  # Use op2's value
    elif op2.timestamp < op1.timestamp:
        # op1 wins - op2 is superseded
        logger.info(f"OT: Op1 wins (later timestamp)")
        op1.transformed = True
        op2.transformed = True
        return op1, op1  # Use op1's value
    else:
        # Same timestamp - use lexicographic ordering of user_id as tie-breaker
        if op1.user_id < op2.user_id:
            logger.info(f"OT: Op1 wins (tie-breaker)")
            op1.transformed = True
            op2.transformed = True
            return op1, op1
        else:
            logger.info(f"OT: Op2 wins (tie-breaker)")
            op1.transformed = True
            op2.transformed = True
            return op2, op2


def apply_operational_transform(room_id: str, operation: Operation) -> Operation:
    """
    Apply operational transform to resolve conflicts with concurrent operations.

    Returns the transformed operation that should be applied.
    """
    if room_id not in operation_history:
        operation_history[room_id] = []

    # Check for concurrent operations on the same element
    concurrent_ops = [
        op for op in operation_history[room_id]
        if op['element_id'] == operation.element_id
        and abs((datetime.fromisoformat(op['timestamp']) - operation.timestamp).total_seconds()) < 1.0
        and op['user_id'] != operation.user_id
        and not op.get('transformed', False)
    ]

    transformed_op = operation

    for concurrent_op_dict in concurrent_ops:
        # Convert dict back to Operation
        concurrent_op = Operation(
            operation_id=concurrent_op_dict['operation_id'],
            user_id=concurrent_op_dict['user_id'],
            element_id=concurrent_op_dict['element_id'],
            operation_type=concurrent_op_dict['operation_type'],
            old_value=concurrent_op_dict['old_value'],
            new_value=concurrent_op_dict['new_value'],
            timestamp=datetime.fromisoformat(concurrent_op_dict['timestamp']),
            transformed=concurrent_op_dict.get('transformed', False)
        )

        # Transform
        transformed_op, _ = transform_operations(transformed_op, concurrent_op)

    # Record operation in history
    operation_history[room_id].append(operation.to_dict())

    # Keep only last 1000 operations per room
    if len(operation_history[room_id]) > 1000:
        operation_history[room_id] = operation_history[room_id][-1000:]

    return transformed_op


@sio.event
async def element_update_ot(sid, data):
    """
    Handle element update with operational transform for conflict resolution.
    Expected data: {
        "room": "file:<file_id>",
        "user_id": "user-id",
        "element_id": "element-id",
        "operation_type": "move",
        "old_value": {...},
        "new_value": {...}
    }
    Feature #396: Operational Transform for concurrent edits
    """
    try:
        room_id = data.get('room')
        user_id = data.get('user_id')
        element_id = data.get('element_id')
        operation_type = data.get('operation_type', 'update')
        old_value = data.get('old_value')
        new_value = data.get('new_value')

        if not room_id or not user_id or not element_id:
            return {"success": False, "error": "room, user_id, and element_id required"}

        # Create operation
        import uuid
        operation = Operation(
            operation_id=str(uuid.uuid4()),
            user_id=user_id,
            element_id=element_id,
            operation_type=operation_type,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.utcnow()
        )

        # Apply operational transform
        transformed_op = apply_operational_transform(room_id, operation)

        logger.info(f"OT: Applied transform for {operation_type} on {element_id} by {user_id}")
        logger.info(f"  Original: {new_value}")
        logger.info(f"  Transformed: {transformed_op.new_value}")

        # Broadcast the transformed operation to all clients
        await sio.emit('element_update_resolved', {
            'element_id': transformed_op.element_id,
            'operation_type': transformed_op.operation_type,
            'value': transformed_op.new_value,
            'resolved_by_ot': transformed_op.transformed,
            'timestamp': transformed_op.timestamp.isoformat()
        }, room=room_id)

        # Update element state
        if room_id not in element_states:
            element_states[room_id] = {}
        element_states[room_id][element_id] = transformed_op.new_value

        return {
            "success": True,
            "transformed": transformed_op.transformed,
            "final_value": transformed_op.new_value
        }
    except Exception as e:
        logger.error(f"Failed to handle OT element update: {e}")
        return {"success": False, "error": str(e)}


@app.post("/ot/apply")
async def apply_ot_operation(operation_data: dict):
    """
    HTTP endpoint to apply an operation with operational transform.
    Feature #396: Operational Transform via HTTP
    """
    try:
        room_id = operation_data.get('room')
        user_id = operation_data.get('user_id')
        element_id = operation_data.get('element_id')
        operation_type = operation_data.get('operation_type', 'update')
        old_value = operation_data.get('old_value')
        new_value = operation_data.get('new_value')

        if not room_id or not user_id or not element_id:
            raise HTTPException(
                status_code=400,
                detail="room, user_id, and element_id required"
            )

        # Create operation
        import uuid
        operation = Operation(
            operation_id=str(uuid.uuid4()),
            user_id=user_id,
            element_id=element_id,
            operation_type=operation_type,
            old_value=old_value,
            new_value=new_value,
            timestamp=datetime.utcnow()
        )

        # Apply operational transform
        transformed_op = apply_operational_transform(room_id, operation)

        logger.info(f"HTTP OT: Applied transform for {operation_type} on {element_id}")

        # Broadcast the transformed operation
        await sio.emit('element_update_resolved', {
            'element_id': transformed_op.element_id,
            'operation_type': transformed_op.operation_type,
            'value': transformed_op.new_value,
            'resolved_by_ot': transformed_op.transformed,
            'timestamp': transformed_op.timestamp.isoformat()
        }, room=room_id)

        # Update element state
        if room_id not in element_states:
            element_states[room_id] = {}
        element_states[room_id][element_id] = transformed_op.new_value

        return {
            "success": True,
            "transformed": transformed_op.transformed,
            "final_value": transformed_op.new_value,
            "operation_id": transformed_op.operation_id
        }
    except Exception as e:
        logger.error(f"Failed to apply OT operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ot/history/{room_id}")
async def get_operation_history(room_id: str, limit: int = 100):
    """
    Get operation history for a room.
    Feature #396: View OT operation history
    """
    try:
        history = operation_history.get(room_id, [])
        return {
            "room": room_id,
            "operations": history[-limit:],
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get operation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/offline/queue")
async def queue_offline_operation(operation: dict):
    """
    Queue an operation for a user who is offline.
    Feature #424: Offline mode - queue edits when disconnected
    """
    try:
        user_id = operation.get('user_id')
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")

        if user_id not in offline_queues:
            offline_queues[user_id] = []

        operation['queued_at'] = datetime.utcnow().isoformat()
        offline_queues[user_id].append(operation)

        return {
            "success": True,
            "queued": len(offline_queues[user_id]),
            "message": "Operation queued for sync when online"
        }
    except Exception as e:
        logger.error(f"Failed to queue operation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/offline/queue/{user_id}")
async def get_offline_queue(user_id: str):
    """
    Get queued operations for a user to sync when they come online.
    Feature #424: Offline mode - retrieve queued edits
    """
    try:
        queue = offline_queues.get(user_id, [])
        return {
            "user_id": user_id,
            "operations": queue,
            "count": len(queue)
        }
    except Exception as e:
        logger.error(f"Failed to get offline queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/offline/queue/{user_id}")
async def clear_offline_queue(user_id: str):
    """
    Clear queued operations after successful sync.
    Feature #424: Offline mode - clear queue after sync
    """
    try:
        if user_id in offline_queues:
            count = len(offline_queues[user_id])
            del offline_queues[user_id]
            return {
                "success": True,
                "cleared": count,
                "message": "Queue cleared"
            }
        return {
            "success": True,
            "cleared": 0,
            "message": "No queue found"
        }
    except Exception as e:
        logger.error(f"Failed to clear offline queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    import ssl
    from pathlib import Path

    port = int(os.getenv("COLLABORATION_SERVICE_PORT", "8083"))
    tls_enabled = os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")

    if tls_enabled:
        # Configure TLS 1.3
        cert_dir = Path(__file__).parent.parent.parent.parent / "certs"
        cert_file = str(cert_dir / "server-cert.pem")
        key_file = str(cert_dir / "server-key.pem")

        # Create SSL context for TLS 1.3
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        # TLS 1.3 cipher suites
        ssl_context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

        # Security options
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_TLSv1_2
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        logger.info(f"Starting collaboration-service with TLS 1.3 on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        logger.info(f"Starting collaboration-service without TLS on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
