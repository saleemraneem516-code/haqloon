import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, log_activity
from ..schemas import ProfileUpdateSchema
from ..security import get_csrf_token, hash_password, verify_csrf, verify_password
from ..templating import templates

router = APIRouter(tags=["profile"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "static" / "uploads"
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 3 * 1024 * 1024  # 3 MB


@router.get("/profile")
def profile_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
                        "user": user,
            "csrf_token": get_csrf_token(request),
            "error": None,
            "success": None,
        },
    )


@router.post("/profile/update")
async def profile_update(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    form = await request.form()
    csrf_token = form.get("csrf_token")

    def render(error=None, success=None, status_code=200):
        return templates.TemplateResponse(
            request,
            "profile.html",
            {
                                "user": user,
                "csrf_token": get_csrf_token(request),
                "error": error,
                "success": success,
            },
            status_code=status_code,
        )

    if not verify_csrf(request, csrf_token):
        return render(error="Your session expired. Please resubmit the form.", status_code=400)

    current_password = form.get("current_password") or ""
    if not verify_password(current_password, user.password_hash):
        return render(error="Current password is incorrect.", status_code=400)

    new_password = (form.get("new_password") or "").strip() or None

    try:
        data = ProfileUpdateSchema(
            username=(form.get("username") or "").strip(),
            email=(form.get("email") or "").strip(),
            full_name=(form.get("full_name") or "").strip(),
            new_password=new_password,
        )
    except ValidationError as exc:
        return render(error=exc.errors()[0]["msg"], status_code=400)

    # Uniqueness checks, excluding the current user.
    from ..models import User  # local import avoids circularity at module load

    clash = (
        db.query(User)
        .filter(User.username == data.username, User.id != user.id)
        .first()
    )
    if clash:
        return render(error="That username is already taken.", status_code=400)

    clash_email = (
        db.query(User).filter(User.email == data.email, User.id != user.id).first()
    )
    if clash_email:
        return render(error="That email is already in use.", status_code=400)

    old_username = user.username
    user.username = data.username
    user.email = data.email
    user.full_name = data.full_name

    if data.new_password:
        user.password_hash = hash_password(data.new_password)

    picture: UploadFile | None = form.get("profile_picture")
    if picture is not None and getattr(picture, "filename", ""):
        if picture.content_type not in ALLOWED_IMAGE_TYPES:
            return render(error="Profile picture must be a PNG, JPEG, WEBP or GIF.", status_code=400)
        contents = await picture.read()
        if len(contents) > MAX_IMAGE_BYTES:
            return render(error="Profile picture must be under 3 MB.", status_code=400)
        ext = Path(picture.filename).suffix or ".png"
        filename = f"{uuid.uuid4().hex}{ext}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        with open(UPLOAD_DIR / filename, "wb") as f:
            f.write(contents)
        user.profile_picture = f"/static/uploads/{filename}"

    db.commit()

    # Username may have changed -- keep the session cookie in sync.
    request.session["username"] = user.username
    log_activity(db, request, old_username, "Updated their profile")

    return render(success="Profile updated successfully.")
