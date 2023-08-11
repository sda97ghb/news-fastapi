from datetime import UTC
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from typing import Any, Protocol

from jwt import decode as decode_jwt
from jwt import encode as encode_jwt


class JWTConfig(Protocol):
    key: str
    issuer: str
    audience: str


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


class MockJWTConfig:
    key = "super-duper-secret-12345678"
    issuer = "https://jwt-issuer"
    audience = "https://jwt-audience"


def encode_test_jwt(claims: dict[str, Any] = {}) -> str:
    jwt_config = MockJWTConfig()
    claims["iss"] = jwt_config.issuer
    claims["aud"] = jwt_config.audience
    now = DateTime.now(tz=UTC)
    claims["iat"] = now
    claims["nbf"] = now
    claims["exp"] = now + TimeDelta(minutes=60)
    claims["sub"] = "69d32daa-f35f-48c9-ac2e-6f8dcd040f9f"
    claims["permissions"] = [
        "authors:create-author",
        "authors:update-author",
        "authors:delete-author",
    ]
    jwt_str = encode_jwt(claims, jwt_config.key, algorithm="HS256")
    return jwt_str
