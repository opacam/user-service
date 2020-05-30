import logging
from datetime import timedelta

import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import PyJWTError
from sqlalchemy.orm import Session
from starlette import status

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

log = logging.getLogger("api")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authenticate")
api_settings = get_api_settings()

app = FastAPI(
    title="user-service",
    description="A simple user api with authentication",
    openapi_url=api_settings.openapi_route,
    debug=api_settings.debug,
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


@app.get("/", tags=["Root"])
async def index():
    """A `GET` call to the root of the server which says hello."""
    return {"msg": "Welcome to user-service"}


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
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "You are not allowed to view the profile of another user, "
                f"please, use your own id: `{current_user.id}`."
            ),
        )
    return crud.get_user(db, user_id=user_id)
