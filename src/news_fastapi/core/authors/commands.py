from dataclasses import dataclass

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.transaction import TransactionManager
from news_fastapi.domain.author import (
    Author,
    AuthorDeleted,
    AuthorFactory,
    AuthorRepository,
)
from news_fastapi.domain.delete_author import can_delete_author
from news_fastapi.domain.news_article import NewsArticleRepository
from news_fastapi.domain.seed_work.events import DomainEventBuffer
from news_fastapi.utils.sentinels import Undefined, UndefinedType


@dataclass
class CreateAuthorResult:
    author: Author


class CreateAuthorService:
    _auth: AuthorsAuth
    _transaction_manager: TransactionManager
    _author_factory: AuthorFactory
    _author_repository: AuthorRepository

    def __init__(
        self,
        auth: AuthorsAuth,
        transaction_manager: TransactionManager,
        author_factory: AuthorFactory,
        author_repository: AuthorRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._author_factory = author_factory
        self._author_repository = author_repository

    async def create_author(self, name: str) -> CreateAuthorResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_create_author()
            author_id = await self._author_repository.next_identity()
            author = self._author_factory.create_author(author_id=author_id, name=name)
            await self._author_repository.save(author)
            return CreateAuthorResult(author=author)


@dataclass
class UpdateAuthorResult:
    updated_author: Author


class UpdateAuthorService:
    _auth: AuthorsAuth
    _transaction_manager: TransactionManager
    _author_repository: AuthorRepository

    def __init__(
        self,
        auth: AuthorsAuth,
        transaction_manager: TransactionManager,
        author_repository: AuthorRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._author_repository = author_repository

    async def update_author(
        self, author_id: str, new_name: str | UndefinedType = Undefined
    ) -> UpdateAuthorResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_update_author(author_id)
            author = await self._author_repository.get_author_by_id(author_id)
            if new_name is not Undefined:
                author.name = new_name
            await self._author_repository.save(author)
            return UpdateAuthorResult(updated_author=author)


@dataclass
class DeleteAuthorResult:
    deleted_author_id: str


class DeleteAuthorService:
    _auth: AuthorsAuth
    _transaction_manager: TransactionManager
    _author_repository: AuthorRepository
    _news_article_repository: NewsArticleRepository
    _domain_event_buffer: DomainEventBuffer

    def __init__(
        self,
        auth: AuthorsAuth,
        transaction_manager: TransactionManager,
        author_factory: AuthorFactory,
        author_repository: AuthorRepository,
        news_article_repository: NewsArticleRepository,
        domain_event_buffer: DomainEventBuffer,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._author_factory = author_factory
        self._author_repository = author_repository
        self._news_article_repository = news_article_repository
        self._domain_event_buffer = domain_event_buffer

    async def delete_author(self, author_id: str) -> DeleteAuthorResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_delete_author(author_id)
            author = await self._author_repository.get_author_by_id(author_id)
            if not await can_delete_author(author_id, self._news_article_repository):
                raise DeleteAuthorError(
                    "Can't delete an author with at least one published news article"
                )
            self._domain_event_buffer.append(AuthorDeleted(author_id=author_id))
            await self._author_repository.remove(author)
            return DeleteAuthorResult(deleted_author_id=author_id)
