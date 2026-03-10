from sqlalchemy.orm import Session
from sqlalchemy import select

from utils import _safe_listdir, get_audio_file, get_music_info, get_video_file, get_photo_file, get_file_url
from config import MUSIC_DIRECTORY, ALLOWED_PHOTO_SUFFIX
from database_models import Music, Artist, Genre
from database import SessionLocal

from logger import get_logger
logger = get_logger(__name__)


class SyncState:
    def __init__(self):
        self.existing_genres = {}
        self.existing_artists = {}
        self.existing_music = {}
        self.actual_music_paths = set()


class DateSynchronizer:
    def __init__(self, db: Session):
        self.db = db
        self.state = SyncState()
        self.music_directory = MUSIC_DIRECTORY / "music"
        self.artists_avatars_directory = MUSIC_DIRECTORY / "artists_avatars"

    def load_existing(self):
        self.state.existing_genres = {
            genre.name: genre
            for genre in self.db.scalars(select(Genre))
        }
        self.state.existing_artists = {
            artist.name: artist
            for artist in self.db.scalars(select(Artist))
        }
        self.state.existing_music = {
            music.path: music
            for music in self.db.scalars(select(Music))
        }
        self.state.actual_music_paths = set()

    def get_artist_avatar(self, artist_name):
        artist_avatar_file = next(
            (f for f in _safe_listdir(self.artists_avatars_directory) if
             f.is_file() and f.suffix.lower() in ALLOWED_PHOTO_SUFFIX and f.name == artist_name), None
        )
        artist_avatar_url = None
        if artist_avatar_file:
            artist_avatar_url = get_file_url(artist_avatar_file)
        return artist_avatar_url

    def sync_music(self):
        for music_folder in _safe_listdir(self.music_directory):
            if not music_folder.is_dir():
                logger.warning(f"Музыка {music_folder.name} не является папкой")
                continue

            music_file = get_audio_file(music_folder)
            if not music_file:
                logger.warning(f"В папке музыки {music_folder.name} нет аудио..")
                continue

            music_path_str = str(music_folder)
            self.state.actual_music_paths.add(music_path_str)

            genre_name, artists_names, duration = get_music_info(music_folder, music_file)

            db_genre = self.sync_genres(genre_name)
            db_artists = self.sync_artists(artists_names)

            music_url = get_file_url(music_file)
            video_clip_url = get_file_url(get_video_file(music_folder))
            preview_url = get_file_url(get_photo_file(music_folder))

            if music_path_str in self.state.existing_music:
                db_music = self.state.existing_music[music_path_str]
                db_music.name = music_folder.name
                db_music.genre_id = db_genre.id
                db_music.genre = db_genre
                db_music.artists = db_artists
                db_music.duration = duration
                db_music.preview_url = preview_url
                db_music.video_clip_url = video_clip_url

                logger.info(f"Обновлена информация в БД для музыки {music_folder.name}")
            else:
                new_music = Music(
                    name=music_folder.name,
                    path=music_path_str,
                    duration=duration,
                    preview_url=preview_url,
                    video_clip_url=video_clip_url,
                    audio_url=music_url,
                    auditions=0,
                    likes=0,
                    genre_id=db_genre.id,
                )
                new_music.genre = db_genre
                new_music.artists = db_artists
                self.db.add(new_music)

                logger.info(f"В БД добавлена новая музыка - {music_folder.name}")

    def sync_genres(self, genre_name: str):
        if genre_name not in self.state.existing_genres:
            new_genre = Genre(name=genre_name)
            self.db.add(new_genre)
            self.db.flush()
            self.state.existing_genres[genre_name] = new_genre

            logger.info(f"В БД добавлен новый жанр - {genre_name}")
        return self.state.existing_genres[genre_name]

    def sync_artists(self, artists_names: list[str]):
        db_artists = []
        for artist_name in artists_names:
            if artist_name not in self.state.existing_artists:
                artist_avatar = self.get_artist_avatar(artist_name)
                new_artist = Artist(name=artist_name, avatar_url=artist_avatar)
                self.db.add(new_artist)
                self.db.flush()
                self.state.existing_artists[artist_name] = new_artist

                logger.info(f"В БД добавлен новый исполнитель - {artist_name}")
            else:
                artist = self.state.existing_artists[artist_name]
                if not artist.avatar_url:
                    artist_avatar = self.get_artist_avatar(artist_name)
                    if artist_avatar:
                        artist.avatar_url = artist_avatar
                        logger.info(f"Обновлен аватар исполнителя - {artist_name}")
            db_artists.append(self.state.existing_artists[artist_name])
        return db_artists

    def delete_unused_from_db(self):
        paths_in_db = set(self.state.existing_music.keys())
        paths_to_delete = paths_in_db - self.state.actual_music_paths

        for path in paths_to_delete:
            self.db.delete(self.state.existing_music[path])

    def sync(self):
        with self.db.begin():
            self.load_existing()
            self.sync_music()
            self.delete_unused_from_db()


# проходимся по всей музыке и записываем их данные в бд
def start_db():
    try:
        with SessionLocal() as db:
            logger.info("Начало синхронизации..")
            synchronizer = DateSynchronizer(db)
            synchronizer.sync()
            logger.info("Синхронизация данных прошла успешно!!")
    except Exception as e:
        print(f"Ошибка при наполнении БД музыкой: {e}")
