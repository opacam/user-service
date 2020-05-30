from typing import List

from pydantic import BaseModel, Field


class ActionBase(BaseModel):
    """A base class for an action."""
    title: str = Field(
        None,
        title="The title of the action",
        description=(
            "The title of the action should describe the action made by the "
            "user, eg: `Account created`, `Login`, `Logout`..."
        ),
    )


class ActionCreate(ActionBase):
    """A class to be used when we need to create an Action."""
    pass


class Action(ActionBase):
    """A class defining an Action."""
    id: int = Field(
        None,
        title="`id` of the action.",
        description=(
            "This field will be automatically set when creating a new action."
        ),
        gt=0,
    )
    owner_id: int = Field(
        None,
        title="id of the user who performed the action.",
        description=(
            "This field will be automatically set when creating a new action."
        ),
        gt=0,
    )
    timestamp: str = Field(
        None,
        title="The datetime when the action was performed.",
    )

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    """A base class for an User."""
    username: str = Field(
        None,
        title="The username of the user.",
        description=(
            "This should be unique in our database."
        ),
    )


class UserCreate(UserBase):
    """A class to be used when we need to create an User."""
    password: str = Field(
        None,
        title="The password of the user.",
        description=(
            "The password supplied will be stored encrypted in our database."
        ),
    )


class User(UserBase):
    """A class which defines an User."""
    id: int = Field(
        None,
        title="`id` of the user.",
        description=(
            "This field will be automatically set when creating a new user."
        ),
        gt=0,
    )
    is_active: bool = Field(
        False,
        title="Is used logged in?.",
        description=(
            "This field will be automatically set when the user authenticates."
        ),
    )
    actions: List[Action] = []

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "username": "johndoe",
                "id": 1,
                "is_active": True,
                "actions": [
                    {
                      "title": "Account created",
                      "id": 1,
                      "owner_id": 1,
                      "timestamp": "2020-05-30 10:19:19"
                    }
                ]
            }
        }


class Token(BaseModel):
    """A class which describes a Token."""
    access_token: str
    token_type: str
