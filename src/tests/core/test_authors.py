from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from news_fastapi.core.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.utils.exceptions import NotFoundError
from tests.core.fixtures import TestAuthorsAuth, TestCoreTransactionManager
from tests.domain.fixtures import (
    HUMAN_NAMES,
    TestAuthor,
    TestAuthorFactory,
    TestAuthorRepository,
    TestDefaultAuthorRepository,
    TestDomainEventIdGenerator,
    TestDomainEventStore,
    TestNewsArticleRepository,
)


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
        self.domain_event_id_generator = TestDomainEventIdGenerator()
        self.domain_event_store = TestDomainEventStore()
        self.authors_service = AuthorsService(
            auth=self.authors_auth,
            transaction_manager=self.transaction_manager,
            author_factory=self.author_factory,
            author_repository=self.author_repository,
            news_article_repository=self.news_article_repository,
            domain_event_id_generator=self.domain_event_id_generator,
            domain_event_store=self.domain_event_store,
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
