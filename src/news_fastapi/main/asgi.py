from contextlib import asynccontextmanager

from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import RequestResponseEndpoint
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from tortoise import Tortoise

from news_fastapi.adapters.auth.http_request import RequestHolder
from news_fastapi.adapters.events.server import DomainEventServer
from news_fastapi.adapters.rest_api.authors import router as authors_router
from news_fastapi.adapters.rest_api.drafts import router as drafts_router
from news_fastapi.adapters.rest_api.news import router as news_router
from news_fastapi.core.exceptions import AuthenticationError, AuthorizationError
from news_fastapi.main.container import DIContainer
from news_fastapi.utils.exceptions import NotFoundError

di_container = DIContainer()
di_container.config.from_dict(
    {
        "db": {
            "url": "sqlite:////tmp/news_fastapi.sqlite3",
        }
    }
)


@asynccontextmanager
@inject
async def lifespan(
    app: FastAPI,  # pylint: disable=redefined-outer-name,unused-argument
    domain_event_server: DomainEventServer = Provide["domain_event_server"],
    tortoise_config: dict = Provide["tortoise_config"],
):
    await Tortoise.init(config=tortoise_config)
    domain_event_server.start()
    yield
    await domain_event_server.stop()
    await Tortoise.close_connections()


app = FastAPI(
    debug=True,
    title="News",
    lifespan=lifespan,
)
app.include_router(authors_router, prefix="/authors")
app.include_router(drafts_router, prefix="/drafts")
app.include_router(news_router, prefix="/news")


@app.exception_handler(AuthorizationError)
def handle_authorization_error(
    request: Request,  # pylint: disable=unused-argument
    err: AuthorizationError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_403_FORBIDDEN)


@app.exception_handler(NotFoundError)
def handle_not_found_error(
    request: Request,  # pylint: disable=unused-argument
    err: NotFoundError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_404_NOT_FOUND)


@app.exception_handler(AuthenticationError)
def handle_authentication_error(
    request: Request,  # pylint: disable=unused-argument
    err: AuthenticationError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_401_UNAUTHORIZED)


@app.middleware("http")
@inject
async def request_holder_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
    request_holder: RequestHolder = Provide["request_holder"],
) -> Response:
    request_holder.set(request)
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


di_container.wire()
