"""Pydantic schemas for request/response bodies."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    image_path: str | None
    likes_count: int
    created_at: datetime
    author: UserOut


class LikeOut(BaseModel):
    id: int
    likes_count: int
