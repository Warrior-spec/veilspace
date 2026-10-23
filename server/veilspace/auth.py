from collections import defaultdict, deque
from contextlib import closing
import re
import secrets
import sqlite3
from threading import Lock
import time
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from veilspace.database import connect_database
from veilspace.security import hash_password, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)
dummy_hash = hash_password(secrets.token_urlsafe(24))


class LoginInput(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address")
        return value


class RegisterInput(LoginInput):
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("display_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Enter your name")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value.isspace():
            raise ValueError("Password cannot contain only spaces")
        return value


class AuthLimiter:
    def __init__(self):
        self.entries: dict[str, deque] = defaultdict(deque)
        self.lock = Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            for old in [key for key, entries in self.entries.items() if not entries or entries[-1] < now - 900]:
                del self.entries[old]
            entries = self.entries[key]
            while entries and entries[0] < now - 900:
                entries.popleft()
            if len(entries) >= 20 or len(self.entries) > 10000:
                raise HTTPException(429, "Too many attempts. Try again later.", headers={"Retry-After": "900"})
            entries.append(now)


def check_attempt(request: Request) -> None:
    request.app.state.auth_limiter.check(request.client.host if request.client else "unknown")


def access_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or len(credentials.credentials) > 256:
        raise HTTPException(401, "Please log in", headers={"WWW-Authenticate": "Bearer"})
    return credentials.credentials


def current_user(request: Request, token: Annotated[str, Depends(access_token)]) -> dict:
    with closing(connect_database(request.app.state.settings.data_dir)) as connection:
        connection.row_factory = sqlite3.Row
        user = connection.execute(
            "SELECT u.id, u.email, u.display_name, m.workspace_id FROM sessions s "
            "JOIN users u ON u.id=s.user_id JOIN memberships m ON m.user_id=u.id "
            "WHERE s.token_hash=? AND s.expires_at>? AND m.workspace_id=1",
            (token_hash(token), int(time.time())),
        ).fetchone()
    if user is None:
        raise HTTPException(401, "Session expired. Please log in.", headers={"WWW-Authenticate": "Bearer"})
    return dict(user)


def create_session(connection: sqlite3.Connection, user: dict, hours: int) -> dict:
    now = int(time.time())
    token = secrets.token_urlsafe(32)
    expires = now + hours * 3600
    connection.execute("DELETE FROM sessions WHERE expires_at<=?", (now,))
    connection.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (token_hash(token), user["id"], expires, now))
    return {"access_token": token, "token_type": "bearer", "expires_at": expires, "user": user}


@router.post("/register", status_code=201, dependencies=[Depends(check_attempt)])
def register(data: RegisterInput, request: Request) -> dict:
    if not request.app.state.settings.allow_registration:
        raise HTTPException(403, "Registration is closed")
    user = {"id": uuid.uuid4().hex, "email": data.email, "display_name": data.display_name, "workspace_id": 1}
    password = hash_password(data.password)
    with closing(connect_database(request.app.state.settings.data_dir)) as connection:
        try:
            with connection:
                connection.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                                   (user["id"], user["email"], user["display_name"], password, int(time.time())))
                connection.execute("INSERT INTO memberships VALUES (1, ?)", (user["id"],))
                return create_session(connection, user, request.app.state.settings.session_hours)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with that email already exists") from None


@router.post("/login", dependencies=[Depends(check_attempt)])
def login(data: LoginInput, request: Request) -> dict:
    with closing(connect_database(request.app.state.settings.data_dir)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM users WHERE email=?", (data.email,)).fetchone()
        valid = verify_password(data.password, row["password_hash"] if row else dummy_hash)
        if row is None or not valid:
            raise HTTPException(401, "Invalid email or password")
        member = connection.execute("SELECT 1 FROM memberships WHERE user_id=? AND workspace_id=1", (row["id"],)).fetchone()
        if not member:
            raise HTTPException(403, "Workspace access is unavailable")
        user = {"id": row["id"], "email": row["email"], "display_name": row["display_name"], "workspace_id": 1}
        with connection:
            return create_session(connection, user, request.app.state.settings.session_hours)


@router.get("/me")
def me(user: Annotated[dict, Depends(current_user)]) -> dict:
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, user: Annotated[dict, Depends(current_user)], token: Annotated[str, Depends(access_token)]):
    with closing(connect_database(request.app.state.settings.data_dir)) as connection:
        with connection:
            connection.execute("DELETE FROM sessions WHERE token_hash=? AND user_id=?", (token_hash(token), user["id"]))
