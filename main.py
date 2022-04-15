import asyncio
from typing import Generator
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect
import janus
import queue

app = FastAPI()

websocket_objects = []
websockets_lock = asyncio.Lock()


# Stub generator function (using websocket B in internal)
def stream_client_start(input_gen: Generator) -> Generator:
    for chunk in input_gen:
        yield f"Get {chunk}"


# queue to generator auxiliary adapter
def queue_to_generator(sync_queue: queue.Queue) -> Generator:
    while True:
        yield sync_queue.get()


async def disconnect(socket_object):
    await socket_object.close()
    for websocket_object in websocket_objects:
        if websocket_object == socket_object:
            websocket_objects.remove(websocket_object)
            break


async def forward(ws_a: WebSocket, queue_b):
    try:
        while True:
            data = await ws_a.receive_bytes()
            print("websocket A received:", data)
            await queue_b.put(data)
    except WebSocketDisconnect:
        await disconnect(ws_a)


async def reverse(queue_b, room_id):
    while True:
        data = await queue_b.get()
        for ws in websocket_objects:
            try:
                if ws['room_id'] == room_id:
                    await ws['ws_object'].send_bytes(data)
                    print("websocket A sent:", data)
            except WebSocketDisconnect:
                await disconnect(ws['ws_object'])


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
    if websocket_objects is None:
        return {'room_id': 1}
    return {'room_id': websocket_objects[-1]['room_id'] + 1}
