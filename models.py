from pydantic import BaseModel
from typing import Optional, List


class ORMModel(BaseModel):
    class Config:
        from_attributes = True


class BasePagination(BaseModel):
    total: int
    page: int
    limit: int
    has_more: bool


class GenreResponse(ORMModel):
    id: int
    name: str


class GenresListResponse(BaseModel):
    genres: List[GenreResponse]


class ArtistResponse(ORMModel):
    id: int
    name: str
    avatar_url: Optional[str] = None


class ArtistsListResponse(BasePagination):
    artists: list[ArtistResponse]


class MusicResponse(ORMModel):
    id: int
    name: str
    duration: int
    audio_url: str
    auditions: int
    likes: int
    preview_url: str
    video_clip_url: Optional[str] = None
    genre_id: int

    genre: GenreResponse
    artists: list[ArtistResponse]


class MusicForListResponse(ORMModel):
    id: int
    name: str
    duration: int
    preview_url: Optional[str] = None

    genre: GenreResponse
    artists: list[ArtistResponse]


class MusicListResponse(BasePagination):
    music: list[MusicForListResponse]


class SearchResponse(BasePagination):
    artists: list[ArtistResponse]
    music: list[MusicForListResponse]


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(ORMModel):
    id: int
    name: str
    avatar_url: Optional[str] = None


class MeResponse(ORMModel):
    user: UserResponse
    token: str


class UserRegister(BaseModel):
    login: str
    password: str
    name: str


class UserLogin(BaseModel):
    login: str
    password: str


class SuccessResponse(ORMModel):
    success: bool


class LikeResponse(ORMModel):
    is_liked: bool


class AvatarResponse(ORMModel):
    new_avatar_url: str
