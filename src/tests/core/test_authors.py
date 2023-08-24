from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock
from uuid import uuid4

from news_fastapi.core.authors.services import DefaultAuthorsService
from news_fastapi.domain.authors import DefaultAuthorRepository


class MockDefaultAuthorRepository(DefaultAuthorRepository):
    _data: dict[str, str | None]

    def __init__(self) -> None:
        self._data = {}

    async def get_default_author_id(self, user_id: str) -> str | None:
        return self._data.get(user_id)

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        self._data[user_id] = author_id


class DefaultAuthorsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.default_author_repository = MockDefaultAuthorRepository()
        self.author_repository = Mock()
        self.default_authors_service = DefaultAuthorsService(
            default_author_repository=self.default_author_repository,
            author_repository=self.author_repository,
        )

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
