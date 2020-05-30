from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """Description for `users` database table."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)

    actions = relationship("Action", back_populates="owner")


class Action(Base):
    """Description for `actions` database table."""
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    timestamp = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="actions")
