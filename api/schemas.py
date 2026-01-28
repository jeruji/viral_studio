from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "user"


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    status: str
    params_json: str | None
    inputs_json: str | None
    log_path: str | None
    report_path: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
