from fastapi import FastAPI

from app.api.config import get_api_settings

api_settings = get_api_settings()

app = FastAPI(
    title="user-service",
    description="A simple user api with authentication",
    openapi_url=api_settings.openapi_route,
    debug=api_settings.debug,
)


@app.get("/", tags=["Root"])
async def index():
    """A `GET` call to the root of the server which says hello."""
    return {"msg": "Welcome to user-service"}
