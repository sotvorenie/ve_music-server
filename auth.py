from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from database_models import User
from httpExceptions import jwt_exception, database_exception
from env import SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth")


# создаем jwt-токен
def create_jwt_token(user_id):
    access_token_expires = timedelta(minutes=60 * 24 * 7)
    to_encode = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + access_token_expires}
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm='HS256')

    return {"access_token": encode_jwt, "token_type": "bearer"}


# получаем пользователя по jwt-токену
def get_user(token: str = Depends(oauth2_scheme)):
    get_user_by_token(token)


# получаем пользователя по токену
def get_user_by_token(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise jwt_exception
    except JWTError:
        raise jwt_exception

    try:
        user = db.query(User).filter_by(id=int(user_id)).first()
        if user is None:
            raise jwt_exception
        return user
    except Exception as e:
        print(f"Ошибка БД: ", e)
        raise database_exception
