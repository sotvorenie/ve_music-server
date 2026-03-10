from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select, update
from pathlib import Path

from models import MusicListResponse, MusicResponse
from database_models import Music
from database import get_db
from utils import get_offset, get_audio_file, db_transaction
from httpExceptions import music_exception

from logger import get_logger
logger = get_logger(__name__)

router = APIRouter(prefix="/music", tags=["Music"])


@router.get("/all", response_model=MusicListResponse)
@db_transaction
def get_all_music(page: int = 1, limit: int = 21, db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    music = db.scalars(select(Music)
                       .options(selectinload(Music.artists))
                       .order_by(Music.name.asc())
                       .offset(skip)
                       .limit(limit)
                       ).all()

    total = db.execute(select(func.count()).select_from(Music)).scalar_one()

    return {
        "music": music,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


@router.get("/{music_id}", response_model=MusicResponse)
@db_transaction
def get_music(music_id: int, db: Session = Depends(get_db)):
    music = db.execute(select(Music)
                       .where(Music.id == music_id)
                       .options(selectinload(Music.artists))
                       ).scalar_one_or_none()

    if not music or not music.audio_url:
        logger.warning(f"В БД нет музыки/информации_о_пути_музыки с id={music_id}")
        raise music_exception

    full_music_path = Path(music.path)

    if not full_music_path.exists() or not full_music_path.is_dir():
        logger.warning(f"Путь к папке музыки {music.name} недействителен..")
        raise music_exception

    music_file = get_audio_file(full_music_path)

    if not music_file:
        logger.warning(f"У музыки {music.name} нет аудио-файла..")
        raise music_exception

    db.execute(update(Music).where(Music.id == music_id).values(auditions=Music.auditions + 1))

    return music


@router.get("/search", response_model=MusicListResponse)
@db_transaction
def get_music_by_name(name: str, page: int = 1, limit: int = 21, db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    query = select(Music)

    if name:
        query = query.where(Music.name.like(f"%{name}%"))

    music = db.scalars(query
                       .options(selectinload(Music.artists))
                       .order_by(Music.name.asc())
                       .offset(skip)
                       .limit(limit)
                       ).all()

    total_query = select(func.count()).select_from(Music)
    if name:
        total_query = total_query.where(Music.name.like(f"%{name}%"))

    total = db.scalar(total_query)

    return {
        "music": music,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }
