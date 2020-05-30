import logging
from sqlalchemy.orm import Session

from app.api import models, schemas, utils, security

log = logging.getLogger("api")


def get_user(db: Session, user_id: int):
    """Given an user id, returns the user information from database."""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """Given an username, returns the user information from database."""
    return (
        db.query(models.User).filter(models.User.username == username).first()
    )


def create_user(db: Session, user: schemas.UserCreate):
    """A convenient function to create a new user."""
    # generate a random salt to be used for hashing user's password
    hash_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username, hashed_password=hash_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    log.info(f"Registered new user: {user}")

    # be sure to register the account creation date
    create_user_action(
        db, schemas.ActionCreate(**{"title": "Account created"}), db_user.id
    )
    return db_user


def create_user_action(
    db: Session, action: schemas.ActionCreate, user_id: int
):
    """Register into database an user action."""
    timestamp = utils.get_timestamp()
    db_action = models.Action(
        **action.dict(), owner_id=user_id, timestamp=timestamp
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return db_action
