from pathlib import Path
from mutagen.mp3 import MP3
from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
import json
import math
import functools

from config import ALLOWED_VIDEO_SUFFIX, ALLOWED_PHOTO_SUFFIX, ALLOWED_MUSIC_SUFFIX, MUSIC_DIRECTORY
from httpExceptions import database_exception
from database_models import Music


# безопасное открытие папки
def _safe_listdir(path: Path):
    try:
        return list(path.iterdir())
    except Exception as e:
        print(f'Ошибка: файл в {path} не найден. Сообщение ошибки: {e}')
        return []


# получаем видео-файл
def get_video_file(path: Path):
    return next(
        (f for f in _safe_listdir(path) if f.is_file() and f.suffix.lower() in ALLOWED_VIDEO_SUFFIX), None
    )


# получаем фото-файл
def get_photo_file(path: Path):
    return next(
        (f for f in _safe_listdir(path) if f.is_file() and f.suffix.lower() in ALLOWED_PHOTO_SUFFIX), None
    )


# получаем аудио-файл
def get_audio_file(path: Path):
    return next(
        (f for f in _safe_listdir(path) if f.is_file() and f.suffix.lower() in ALLOWED_MUSIC_SUFFIX), None
    )


# получаем url файла
def get_file_url(path: Path):
    if not path:
        return None
    return f"static/{path.relative_to(MUSIC_DIRECTORY).as_posix()}"


# получаем путь файла
def get_file_path(url: str):
    if not url:
        return None
    relative_path = Path(url.replace("static/", "", 1))
    return MUSIC_DIRECTORY / relative_path


# получаем длительность музыки
def get_music_duration(music_file: Path) -> int:
    if not music_file.exists():
        return 0
    audio = MP3(music_file)
    return math.ceil(audio.info.length)


# получаем информацию о музыке: длительность, жанр, исполнители (здесь же создаем (если не создан) info.json)
def get_music_info(music_path: Path, music_file: Path):
    info_file = music_path / "info.json"

    genre = ''
    artists = []

    needs_write = False

    if music_file.exists():
        try:
            with open(info_file, "r", encoding="utf-8") as file:
                data = json.load(file)
                genre = data.get('genre', '')
                artists = data.get('artists', [])
        except Exception as e:
            print(f"Не удалось прочитать музыку: {music_file.name}, {e}")
            needs_write = True
    else:
        needs_write = True

    duration = get_music_duration(music_file)

    if needs_write:
        try:
            with open(info_file, "w", encoding="utf-8") as file:
                json.dump({
                    'genre': genre,
                    'artists': artists,
                    'duration': duration
                }, file, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка записи информации о музыке: {music_file.name}, {e}")

    return genre, artists, duration


# декоратор для запросов с бд
def db_transaction(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        db = next((v for v in kwargs.values() if isinstance(v, Session)), None)
        try:
            result = function(*args, **kwargs)
            if db:
                db.commit()
            return result
        except HTTPException:
            if db:
                db.rollback()
            raise
        except Exception as e:
            if db:
                db.rollback()
            print(f"Ошибка БД: ", e)
            raise database_exception

    return wrapper


# получаем offset для запроса к бд
def get_offset(page: int = 1, limit: int = 21) -> int:
    return (page - 1) * limit


# получаем total и список музыки с таблицы: для like, history
def get_total_and_music_from_db(model, user_id, page, limit, db: Session):
    skip = get_offset(page, limit)

    music = db.scalars(select(model)
                       .where(model.user_id == user_id)
                       .options(
                            joinedload(model.music).joinedload(Music.artists),
                            joinedload(model.music).joinedload(Music.genre))
                       .order_by(model.date.desc())
                       .offset(skip)
                       .limit(limit)).all()
    total = db.scalar(select(func.count(model.id)).where(model.user_id == user_id))

    return {
        "music": music,
        "total": total,
        "page": page,
        "limit": limit,
        "has_more": (skip + limit) < total,
    }
