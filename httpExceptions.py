from fastapi import HTTPException


jwt_exception = HTTPException(
        status_code=401,
        detail="Не удалось валидировать токен",
        headers={"WWW-Authenticate": "Bearer"},
)

registration_exception = HTTPException(
    status_code=400,
    detail="Пользователь с таким именем уже существует",
)

auth_exception = HTTPException(
    status_code=401,
    detail="Неверный логин или пароль"
)


artist_exception = HTTPException(
    status_code=404,
    detail="Исполнитель не найден..",
)


music_exception = HTTPException(
    status_code=404,
    detail="Музыка не найдена..",
)


database_exception = HTTPException(
    status_code=500,
    detail=f"Ошибка БД",
)


user_exception = HTTPException(
    status_code=404,
    detail=f"Пользователь не найден",
)


empty_user_name_exception = HTTPException(
    status_code=400,
    detail="Неверное имя пользователя",
)
