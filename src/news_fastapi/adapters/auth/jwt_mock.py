from datetime import UTC, datetime as DateTime, timedelta as TimeDelta
from typing import Any

from jwt import encode as encode_jwt


class MockJWTConfig:
    key = "super-duper-secret-12345678"
    issuer = "https://jwt-issuer"
    audience = "https://jwt-audience"


def encode_test_jwt(claims: dict[str, Any] | None = None) -> str:
    if claims is None:
        claims = {}
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
        "authors:get-default-author",
        "authors:set-default-author",
        "drafts:manage",
        "drafts:delete-published",
        "drafts:publish",
        "news:revoke",
    ]
    jwt_str = encode_jwt(claims, jwt_config.key, algorithm="HS256")
    return jwt_str


if __name__ == "__main__":
    print(encode_test_jwt())
