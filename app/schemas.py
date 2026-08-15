import re

from pydantic import BaseModel, EmailStr, field_validator

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{3,32}$")


def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must contain both letters and numbers.")
    return password


class LoginSchema(BaseModel):
    username: str
    password: str


class ProfileUpdateSchema(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    new_password: str | None = None

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-32 characters: letters, numbers, dot or underscore."
            )
        return v

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str | None) -> str | None:
        if v:
            return validate_password_strength(v)
        return v


class UserCreateSchema(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    password: str
    role: str

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-32 characters: letters, numbers, dot or underscore."
            )
        return v

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        if v not in ("admin", "employee"):
            raise ValueError("Role must be 'admin' or 'employee'.")
        return v


class UserEditSchema(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    role: str
    is_active: bool

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-32 characters: letters, numbers, dot or underscore."
            )
        return v

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        if v not in ("admin", "employee"):
            raise ValueError("Role must be 'admin' or 'employee'.")
        return v
