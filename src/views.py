import asyncio

from fastapi import WebSocket
import janus

from src.main import app
from src.manager import Manager

manager = Manager()


@app.get('/unique_room_id')
async def get_unique_room_id():
    if len(manager.websocket_objects) == 0:
        return {'room_id': 1}
    return {'room_id': manager.websocket_objects[-1]['room_id'] + 1}


@app.websocket('/ws_a/{room_id}')
async def websocket_a(ws_a: WebSocket, room_id: int):
    loop = asyncio.get_event_loop()
    fwd_queue = janus.Queue()
    rev_queue = janus.Queue()
    await ws_a.accept()

    async with manager.websockets_lock:
        manager.websocket_objects.append({'ws_object': ws_a, 'room_id': room_id})

    process_client_task = loop.run_in_executor(None, manager.process_b_client, fwd_queue.sync_q, rev_queue.sync_q)
    fwd_task = asyncio.create_task(manager.forward(ws_a, fwd_queue.async_q))
    rev_task = asyncio.create_task(manager.reverse(rev_queue.async_q, room_id))
    await asyncio.gather(process_client_task, fwd_task, rev_task)
