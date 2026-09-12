from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import SensorData


router = APIRouter(
    tags=["Sensors"]
)


templates = Jinja2Templates(
    directory="app/templates"
)


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()



# ==========================
# Sensors HTML Page
# ==========================

@router.get("/sensors")
async def sensors_page(
    request: Request,
    db: Session = Depends(get_db)
):

    latest = (
        db.query(SensorData)
        .order_by(SensorData.id.desc())
        .first()
    )


    if latest:

        data = {
            "sensors": {
                "temperature": latest.temperature,
                "humidity": latest.humidity,
                "distance": latest.distance,
                "lidar": latest.lidar
            },

            "last_update": latest.created_at
        }

    else:

        data = {
            "sensors": {
                "temperature": 0,
                "humidity": 0,
                "distance": 0,
                "lidar": 0
            },

            "last_update": "No data"
        }


    return templates.TemplateResponse(
        "sensors.html",
        {
            "request": request,
            "data": data
        }
    )



# ==========================
# Receive Raspberry Pi Data
# ==========================

@router.post("/api/sensors")
async def receive_sensor_data(
    data: dict,
    db: Session = Depends(get_db)
):

    sensor = SensorData(

        temperature=data["sensors"].get("temperature"),

        humidity=data["sensors"].get("humidity"),

        distance=data["sensors"].get("distance"),

        lidar=data["sensors"].get("lidar")

    )


    db.add(sensor)

    db.commit()

    db.refresh(sensor)


    return {
        "status": "saved",
        "id": sensor.id
    }



# ==========================
# Get Latest Sensor Data
# ==========================

@router.get("/api/sensors")
async def get_sensor_data(
    db: Session = Depends(get_db)
):

    latest = (
        db.query(SensorData)
        .order_by(SensorData.id.desc())
        .first()
    )


    if latest is None:

        return {
            "message": "No sensor data"
        }


    return {

        "sensors": {

            "temperature": latest.temperature,
            "humidity": latest.humidity,
            "distance": latest.distance,
            "lidar": latest.lidar

        },

        "last_update": latest.created_at

    }