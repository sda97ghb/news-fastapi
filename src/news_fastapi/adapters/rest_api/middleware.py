from dependency_injector.wiring import Provide, inject
from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

from news_fastapi.adapters.auth.http_request import RequestHolder


@inject
async def request_holder_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
    request_holder: RequestHolder = Provide["request_holder"],
) -> Response:
    request_holder.set(request)
    return await call_next(request)
