from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models import SuccessResponse
from database_models import User
from utils import db_transaction
from database import get_db
from httpExceptions import user_exception, empty_user_name_exception

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
