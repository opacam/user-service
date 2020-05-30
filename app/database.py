from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.config import SQLALCHEMY_DATABASE_URI
from app.api.models import Base


# Create our sqlite3 database
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    # By default SQLite will only allow one thread to communicate with it,
    # assuming that each thread would handle an independent request. But in
    # FastAPI, using normal functions (def) more than one thread could
    # interact with the database for the same request, so we need to make
    # SQLite know that it should allow that.
    connect_args={"check_same_thread": False}
)
# Create a database session for our engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Create all tables stored in `app.pi.models` metadata
Base.metadata.create_all(bind=engine)
