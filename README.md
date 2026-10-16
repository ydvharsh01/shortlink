# ShortLink - URL Shortener API

A small REST API that turns a long URL into a short 6-character code. Opening the short
link redirects to the original URL and counts the click. Built with **FastAPI** and
**SQLAlchemy**, tested with **pytest**, and packaged with **Docker**.

I built it to learn how a URL shortener works end to end: unique code generation,
HTTP redirects, input validation, and updating a counter safely.

## Features

- `POST /shorten` - create a short code for a valid `http`/`https` URL
- `GET /{code}` - redirect (HTTP 307) to the original URL and count the click
- `GET /stats/{code}` - see the original URL and the number of clicks
- Random 6-character codes from 62 characters (a-z, A-Z, 0-9), about 56 billion combinations
- Collision handling: a new code is generated if one already exists (plus a unique constraint in the database)
- URL validation with Pydantic (invalid URLs return `422`)
- Atomic click counter done inside the database (`clicks = clicks + 1`)
- Interactive API docs at `/docs`
- pytest test suite and Dockerfile

## Tech stack

Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2 (SQLite by default, any SQLAlchemy database via `DATABASE_URL`), Pydantic v2, pytest, Docker.

## Project structure

```
shortlink/
  app/
    main.py       endpoints, code generation, redirect logic
    models.py     Link table
    database.py   engine, session, get_db dependency
  tests/
    test_shortlink.py
  Dockerfile
  requirements.txt
```

## Run locally

```bash
git clone https://github.com/ydvharsh01/shortlink.git
cd shortlink
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API in the browser.

## Run with Docker

```bash
docker build -t shortlink .
docker run -p 8000:8000 shortlink
```

## Run the tests

```bash
pytest -q
```

## Usage example

```bash
curl -X POST localhost:8000/shorten -H "Content-Type: application/json" \
  -d '{"url":"https://github.com/ydvharsh01"}'
# {"code":"aB3xZ9","original_url":"https://github.com/ydvharsh01","clicks":0}

# open http://localhost:8000/aB3xZ9 in a browser (redirects to the original URL)

curl localhost:8000/stats/aB3xZ9
# {"code":"aB3xZ9","original_url":"https://github.com/ydvharsh01","clicks":1}
```

## API endpoints

| Method | Path | Description | Responses |
|---|---|---|---|
| POST | `/shorten` | Body `{"url": "https://..."}` returns code, URL, clicks | 201, 422 invalid URL |
| GET | `/{code}` | Redirects to the original URL and increments clicks | 307, 404 unknown code |
| GET | `/stats/{code}` | Returns code, original URL and click count | 200, 404 |

## Design decisions

- **Random codes with `secrets`** instead of sequential IDs, so codes cannot be guessed
  one after another. Trade-off: a collision check is needed (done in code and enforced by a unique index).
- **307 instead of 301 redirect.** A 301 is cached by browsers, so later clicks would never
  reach the server and could not be counted.
- **Atomic counter.** `UPDATE links SET clicks = clicks + 1` runs inside the database, so two
  simultaneous clicks are both counted (no read-modify-write race in Python).
- The `/stats/{code}` route is defined before `/{code}` so it is not mistaken for a short code.

## Known limitations / next steps

- No rate limiting or malicious-URL checks
- Custom aliases and link expiry (`expires_at`, return 410 Gone)
- Redis cache for hot links and batched click updates for high traffic
- Alembic migrations and GitHub Actions CI

## Author

Harsh Yadav - [GitHub](https://github.com/ydvharsh01) | [LinkedIn](https://www.linkedin.com/in/harsh-yadav-013359367)
