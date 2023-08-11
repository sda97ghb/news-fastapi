from functools import cached_property
from typing import Any

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.rest_api.authentication import (
    AuthenticationResult,
    JWTAuthenticationResult,
)


class JWTAuthorsAuth(AuthorsAuth):
    _jwt_claims: dict[str, Any]

    def __init__(self, jwt_claims: dict[str, Any]) -> None:
        self._jwt_claims = jwt_claims

    @cached_property
    def _permissions(self) -> list[str]:
        return self._jwt_claims.get("permissions", [])

    def can_create_author(self) -> bool:
        return "authors:create-author" in self._permissions

    def can_update_author(self, author_id: str) -> bool:
        return "authors:update-author" in self._permissions

    def can_delete_author(self, author_id: str) -> bool:
        return "authors:delete-author" in self._permissions

    def get_current_user_id(self) -> str:
        return self._jwt_claims["sub"]


def authors_auth(authentication_result: AuthenticationResult) -> AuthorsAuth:
    if isinstance(authentication_result, JWTAuthenticationResult):
        return JWTAuthorsAuth(jwt_claims=authentication_result.jwt_claims)
    raise ValueError("Unsupported authentication method")
