from collections.abc import Iterable
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from news_fastapi.core.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.domain.authors import AuthorDeleted
from news_fastapi.domain.events import DomainEvent, DomainEventBuffer
from news_fastapi.utils.exceptions import NotFoundError
from tests.core.fixtures import TestAuthorsAuth, TestCoreTransactionManager
from tests.domain.fixtures import (
    TestAuthor,
    TestAuthorFactory,
    TestAuthorRepository,
    TestDefaultAuthorRepository,
    TestNewsArticleRepository,
)
from tests.fixtures import HUMAN_NAMES


class AuthorsListServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.author_factory = TestAuthorFactory()
        self.author_repository = TestAuthorRepository()
        self.authors_list_service = AuthorsListService(
            author_repository=self.author_repository
        )

    async def asyncSetUp(self) -> None:
        await self._populate_authors()

    async def _populate_authors(self) -> None:
        for name in HUMAN_NAMES:
            author_id = await self.author_repository.next_identity()
            author = self.author_factory.create_author(author_id=author_id, name=name)
            await self.author_repository.save(author)

    async def test_get_page(self) -> None:
        limit = 50
        page = await self.authors_list_service.get_page(offset=0, limit=limit)
        self.assertGreater(len(page), 0)
        self.assertLessEqual(len(page), limit)

    async def test_get_page_big_offset_returns_nothing(self) -> None:
        page = await self.authors_list_service.get_page(offset=10000, limit=50)
        self.assertEqual(len(page), 0)

    async def test_get_page_negative_offset_raises_error(self) -> None:
        try:
            await self.authors_list_service.get_page(offset=-1, limit=50)
        except ValueError:
            pass
        else:
            self.fail("get_page didn't raise ValueError on negative offset value")


class AuthorsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = TestAuthorsAuth(
            current_user_id="11111111-1111-1111-1111-111111111111"
        )
        self.transaction_manager = TestCoreTransactionManager()
        self.author_factory = TestAuthorFactory()
        self.author_repository = TestAuthorRepository()
        self.news_article_repository = TestNewsArticleRepository()
        self.domain_event_buffer = DomainEventBuffer()
        self.authors_service = AuthorsService(
            auth=self.authors_auth,
            transaction_manager=self.transaction_manager,
            author_factory=self.author_factory,
            author_repository=self.author_repository,
            news_article_repository=self.news_article_repository,
            domain_event_buffer=self.domain_event_buffer,
        )

    async def _create_author(self) -> str:
        author_id = "22222222-2222-2222-2222-222222222222"
        author_to_save = self.author_factory.create_author(
            author_id=author_id, name="John Doe"
        )
        await self.author_repository.save(author_to_save)
        return author_id

    async def test_get_author(self) -> None:
        author_id = await self._create_author()
        author_from_service = await self.authors_service.get_author(author_id=author_id)
        self.assertEqual(author_from_service.id, author_id)

    async def test_create_author(self) -> None:
        name = "John Doe"

        author_id = await self.authors_service.create_author(name=name)

        author = await self.author_repository.get_author_by_id(author_id)
        self.assertEqual(author.name, name)

    async def test_create_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_create_author()
        with self.assertRaises(AuthorizationError):
            await self.authors_service.create_author(name="John Doe")

    async def test_update_author(self) -> None:
        author_id = await self._create_author()
        new_name = "Tim Gray"

        await self.authors_service.update_author(author_id=author_id, new_name=new_name)

        author = await self.author_repository.get_author_by_id(author_id)
        self.assertEqual(author.name, new_name)

    async def test_update_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_update_author()
        with self.assertRaises(AuthorizationError):
            await self.authors_service.update_author(
                author_id="22222222-2222-2222-2222-222222222222", new_name="Tim Gray"
            )

    async def test_delete_author(self) -> None:
        author_id = await self._create_author()

        await self.authors_service.delete_author(author_id)

        with self.assertRaises(NotFoundError):
            await self.author_repository.get_author_by_id(author_id)

    async def test_delete_author_requires_authorization(self) -> None:
        self.authors_auth.forbid_delete_author()
        with self.assertRaises(AuthorizationError):
            await self.authors_service.delete_author(
                author_id="22222222-2222-2222-2222-222222222222"
            )

    async def test_delete_author_emits_author_deleted_domain_event(self) -> None:
        author_id = await self._create_author()

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


class DefaultAuthorsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = TestAuthorsAuth(
            current_user_id="33333333-3333-3333-3333-333333333333"
        )
        self.default_author_repository = TestDefaultAuthorRepository()
        self.author_repository = Mock()
        self.default_authors_service = DefaultAuthorsService(
            auth=self.authors_auth,
            default_author_repository=self.default_author_repository,
            author_repository=self.author_repository,
        )

    async def test_get_default_author(self) -> None:
        user_id = "11111111-1111-1111-1111-111111111111"
        author_id = "22222222-2222-2222-2222-222222222222"
        await self.default_author_repository.set_default_author_id(
            user_id=user_id, author_id=author_id
        )
        self.author_repository.get_author_by_id = AsyncMock(
            return_value=TestAuthor(id=author_id, name="John Doe")
        )
        author = await self.default_authors_service.get_default_author(user_id=user_id)
        self.assertEqual(author.id, author_id)

    async def test_set_default_author(self) -> None:
        user_id = str(uuid4())
        author_id = str(uuid4())
        await self.default_authors_service.set_default_author(
            user_id=user_id, author_id=author_id
        )
        self.assertEqual(
            await self.default_author_repository.get_default_author_id(user_id),
            author_id,
        )
