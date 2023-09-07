from typing import Iterable
from unittest import IsolatedAsyncioTestCase

from news_fastapi.core.authors.commands import (
    CreateAuthorService,
    DeleteAuthorService,
    UpdateAuthorService,
)
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.domain.author import AuthorDeleted, AuthorFactory
from news_fastapi.domain.seed_work.events import DomainEvent, DomainEventBuffer
from news_fastapi.utils.exceptions import NotFoundError
from tests.core.authors.mixins import AuthorTestsMixin
from tests.core.fixtures import AuthorsAuthFixture, TransactionManagerFixture
from tests.domain.fixtures import AuthorRepositoryFixture, NewsArticleRepositoryFixture


class CreateAuthorServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = AuthorsAuthFixture(
            current_user_id="11111111-1111-1111-1111-111111111111"
        )
        self.transaction_manager = TransactionManagerFixture()
        self.author_factory = AuthorFactory()
        self.author_repository = AuthorRepositoryFixture()
        self.service = CreateAuthorService(
            auth=self.authors_auth,
            transaction_manager=self.transaction_manager,
            author_factory=self.author_factory,
            author_repository=self.author_repository,
        )

    async def test_create_author(self) -> None:
        name = "John Doe"
        result = await self.service.create_author(name=name)

        # check result is correct
        self.assertEqual(result.author.name, name)

        # get the author from the repo to check if it was saved
        author = await self.author_repository.get_author_by_id(result.author.id)
        self.assertEqual(author.name, name)

    async def test_create_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_create_author()
        with self.assertRaises(AuthorizationError):
            await self.service.create_author(name="John Doe")


class UpdateAuthorServiceTests(AuthorTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = AuthorsAuthFixture(
            current_user_id="11111111-1111-1111-1111-111111111111"
        )
        self.transaction_manager = TransactionManagerFixture()
        self.author_factory = AuthorFactory()
        self.author_repository = AuthorRepositoryFixture()
        self.service = UpdateAuthorService(
            auth=self.authors_auth,
            transaction_manager=self.transaction_manager,
            author_repository=self.author_repository,
        )

    async def test_update_author(self) -> None:
        author_id = await self._populate_author()
        new_name = "Tim Gray"

        result = await self.service.update_author(
            author_id=author_id, new_name=new_name
        )

        self.assertEqual(result.updated_author.id, author_id)
        self.assertEqual(result.updated_author.name, new_name)

        author = await self.author_repository.get_author_by_id(author_id)
        self.assertEqual(author.name, new_name)

    async def test_update_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_update_author()
        with self.assertRaises(AuthorizationError):
            await self.service.update_author(
                author_id="22222222-2222-2222-2222-222222222222", new_name="Tim Gray"
            )


class DeleteAuthorServiceTests(AuthorTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = AuthorsAuthFixture(
            current_user_id="11111111-1111-1111-1111-111111111111"
        )
        self.transaction_manager = TransactionManagerFixture()
        self.author_factory = AuthorFactory()
        self.author_repository = AuthorRepositoryFixture()
        self.news_article_repository = NewsArticleRepositoryFixture()
        self.domain_event_buffer = DomainEventBuffer()
        self.authors_service = DeleteAuthorService(
            auth=self.authors_auth,
            transaction_manager=self.transaction_manager,
            author_factory=self.author_factory,
            author_repository=self.author_repository,
            news_article_repository=self.news_article_repository,
            domain_event_buffer=self.domain_event_buffer,
        )

    async def test_delete_author(self) -> None:
        author_id = await self._populate_author()

        result = await self.authors_service.delete_author(author_id)

        self.assertEqual(result.deleted_author_id, author_id)

        with self.assertRaises(NotFoundError):
            await self.author_repository.get_author_by_id(author_id)

    async def test_delete_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_delete_author()
        with self.assertRaises(AuthorizationError):
            await self.authors_service.delete_author(
                author_id="22222222-2222-2222-2222-222222222222"
            )

    async def test_delete_author_emits_author_deleted_domain_event(self) -> None:
        author_id = await self._populate_author()

        await self.authors_service.delete_author(author_id)

        events = self.domain_event_buffer.complete()
        self.assertEventEmitted(events, AuthorDeleted, author_id=author_id)

    def assertEventEmitted(
        self, events: Iterable[DomainEvent], event_type: type[DomainEvent], **kwargs
    ) -> None:
        for event in events:
            if isinstance(event, event_type) and all(
                getattr(event, attr) == expected_value
                for attr, expected_value in kwargs.items()
            ):
                return
        self.fail(
            f"Expected event {event_type.__name__}({kwargs}) was not emitted. "
            f"Emitted events: {events}"
        )
