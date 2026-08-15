from fastapi import APIRouter
from datetime import datetime


router = APIRouter(
    prefix="/api/ai",
    tags=["AI Detection"]
)


latest_ai = {

    "result": "No Detection",

    "confidence": 0,

    "image": None,

    "time": None

}



@router.get("/result")
def get_ai_result():

    return latest_ai