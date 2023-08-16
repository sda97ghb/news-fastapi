from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from jwt import PyJWTError
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED

from news_fastapi.application.rest_api.jwt import JWTConfig, decode_and_verify_jwt


class AuthenticationResult:
    pass


@dataclass
class JWTAuthenticationResult(AuthenticationResult):
    jwt_str: str
    jwt_claims: dict[str, Any]


def authenticate(request: Request, jwt_config: JWTConfig) -> AuthenticationResult:
    authorization_header = request.headers.get("Authorization")
    if authorization_header and authorization_header.startswith("Bearer "):
        jwt_str = authorization_header.removeprefix("Bearer ")
        try:
            jwt_claims = decode_and_verify_jwt(jwt_str, jwt_config)
            return JWTAuthenticationResult(jwt_str=jwt_str, jwt_claims=jwt_claims)
        except PyJWTError as err:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT provided: {err}"
            )
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Please provide authorization header with bearer scheme",
    )
