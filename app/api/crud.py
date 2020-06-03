import logging
from datetime import datetime, timedelta
from typing import Literal

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


def change_user_password(db: Session, user_id: int, new_password):
    """Change user password."""
    db_user = get_user(db, user_id)
    db_user.hashed_password = security.get_password_hash(new_password)
    db.commit()
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


def get_all_actions(db: Session, skip: int = 0):
    """A function that return all actions from all users."""
    return db.query(models.Action).offset(skip).all()


def get_all_actions_in_a_period(
        db: Session, period_time: Literal["hour", "day", "month"] = "day",
) -> list:
    """Return all actions in a period of time since the current datetime."""
    current_time = datetime.utcnow()
    if period_time == "hour":
        time_ago = current_time - timedelta(hours=1)
    elif period_time == "day":
        time_ago = current_time - timedelta(days=1)
    else:
        time_ago = current_time - timedelta(days=31)

    query = db.query(models.Action).filter(
        models.Action.timestamp > time_ago
    )

    return query.all()


def get_users_periods_histogram(
        db: Session, period_time: Literal["hour", "day", "month", ""] = "",
) -> dict:
    """
    Return all types of registered actions with the datetime for each
    registered action. The result will be in a dict format, where the keys are
    the actions and the values are lists containing datetime objects.
    """
    if period_time == "":
        all_actions = get_all_actions(db)
    else:
        all_actions = get_all_actions_in_a_period(
            db, period_time=period_time,
        )
    histogram = {}
    for row in all_actions:
        title = row.title
        dt = row.timestamp
        if row.title in histogram:
            histogram[title]["timestamps"].append(dt)
            histogram[title]["size"] += 1
            continue
        histogram[title] = {
            "timestamps": [dt],
            "size": 1,
        }

    # now set the min and max values, which will be
    # the first and the last item of the timestamps list since the timestamps
    # are registered in a linear sequence of time, so no need to check the
    # values.
    for key, data in histogram.items():
        histogram[key]["min"] = data["timestamps"][0]
        histogram[key]["max"] = data["timestamps"][-1]
    return histogram


def get_users_types_histogram(db: Session) -> dict:
    """
    Return all types of registered actions as well as the number of times that
    the action was used in a dict format.
    """
    actions_data = get_users_periods_histogram(db, period_time="")
    counted_actions = {}
    for k, v in actions_data.items():
        counted_actions[k] = v["size"]
    return counted_actions


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
