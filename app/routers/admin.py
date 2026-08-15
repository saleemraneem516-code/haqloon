import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, log_activity
from ..models import ActivityLog, User
from ..schemas import UserCreateSchema, UserEditSchema
from ..security import get_csrf_token, hash_password, verify_csrf
from ..templating import templates

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(request: Request, db: Session):
    """Returns the current user if they're an active administrator,
    otherwise returns a redirect response to send back to callers."""
    user = get_current_user(request, db)
    if not user:
        return None, RedirectResponse("/login", status_code=303)
    if not user.is_admin:
        return None, RedirectResponse("/dashboard?denied=1", status_code=303)
    return user, None


@router.get("")
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active.is_(True)).count()
    admin_count = db.query(User).filter(User.role == "admin").count()
    recent_logins = (
        db.query(User)
        .filter(User.last_login.isnot(None))
        .order_by(User.last_login.desc())
        .limit(5)
        .all()
    )
    recent_activity = (
        db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(15).all()
    )

    return templates.TemplateResponse(
        request,
        "admin/dashboard.html",
        {
                        "user": admin,
            "active": "admin",
            "total_users": total_users,
            "active_users": active_users,
            "admin_count": admin_count,
            "disabled_users": total_users - active_users,
            "recent_logins": recent_logins,
            "recent_activity": recent_activity,
        },
    )


@router.get("/users")
def list_users(request: Request, q: str = "", db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(User.username.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        )
    users = query.order_by(User.created_at.desc()).all()

    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {
                        "user": admin,
            "active": "admin",
            "users": users,
            "q": q,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.get("/users/add")
def add_user_form(request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request,
        "admin/user_form.html",
        {
                        "user": admin,
            "active": "admin",
            "csrf_token": get_csrf_token(request),
            "mode": "add",
            "target": None,
            "error": None,
        },
    )


@router.post("/users/add")
async def add_user_submit(request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect

    form = await request.form()

    def render(error, status_code=400):
        return templates.TemplateResponse(
            request,
            "admin/user_form.html",
            {
                                "user": admin,
                "active": "admin",
                "csrf_token": get_csrf_token(request),
                "mode": "add",
                "target": None,
                "error": error,
                "form": form,
            },
            status_code=status_code,
        )

    if not verify_csrf(request, form.get("csrf_token")):
        return render("Your session expired. Please resubmit the form.")

    try:
        data = UserCreateSchema(
            full_name=(form.get("full_name") or "").strip(),
            username=(form.get("username") or "").strip(),
            email=(form.get("email") or "").strip(),
            password=form.get("password") or "",
            role=form.get("role") or "employee",
        )
    except ValidationError as exc:
        return render(exc.errors()[0]["msg"])

    if db.query(User).filter(User.username == data.username).first():
        return render("That username is already taken.")
    if db.query(User).filter(User.email == data.email).first():
        return render("That email is already registered.")

    new_user = User(
        full_name=data.full_name,
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    log_activity(db, request, admin.username, f"Created user '{new_user.username}'")

    return RedirectResponse("/admin/users", status_code=303)


@router.get("/users/edit/{user_id}")
def edit_user_form(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return RedirectResponse("/admin/users", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin/user_form.html",
        {
                        "user": admin,
            "active": "admin",
            "csrf_token": get_csrf_token(request),
            "mode": "edit",
            "target": target,
            "error": None,
        },
    )


@router.post("/users/edit/{user_id}")
async def edit_user_submit(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return RedirectResponse("/admin/users", status_code=303)

    form = await request.form()

    def render(error, status_code=400):
        return templates.TemplateResponse(
            request,
            "admin/user_form.html",
            {
                                "user": admin,
                "active": "admin",
                "csrf_token": get_csrf_token(request),
                "mode": "edit",
                "target": target,
                "error": error,
            },
            status_code=status_code,
        )

    if not verify_csrf(request, form.get("csrf_token")):
        return render("Your session expired. Please resubmit the form.")

    if target.id == admin.id and form.get("role") != "admin":
        return render("You cannot remove your own administrator role.")
    if target.id == admin.id and not form.get("is_active"):
        return render("You cannot disable your own account.")

    try:
        data = UserEditSchema(
            full_name=(form.get("full_name") or "").strip(),
            username=(form.get("username") or "").strip(),
            email=(form.get("email") or "").strip(),
            role=form.get("role") or "employee",
            is_active=bool(form.get("is_active")),
        )
    except ValidationError as exc:
        return render(exc.errors()[0]["msg"])

    clash = (
        db.query(User)
        .filter(User.username == data.username, User.id != target.id)
        .first()
    )
    if clash:
        return render("That username is already taken.")
    clash_email = (
        db.query(User).filter(User.email == data.email, User.id != target.id).first()
    )
    if clash_email:
        return render("That email is already registered.")

    target.full_name = data.full_name
    target.username = data.username
    target.email = data.email
    target.role = data.role
    target.is_active = data.is_active
    db.commit()
    log_activity(db, request, admin.username, f"Edited user '{target.username}'")

    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/delete/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    form = await request.form()
    if not verify_csrf(request, form.get("csrf_token")):
        return RedirectResponse("/admin/users", status_code=303)

    if user_id == admin.id:
        return RedirectResponse("/admin/users?error=self_delete", status_code=303)

    target = db.query(User).filter(User.id == user_id).first()
    if target:
        db.delete(target)
        db.commit()
        log_activity(db, request, admin.username, f"Deleted user '{target.username}'")

    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/toggle-status/{user_id}")
async def toggle_status(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    form = await request.form()
    if not verify_csrf(request, form.get("csrf_token")):
        return RedirectResponse("/admin/users", status_code=303)

    if user_id == admin.id:
        return RedirectResponse("/admin/users?error=self_disable", status_code=303)

    target = db.query(User).filter(User.id == user_id).first()
    if target:
        target.is_active = not target.is_active
        db.commit()
        state = "enabled" if target.is_active else "disabled"
        log_activity(db, request, admin.username, f"{state.capitalize()} user '{target.username}'")

    return RedirectResponse("/admin/users", status_code=303)


@router.post("/users/reset-password/{user_id}")
async def reset_password(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin, redirect = _require_admin(request, db)
    if redirect:
        return redirect
    form = await request.form()
    if not verify_csrf(request, form.get("csrf_token")):
        return RedirectResponse("/admin/users", status_code=303)

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        return RedirectResponse("/admin/users", status_code=303)

    temp_password = secrets.token_urlsafe(9)
    target.password_hash = hash_password(temp_password)
    db.commit()
    log_activity(db, request, admin.username, f"Reset password for '{target.username}'")

    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "admin/users.html",
        {
                        "user": admin,
            "active": "admin",
            "users": users,
            "q": "",
            "csrf_token": get_csrf_token(request),
            "reset_username": target.username,
            "reset_password_value": temp_password,
        },
    )
