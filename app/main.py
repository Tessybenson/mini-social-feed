"""
Mini Social Media Feed — FastAPI + SQLAlchemy ORM + local PostgreSQL.

Endpoints:
    POST /users/                   Register a user
    POST /posts/                   Create a post (multipart form, optional image)
    GET  /posts/                   List all posts
    GET  /users/{username}/posts   List all posts by a user
    POST /posts/{post_id}/like     Like a post
"""

import os
import uuid
from typing import cast
from dotenv import load_dotenv
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import Base, engine, get_db

# Create tables on startup (fine for a small app; use Alembic migrations for anything bigger)
Base.metadata.create_all(bind=engine)

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

app = FastAPI(title="Mini Social Media Feed")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@app.post("/users/", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(username=user_in.username, email=user_in.email)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already taken")
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------

@app.post("/posts/", response_model=schemas.PostOut, status_code=status.HTTP_201_CREATED)
def create_post(
    username: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    author = db.query(models.User).filter(models.User.username == username).first()
    if author is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")

    image_path = None
    if image is not None and image.filename:
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported image type")
        extension = Path(image.filename).suffix
        stored_name = f"{uuid.uuid4().hex}{extension}"
        destination = UPLOAD_DIR / stored_name
        with destination.open("wb") as f:
            f.write(image.file.read())
        image_path = f"/static/uploads/{stored_name}"

    post = models.Post(
        title=title,
        content=content,
        image_path=image_path,
        author_id=author.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@app.get("/posts/", response_model=list[schemas.PostOut])
def list_posts(db: Session = Depends(get_db)):
    return db.query(models.Post).order_by(models.Post.created_at.desc()).all()


@app.get("/users/{username}/posts", response_model=list[schemas.PostOut])
def list_posts_by_user(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail=f"User '{username}' not found")
    return (
        db.query(models.Post)
        .filter(models.Post.author_id == user.id)
        .order_by(models.Post.created_at.desc())
        .all()
    )


@app.post("/posts/{post_id}/like", response_model=schemas.LikeOut)
def like_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    setattr(post, "likes_count", post.likes_count + 1)
    db.commit()
    db.refresh(post)
    return schemas.LikeOut(
        id=cast(int, post.id),
        likes_count=cast(int, post.likes_count),
    )
