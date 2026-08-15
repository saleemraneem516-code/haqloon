from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/api/ros2",
    tags=["ROS2"]
)


class GPSData(BaseModel):
    latitude: float
    longitude: float


class ROS2Data(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    ultrasonic: Optional[float] = None
    lidar: Optional[float] = None
    gps: Optional[GPSData] = None


# تخزين مؤقت لآخر بيانات وصلت
latest_ros2_data = {}


@router.post("")
async def receive_ros2_data(data: ROS2Data):
    global latest_ros2_data

    latest_ros2_data = data.model_dump()

    return {
        "status": "success",
        "message": "ROS2 data received",
        "data": latest_ros2_data
    }


@router.get("")
async def get_latest_ros2_data():
    return {
        "status": "success",
        "data": latest_ros2_data
    }