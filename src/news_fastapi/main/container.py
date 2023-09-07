from contextlib import asynccontextmanager

# pylint: disable=no-name-in-module
from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import (
    Configuration,
    ContextLocalSingleton,
    Dict,
    List,
    Object,
    Singleton,
)
from dependency_injector.wiring import Provide, inject
from fastapi import FastAPI
from tortoise import Tortoise

from news_fastapi.adapters.auth.http_request import RequestAuthFactory, RequestHolder
from news_fastapi.adapters.auth.jwt_mock import MockJWTConfig
from news_fastapi.adapters.persistence.tortoise.author import (
    TortoiseAuthorDetailsQueries,
    TortoiseAuthorRepository,
    TortoiseAuthorsListQueries,
    TortoiseDefaultAuthorRepository,
)
from news_fastapi.adapters.persistence.tortoise.draft import (
    TortoiseDraftDetailsQueries,
    TortoiseDraftRepository,
    TortoiseDraftsListQueries,
)
from news_fastapi.adapters.persistence.tortoise.news_article import (
    TortoiseNewsArticleDetailsQueries,
    TortoiseNewsArticleRepository,
    TortoiseNewsArticlesListQueries,
)
from news_fastapi.adapters.persistence.tortoise.transaction import (
    TortoiseTransactionManager,
)
from news_fastapi.adapters.rest_api.asgi import create_asgi_app
from news_fastapi.core.authors.commands import (
    CreateAuthorService,
    DeleteAuthorService,
    UpdateAuthorService,
)
from news_fastapi.core.authors.default_author import DefaultAuthorService
from news_fastapi.core.authors.queries import AuthorDetailsService, AuthorsListService
from news_fastapi.core.drafts.commands import (
    CreateDraftService,
    DeleteDraftService,
    PublishDraftService,
    UpdateDraftService,
)
from news_fastapi.core.drafts.queries import DraftDetailsService, DraftsListService
from news_fastapi.core.events.handlers import domain_event_handler_registry
from news_fastapi.core.news.commands import RevokeNewsArticleService
from news_fastapi.core.news.queries import (
    NewsArticleDetailsService,
    NewsArticlesListService,
)
from news_fastapi.domain.author import AuthorFactory
from news_fastapi.domain.draft import DraftFactory
from news_fastapi.domain.news_article import NewsArticleFactory
from news_fastapi.domain.publish import PublishService
from news_fastapi.domain.seed_work.events import DomainEventBuffer


@asynccontextmanager
@inject
async def asgi_lifespan(
    app: FastAPI,  # pylint: disable=redefined-outer-name,unused-argument
    tortoise_config: dict = Provide["tortoise_config"],
):
    await Tortoise.init(config=tortoise_config)
    yield
    await Tortoise.close_connections()


class DIContainer(DeclarativeContainer):
    wiring_config = WiringConfiguration(
        packages=[
            "news_fastapi.adapters",
            "news_fastapi.main",
        ],
        auto_wire=False,
    )

    config = Configuration()

    # region Domain Events

    domain_event_buffer = ContextLocalSingleton(DomainEventBuffer)

    # endregion

    # region Domain Factories

    author_factory = ContextLocalSingleton(AuthorFactory)
    draft_factory = ContextLocalSingleton(DraftFactory)
    news_article_factory = ContextLocalSingleton(NewsArticleFactory)

    # endregion

    # region Repositories

    author_repository = ContextLocalSingleton(TortoiseAuthorRepository)
    default_author_repository = ContextLocalSingleton(TortoiseDefaultAuthorRepository)
    draft_repository = ContextLocalSingleton(TortoiseDraftRepository)
    news_article_repository = ContextLocalSingleton(TortoiseNewsArticleRepository)

    # endregion

    # region Domain Services

    publish_service = ContextLocalSingleton(PublishService)

    # endregion

    # region Transaction Manager

    transaction_manager = ContextLocalSingleton(
        TortoiseTransactionManager,
        domain_event_buffer=domain_event_buffer,
        domain_event_handler_registry=domain_event_handler_registry,
    )

    # endregion

    # region Auth

    jwt_config = Singleton(MockJWTConfig)

    request_holder = ContextLocalSingleton(RequestHolder)
    request_auth_factory = ContextLocalSingleton(
        RequestAuthFactory, request_holder=request_holder, jwt_config=jwt_config
    )
    authors_auth = ContextLocalSingleton(
        lambda request_auth_factory: request_auth_factory.authors_auth(),
        request_auth_factory=request_auth_factory,
    )
    drafts_auth = ContextLocalSingleton(
        lambda request_auth_factory: request_auth_factory.drafts_auth(),
        request_auth_factory=request_auth_factory,
    )
    news_auth = ContextLocalSingleton(
        lambda request_auth_factory: request_auth_factory.news_auth(),
        request_auth_factory=request_auth_factory,
    )

    # endregion

    # region Application Core Queries

    authors_list_queries = ContextLocalSingleton(TortoiseAuthorsListQueries)
    author_details_queries = ContextLocalSingleton(TortoiseAuthorDetailsQueries)

    draft_list_queries = ContextLocalSingleton(TortoiseDraftsListQueries)
    draft_details_queries = ContextLocalSingleton(TortoiseDraftDetailsQueries)

    news_articles_list_queries = ContextLocalSingleton(TortoiseNewsArticlesListQueries)
    news_article_details_queries = ContextLocalSingleton(
        TortoiseNewsArticleDetailsQueries
    )

    # endregion

    # region Application Core Services

    authors_list_service = ContextLocalSingleton(
        AuthorsListService, authors_list_queries=authors_list_queries
    )
    author_details_service = ContextLocalSingleton(
        AuthorDetailsService, author_details_queries=author_details_queries
    )
    default_author_service = ContextLocalSingleton(
        DefaultAuthorService,
        auth=authors_auth,
        default_author_repository=default_author_repository,
        author_repository=author_repository,
    )
    create_author_service = ContextLocalSingleton(
        CreateAuthorService,
        auth=authors_auth,
        transaction_manager=transaction_manager,
        author_factory=author_factory,
        author_repository=author_repository,
    )
    update_author_service = ContextLocalSingleton(
        UpdateAuthorService,
        auth=authors_auth,
        transaction_manager=transaction_manager,
        author_repository=author_repository,
    )
    delete_author_service = ContextLocalSingleton(
        DeleteAuthorService,
        auth=authors_auth,
        transaction_manager=transaction_manager,
        author_factory=author_factory,
        author_repository=author_repository,
        news_article_repository=news_article_repository,
        domain_event_buffer=domain_event_buffer,
    )

    drafts_list_service = ContextLocalSingleton(
        DraftsListService,
        drafts_auth=drafts_auth,
        draft_list_queries=draft_list_queries,
    )
    draft_details_service = ContextLocalSingleton(
        DraftDetailsService,
        auth=drafts_auth,
        draft_details_queries=draft_details_queries,
    )
    create_draft_service = ContextLocalSingleton(
        CreateDraftService,
        auth=drafts_auth,
        transaction_manager=transaction_manager,
        draft_factory=draft_factory,
        draft_repository=draft_repository,
        default_author_repository=default_author_repository,
        news_article_repository=news_article_repository,
    )
    update_draft_service = ContextLocalSingleton(
        UpdateDraftService,
        auth=drafts_auth,
        transaction_manager=transaction_manager,
        draft_repository=draft_repository,
    )
    delete_draft_service = ContextLocalSingleton(
        DeleteDraftService,
        auth=drafts_auth,
        transaction_manager=transaction_manager,
        draft_repository=draft_repository,
    )
    publish_draft_service = ContextLocalSingleton(
        PublishDraftService,
        auth=drafts_auth,
        transaction_manager=transaction_manager,
        publish_service=publish_service,
    )

    news_articles_list_service = ContextLocalSingleton(
        NewsArticlesListService, news_articles_list_queries=news_articles_list_queries
    )
    news_article_details_service = ContextLocalSingleton(
        NewsArticleDetailsService,
        news_article_details_queries=news_article_details_queries,
    )
    revoke_news_article_service = ContextLocalSingleton(
        RevokeNewsArticleService,
        auth=news_auth,
        transaction_manager=transaction_manager,
        news_article_repository=news_article_repository,
    )

    # endregion

    # region Tortoise

    tortoise_config = Dict(
        connections=Dict(
            default=config.db.url,
        ),
        apps=Dict(
            news_fastapi=Dict(
                models=List(
                    Object("news_fastapi.adapters.persistence.tortoise.models"),
                )
            )
        ),
    )

    # endregion

    # region ASGI app

    asgi_app = Singleton(
        create_asgi_app,
        config=config.fastapi,
        lifespan=Object(asgi_lifespan),
    )

    # endregion
