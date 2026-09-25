# Mini Social Media Feed

FastAPI + SQLAlchemy ORM backend, running against a local PostgreSQL database.
Users register, create posts (with an optional image upload), browse the feed,
filter posts by user, and like posts.

## 1. Create the local PostgreSQL database

```bash
createdb mini_social_feed
createuser -s postgres
```

## 2. Set the DATABASE_URL environment variable

The app reads its connection string entirely from this variable — no
credentials are hard-coded anywhere.

```bash
cp .env.example .env
# edit .env with your local Postgres user/password, then:
export $(cat .env | xargs)
```

Or just export it directly:

```bash
export DATABASE_URL="postgresql+psycopg2://postgres:password@localhost:5432/mini_social_feed"
```

## 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Run the app

```bash
uvicorn app.main:app --reload
```

Tables are created automatically on startup (`Base.metadata.create_all`).
Interactive API docs: http://localhost:8000/docs

## Endpoints

| Method | Path                       | Description                         |
|--------|----------------------------|--------------------------------------|
| POST   | `/users/`                  | Register a user (JSON body)         |
| POST   | `/posts/`                  | Create a post (multipart form)      |
| GET    | `/posts/`                  | List all posts                      |
| GET    | `/users/{username}/posts`  | List all posts by a user            |
| POST   | `/posts/{post_id}/like`    | Like a post (increments counter)    |

## Example requests

```bash
# Register a user
curl -X POST http://localhost:8000/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "amaka", "email": "amaka@example.com"}'

# Create a post with an image
curl -X POST http://localhost:8000/posts/ \
  -F "username=amaka" \
  -F "title=Hello world" \
  -F "content=My first post!" \
  -F "image=@/path/to/photo.jpg"

# Create a post without an image
curl -X POST http://localhost:8000/posts/ \
  -F "username=amaka" \
  -F "title=Text only" \
  -F "content=No image on this one"

# List the feed
curl http://localhost:8000/posts/

# List one user's posts
curl http://localhost:8000/users/amaka/posts

# Like a post
curl -X POST http://localhost:8000/posts/1/like
```

## Notes / design decisions

- **Data model**: `User` (id, username, email, created_at) and `Post`
  (id, title, content, image_path, likes_count, created_at, author_id FK).
  Likes are a simple counter on `Post` rather than a separate `Like` table,
  since the spec has no auth on the like endpoint to identify *who* liked —
  add a `Like(user_id, post_id)` join table later if you need "did I already
  like this" checks or a list of likers.
- **Images** are saved to `app/static/uploads/` under a randomly generated
  filename (to avoid collisions/overwrites) and served back at
  `/static/uploads/<file>`. For production, swap this for S3 or similar
  object storage.
- **Uniqueness**: usernames and emails are unique; registering a duplicate
  returns `400`.
