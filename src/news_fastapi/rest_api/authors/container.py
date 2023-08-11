from functools import cached_property

from starlette.requests import Request

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.dao import (
    AuthorsDAO,
    DefaultAuthorsDAO,
    MockAuthorsDAO,
    MockDefaultAuthorsDAO,
)
from news_fastapi.core.authors.services import AuthorsService
from news_fastapi.core.drafts.dao import DraftsDAO, MockDraftsDAO
from news_fastapi.core.news.dao import MockNewsDAO, NewsDAO
from news_fastapi.rest_api.authentication import AuthenticationResult, authenticate
from news_fastapi.rest_api.authors.auth import authors_auth
from news_fastapi.rest_api.jwt import JWTConfig, MockJWTConfig


class AuthorsRequestContainer:
    _request: Request

    def __init__(self, request: Request) -> None:
        self._request = request

    @cached_property
    def jwt_config(self) -> JWTConfig:
        return MockJWTConfig()

    @cached_property
    def authentication_result(self) -> AuthenticationResult:
        return authenticate(self._request, self.jwt_config)

    @cached_property
    def auth(self) -> AuthorsAuth:
        return authors_auth(self.authentication_result)

    @cached_property
    def authors_dao(self) -> AuthorsDAO:
        return MockAuthorsDAO()

    @cached_property
    def news_dao(self) -> NewsDAO:
        return MockNewsDAO()

    @cached_property
    def drafts_dao(self) -> DraftsDAO:
        return MockDraftsDAO()

    @cached_property
    def default_authors_dao(self) -> DefaultAuthorsDAO:
        return MockDefaultAuthorsDAO()

    @cached_property
    def authors_service(self) -> AuthorsService:
        return AuthorsService(
            auth=self.auth,
            dao=self.authors_dao,
            news_dao=self.news_dao,
            drafts_dao=self.drafts_dao,
            default_authors_dao=self.default_authors_dao,
        )
