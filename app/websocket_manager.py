from fastapi import WebSocket

clients = []


async def connect(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)


def disconnect(websocket: WebSocket):
    if websocket in clients:
        clients.remove(websocket)


async def broadcast(data):
    disconnected = []

    for client in clients:
        try:
            await client.send_json(data)
        except Exception:
            disconnected.append(client)

    for client in disconnected:
        disconnect(client)