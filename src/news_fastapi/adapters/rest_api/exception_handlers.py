from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from news_fastapi.core.exceptions import AuthenticationError, AuthorizationError
from news_fastapi.utils.exceptions import NotFoundError


def handle_authorization_error(
    request: Request,  # pylint: disable=unused-argument
    err: AuthorizationError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_403_FORBIDDEN)


def handle_not_found_error(
    request: Request,  # pylint: disable=unused-argument
    err: NotFoundError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_404_NOT_FOUND)


def handle_authentication_error(
    request: Request,  # pylint: disable=unused-argument
    err: AuthenticationError,
) -> JSONResponse:
    return JSONResponse({"message": str(err)}, status_code=HTTP_401_UNAUTHORIZED)
