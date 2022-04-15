import asyncio
import time
from typing import Generator
from fastapi import FastAPI
from fastapi import WebSocket
import janus
import queue

app = FastAPI()


# Stub generator function (using websocket B in internal)
def stream_client_start(input_gen: Generator) -> Generator:
    for chunk in input_gen:
        time.sleep(1)
        yield f"Get {chunk}"


# queue to generator auxiliary adapter
def queue_to_generator(sync_queue: queue.Queue) -> Generator:
    while True:
        yield sync_queue.get()


async def forward(ws_a: WebSocket, queue_b):
    while True:
        data = await ws_a.receive_text()
        print("websocket A received:", data)
        await queue_b.put(data)


async def reverse(ws_a: WebSocket, queue_b):
    while True:
        data = await queue_b.get()
        await ws_a.send_text(data)
        print("websocket A sent:", data)


def process_b_client(fwd_queue, rev_queue):
    response_generator = stream_client_start(queue_to_generator(fwd_queue))
    for r in response_generator:
        rev_queue.put(r)


@app.websocket("/ws_a")
async def websocket_a(ws_a: WebSocket):
    loop = asyncio.get_event_loop()
    fwd_queue = janus.Queue()
    rev_queue = janus.Queue()
    await ws_a.accept()

    process_client_task = loop.run_in_executor(None, process_b_client, fwd_queue.sync_q, rev_queue.sync_q)
    fwd_task = asyncio.create_task(forward(ws_a, fwd_queue.async_q))
    rev_task = asyncio.create_task(reverse(ws_a, rev_queue.async_q))
    await asyncio.gather(process_client_task, fwd_task, rev_task)
