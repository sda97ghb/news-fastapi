from datetime import UTC, datetime as DateTime

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.transaction import TransactionManager
from news_fastapi.domain.authors import (
    Author,
    AuthorDeleted,
    AuthorFactory,
    AuthorRepository,
    DefaultAuthorRepository,
)
from news_fastapi.domain.events.publisher import DomainEventIdGenerator
from news_fastapi.domain.events.store import DomainEventStore
from news_fastapi.domain.news import NewsArticleRepository
from news_fastapi.utils.sentinels import Undefined, UndefinedType


class AuthorsListService:
    _author_repository: AuthorRepository

    def __init__(self, author_repository: AuthorRepository) -> None:
        self._author_repository = author_repository

    async def get_page(self, offset: int = 0, limit: int = 50) -> list[Author]:
        if offset < 0:
            raise ValueError("Offset must be positive integer or 0")
        return list(await self._author_repository.get_authors_list(offset, limit))


class AuthorsService:
    _auth: AuthorsAuth
    _transaction_manager: TransactionManager
    _author_factory: AuthorFactory
    _author_repository: AuthorRepository
    _news_article_repository: NewsArticleRepository
    _domain_event_id_generator: DomainEventIdGenerator
    _domain_event_store: DomainEventStore

    def __init__(
        self,
        auth: AuthorsAuth,
        transaction_manager: TransactionManager,
        author_factory: AuthorFactory,
        author_repository: AuthorRepository,
        news_article_repository: NewsArticleRepository,
        domain_event_id_generator: DomainEventIdGenerator,
        domain_event_store: DomainEventStore,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._author_factory = author_factory
        self._author_repository = author_repository
        self._news_article_repository = news_article_repository
        self._domain_event_id_generator = domain_event_id_generator
        self._domain_event_store = domain_event_store

    async def get_author(self, author_id: str) -> Author:
        return await self._author_repository.get_author_by_id(author_id)

    async def create_author(self, name: str) -> str:
        async with self._transaction_manager.in_transaction():
            self._auth.check_create_author()
            author_id = await self._author_repository.next_identity()
            author = self._author_factory.create_author(author_id=author_id, name=name)
            await self._author_repository.save(author)
            return author.id

    async def update_author(
        self, author_id: str, new_name: str | UndefinedType = Undefined
    ) -> None:
        async with self._transaction_manager.in_transaction():
            self._auth.check_update_author(author_id)
            author = await self._author_repository.get_author_by_id(author_id)
            if new_name is not Undefined:
                author.name = new_name
            await self._author_repository.save(author)

    async def delete_author(self, author_id: str) -> None:
        async with self._transaction_manager.in_transaction():
            self._auth.check_delete_author(author_id)
            author = await self._author_repository.get_author_by_id(author_id)
            news_for_author = await self._news_article_repository.count_for_author(
                author.id
            )
            has_author_published_news = news_for_author > 0
            if has_author_published_news:
                raise DeleteAuthorError(
                    "Can't delete an author with at least one published news article"
                )
            await self._publish_author_deleted(author_id)
            await self._author_repository.remove(author)

    async def _publish_author_deleted(self, author_id: str) -> None:
        event_id = await self._domain_event_id_generator.next_event_id()
        now = DateTime.now(UTC)
        event = AuthorDeleted(event_id=event_id, date_occurred=now, author_id=author_id)
        await self._domain_event_store.append(event)


class DefaultAuthorsService:
    _auth: AuthorsAuth
    _default_author_repository: DefaultAuthorRepository
    _author_repository: AuthorRepository

    def __init__(
        self,
        auth: AuthorsAuth,
        default_author_repository: DefaultAuthorRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._auth = auth
        self._default_author_repository = default_author_repository
        self._author_repository = author_repository

    async def get_default_author(self, user_id: str) -> Author | None:
        self._auth.check_get_default_author()
        author_id = await self._default_author_repository.get_default_author_id(user_id)
        if author_id is None:
            return None
        author = await self._author_repository.get_author_by_id(author_id)
        return author

    async def set_default_author(self, user_id: str, author_id: str | None) -> None:
        self._auth.check_set_default_author()
        await self._default_author_repository.set_default_author_id(user_id, author_id)
