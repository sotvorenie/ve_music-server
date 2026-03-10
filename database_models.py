from sqlalchemy import (Column, Integer, String,
                        Table, ForeignKey, DateTime,
                        func, UniqueConstraint, Index)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

from database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    login: Mapped[str] = mapped_column(String(20))
    password: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False,
                                                 onupdate=func.now()
                                                 )

    likes: Mapped[list["Like"]] = relationship(back_populates='user', cascade='all, delete-orphan')
    history: Mapped[list["History"]] = relationship(back_populates='user', cascade='all, delete-orphan')


music_artist_association = Table(
    'music_artist_association',
    Base.metadata,
    Column('music_id', Integer, ForeignKey('musics.id', ondelete='CASCADE'), primary_key=True),
    Column('artist_id', Integer, ForeignKey('artists.id'), primary_key=True),
)


class Music(Base):
    __tablename__ = 'musics'

    __table_args__ = (
        Index("ix_music_name", "name"),
        Index("ix_music_auditions", "auditions"),
        Index("ix_music_likes", "likes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    path: Mapped[str] = mapped_column(unique=True)
    duration: Mapped[int] = mapped_column()
    audio_url: Mapped[str] = mapped_column()
    auditions: Mapped[int] = mapped_column(default=0, server_default='0', nullable=False)
    likes: Mapped[int] = mapped_column(default=0, server_default='0', nullable=False)
    preview_url: Mapped[str] = mapped_column()
    video_clip_url: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                 server_default=func.now(),
                                                 nullable=False,
                                                 onupdate=func.now()
                                                 )

    genre_id: Mapped[int | None] = mapped_column(ForeignKey('genres.id', ondelete='RESTRICT'),
                                                 index=True,
                                                 nullable=True)

    genre: Mapped["Genre"] = relationship(back_populates='music')
    artists: Mapped[list["Artist"]] = relationship(secondary=music_artist_association, back_populates='music')


class Genre(Base):
    __tablename__ = 'genres'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    music: Mapped[list["Music"]] = relationship(back_populates='genre')


class Artist(Base):
    __tablename__ = 'artists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    music: Mapped[list["Music"]] = relationship(secondary=music_artist_association, back_populates='artists')


class Like(Base):
    __tablename__ = 'likes'

    __table_args__ = (UniqueConstraint('user_id', 'music_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    music_id: Mapped[int] = mapped_column(ForeignKey('musics.id', ondelete='CASCADE'), index=True)

    user: Mapped["User"] = relationship(back_populates='likes')
    music: Mapped["Music"] = relationship()


class History(Base):
    __tablename__ = 'histories'

    __table_args__ = (UniqueConstraint('user_id', 'music_id'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    music_id: Mapped[int] = mapped_column(ForeignKey('musics.id', ondelete='CASCADE'), index=True)

    user: Mapped["User"] = relationship(back_populates='history')
    music: Mapped["Music"] = relationship()
