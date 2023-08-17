from functools import cached_property

from fastapi import Request

from news_fastapi.application.authors import (
    AuthorsAuth,
    AuthorsDAO,
    DefaultAuthorsDAO,
    MockAuthorsDAO,
    MockDefaultAuthorsDAO,
)
from news_fastapi.application.authors.services import AuthorsService
from news_fastapi.application.drafts import DraftsDAO, MockDraftsDAO
from news_fastapi.application.news import MockNewsDAO, NewsAuth, NewsDAO, NewsService
from news_fastapi.infrastructure.auth.authentication import JWTConfig, MockJWTConfig
from news_fastapi.infrastructure.rest_api.authentication import (
    AuthenticationResult,
    authenticate,
)
from news_fastapi.infrastructure.rest_api.authors.auth import authors_auth
from news_fastapi.infrastructure.rest_api.news.auth import news_auth


class NewsRequestContainer:
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
    def auth(self) -> NewsAuth:
        return news_auth(self.authentication_result)

    @cached_property
    def authors_auth(self) -> AuthorsAuth:
        return authors_auth(self.authentication_result)

    @cached_property
    def news_dao(self) -> NewsDAO:
        return MockNewsDAO()

    @cached_property
    def news_service(self) -> NewsService:
        return NewsService(auth=self.auth, news_dao=self.news_dao)

    @cached_property
    def authors_dao(self) -> AuthorsDAO:
        return MockAuthorsDAO()

    @cached_property
    def drafts_dao(self) -> DraftsDAO:
        return MockDraftsDAO()

    @cached_property
    def default_authors_dao(self) -> DefaultAuthorsDAO:
        return MockDefaultAuthorsDAO()

    @cached_property
    def authors_service(self) -> AuthorsService:
        return AuthorsService(
            auth=self.authors_auth,
            dao=self.authors_dao,
            news_dao=self.news_dao,
            drafts_dao=self.drafts_dao,
            default_authors_dao=self.default_authors_dao,
        )
