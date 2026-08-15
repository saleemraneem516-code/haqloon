from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..templating import templates
from ..models import SensorData, Notification, Alert


router = APIRouter(
    tags=["dashboard"]
)


# =========================
# Main Dashboard
# =========================

@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "user": user,
            "active": "dashboard"
        }
    )


# =========================
# Alerts History Page
# =========================

@router.get("/alerts")
async def alerts_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    alerts = (
        db.query(Alert)
        .order_by(
            Alert.id.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request,
        "alerts.html",
        {
            "user": user,
            "active": "alerts",
            "alerts": alerts
        }
    )


# =========================
# AI Detection
# =========================

@router.get("/ai-detection")
async def ai_detection_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "ai_detection.html",
        {
            "user": user,
            "active": "ai-detection"
        }
    )


# =========================
# Rover Control Page
# =========================

@router.get("/rover")
async def rover_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    return templates.TemplateResponse(
        request,
        "rover.html",
        {
            "user": user,
            "active": "rover"
        }
    )


# =========================
# Notifications Page
# =========================

@router.get("/notifications")
async def notifications_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            "/login",
            status_code=303
        )

    notifications = (
        db.query(Notification)
        .order_by(
            Notification.id.desc()
        )
        .all()
    )

    return templates.TemplateResponse(
        request,
        "notifications.html",
        {
            "user": user,
            "active": "notifications",
            "notifications": notifications
        }
    )


# =========================
# Other Feature Pages
# =========================

FEATURE_PAGES = {

    "sensors": "Sensor Data",

    "camera": "Camera Feed",

    "gps": "GPS Tracking",

    "alerts": "Alerts History",

}


def _feature_page(
    slug: str,
    title: str
):

    async def handler(
        request: Request,
        db: Session = Depends(get_db)
    ):

        user = get_current_user(
            request,
            db
        )

        if not user:
            return RedirectResponse(
                "/login",
                status_code=303
            )


        latest_sensor = (
            db.query(SensorData)
            .order_by(
                SensorData.id.desc()
            )
            .first()
        )


        return templates.TemplateResponse(
            request,
            "feature.html",
            {
                "user": user,
                "active": slug,
                "page_title": title,
                "sensor": latest_sensor,
            },
        )


    return handler



for _slug, _title in FEATURE_PAGES.items():

    router.add_api_route(
        f"/{_slug}",

        _feature_page(
            _slug,
            _title
        ),

        methods=["GET"],

        name=f"feature_{_slug}",

    )