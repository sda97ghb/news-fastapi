from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from news_fastapi.adapters.persistence.authors import (
    DefaultAuthor,
    TortoiseDefaultAuthorRepository,
)
from tests.adapters.persistence.tortoise import tortoise_orm


class TortoiseDefaultAuthorRepositoryTests(IsolatedAsyncioTestCase):
    async def test_set_default_author_id(self) -> None:
        async with tortoise_orm():
            user_id = str(uuid4())
            author_id = str(uuid4())
            repository = TortoiseDefaultAuthorRepository()
            await repository.set_default_author_id(user_id=user_id, author_id=author_id)
            self.assertIsNotNone(await DefaultAuthor.get_or_none(user_id=user_id))

    async def test_set_default_author_to_null(self) -> None:
        async with tortoise_orm():
            user_id = str(uuid4())
            repository = TortoiseDefaultAuthorRepository()
            await repository.set_default_author_id(user_id=user_id, author_id=None)
            self.assertIsNone(await DefaultAuthor.get_or_none(user_id=user_id))
