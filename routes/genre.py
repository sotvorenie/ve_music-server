from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select

from models import GenresListResponse, MusicListResponse
from database_models import Music, Genre
from database import get_db
from utils import get_offset, db_transaction

from logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/genre", tags=["Genre"])


@router.get("/all", response_model=GenresListResponse)
@db_transaction
def get_all_genres(db: Session = Depends(get_db)):
    genres = db.query(Genre).all()

    return {
        "genres": genres
    }


@router.get("/{genre_id}", response_model=MusicListResponse)
@db_transaction
def get_genres_music(genre_id: int, page: int = 1, limit: int = 21, db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    music = db.execute(select(Music)
                       .where(Music.genre_id == genre_id)
                       .order_by(Music.name.asc())
                       .offset(skip)
                       .limit(limit)
                       ).all()

    total = db.scalar(select(func.count()).select_from(Music).where(Music.genre_id == genre_id))

    return {
        "music": music,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


@router.get("/search_music", response_model=GenresListResponse)
@db_transaction
def get_music_in_genre_by_name(name: str,
                               genre_id: int,
                               page: int = 1,
                               limit: int = 21,
                               db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    query = select(Music).where(Music.genre_id == genre_id)

    if name:
        query = query.where(Music.name.ilike(f"%{name}%"))

    music = db.scalars(query
                       .options(selectinload(Music.artists))
                       .order_by(Music.name.asc())
                       .offset(skip)
                       .limit(limit)
                       ).all()

    total_query = select(func.count()).select_from(Music).where(Music.genre_id == genre_id)
    if name:
        total_query = total_query.where(Music.name.ilike(f"%{name}%"))

    total = db.scalar(total_query)

    return {
        "music": music,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }
