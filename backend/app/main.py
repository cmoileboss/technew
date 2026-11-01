from contextlib import asynccontextmanager
from hmac import digest

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import db
from .exceptions import DomainError
from .routers import articles, feeds

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TechNews RSS", lifespan=lifespan)
app.include_router(feeds.router)
app.include_router(articles.router)

@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
