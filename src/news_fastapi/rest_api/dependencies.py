from collections.abc import AsyncIterable
from functools import cache
from typing import Annotated

from fastapi import Depends, Request

from news_fastapi.application.authors.auth import AuthorsAuth
from news_fastapi.application.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)
from news_fastapi.application.news.auth import NewsAuth
from news_fastapi.application.news.services import NewsListService, NewsService
from news_fastapi.application.transaction import TransactionManager
from news_fastapi.domain.authors import (
    AuthorFactory,
    AuthorRepository,
    DefaultAuthorRepository,
)
from news_fastapi.domain.events.models import DomainEvent
from news_fastapi.domain.events.server import DomainEventServer
from news_fastapi.domain.news import NewsArticleRepository
from news_fastapi.infrastructure.auth.http_request import RequestAuthFactory
from news_fastapi.infrastructure.auth.jwt import JWTConfig
from news_fastapi.infrastructure.auth.jwt_mock import MockJWTConfig
from news_fastapi.infrastructure.persistence.authors import (
    TortoiseAuthorFactory,
    TortoiseAuthorRepository,
    TortoiseDefaultAuthorRepository,
)
from news_fastapi.infrastructure.persistence.news import TortoiseNewsArticleRepository
from news_fastapi.infrastructure.persistence.transaction import (
    TortoiseTransactionManager,
)


def jwt_config_provider() -> JWTConfig:
    return MockJWTConfig()


def request_auth_factory_provider(
    request: Request,
    jwt_config: Annotated[JWTConfig, Depends(jwt_config_provider)],
) -> RequestAuthFactory:
    return RequestAuthFactory(request=request, jwt_config=jwt_config)


def authors_auth_provider(
    request_auth_factory: Annotated[
        RequestAuthFactory, Depends(request_auth_factory_provider)
    ]
) -> AuthorsAuth:
    return request_auth_factory.authors_auth()


def news_auth_provider(
    request_auth_factory: Annotated[
        RequestAuthFactory, Depends(request_auth_factory_provider)
    ]
) -> NewsAuth:
    return request_auth_factory.news_auth()


@cache
def domain_event_server_provider() -> DomainEventServer:
    async def mock_event_stream() -> AsyncIterable[DomainEvent]:
        # pylint: disable=import-outside-toplevel
        from datetime import datetime as DateTime

        from news_fastapi.domain.events.publisher import UUID4DomainEventIdGenerator

        yield DomainEvent(
            event_id=await UUID4DomainEventIdGenerator().next_event_id(),
            date_occurred=DateTime.now(),
        )

    return DomainEventServer(event_stream=mock_event_stream())


def transaction_manager_provider(
    domain_event_server: Annotated[
        DomainEventServer, Depends(domain_event_server_provider)
    ]
) -> TransactionManager:
    flag = domain_event_server.should_send_domain_events_flag
    return TortoiseTransactionManager(should_send_domain_events_flag=flag)


def author_factory_provider() -> AuthorFactory:
    return TortoiseAuthorFactory()


def author_repository_provider() -> AuthorRepository:
    return TortoiseAuthorRepository()


def news_article_repository_provider() -> NewsArticleRepository:
    return TortoiseNewsArticleRepository()


def authors_service_provider(
    authors_auth: Annotated[AuthorsAuth, Depends(authors_auth_provider)],
    transaction_manager: Annotated[
        TransactionManager, Depends(transaction_manager_provider)
    ],
    author_factory: Annotated[AuthorFactory, Depends(author_factory_provider)],
    author_repository: Annotated[AuthorRepository, Depends(author_repository_provider)],
    news_article_repository: Annotated[
        NewsArticleRepository, Depends(news_article_repository_provider)
    ],
) -> AuthorsService:
    return AuthorsService(
        auth=authors_auth,
        transaction_manager=transaction_manager,
        author_factory=author_factory,
        author_repository=author_repository,
        news_article_repository=news_article_repository,
    )


def authors_list_service_provider(
    author_repository: Annotated[AuthorRepository, Depends(author_repository_provider)],
) -> AuthorsListService:
    return AuthorsListService(author_repository=author_repository)


def default_author_repository_provider() -> DefaultAuthorRepository:
    return TortoiseDefaultAuthorRepository()


def default_authors_service_provider(
    author_repository: Annotated[AuthorRepository, Depends(author_repository_provider)],
    default_author_repository: Annotated[
        DefaultAuthorRepository, Depends(default_author_repository_provider)
    ],
) -> DefaultAuthorsService:
    return DefaultAuthorsService(
        default_author_repository=default_author_repository,
        author_repository=author_repository,
    )


def news_service_provider(
    news_auth: Annotated[NewsAuth, Depends(news_auth_provider)],
    news_article_repository: Annotated[
        NewsArticleRepository, Depends(news_article_repository_provider)
    ],
    author_repository: Annotated[AuthorRepository, Depends(author_repository_provider)],
) -> NewsService:
    return NewsService(
        auth=news_auth,
        news_article_repository=news_article_repository,
        author_repository=author_repository,
    )


def news_list_service_provider(
    news_article_repository: Annotated[
        NewsArticleRepository, Depends(news_article_repository_provider)
    ],
    author_repository: Annotated[AuthorRepository, Depends(author_repository_provider)],
) -> NewsListService:
    return NewsListService(
        news_article_repository=news_article_repository,
        author_repository=author_repository,
    )
