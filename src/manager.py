import asyncio
import base64
from typing import Generator
import queue

from fastapi import WebSocket, WebSocketDisconnect
from websockets.exceptions import ConnectionClosedError
import numpy as np
import cv2

from network.face_detection import transform


class Manager:
    websocket_objects = []
    websockets_lock = asyncio.Lock()

    @staticmethod
    def stream_client_start(input_gen: Generator) -> Generator:
        """Stub generator function (using websocket B in internal)."""
        for chunk in input_gen:
            yield chunk

    @staticmethod
    def queue_to_generator(sync_queue: queue.Queue) -> Generator:
        """Queue to generator auxiliary adapter."""
        while True:
            yield sync_queue.get()

    async def remove_ws_object_from_websockets(self, ws_obj):
        async with self.websockets_lock:
            for websocket_object in self.websocket_objects:
                if websocket_object == ws_obj:
                    self.websocket_objects.remove(websocket_object)
                    break

    async def disconnect(self, socket_object: WebSocket):
        try:
            await socket_object.close()
        except RuntimeError:
            pass
        finally:
            await self.remove_ws_object_from_websockets(socket_object)

    async def forward(self, ws_a: WebSocket, queue_b):
        try:
            while True:
                data = await ws_a.receive_bytes()
                frame = np.asarray(bytearray(data), np.uint8)
                frame = cv2.imdecode(frame, -1)
                frame = transform(frame)
                frame = cv2.imencode('.jpg', frame)[1]
                data = base64.b64encode(frame).decode('utf-8')
                await queue_b.put(data)
        except (WebSocketDisconnect, ConnectionClosedError):
            await self.disconnect(ws_a)

    async def reverse(self, queue_b, room_id):
        while True:
            data = await queue_b.get()
            for ws in self.websocket_objects:
                if ws['room_id'] == room_id:
                    try:
                        await ws['ws_object'].send_bytes(data)
                    except (WebSocketDisconnect, ConnectionClosedError):
                        await self.disconnect(ws['ws_object'])
                    except RuntimeError:
                        await self.remove_ws_object_from_websockets(ws['ws_object'])

    def process_b_client(self, fwd_queue, rev_queue):
        response_generator = self.stream_client_start(self.queue_to_generator(fwd_queue))
        for r in response_generator:
            rev_queue.put(r)
