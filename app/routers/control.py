from fastapi import APIRouter
from pydantic import BaseModel

from ..websocket_manager import broadcast


router = APIRouter(
    prefix="/api/control",
    tags=["rover control"]
)



class RoverCommand(BaseModel):

    command: str




current_command = {
    "command": "STOP"
}





@router.post("/move")
async def move_rover(
    data: RoverCommand
):

    global current_command


    current_command["command"] = data.command


    await broadcast(
        {
            "rover_command": data.command
        }
    )


    return {

        "status": "sent",

        "command": data.command

    }





@router.get("/status")
def rover_status():

    return current_command