from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session
import shutil
import time
from pathlib import Path
import os

from models import SuccessResponse, AvatarResponse
from database_models import User
from utils import db_transaction, get_file_url, get_file_path
from database import get_db
from httpExceptions import user_exception, empty_user_name_exception
from config import AVATARS_DIRECTORY
from auth import get_user

from logger import get_logger
logger = get_logger(__name__)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/redact_name", response_model=SuccessResponse)
@db_transaction
def redact_user_name(name: str, db: Session = Depends(get_db)):
    if not name:
        raise empty_user_name_exception

    user_db = db.query(User).filter_by(name=name).first()

    if not user_db:
        raise user_exception

    user_db.name = name


@router.post("/redact_avatar", response_model=AvatarResponse)
@db_transaction
def redact_user_avatar(file: UploadFile, current_user: User = Depends(get_user), db: Session = Depends(get_db)):
    suffix = Path(file.filename).suffix.lower()
    file_name = f"{current_user.login}_{int(time.time())}{suffix}"
    file_path = AVATARS_DIRECTORY / file_name

    try:
        with file_path.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    finally:
        file.file.close()

    if current_user.avatar_url:
        old_avatar_file = get_file_path(current_user.avatar_url)

        if old_avatar_file and old_avatar_file.exists():
            try:
                os.remove(old_avatar_file)
            except Exception as e:
                logger.error(f"Ошибка удаления файла {old_avatar_file}: {e}")

    new_avatar_url = get_file_url(file_path)
    current_user.avatar_url = new_avatar_url

    return {
        "new_avatar_url": new_avatar_url
    }
