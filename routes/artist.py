from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select

from models import MusicListResponse, ArtistsListResponse
from database_models import Artist, Music
from database import get_db
from utils import get_offset, db_transaction
from httpExceptions import artist_exception

from logger import get_logger
logger = get_logger(__name__)


router = APIRouter(prefix="/artist", tags=["Artist"])


@router.get("/all", response_model=ArtistsListResponse)
@db_transaction
def get_all_artists(page: int = 1, limit: int = 21, db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    artists = (db.scalars(
        select(Artist)
        .order_by(Artist.name.asc())
        .offset(skip)
        .limit(limit))
               .all())

    total = db.scalar(select(func.count()).select_from(Artist))

    return {
        "artists": artists,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }


@router.get("/search", response_model=ArtistsListResponse)
@db_transaction
def get_artists_by_name(name: str, page: int = 1, limit: int = 21, db: Session = Depends(get_db)):
    skip = get_offset(page, limit)

    query = select(Artist)

    if name:
        query = query.where(Artist.name.ilike(f"%{name}%"))

    artists = db.scalars(query
                         .order_by(Artist.name.asc())
                         .offset(skip)
                         .limit(limit)
                         ).all()

    query_total = select(func.count()).select_from(Artist)
    if name:
        query_total = query_total.where(Artist.name.ilike(f"%{name}%"))
    total = db.scalar(query_total)

    return {
        "artists": artists,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }
