from typing import Any

from fastapi import FastAPI
from fastapi.applications import Lifespan
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from news_fastapi.adapters.rest_api.authors import router as authors_router
from news_fastapi.adapters.rest_api.drafts import router as drafts_router
from news_fastapi.adapters.rest_api.exception_handlers import (
    handle_authentication_error,
    handle_authorization_error,
    handle_not_found_error,
)
from news_fastapi.adapters.rest_api.middleware import request_holder_middleware
from news_fastapi.adapters.rest_api.news import router as news_router
from news_fastapi.core.exceptions import AuthenticationError, AuthorizationError
from news_fastapi.utils.exceptions import NotFoundError


def create_asgi_app(config: Any, lifespan: Lifespan[FastAPI]) -> FastAPI:
    app = FastAPI(
        debug=config["debug"],
        title="News",
        lifespan=lifespan,
    )

    app.include_router(authors_router, prefix="/authors")
    app.include_router(drafts_router, prefix="/drafts")
    app.include_router(news_router, prefix="/news")

    app.add_exception_handler(AuthorizationError, handle_authorization_error)
    app.add_exception_handler(NotFoundError, handle_not_found_error)
    app.add_exception_handler(AuthenticationError, handle_authentication_error)

    app.add_middleware(BaseHTTPMiddleware, dispatch=request_holder_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["cors"]["allow_origins"],
        allow_credentials=config["cors"]["allow_credentials"],
        allow_methods=config["cors"]["allow_methods"],
        allow_headers=config["cors"]["allow_headers"],
    )

    return app
