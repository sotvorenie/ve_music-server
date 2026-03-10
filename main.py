from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from cache import start_db
from database import Base, engine, SessionLocal, get_db
from database_models import Music
from routes import artist, auth, genre, history, like, music, user
from utils import db_transaction
from logger import setup_logger, get_logger


setup_logger()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Запуск сервера..")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        start_db()
    finally:
        db.close()

    yield
    logger.info("Сервер останавливается..")


app = FastAPI(lifespan=lifespan)

app.include_router(artist.router)
app.include_router(auth.router)
app.include_router(genre.router)
app.include_router(history.router)
app.include_router(like.router)
app.include_router(music.router)
app.include_router(user.router)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_methods=['GET', 'POST'],
    allow_headers=['*'],
)


@app.get('/test')
@db_transaction
def test(db: Session = Depends(get_db)):
    music_count = db.execute(select(func.count()).select_from(Music)).scalar_one()

    return {
        "message": "Сервер жив!! (пока что.. :) )",
        "music": music_count
    }
