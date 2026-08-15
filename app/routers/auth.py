from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db, log_activity
from ..models import User, Notification
from ..security import get_csrf_token, verify_csrf, verify_password
from ..templating import templates


router = APIRouter(
    tags=["auth"]
)



# =========================
# Root
# =========================

@router.get("/")
def root(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    return RedirectResponse(
        "/dashboard" if user else "/login",
        status_code=303
    )



# =========================
# Login Page
# =========================

@router.get("/login")
def login_form(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )

    if user:

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )


    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "csrf_token": get_csrf_token(request),
            "error": None,
        },
    )





# =========================
# Login Submit
# =========================

@router.post("/login")
async def login_submit(
    request: Request,
    db: Session = Depends(get_db)
):

    form = await request.form()


    username = (
        form.get("username") or ""
    ).strip()


    password = (
        form.get("password") or ""
    )


    csrf_token = form.get(
        "csrf_token"
    )



    def fail(message: str):

        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "csrf_token": get_csrf_token(request),
                "error": message,
                "username": username,
            },
            status_code=400,
        )



    if not verify_csrf(
        request,
        csrf_token
    ):

        return fail(
            "Your session expired. Please try again."
        )



    if not username or not password:

        return fail(
            "Enter both username and password."
        )



    user = (
        db.query(User)
        .filter(
            User.username == username
        )
        .first()
    )



    if not user or not verify_password(
        password,
        user.password_hash
    ):

        log_activity(
            db,
            request,
            username,
            "Failed login attempt"
        )


        return fail(
            "Incorrect username or password."
        )



    if not user.is_active:

        return fail(
            "This account has been disabled. Contact an administrator."
        )



    # Update Login Time

    user.last_login = datetime.utcnow()

    db.commit()



    # Create Session

    request.session.clear()

    request.session["user_id"] = user.id

    request.session["username"] = user.username



    # Activity Log

    log_activity(
        db,
        request,
        user.username,
        "Logged in"
    )



    # =========================
    # Login Notification
    # =========================

    notification = Notification(

        title="User Login",

        message=f"{user.username} logged in successfully.",

        level="INFO"

    )


    db.add(notification)

    db.commit()



    return RedirectResponse(
        "/welcome",
        status_code=303
    )







# =========================
# Welcome
# =========================

@router.get("/welcome")
def welcome(
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
        "welcome.html",
        {
            "user": user
        }
    )







# =========================
# Logout
# =========================

@router.get("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db)
):

    user = get_current_user(
        request,
        db
    )


    username = (
        user.username
        if user
        else request.session.get(
            "username",
            "there"
        )
    )



    if user:


        # Activity Log

        log_activity(
            db,
            request,
            user.username,
            "Logged out"
        )



        # =========================
        # Logout Notification
        # =========================

        notification = Notification(

            title="User Logout",

            message=f"{user.username} logged out.",

            level="INFO"

        )


        db.add(notification)

        db.commit()



    request.session.clear()



    return RedirectResponse(
        f"/goodbye?u={quote(username)}",
        status_code=303
    )







# =========================
# Goodbye
# =========================

@router.get("/goodbye")
def goodbye(
    request: Request,
    u: str = "there"
):

    return templates.TemplateResponse(
        request,
        "goodbye.html",
        {
            "username": u
        }
    )