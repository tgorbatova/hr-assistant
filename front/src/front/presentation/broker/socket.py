import socketio
import structlog

_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)

class SocketManager:
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
        self.app = socketio.ASGIApp(self.sio)

    async def has_clients_in_room(self, room: str) -> bool:
        rooms = self.sio.rooms(room)
        _logger.debug("Checking if there are clients in room %s", rooms)
        return bool(rooms)

    def get_socket_app(self):
        return self.app

    async def emit_to_room(self, room: str, event: str, data: dict):
        await self.sio.emit(event, data, room=room)

    def setup_handlers(self):
        @self.sio.event
        async def connect(sid, environ):
            print("Connected:", sid)

        @self.sio.event
        async def join(sid, data):
            room = data["room"]
            await self.sio.enter_room(sid, room)

        @self.sio.event
        async def disconnect(sid):
            print("Disconnected:", sid)
