from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from ..models import SensorData


router = APIRouter(
    tags=["Sensors"]
)


templates = Jinja2Templates(
    directory="app/templates"
)


# ==================================================
# Database Session
# ==================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==================================================
# Incoming Sensor Data Models
# ==================================================

class SensorValues(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    distance: float | None = None
    lidar: float | None = None


class SensorRequest(BaseModel):
    sensors: SensorValues


# ==================================================
# Convert Database Record to Dictionary
# ==================================================

def sensor_to_dict(sensor: SensorData) -> dict:
    return {
        "id": sensor.id,
        "temperature": sensor.temperature,
        "humidity": sensor.humidity,
        "distance": sensor.distance,
        "lidar": sensor.lidar,
        "created_at": (
            sensor.created_at.isoformat()
            if sensor.created_at
            else None
        )
    }


# ==================================================
# Sensors HTML Page
# ==================================================

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

    history_records = (
        db.query(SensorData)
        .order_by(SensorData.id.desc())
        .limit(100)
        .all()
    )

    history = [
        sensor_to_dict(record)
        for record in history_records
    ]

    if latest:
        data = {
            "sensors": {
                "temperature": latest.temperature,
                "humidity": latest.humidity,
                "distance": latest.distance,
                "lidar": latest.lidar
            },
            "last_update": (
                latest.created_at.isoformat()
                if latest.created_at
                else None
            )
        }

    else:
        data = {
            "sensors": {
                "temperature": None,
                "humidity": None,
                "distance": None,
                "lidar": None
            },
            "last_update": None
        }

    return templates.TemplateResponse(
        request=request,
        name="sensors.html",
        context={
            "data": data,
            "history": history
        }
    )


# ==================================================
# Receive Sensor Data
# ==================================================

@router.post("/api/sensors")
async def receive_sensor_data(
    request_data: SensorRequest,
    db: Session = Depends(get_db)
):
    values = request_data.sensors

    if (
        values.temperature is None
        and values.humidity is None
        and values.distance is None
        and values.lidar is None
    ):
        raise HTTPException(
            status_code=400,
            detail="No sensor values were provided."
        )

    sensor = SensorData(
        temperature=values.temperature,
        humidity=values.humidity,
        distance=values.distance,
        lidar=values.lidar
    )

    try:
        db.add(sensor)
        db.commit()
        db.refresh(sensor)

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not save sensor data: {error}"
        )

    return {
        "status": "saved",
        "sensor": sensor_to_dict(sensor)
    }


# ==================================================
# Get Latest Sensor Data
# ==================================================

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
            "sensors": {
                "temperature": None,
                "humidity": None,
                "distance": None,
                "lidar": None
            },
            "last_update": None
        }

    return {
        "sensors": {
            "temperature": latest.temperature,
            "humidity": latest.humidity,
            "distance": latest.distance,
            "lidar": latest.lidar
        },
        "last_update": (
            latest.created_at.isoformat()
            if latest.created_at
            else None
        )
    }


# ==================================================
# Get Stored Sensor History
# ==================================================

@router.get("/api/sensors/history")
async def get_sensor_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    ),
    db: Session = Depends(get_db)
):
    records = (
        db.query(SensorData)
        .order_by(SensorData.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(records),
        "records": [
            sensor_to_dict(record)
            for record in records
        ]
    }


# ==================================================
# Delete Sensor History
# ==================================================

@router.delete("/api/sensors/history")
async def delete_sensor_history(
    db: Session = Depends(get_db)
):
    try:
        deleted_count = (
            db.query(SensorData)
            .delete()
        )

        db.commit()

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Could not delete sensor history: {error}"
        )

    return {
        "status": "deleted",
        "deleted_records": deleted_count
    }