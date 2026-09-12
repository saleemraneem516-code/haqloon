from fastapi import APIRouter, WebSocket
from pydantic import BaseModel
from datetime import datetime
import base64
from pathlib import Path

from ..websocket_manager import connect, disconnect, broadcast
from ..database import SessionLocal
from ..models import Notification, Alert, LidarData


router = APIRouter(
    prefix="/api/rover",
    tags=["rover"]
)


# =========================
# Camera Upload Folder
# =========================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = (
    BASE_DIR /
    "static" /
    "uploads" /
    "camera_images"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_camera_image(base64_image):

    try:

        if not base64_image:
            return None


        if "," in base64_image:
            base64_image = base64_image.split(",")[1]


        image_bytes = base64.b64decode(
            base64_image
        )


        filename = (
            datetime.now().strftime(
                "captured_%Y%m%d_%H%M%S_%f.jpg"
            )
        )


        with open(
            UPLOAD_DIR / filename,
            "wb"
        ) as f:

            f.write(image_bytes)



        with open(
            UPLOAD_DIR / "latest.jpg",
            "wb"
        ) as f:

            f.write(image_bytes)



        return "/static/uploads/camera_images/latest.jpg"


    except Exception as e:

        print(
            "Image Save Error:",
            e
        )

        return None



# =========================
# Create Notification
# =========================

def create_notification(
    title,
    message,
    level="INFO"
):

    db = SessionLocal()

    try:

        notification = Notification(
            title=title,
            message=message,
            level=level
        )

        db.add(notification)
        db.commit()

    finally:

        db.close()



# =========================
# Create Alert
# =========================

def create_alert(
    title,
    message,
    level="WARNING"
):

    db = SessionLocal()

    try:

        alert = Alert(
            title=title,
            message=message,
            level=level
        )

        db.add(alert)
        db.commit()

    finally:

        db.close()



# =========================
# Latest Rover Data
# =========================

latest_data = {

    "sensors": {

        "temperature": "Offline",
        "humidity": "Offline",
        "distance": "Offline",
        "lidar": "Offline"

    },


    "lidar_map": [],


    "gps": {

        "location": None

    },


    "camera": {

        "status": "Offline",
        "image": None

    },


    "ai": {

        "result": "No Detection",
        "confidence": 0,
        "time": None

    },


    "arduino": "Offline",

    "raspberry_pi": "Offline",

    "rover_status": "Disconnected",

    "last_update": None

}



# =========================
# Data Model
# =========================

class RoverData(BaseModel):

    temperature: float | None = None

    humidity: float | None = None

    distance: float | None = None

    lidar: float | None = None


    lidar_points: list | None = None


    gps: str | None = None


    camera: str | None = None

    image: str | None = None


    ai_result: str | None = None

    confidence: float | None = None



# =========================
# Receive Raspberry Data
# =========================

@router.post("/data")
async def receive_data(
    data: RoverData
):

    global latest_data



    latest_data["sensors"] = {

        "temperature":
            data.temperature
            if data.temperature is not None
            else "Offline",


        "humidity":
            data.humidity
            if data.humidity is not None
            else "Offline",


        "distance":
            data.distance
            if data.distance is not None
            else "Offline",


        "lidar":
            data.lidar
            if data.lidar is not None
            else "Offline"

    }



    # =========================
    # LiDAR Map + Database
    # =========================

    if data.lidar_points:


        latest_data["lidar_map"] = data.lidar_points



        db = SessionLocal()

        try:

            lidar_record = LidarData(

                points=str(
                    data.lidar_points
                )

            )

            db.add(lidar_record)

            db.commit()


        finally:

            db.close()



    # =========================
    # Obstacle Alert
    # =========================

    if (
        data.distance is not None
        and data.distance < 30
    ):


        create_notification(
            "Obstacle Detected",
            f"Obstacle detected at {data.distance} cm.",
            "WARNING"
        )


        create_alert(
            "Obstacle Detected",
            f"Obstacle detected at {data.distance} cm.",
            "WARNING"
        )



    # =========================
    # Camera
    # =========================

    if data.image:


        image_url = save_camera_image(
            data.image
        )


        if image_url:


            latest_data["camera"]["image"] = image_url

            latest_data["camera"]["status"] = "Online"


            create_notification(
                "Camera",
                "New image captured by rover.",
                "INFO"
            )



    # =========================
    # AI
    # =========================

    if data.ai_result:


        latest_data["ai"] = {

            "result": data.ai_result,

            "confidence":
                data.confidence
                if data.confidence
                else 0,


            "time":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

        }



    # =========================
    # Status
    # =========================

    if (
        data.temperature is not None
        or data.humidity is not None
        or data.distance is not None
        or data.lidar is not None
    ):

        latest_data["raspberry_pi"] = "Online"

        latest_data["arduino"] = "Online"

        latest_data["rover_status"] = "Connected"


    else:

        latest_data["raspberry_pi"] = "Offline"

        latest_data["arduino"] = "Offline"

        latest_data["rover_status"] = "Disconnected"



    latest_data["last_update"] = (
        datetime.now().isoformat()
    )


    await broadcast(
        latest_data
    )


    return {

        "status": "received",

        "data": latest_data

    }



# =========================
# Get Data
# =========================

@router.get("/data")
def get_data():

    return latest_data



# =========================
# WebSocket
# =========================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await connect(
        websocket
    )


    try:

        await websocket.send_json(
            latest_data
        )


        while True:

            await websocket.receive_text()


    except Exception:

        disconnect(
            websocket
        )