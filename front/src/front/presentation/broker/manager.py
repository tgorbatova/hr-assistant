import asyncio
import json
from collections import defaultdict

import structlog
from nats.aio.client import Client as NatsClient
from nats.js.api import ConsumerConfig, DeliverPolicy

from front.presentation.broker.socket import SocketManager

_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class NATSManager:
    def __init__(self, nats_client: NatsClient, socket_manager: SocketManager):
        self.nats = nats_client
        self.socket_manager = socket_manager
        self.pending_rooms: dict[str, asyncio.Event] = defaultdict(asyncio.Event)

    async def handle_message(self, room: str, data: dict, msg):
        await self.socket_manager.emit_to_room(room, "task_ready", data)
        _logger.debug("Message sent to room %s and acknowledged", room)

    async def subscribe(self):
        async def callback(msg):
            _logger.debug("Got message from subscriber: %s", msg)
            data = json.loads(msg.data.decode())
            _logger.debug("Got data from subscriber: %s", data)
            room = data["file_id"]

            # Create a task to handle this message independently
            asyncio.create_task(self.handle_message(room, data, msg))

        js = self.nats.jetstream()

        config = ConsumerConfig(
            durable_name="front_websocket",
            deliver_policy=DeliverPolicy.LAST,
        )

        await js.subscribe(subject="inference.formatted", durable="websocket", cb=callback, config=config)

        _logger.debug("Subscribing to inference.converted")
