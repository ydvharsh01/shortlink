import secrets
import string

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, HttpUrl
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Link

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShortLink")

ALPHABET = string.ascii_letters + string.digits  # 62 characters
CODE_LENGTH = 6  # 62^6 = ~56 billion combinations


class ShortenRequest(BaseModel):
    url: HttpUrl


class LinkOut(BaseModel):
    code: str
    original_url: str
    clicks: int
    model_config = ConfigDict(from_attributes=True)


def generate_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))


@app.post("/shorten", response_model=LinkOut, status_code=201)
def shorten(data: ShortenRequest, db: Session = Depends(get_db)):
    for _ in range(5):  # collision ho to naya code try karo
        code = generate_code()
        if db.scalar(select(Link).where(Link.code == code)) is None:
            link = Link(code=code, original_url=str(data.url))
            db.add(link)
            db.commit()
            db.refresh(link)
            return link
    raise HTTPException(500, "Could not generate a unique code, try again")


@app.get("/stats/{code}", response_model=LinkOut)
def stats(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(404, "Short link not found")
    return link


@app.get("/{code}")
def redirect(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if link is None:
        raise HTTPException(404, "Short link not found")
    # atomic increment: do requests ek saath aaye to bhi count sahi rahe
    db.execute(update(Link).where(Link.id == link.id).values(clicks=Link.clicks + 1))
    db.commit()
    return RedirectResponse(link.original_url, status_code=307)
