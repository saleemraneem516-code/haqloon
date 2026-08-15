import base64
import json

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel

from ..database import SessionLocal
from ..models import (
    SensorData,
    GPSData,
    LidarData,
    Notification,
    Alert,
)


router = APIRouter(
    prefix="/api/rover",
    tags=["rover"],
)


# ==================================================
# WebSocket Connections
# ==================================================

active_connections: list[WebSocket] = []


async def connect(websocket: WebSocket) -> None:
    """
    Accept a new WebSocket connection and add it
    to the active connections list.
    """

    await websocket.accept()

    active_connections.append(websocket)


def disconnect(websocket: WebSocket) -> None:
    """
    Remove a disconnected WebSocket client.
    """

    if websocket in active_connections:
        active_connections.remove(websocket)


async def broadcast(data: dict) -> None:
    """
    Send the latest rover data to all connected
    website clients.
    """

    disconnected_clients: list[WebSocket] = []

    for connection in active_connections:

        try:

            await connection.send_json(data)

        except Exception:

            disconnected_clients.append(connection)

    for connection in disconnected_clients:
        disconnect(connection)


# ==================================================
# Camera Upload Folder
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = (
    BASE_DIR
    / "static"
    / "uploads"
    / "camera_images"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ==================================================
# Save Camera Image
# ==================================================

def save_camera_image(
    base64_image: str | None,
) -> str | None:
    """
    Decode a Base64 camera image and save it
    inside the website static directory.
    """

    try:

        if not base64_image:
            return None

        # Support strings such as:
        # data:image/jpeg;base64,/9j/4AAQ...
        if "," in base64_image:
            base64_image = base64_image.split(",", 1)[1]

        image_bytes = base64.b64decode(
            base64_image
        )

        filename = datetime.now().strftime(
            "captured_%Y%m%d_%H%M%S_%f.jpg"
        )

        captured_image_path = UPLOAD_DIR / filename
        latest_image_path = UPLOAD_DIR / "latest.jpg"

        # Save a historical copy.
        with open(
            captured_image_path,
            "wb",
        ) as file:

            file.write(image_bytes)

        # Save the latest image using a fixed filename.
        with open(
            latest_image_path,
            "wb",
        ) as file:

            file.write(image_bytes)

        return (
            "/static/uploads/"
            "camera_images/latest.jpg"
        )

    except Exception as error:

        print(
            "Image Save Error:",
            error,
        )

        return None


# ==================================================
# Create Notification
# ==================================================

def create_notification(
    title: str,
    message: str,
    level: str = "INFO",
) -> None:

    db = SessionLocal()

    try:

        notification = Notification(
            title=title,
            message=message,
            level=level,
        )

        db.add(notification)
        db.commit()

    except Exception as error:

        db.rollback()

        print(
            "Notification Database Error:",
            error,
        )

    finally:

        db.close()


# ==================================================
# Create Alert
# ==================================================

def create_alert(
    title: str,
    message: str,
    level: str = "WARNING",
) -> None:

    db = SessionLocal()

    try:

        alert = Alert(
            title=title,
            message=message,
            level=level,
        )

        db.add(alert)
        db.commit()

    except Exception as error:

        db.rollback()

        print(
            "Alert Database Error:",
            error,
        )

    finally:

        db.close()


# ==================================================
# Latest Rover Data
# ==================================================

latest_data = {

    "sensors": {

        "temperature": "Offline",
        "humidity": "Offline",
        "distance": "Offline",
        "lidar": "Offline",

    },

    "lidar_map": [],

    "gps": {

        "location": None,
        "latitude": None,
        "longitude": None,
        "altitude": None,
        "satellites": None,

    },

    "camera": {

        "status": "Offline",
        "image": None,

    },

    "ai": {

        "result": "No Detection",
        "confidence": 0,
        "time": None,

    },

    "arduino": "Offline",

    "raspberry_pi": "Offline",

    "rover_status": "Disconnected",

    "last_update": None,

}


# ==================================================
# Incoming Rover Data Model
# ==================================================

class RoverData(BaseModel):

    # Sensors
    temperature: float | None = None
    humidity: float | None = None
    distance: float | None = None
    lidar: float | None = None

    # LiDAR map points
    lidar_points: list | None = None

    # GPS
    gps: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    satellites: int | None = None

    # Camera
    camera: str | None = None
    image: str | None = None

    # Artificial intelligence
    ai_result: str | None = None
    confidence: float | None = None


# ==================================================
# Receive Raspberry Pi / Rover Data
# ==================================================

@router.post("/data")
async def receive_data(
    data: RoverData,
):

    global latest_data

    sensor_record_id = None
    gps_record_id = None
    lidar_record_id = None

    # ==================================================
    # Update Sensor Values
    # ==================================================

    if data.temperature is not None:

        latest_data["sensors"]["temperature"] = (
            data.temperature
        )

    if data.humidity is not None:

        latest_data["sensors"]["humidity"] = (
            data.humidity
        )

    if data.distance is not None:

        latest_data["sensors"]["distance"] = (
            data.distance
        )

    if data.lidar is not None:

        latest_data["sensors"]["lidar"] = (
            data.lidar
        )

    # ==================================================
    # Save Sensor Data
    # ==================================================

    received_sensor_data = (

        data.temperature is not None
        or data.humidity is not None
        or data.distance is not None
        or data.lidar is not None

    )

    if received_sensor_data:

        db = SessionLocal()

        try:

            sensor_record = SensorData(
                temperature=data.temperature,
                humidity=data.humidity,
                distance=data.distance,
                lidar=data.lidar,
            )

            db.add(sensor_record)
            db.commit()
            db.refresh(sensor_record)

            sensor_record_id = sensor_record.id

        except Exception as error:

            db.rollback()

            print(
                "Sensor Database Error:",
                error,
            )

        finally:

            db.close()

    # ==================================================
    # LiDAR Map + Database
    # ==================================================

    if data.lidar_points is not None:

        latest_data["lidar_map"] = (
            data.lidar_points
        )

        if len(data.lidar_points) > 0:

            db = SessionLocal()

            try:

                lidar_record = LidarData(
                    points=json.dumps(
                        data.lidar_points
                    )
                )

                db.add(lidar_record)
                db.commit()
                db.refresh(lidar_record)

                lidar_record_id = lidar_record.id

            except Exception as error:

                db.rollback()

                print(
                    "LiDAR Database Error:",
                    error,
                )

            finally:

                db.close()

    # ==================================================
    # GPS Display
    # ==================================================

    if data.gps is not None:

        latest_data["gps"]["location"] = (
            data.gps
        )

    if data.latitude is not None:

        latest_data["gps"]["latitude"] = (
            data.latitude
        )

    if data.longitude is not None:

        latest_data["gps"]["longitude"] = (
            data.longitude
        )

    if data.altitude is not None:

        latest_data["gps"]["altitude"] = (
            data.altitude
        )

    if data.satellites is not None:

        latest_data["gps"]["satellites"] = (
            data.satellites
        )

    if (
        data.latitude is not None
        and data.longitude is not None
    ):

        latest_data["gps"]["location"] = (
            f"{data.latitude}, {data.longitude}"
        )

    # ==================================================
    # Save GPS Data
    # ==================================================

    received_gps_data = (

        data.latitude is not None
        or data.longitude is not None
        or data.altitude is not None
        or data.satellites is not None

    )

    if received_gps_data:

        db = SessionLocal()

        try:

            gps_record = GPSData(
                latitude=data.latitude,
                longitude=data.longitude,
                altitude=data.altitude,
                satellites=data.satellites,
            )

            db.add(gps_record)
            db.commit()
            db.refresh(gps_record)

            gps_record_id = gps_record.id

        except Exception as error:

            db.rollback()

            print(
                "GPS Database Error:",
                error,
            )

        finally:

            db.close()

    # ==================================================
    # Obstacle Alert
    # ==================================================

    if (
        data.distance is not None
        and data.distance < 30
    ):

        obstacle_message = (
            f"Obstacle detected at "
            f"{data.distance} cm."
        )

        create_notification(
            title="Obstacle Detected",
            message=obstacle_message,
            level="WARNING",
        )

        create_alert(
            title="Obstacle Detected",
            message=obstacle_message,
            level="WARNING",
        )

    # ==================================================
    # Camera Status
    # ==================================================

    if data.camera is not None:

        latest_data["camera"]["status"] = (
            data.camera
        )

    # ==================================================
    # Camera Image
    # ==================================================

    if data.image:

        image_url = save_camera_image(
            data.image
        )

        if image_url:

            latest_data["camera"]["image"] = (
                image_url
            )

            latest_data["camera"]["status"] = (
                "Online"
            )

            create_notification(
                title="Camera",
                message="New image captured by rover.",
                level="INFO",
            )

    # ==================================================
    # Artificial Intelligence
    # ==================================================

    if data.ai_result is not None:

        latest_data["ai"] = {

            "result": data.ai_result,

            "confidence": (
                data.confidence
                if data.confidence is not None
                else 0
            ),

            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        }

    # ==================================================
    # Connection Status
    # ==================================================

    received_any_data = (

        data.temperature is not None
        or data.humidity is not None
        or data.distance is not None
        or data.lidar is not None
        or data.lidar_points is not None
        or data.gps is not None
        or data.latitude is not None
        or data.longitude is not None
        or data.altitude is not None
        or data.satellites is not None
        or data.camera is not None
        or data.image is not None
        or data.ai_result is not None

    )

    if received_any_data:

        latest_data["raspberry_pi"] = (
            "Online"
        )

        latest_data["rover_status"] = (
            "Connected"
        )

        latest_data["last_update"] = (
            datetime.now().isoformat()
        )

    # ==================================================
    # Arduino Status
    # ==================================================

    received_arduino_data = (

        data.temperature is not None
        or data.humidity is not None
        or data.distance is not None

    )

    if received_arduino_data:

        latest_data["arduino"] = (
            "Online"
        )

    # ==================================================
    # Send Data to Website
    # ==================================================

    await broadcast(
        latest_data
    )

    # ==================================================
    # API Response
    # ==================================================

    return {

        "status": "received",

        "saved_records": {

            "sensor_record_id": sensor_record_id,
            "gps_record_id": gps_record_id,
            "lidar_record_id": lidar_record_id,

        },

        "data": latest_data,

    }


# ==================================================
# Get Latest Rover Data
# ==================================================

@router.get("/data")
def get_data():

    return latest_data


# ==================================================
# WebSocket
# ==================================================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await connect(
        websocket
    )

    try:

        await websocket.send_json(
            latest_data
        )

        while True:

            # Keeps the WebSocket connection open.
            await websocket.receive_text()

    except Exception:

        disconnect(
            websocket
        )