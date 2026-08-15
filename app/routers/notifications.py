from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..templating import templates
from ..models import Notification



router = APIRouter(
    tags=["notifications"]
)



# ==============================
# Notifications Page
# ==============================

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



    # Get notifications from database

    notifications = (
        db.query(Notification)
        .order_by(
            Notification.id.desc()
        )
        .all()
    )



    print(
        "NOTIFICATIONS FOUND:",
        len(notifications)
    )


    for n in notifications:

        print(
            n.title,
            n.message,
            n.level
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