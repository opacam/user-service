from fastapi import FastAPI

app = FastAPI()


@app.get("/", tags=["Root"])
async def index():
    """A `GET` call to the root of the server which says hello."""
    return {"msg": "Welcome to user-service"}
