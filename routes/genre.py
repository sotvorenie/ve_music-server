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
