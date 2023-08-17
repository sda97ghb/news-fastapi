from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from news_fastapi.application.exceptions import AuthenticationError, AuthorizationError
from news_fastapi.rest_api.authors.endpoints import router as authors_router
from news_fastapi.rest_api.drafts.endpoints import router as drafts_router
from news_fastapi.rest_api.news.endpoints import router as news_router
from news_fastapi.utils.exceptions import NotFoundError

app = FastAPI(
    debug=True,
    title="News",
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
