from typing import Any

from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.rest_api.authentication import AuthenticationResult, \
    JWTAuthenticationResult


class JWTNewsAuth(NewsAuth):
    _jwt_claims: dict[str, Any]

    def __init__(self, jwt_claims: dict[str, Any]) -> None:
        self._jwt_claims = jwt_claims


def news_auth(authentication_result: AuthenticationResult) -> NewsAuth:
    if isinstance(authentication_result, JWTAuthenticationResult):
        return JWTNewsAuth(jwt_claims=authentication_result.jwt_claims)
    raise ValueError("Unsupported authentication method")
