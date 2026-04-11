from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from datetime import datetime, timezone

from models import SuccessResponse, MusicListResponse
from database_models import User, Music, History
from utils import db_transaction, get_total_and_music_from_db
from auth import get_user
from database import get_db
from httpExceptions import music_exception

from logger import get_logger
logger = get_logger(__name__)

router = APIRouter(prefix="/history", tags=["History"])


@router.post("/set/{music_id}", response_model=SuccessResponse)
@db_transaction
def set_to_history(music_id: int, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    music = db.get(Music, music_id)
    if not music:
        logger.warning(f"Музыки с id={music_id} нет в БД..")
        raise music_exception

    history_entry = db.execute(select(History).where(History.user_id == current_user.id)).scalar_one_or_none()
    if history_entry:
        history_entry.date = datetime.now(timezone.utc)
    else:
        new_history = History(user_id=current_user.id, music_id=music_id)
        db.add(new_history)

    total = db.scalar(select(func.count()).select_from(History).where(History.user_id == current_user.id))
    if total > 100:
        last_history_music_id = (select(History.id)
                                 .where(History.user_id == current_user.id)
                                 .order_by(History.date.asc())
                                 .limit(1)
                                 .scalar_subquery()
                                 )
        db.execute(delete(History).where(History.id == last_history_music_id))

    return {"success": True}


@router.get("/all", response_model=MusicListResponse)
@db_transaction
def get_list_history(page: int = 1,
                     limit: int = 21,
                     current_user: User = Depends(get_user),
                     db: Session = Depends(get_db)):
    return get_total_and_music_from_db(History, current_user.id, page, limit, db)
