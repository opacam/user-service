from datetime import datetime
from typing import Union

from fastapi import HTTPException
from starlette import status

UNAUTHORIZED_USER_QUERY_MSG = (
    "You are not allowed to view/modify the {section} "
    "of another user, please, use your own id: `{user_id}`."
)


def get_timestamp() -> str:
    """Get current datetime in string format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_user_id(
        current_user_id: int,
        target_user_id: int,
        affected_section: str = "profile",
) -> Union[bool, HTTPException]:
    """
    A function that raises `fastapi.HTTPException` if user ids aren't equal.
    """
    if current_user_id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                UNAUTHORIZED_USER_QUERY_MSG.format(
                    section=affected_section, user_id=current_user_id,
                ),
            ),
        )
    return True
