from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseSettings

BASEDIR = Path(Path(__file__).parent)
DB_DIRECTORY = Path(BASEDIR, "db-data")
DB_DIRECTORY.mkdir(parents=True, exist_ok=True)
SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(DB_DIRECTORY, 'users.db')}"


class APISettings(BaseSettings):
    """A class that holds the API configuration."""
    api_v1_route: str = "/api/v1"
    openapi_route: str = "/api/v1/openapi.json"

    debug: bool = True
    debug_exceptions: bool = True

    disable_superuser_dependency: bool = False
    include_admin_routes: bool = False

    class Config:
        env_prefix = ""


@lru_cache()
def get_api_settings() -> APISettings:
    """
    A function to load API's settings. This function is decorated with
    `lru_cache` which modifies the function to return the same value that was
    returned the first time, instead of computing it again, executing the code
    of the function every time.
    """
    return APISettings()
