from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Float
)

from .database import Base



class RoleEnum:

    ADMIN = "admin"

    EMPLOYEE = "employee"





# ==============================
# Users
# ==============================

class User(Base):

    __tablename__ = "users"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    full_name = Column(
        String(120),
        nullable=False
    )


    username = Column(
        String(60),
        unique=True,
        index=True,
        nullable=False
    )


    password_hash = Column(
        String(255),
        nullable=False
    )


    email = Column(
        String(120),
        unique=True,
        index=True,
        nullable=False
    )


    role = Column(
        String(20),
        nullable=False,
        default=RoleEnum.EMPLOYEE
    )


    profile_picture = Column(
        String(255),
        default="/static/uploads/default.svg"
    )


    last_login = Column(
        DateTime,
        nullable=True
    )


    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


    @property
    def is_admin(self) -> bool:
        return self.role == RoleEnum.ADMIN


    @property
    def status_label(self) -> str:
        return "Active" if self.is_active else "Disabled"





# ==============================
# Activity Logs
# ==============================

class ActivityLog(Base):

    __tablename__ = "activity_logs"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    username = Column(
        String(60),
        nullable=False
    )


    action = Column(
        String(255),
        nullable=False
    )


    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )


    ip_address = Column(
        String(64),
        nullable=True
    )







# ==============================
# Rover Sensor Data
# ==============================

class SensorData(Base):

    __tablename__ = "sensor_data"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    temperature = Column(
        Float,
        nullable=True
    )


    humidity = Column(
        Float,
        nullable=True
    )


    distance = Column(
        Float,
        nullable=True
    )


    lidar = Column(
        Float,
        nullable=True
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )






# ==============================
# GPS Tracking History
# ==============================

class GPSData(Base):

    __tablename__ = "gps_data"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    latitude = Column(
        Float,
        nullable=True
    )


    longitude = Column(
        Float,
        nullable=True
    )


    altitude = Column(
        Float,
        nullable=True
    )


    satellites = Column(
        Integer,
        nullable=True
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )





# ==============================
# Rover Notifications
# ==============================

class Notification(Base):

    __tablename__ = "notifications"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    title = Column(
        String(120),
        nullable=False
    )


    message = Column(
        String(255),
        nullable=False
    )


    level = Column(
        String(20),
        default="INFO"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )





# ==============================
# Rover Alerts History
# ==============================

class Alert(Base):

    __tablename__ = "alerts"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    title = Column(
        String(120),
        nullable=False
    )


    message = Column(
        String(255),
        nullable=False
    )


    level = Column(
        String(20),
        default="WARNING"
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )





# ==============================
# LiDAR Data History
# ==============================

class LidarData(Base):

    __tablename__ = "lidar_data"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    points = Column(
        String,
        nullable=False
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )