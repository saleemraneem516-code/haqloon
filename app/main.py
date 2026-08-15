import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, SessionLocal, engine
from .models import User

from .routers import (
    admin,
    auth,
    dashboard,
    profile,
    rover,
    sensors,
    ai_detection,
    control,
    notifications,
    lidar,
    ros2
)

from .security import hash_password


# ==============================
# Base Directory
# ==============================

BASE_DIR = Path(__file__).resolve().parent



# ==============================
# FastAPI App
# ==============================

app = FastAPI(
    title="HAQLOON Control System"
)



# ==============================
# Session Middleware
# ==============================

app.add_middleware(
    SessionMiddleware,

    secret_key=os.environ.get(
        "HAQLOON_SECRET_KEY",
        secrets.token_hex(32)
    ),

    session_cookie="haqloon_session",

    same_site="lax",

    https_only=False,

    max_age=60 * 60 * 8,
)



# ==============================
# Static Files
# ==============================

app.mount(
    "/static",

    StaticFiles(
        directory=str(
            BASE_DIR / "static"
        )
    ),

    name="static"
)



# ==============================
# Routers
# ==============================

app.include_router(auth.router)

app.include_router(dashboard.router)

app.include_router(profile.router)

app.include_router(admin.router)

app.include_router(rover.router)

app.include_router(sensors.router)

app.include_router(ai_detection.router)

app.include_router(control.router)

app.include_router(notifications.router)

app.include_router(lidar.router)
app.include_router(ros2.router)

# ==============================
# Startup
# ==============================

@app.on_event("startup")
def on_startup():

    Base.metadata.create_all(
        bind=engine
    )

    create_default_admin()



# ==============================
# Create Default Admin
# ==============================

def create_default_admin():

    db = SessionLocal()

    try:

        user_exists = (
            db.query(User)
            .filter(
                (User.username == "admin") |
                (User.email == "admin@haqloon.io")
            )
            .first()
        )


        if not user_exists:

            admin = User(

                full_name="System Administrator",

                username="admin",

                email="admin@haqloon.io",

                password_hash=hash_password(
                    "Admin@12345"
                ),

                role="admin",

                is_active=True
            )


            db.add(admin)

            db.commit()


    finally:

        db.close()