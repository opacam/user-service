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


def remove_user(db: Session, user_id: int) -> schemas.UserRemoved:
    """
     Given an user id, removes an user and all his information from database.
    """
    db_user = get_user(db, user_id)
    db.delete(db_user)
    db.commit()
    removed_user = schemas.UserRemoved(**{
        "username": db_user.username, "id": db_user.id,
    })
    log.info(f"Removed user: {removed_user}")
    return removed_user


def _get_user_all_actions(db: Session, user_id: int):
    """A private function that return all actions performed by an user."""
    return db.query(models.Action).filter(models.Action.owner_id == user_id)


def get_user_actions(
    db: Session, user_id: int, sort: str = "desc", limit: int = 100
) -> list:
    """
    A function that returns user actions sorted depending on the supplied kwarg
    `sort`. You also can limit the results shown via the kwarg `limit`. I you
    set `limit=0`, it will show all the results.
    """
    query = _get_user_all_actions(db, user_id)
    log.debug(f"Selected order for user actions is: {sort}")
    not_limited = limit == 0
    sort_desc = sort == "desc"
    if not_limited:
        if sort_desc:
            return query.order_by(models.Action.timestamp.desc()).all()
        return query.order_by(models.Action.timestamp.asc()).all()

    if sort_desc:
        return (
            query.order_by(models.Action.timestamp.desc()).limit(limit).all()
        )
    return query.order_by(models.Action.timestamp.asc()).limit(limit).all()


def get_latest_user_actions(db: Session, user_id: int) -> list:
    """
    A function that queries all the user actions but keeps only the latest of
    each kind.
    """
    added_actions = set()
    last_actions = []
    query = get_user_actions(db, user_id, sort="desc", limit=0)
    for row in query:
        if row.title in added_actions:
            continue
        added_actions.add(row.title)
        last_actions.append(row)
    return last_actions


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
