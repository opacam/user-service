import logging

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.api import crud, schemas
from app.api.config import get_api_settings

log = logging.getLogger("api")
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


@app.get("/", tags=["Root"])
async def index():
    """A `GET` call to the root of the server which says hello."""
    return {"msg": "Welcome to user-service"}


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


@app.get("/users/{user_id}", response_model=schemas.User, tags=["Users"])
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """A `GET` call to retrieve user information."""
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
