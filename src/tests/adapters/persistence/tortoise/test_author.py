from unittest import IsolatedAsyncioTestCase, TestCase
from uuid import UUID, uuid4

from news_fastapi.adapters.persistence.tortoise.author import (
    TortoiseAuthorDetailsQueries,
    TortoiseAuthorRepository,
    TortoiseAuthorsListQueries,
    TortoiseDefaultAuthorRepository,
)
from news_fastapi.adapters.persistence.tortoise.models import (
    AuthorModel,
    DefaultAuthorModel,
)
from news_fastapi.domain.author import Author
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.fixtures import HUMAN_NAMES
from tests.utils import AssertMixin


class AuthorTestsMixin:
    def _create_valid_author_model_instance(self) -> AuthorModel:
        author_id = "11111111-1111-1111-1111-111111111111"
        name = "John Doe"
        return AuthorModel(id=author_id, name=name)

    async def _populate_author(self) -> AuthorModel:
        model_instance = self._create_valid_author_model_instance()
        await model_instance.save()
        return model_instance

    async def _populate_authors(self) -> None:
        self.assertGreater(len(HUMAN_NAMES), 50)
        for name in HUMAN_NAMES:
            await AuthorModel.create(id=str(uuid4()), name=name)


class TortoiseAuthorsListQueriesTests(
    AuthorTestsMixin, AssertMixin, IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.queries = TortoiseAuthorsListQueries()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_get_page(self) -> None:
        await self._populate_authors()
        offset = 0
        limit = 50
        page = await self.queries.get_page(offset=offset, limit=limit)
        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page_too_big_offset_returns_empty_list(self) -> None:
        await self._populate_authors()
        page = await self.queries.get_page(offset=10000, limit=50)
        self.assertEmpty(page.items)

    async def test_get_page_negative_offset_raises_values_error(self) -> None:
        await self._populate_authors()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=50)


class TortoiseAuthorDetailsQueriesTests(AuthorTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.queries = TortoiseAuthorDetailsQueries()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_get_author(self) -> None:
        saved_author_model_instance = await self._populate_author()
        author_id = saved_author_model_instance.id
        details = await self.queries.get_author(author_id=author_id)
        self.assertEqual(details.author_id, saved_author_model_instance.id)
        self.assertEqual(details.name, saved_author_model_instance.name)

    async def test_get_author_raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_author(author_id=non_existent_author_id)


class TortoiseAuthorRepositoryTests(
    AuthorTestsMixin, AssertMixin, IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.repository = TortoiseAuthorRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    def _create_author(self) -> Author:
        return Author(id_="11111111-1111-1111-1111-111111111111", name="John Doe")

    def assertAuthorAndModelAreCompletelyEqual(
        self, author: Author, model_instance: AuthorModel
    ) -> None:
        self.assertEqual(author.id, model_instance.id)
        self.assertEqual(author.name, model_instance.name)

    async def test_next_identity(self) -> None:
        id_1 = await self.repository.next_identity()
        id_2 = await self.repository.next_identity()
        for id_ in [id_1, id_2]:
            try:
                UUID(id_)
            except ValueError:
                self.fail(f"next_identity returned badly formed UUID: {id_}")
        self.assertNotEqual(id_1, id_2)

    async def test_get_author_by_id(self) -> None:
        saved_author_model_instance = await self._populate_author()

        author_id = saved_author_model_instance.id
        author_from_db = await self.repository.get_author_by_id(author_id=author_id)

        self.assertAuthorAndModelAreCompletelyEqual(
            author_from_db, saved_author_model_instance
        )

    async def test_get_author_by_id_raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_author_by_id(non_existent_author_id)

    async def test_get_authors_list(self) -> None:
        await self._populate_authors()
        limit = 50
        authors_list = await self.repository.get_authors_list(offset=0, limit=limit)
        self.assertEqual(len(authors_list), limit)

    async def test_get_authors_list_too_big_offset_returns_empty_list(self) -> None:
        await self._populate_authors()
        authors_list = await self.repository.get_authors_list(offset=10000, limit=50)
        self.assertEmpty(authors_list)

    async def test_get_authors_list_negative_offset_raises_values_error(self) -> None:
        await self._populate_authors()
        with self.assertRaises(ValueError):
            await self.repository.get_authors_list(offset=-1, limit=50)

    async def test_get_authors_in_bulk(self) -> None:
        id_list = [
            "11111111-1111-1111-1111-111111111111",
            "22222222-2222-2222-2222-222222222222",
            "33333333-3333-3333-3333-333333333333",
            "44444444-4444-4444-4444-444444444444",
        ]
        for author_id, name in zip(id_list, HUMAN_NAMES[:4]):
            await AuthorModel.create(id=author_id, name=name)
        id_list = [
            "22222222-2222-2222-2222-222222222222",
            "44444444-4444-4444-4444-444444444444",
        ]
        authors_mapping = await self.repository.get_authors_in_bulk(id_list=id_list)
        for id_ in id_list:
            self.assertIn(id_, authors_mapping)
            self.assertIsNotNone(authors_mapping[id_])
            self.assertEqual(id_, authors_mapping[id_].id)

    async def test_get_authors_in_bulk_returns_empty_mapping_on_empty_id_list(
        self,
    ) -> None:
        authors_mapping = await self.repository.get_authors_in_bulk(id_list=[])
        self.assertEmpty(authors_mapping)

    async def test_get_authors_in_bulk_ignores_not_found(self) -> None:
        non_existent_id = str(uuid4())
        authors_mapping = await self.repository.get_authors_in_bulk(
            id_list=[non_existent_id]
        )
        self.assertNotIn(non_existent_id, authors_mapping)

    async def test_save_creates_if_does_not_exist(self) -> None:
        author = self._create_author()
        await self.repository.save(author)
        author_model_instance_from_get = await AuthorModel.get(id=author.id)
        self.assertAuthorAndModelAreCompletelyEqual(
            author, author_model_instance_from_get
        )

    async def test_save_updates_if_exists(self) -> None:
        author_model_instance = await self._populate_author()

        new_name = "Tim Gray"
        author = Author(id_=author_model_instance.id, name=new_name)
        await self.repository.save(author)

        author_model_instance_from_get = await AuthorModel.get(id=author.id)
        self.assertAuthorAndModelAreCompletelyEqual(
            author, author_model_instance_from_get
        )

    async def test_remove(self) -> None:
        author_model_instance = await self._populate_author()
        author = Author(id_=author_model_instance.id, name=author_model_instance.name)

        await self.repository.remove(author=author)

        self.assertFalse(await AuthorModel.exists(id=author_model_instance.id))


class TortoiseDefaultAuthorRepositoryTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = TortoiseDefaultAuthorRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_get_default_author_id(self) -> None:
        user_id = str(uuid4())
        expected_author_id = str(uuid4())
        await DefaultAuthorModel.create(user_id=user_id, author_id=expected_author_id)

        returned_author_id = await self.repository.get_default_author_id(
            user_id=user_id
        )

        self.assertEqual(returned_author_id, expected_author_id)

    async def test_get_default_author_id_returns_null_if_never_set(self) -> None:
        never_set_user_id = str(uuid4())
        author_id = await self.repository.get_default_author_id(
            user_id=never_set_user_id
        )
        self.assertIsNone(author_id)

    async def test_set_default_author_id(self) -> None:
        user_id = str(uuid4())
        author_id = str(uuid4())
        await self.repository.set_default_author_id(
            user_id=user_id, author_id=author_id
        )
        self.assertIsNotNone(await DefaultAuthorModel.get_or_none(user_id=user_id))

    async def test_set_default_author_to_null(self) -> None:
        user_id = str(uuid4())
        await self.repository.set_default_author_id(user_id=user_id, author_id=None)
        self.assertIsNone(await DefaultAuthorModel.get_or_none(user_id=user_id))
