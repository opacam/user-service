import logging
from datetime import timedelta
from typing import List

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from sqlalchemy.orm import Session
from starlette import status
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
# to support Python versions lower than 3.8, we import
# `Literal` from typing_extensions instead from the builtin module
#   See also: https://docs.python.org/3/library/typing.html#typing.Literal
from typing_extensions import Literal

from app.database import SessionLocal
from app.api import crud, schemas
from app.api.config import get_api_settings
from app.api.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    verify_password,
)
from app.api.utils import check_user_id

log = logging.getLogger("api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authenticate")
api_settings = get_api_settings()

app = FastAPI(
    title="user-service",
    description=(
        "A **RESTful** API to manage user accounts which registers all user "
        "calls to the API. It also provide endpoints to generate histograms "
        "of the actions performed by all the users."
    ),
    openapi_url=api_settings.openapi_route,
    debug=api_settings.debug,
)
app.mount("/public", StaticFiles(directory="public"), name="public")

WRONG_QUERY_ARGUMENTS_MSG = (
    "The Query parameter supplied for `{query_arg}` is invalid."
)


def get_db():
    """A function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def authenticate_user(
    username: str, password: str, db: Session = Depends(get_db)
):
    """A function to check user password. If not succeed, will return False."""
    db_user = crud.get_user_by_username(db, username=username)
    if not db_user:
        return False
    if not verify_password(password, db_user.hashed_password):
        return False
    return db_user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """A function to check that the user has the proper credentials (token)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise credentials_exception
    return db_user


@app.get("/", include_in_schema=False)
async def index():
    """
    A `GET` call to the root of the server which supplies a link to the API
    documentation.
    """
    return FileResponse('public/index.html')


@app.post(
    "/authenticate",
    response_model=schemas.Token,
    tags=["Authentication"],
    summary="Grant a user access to the API.",
    description=(
            "To be able to access most of the API's functionality an user "
            "should get an access token via this post request."
    ),
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    A `POST` call to login into the server and receive a `Token` to be used for
    API's private calls.
    """
    db_user = authenticate_user(form_data.username, form_data.password, db)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # register user login
    crud.create_user_action(
        db,
        schemas.ActionCreate(**{"title": "Logged into account"}),
        db_user.id,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/users/histogram-types",
    tags=["Histogram (private)"],
    summary="Types histogram"
)
async def read_users_actions_types_histogram(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """
    A `GET` call that returns all types of registered actions, alongside the
    count for each action. The result will be a dict, where the keys are the
    action's title, and the value the number of times that the action was used.
    """

    types_of_actions = crud.get_users_types_histogram(db)

    # register actions types query
    crud.create_user_action(
        db,
        schemas.ActionCreate(**{"title": "Queried types histogram"}),
        current_user.id,
    )
    return types_of_actions


@app.get(
    "/users/histogram-period",
    tags=["Histogram (private)"],
    summary="Period histogram"
)
async def read_users_actions_periods_histogram(
    db: Session = Depends(get_db),
    period_time: Literal["hour", "day", "month"] = Query(
        "day",
        description=(
            "Period of time for the histogram. It should be one of:\n\n"
            "- `hour`\n- `day`\n- `month`\n"
        ),
    ),
    current_user: schemas.User = Depends(get_current_user),
):
    """
    A `GET` call that returns an histogram containing information about all
    different types of actions. Each registered action will have the
    following information:

    - **timestamps**: A list with the timestamps of the action
    - **size**: The total number of timestamps for the action
    - **min**: The first timestamp of the action
    - **max**: The last timestamp of the action
    """
    actions_data = crud.get_users_periods_histogram(db, period_time)

    # register last actions query
    crud.create_user_action(
        db,
        schemas.ActionCreate(
            **{"title": f"Queried period histogram ({period_time})"},
        ),
        current_user.id,
    )
    return actions_data


@app.post("/users/", response_model=schemas.User, tags=["Users"])
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """A `POST` call to add a new user."""
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="username already registered"
        )
    log.debug(f"Creating user: {user}")
    return crud.create_user(db=db, user=user)


@app.delete(
    "/users/{user_id}",
    response_model=schemas.UserRemoved,
    tags=["Users (private)"],
    description=(
            "This `delete` call, will also remove any information "
            "related with the user."
    ),
)
async def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_user),
):
    """A `DELETE` call to remove an user from database."""
    assert check_user_id(current_user.id, user_id, "profile") is True

    removed_user = crud.remove_user(db, user_id)
    log.info(f"Removed user: {removed_user}")
    return removed_user


@app.get(
    "/users/{user_id}",
    response_model=schemas.User,
    tags=["Users (private)"],
)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """A `GET` call to retrieve user information."""
    assert check_user_id(current_user.id, user_id, "profile") is True

    return crud.get_user(db, user_id=user_id)


@app.put(
    "/users/{user_id}/password",
    tags=["Users (private)"],
)
async def change_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """A `PUT` call to update user password."""
    assert check_user_id(current_user.id, user_id, "password") is True

    crud.change_user_password(db, user_id, new_password)

    # register action: changed user password
    crud.create_user_action(
        db,
        schemas.ActionCreate(**{"title": "Changed user password"}),
        user_id,
    )
    return {"details": "Successfully changed user password"}


@app.get(
    # This path could be build without enforcing the `user_id` but, imho, I
    # think it's better to enforce the user_id, since the path looks like more
    # consistent, since we are querying an user specific information, plus
    # gives us more freedom, like having a super admin account that could
    # bypass the restrictions set.
    "/users/{user_id}/actions",
    response_model=List[schemas.Action],
    tags=["Users (private)"],
)
async def read_actions(
    user_id: int,
    sort: str = Query(
        "desc",
        title="Sort results",
        description="It should be one of: `asc` or `desc`",
    ),
    limit: int = Query(
        100,
        title="Limit results",
        description=(
                "The results will be limited to the supplied number. If the "
                "supplied number is `0`, all the result will be shown."
        ),
    ),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """A `GET` call to retrieve the user actions information."""
    assert check_user_id(current_user.id, user_id, "actions") is True

    if sort not in {"asc", "desc"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                WRONG_QUERY_ARGUMENTS_MSG.format(query_arg="order_direction")
                + "It should be one of: `asc` or `desc`."
            ),
        )
    actions = crud.get_user_actions(
        db, user_id=user_id, sort=sort, limit=limit,
    )

    # register actions query
    order = {"asc": "ascending", "desc": "descending"}
    lim = f"{'unlimited' if limit == 0 else ('limited to ' + str(limit))}"
    crud.create_user_action(
        db,
        schemas.ActionCreate(
            **{"title": f"Queried actions in {order[sort]} sorting ({lim})"},
        ),
        user_id,
    )
    return actions


@app.get(
    "/users/{user_id}/last_actions",
    response_model=List[schemas.Action],
    tags=["Users (private)"],
)
async def read_last_actions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user),
):
    """A `GET` call to query latest action of each kind."""
    assert check_user_id(current_user.id, user_id, "last actions") is True

    last_actions = crud.get_latest_user_actions(
        db, user_id=user_id,
    )

    # register last actions query
    crud.create_user_action(
        db,
        schemas.ActionCreate(**{"title": f"Queried last actions"}),
        user_id,
    )
    return last_actions
