from dataclasses import dataclass
from functools import cached_property
from typing import Any, Protocol

from jwt import PyJWTError, decode as decode_jwt

from news_fastapi.application.exceptions import AuthenticationError


class JWTConfig(Protocol):
    key: str
    issuer: str
    audience: str


@dataclass
class JWTAuthenticationResult:
    jwt_str: str
    jwt_claims: dict[str, Any]


def authenticate_jwt(jwt_str: str, jwt_config: JWTConfig) -> JWTAuthenticationResult:
    try:
        jwt_claims = decode_and_verify_jwt(jwt_str, jwt_config)
        return JWTAuthenticationResult(jwt_str=jwt_str, jwt_claims=jwt_claims)
    except PyJWTError as err:
        raise AuthenticationError("Invalid JWT provided") from err


def decode_and_verify_jwt(jwt_str: str, jwt_config: JWTConfig) -> dict[str, Any]:
    claims = decode_jwt(
        jwt_str,
        jwt_config.key,
        algorithms=["HS256"],
        options={
            "require": ["exp", "nbf", "iat", "iss", "aud", "sub"],
        },
        audience=jwt_config.audience,
        issuer=jwt_config.issuer,
    )
    return claims


class BaseJWTAuth:
    _jwt_claims: dict[str, Any]

    def __init__(self, jwt_claims: dict[str, Any]) -> None:
        self._jwt_claims = jwt_claims

    @cached_property
    def permissions(self) -> list[str]:
        return self._jwt_claims.get("permissions", [])

    @cached_property
    def sub(self) -> str:
        return self._jwt_claims["sub"]
