from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

from news_fastapi.core.authors.default_author import DefaultAuthorService
from news_fastapi.domain.author import Author
from tests.core.fixtures import AuthorsAuthFixture
from tests.domain.fixtures import DefaultAuthorRepositoryFixture


class DefaultAuthorsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_auth = AuthorsAuthFixture(
            current_user_id="33333333-3333-3333-3333-333333333333"
        )
        self.default_author_repository = DefaultAuthorRepositoryFixture()
        self.author_repository = Mock()
        self.default_authors_service = DefaultAuthorService(
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
            return_value=Author(id_=author_id, name="John Doe")
        )
        default_author_info = await self.default_authors_service.get_default_author(
            user_id=user_id
        )
        self.assertIsNotNone(default_author_info)
        self.assertEqual(default_author_info.user_id, user_id)
        self.assertEqual(default_author_info.author.id, author_id)

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

    async def test_set_default_author_to_none(self) -> None:
        user_id = str(uuid4())
        await self.default_authors_service.set_default_author(
            user_id=user_id, author_id=None
        )
        self.assertIsNone(
            await self.default_author_repository.get_default_author_id(user_id)
        )
