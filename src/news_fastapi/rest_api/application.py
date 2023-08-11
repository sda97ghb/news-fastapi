from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from news_fastapi.core.exceptions import AuthorizationError, NotFoundError
from news_fastapi.rest_api.authors.endpoints import router as authors_router
from news_fastapi.rest_api.drafts.endpoints import router as drafts_router
from news_fastapi.rest_api.news.endpoints import router as news_router

app = FastAPI(
    debug=True,
    title="News",
)
app.include_router(authors_router, prefix="/authors")
app.include_router(drafts_router, prefix="/drafts")
app.include_router(news_router, prefix="/news")


@app.exception_handler(AuthorizationError)
def handle_authorization_error(
    request: Request, err: AuthorizationError
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_403_FORBIDDEN)


@app.exception_handler(NotFoundError)
def handle_not_found_error(request: Request, err: NotFoundError) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_404_NOT_FOUND)
