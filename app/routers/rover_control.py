from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/control",
    tags=["rover control"]
)



# الأجهزة المتصلة
connected_clients = []



class RoverCommand(BaseModel):

    command: str





# =========================
# Website sends command
# =========================

@router.post("/move")
async def move_rover(
    data: RoverCommand
):

    message = {
        "command": data.command
    }


    for client in connected_clients:

        await client.send_json(
            message
        )


    return {

        "status":"sent",

        "command":data.command

    }







# =========================
# Raspberry WebSocket
# =========================

@router.websocket("/ws")
async def rover_control_ws(
    websocket: WebSocket
):

    await websocket.accept()


    connected_clients.append(
        websocket
    )


    print(
        "Raspberry Connected"
    )


    try:

        while True:

            await websocket.receive_text()


    except WebSocketDisconnect:


        connected_clients.remove(
            websocket
        )


        print(
            "Raspberry Disconnected"
        )