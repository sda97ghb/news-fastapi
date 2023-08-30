from collections.abc import AsyncIterable
from typing import Any

# pylint: disable=no-name-in-module
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import (
    Configuration,
    ContextLocalSingleton,
    Dict,
    Factory,
    List,
    Object,
    Singleton,
)

from news_fastapi.adapters.auth.http_request import RequestAuthFactory, RequestHolder
from news_fastapi.adapters.auth.jwt_mock import MockJWTConfig
from news_fastapi.adapters.events.handlers import domain_event_handler_registry
from news_fastapi.adapters.events.server import (
    DomainEventPublisher,
    DomainEventServer,
    PublishChannel,
    PublishServer,
)
from news_fastapi.adapters.persistence.tortoise.authors import (
    TortoiseAuthorFactory,
    TortoiseAuthorRepository,
    TortoiseDefaultAuthorRepository,
)
from news_fastapi.adapters.persistence.tortoise.events import TortoiseDomainEventStore
from news_fastapi.adapters.persistence.tortoise.news import (
    TortoiseNewsArticleRepository,
)
from news_fastapi.adapters.persistence.tortoise.transaction import (
    TortoiseTransactionManager,
)
from news_fastapi.core.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)
from news_fastapi.core.news.services import NewsListService, NewsService
from news_fastapi.domain.events import (
    DomainEvent,
    DomainEventStore,
    UUID4DomainEventIdGenerator,
)


async def mock_event_stream() -> AsyncIterable[DomainEvent]:
    # pylint: disable=import-outside-toplevel
    from dataclasses import dataclass
    from datetime import datetime as DateTime

    @dataclass
    class MockEvent(DomainEvent):
        def _to_json_extra_fields(self) -> dict[str, Any]:
            return {}

    yield MockEvent(
        event_id=await UUID4DomainEventIdGenerator().next_event_id(),
        date_occurred=DateTime.now(),
    )


class MockPublishChannel(PublishChannel):
    async def publish(self, event: DomainEvent) -> None:
        pass


def create_domain_event_server(
    domain_event_store: DomainEventStore,
    publish_server: PublishServer,
) -> DomainEventServer:
    server = DomainEventServer(
        event_stream=mock_event_stream(),
        domain_event_store=domain_event_store,
        publish_server=publish_server,
    )
    server.include_registry(domain_event_handler_registry)
    return server


class DIContainer(DeclarativeContainer):
    wiring_config = WiringConfiguration(
        packages=[
            "news_fastapi.adapters",
            "news_fastapi.main",
        ],
        auto_wire=False,
    )

    config = Configuration()

    tortoise_config = Dict(
        connections=Dict(
            default=config.db.url,
        ),
        apps=Dict(
            news_fastapi=Dict(
                models=List(
                    Object("news_fastapi.adapters.persistence.authors"),
                    Object("news_fastapi.adapters.persistence.drafts"),
                    Object("news_fastapi.adapters.persistence.events"),
                    Object("news_fastapi.adapters.persistence.news"),
                )
            )
        ),
    )

    jwt_config = Singleton(MockJWTConfig)

    domain_event_id_generator = Singleton(UUID4DomainEventIdGenerator)
    domain_event_store = Singleton(TortoiseDomainEventStore)
    publisher = Singleton(
        DomainEventPublisher,
        publish_channels=List(Factory(MockPublishChannel)),
        domain_event_store=domain_event_store,
        send_batch_size=50,
    )
    publish_server = Singleton(PublishServer, publisher=publisher)
    domain_event_server = Singleton(
        create_domain_event_server,
        domain_event_store=domain_event_store,
        publish_server=publish_server,
    )

    transaction_manager = ContextLocalSingleton(
        lambda domain_event_server: TortoiseTransactionManager(
            should_send_domain_events_flag=domain_event_server.should_send_domain_events_flag,
        ),
        domain_event_server=domain_event_server,
    )

    request_holder = ContextLocalSingleton(RequestHolder)
    request_auth_factory = ContextLocalSingleton(
        RequestAuthFactory, request_holder=request_holder, jwt_config=jwt_config
    )
    authors_auth = ContextLocalSingleton(
        lambda request_auth_factory: request_auth_factory.authors_auth(),
        request_auth_factory=request_auth_factory,
    )
    news_auth = ContextLocalSingleton(
        lambda request_auth_factory: request_auth_factory.news_auth(),
        request_auth_factory=request_auth_factory,
    )

    author_factory = ContextLocalSingleton(TortoiseAuthorFactory)

    author_repository = ContextLocalSingleton(TortoiseAuthorRepository)
    news_article_repository = ContextLocalSingleton(TortoiseNewsArticleRepository)
    default_author_repository = ContextLocalSingleton(TortoiseDefaultAuthorRepository)

    authors_list_service = ContextLocalSingleton(
        AuthorsListService, author_repository=author_repository
    )
    authors_service = ContextLocalSingleton(
        AuthorsService,
        auth=authors_auth,
        transaction_manager=transaction_manager,
        author_factory=author_factory,
        author_repository=author_repository,
        news_article_repository=news_article_repository,
        domain_event_id_generator=domain_event_id_generator,
        domain_event_store=domain_event_store,
    )
    default_authors_service = ContextLocalSingleton(
        DefaultAuthorsService,
        default_author_repository=default_author_repository,
        author_repository=author_repository,
    )
    news_list_service = ContextLocalSingleton(
        NewsListService,
        news_article_repository=news_article_repository,
        author_repository=author_repository,
    )
    news_service = ContextLocalSingleton(
        NewsService,
        auth=news_auth,
        news_article_repository=news_article_repository,
        author_repository=author_repository,
    )
