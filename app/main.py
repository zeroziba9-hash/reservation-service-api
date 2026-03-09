from fastapi import FastAPI

from app.api.routes import router
from app.db.base import Base
from app.db.session import engine

app = FastAPI(title="FastAPI Service Template", version="0.1.0")
app.include_router(router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
