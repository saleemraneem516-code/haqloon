from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import ast

from ..dependencies import get_current_user, get_db
from ..models import LidarData
from ..templating import templates


router = APIRouter(tags=["lidar"])


# =========================
# LiDAR Map Page
# =========================

@router.get("/lidar")
def lidar_page(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if not user:
        return RedirectResponse(
            url="/login",
            status_code=303
        )


    latest_lidar = (
        db.query(LidarData)
        .order_by(
            LidarData.id.desc()
        )
        .first()
    )


    points = []

    if latest_lidar:
        try:
            points = ast.literal_eval(
                latest_lidar.points
            )
        except:
            points = []


    return templates.TemplateResponse(
        request,
        "lidar.html",
        {
            "user": user,
            "active": "lidar",
            "points": points
        }
    )



# =========================
# LiDAR API
# =========================

@router.get("/api/lidar")
def get_lidar(
    db: Session = Depends(get_db)
):

    latest = (
        db.query(LidarData)
        .order_by(
            LidarData.id.desc()
        )
        .first()
    )


    if not latest:
        return {
            "points": []
        }


    return {
        "points": ast.literal_eval(
            latest.points
        )
    }