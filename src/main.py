import asyncio
import logging

from typing import Generator
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from websockets.exceptions import ConnectionClosedError

import janus
import queue
import numpy as np
import cv2
import base64

from network.face_detection import transform


app = FastAPI()

logger = logging.getLogger()
# add_timing_middleware(app, record=logger.info, prefix="app", exclude="untimed")

websocket_objects = []
websockets_lock = asyncio.Lock()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Stub generator function (using websocket B in internal)
def stream_client_start(input_gen: Generator) -> Generator:
    for chunk in input_gen:
        yield chunk


# queue to generator auxiliary adapter
def queue_to_generator(sync_queue: queue.Queue) -> Generator:
    while True:
        yield sync_queue.get()


async def remove_ws_object_from_websockets(ws_obj):
    async with websockets_lock:
        for websocket_object in websocket_objects:
            if websocket_object == ws_obj:
                websocket_objects.remove(websocket_object)
                break


async def disconnect(socket_object: WebSocket):
    try:
        await socket_object.close()
    except RuntimeError:
        pass
    finally:
        await remove_ws_object_from_websockets(socket_object)


async def forward(ws_a: WebSocket, queue_b):
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
        await disconnect(ws_a)


async def reverse(queue_b, room_id):
    while True:
        data = await queue_b.get()
        for ws in websocket_objects:
            if ws['room_id'] == room_id:
                try:
                    await ws['ws_object'].send_bytes(data)
                except (WebSocketDisconnect, ConnectionClosedError):
                    await disconnect(ws['ws_object'])
                except RuntimeError:
                    await remove_ws_object_from_websockets(ws['ws_object'])


def process_b_client(fwd_queue, rev_queue):
    response_generator = stream_client_start(queue_to_generator(fwd_queue))
    for r in response_generator:
        rev_queue.put(r)


@app.websocket("/ws_a/{room_id}")
async def websocket_a(ws_a: WebSocket, room_id: int):
    loop = asyncio.get_event_loop()
    fwd_queue = janus.Queue()
    rev_queue = janus.Queue()
    await ws_a.accept()

    async with websockets_lock:
        websocket_objects.append({'ws_object': ws_a, 'room_id': room_id})

    process_client_task = loop.run_in_executor(None, process_b_client, fwd_queue.sync_q, rev_queue.sync_q)
    fwd_task = asyncio.create_task(forward(ws_a, fwd_queue.async_q))
    rev_task = asyncio.create_task(reverse(rev_queue.async_q, room_id))
    await asyncio.gather(process_client_task, fwd_task, rev_task)


@app.get("/unique_room_id")
async def get_unique_room_id():
    if len(websocket_objects) == 0:
        return {'room_id': 1}
    return {'room_id': websocket_objects[-1]['room_id'] + 1}