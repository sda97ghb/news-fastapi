from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy_orm.author import (
    SQLAlchemyORMAuthorDetailsQueries,
    SQLAlchemyORMAuthorRepository,
    SQLAlchemyORMAuthorsListQueries,
    SQLAlchemyORMDefaultAuthorRepository,
)
from news_fastapi.adapters.persistence.sqlalchemy_orm.models import (
    AuthorModel,
    DefaultAuthorModel,
    Model,
)
from news_fastapi.domain.author import Author
from news_fastapi.utils.exceptions import NotFoundError
from tests.fixtures import HUMAN_NAMES
from tests.utils import AssertMixin


class TortoiseAuthorsListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.queries = SQLAlchemyORMAuthorsListQueries(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _populate_authors(self) -> None:
        self.assertGreater(len(HUMAN_NAMES), 50)
        self.session.add_all(
            AuthorModel(id=str(uuid4()), name=name) for name in HUMAN_NAMES
        )
        await self.session.flush()

    async def test_get_page(self) -> None:
        await self._populate_authors()
        offset = 0
        limit = 50
        page = await self.queries.get_page(offset=offset, limit=limit)
        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page__too_big_offset_returns_empty_list(self) -> None:
        await self._populate_authors()
        page = await self.queries.get_page(offset=10000, limit=50)
        self.assertEmpty(page.items)

    async def test_get_page__negative_offset_raises_values_error(self) -> None:
        await self._populate_authors()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=50)


class TortoiseAuthorDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.queries = SQLAlchemyORMAuthorDetailsQueries(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _populate_author(self) -> AuthorModel:
        model_instance = AuthorModel(id=str(uuid4()), name="John Doe")
        self.session.add(model_instance)
        await self.session.flush()
        return model_instance

    async def test_get_author(self) -> None:
        saved_author_model_instance = await self._populate_author()
        author_id = saved_author_model_instance.id
        details = await self.queries.get_author(author_id=author_id)
        self.assertEqual(details.author_id, saved_author_model_instance.id)
        self.assertEqual(details.name, saved_author_model_instance.name)

    async def test_get_author__raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_author(author_id=non_existent_author_id)


class TortoiseAuthorRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.repository = SQLAlchemyORMAuthorRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    def _create_author(self) -> Author:
        return Author(id_=str(uuid4()), name="John Doe")

    async def _populate_author(self) -> AuthorModel:
        model_instance = AuthorModel(id=str(uuid4()), name="John Doe")
        self.session.add(model_instance)
        await self.session.flush()
        return model_instance

    async def _populate_authors(self) -> None:
        self.assertGreater(len(HUMAN_NAMES), 50)
        self.session.add_all(
            AuthorModel(id=str(uuid4()), name=name) for name in HUMAN_NAMES
        )
        await self.session.flush()

    async def _populate_authors_with_ids(self, id_list: list[str]) -> None:
        self.session.add_all(
            AuthorModel(id=author_id, name=name)
            for author_id, name in zip(id_list, HUMAN_NAMES)
        )
        await self.session.flush()

    def assertAuthorAndModelAreCompletelyEqual(
        self, author: Author, model_instance: AuthorModel
    ) -> None:
        self.assertEqual(author.id, model_instance.id)
        self.assertEqual(author.name, model_instance.name)

    async def assertAuthorDoesNotExist(self, author_id: str) -> None:
        self.assertIsNone(await self.session.get(AuthorModel, author_id))

    async def test_get_author_by_id(self) -> None:
        saved_author_model_instance = await self._populate_author()

        author_id = saved_author_model_instance.id
        author_from_db = await self.repository.get_author_by_id(author_id=author_id)

        self.assertAuthorAndModelAreCompletelyEqual(
            author_from_db, saved_author_model_instance
        )

    async def test_get_author_by_id__raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_author_by_id(non_existent_author_id)

    async def test_get_authors_list(self) -> None:
        await self._populate_authors()
        limit = 50
        authors_list = await self.repository.get_authors_list(offset=0, limit=limit)
        self.assertEqual(len(authors_list), limit)

    async def test_get_authors_list__too_big_offset_returns_empty_list(self) -> None:
        await self._populate_authors()
        authors_list = await self.repository.get_authors_list(offset=10000, limit=50)
        self.assertEmpty(authors_list)

    async def test_get_authors_list__negative_offset_raises_values_error(self) -> None:
        await self._populate_authors()
        with self.assertRaises(ValueError):
            await self.repository.get_authors_list(offset=-1, limit=50)

    async def test_get_authors_in_bulk(self) -> None:
        await self._populate_authors_with_ids(
            id_list=[
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
                "33333333-3333-3333-3333-333333333333",
                "44444444-4444-4444-4444-444444444444",
            ]
        )
        id_list = [
            "22222222-2222-2222-2222-222222222222",
            "44444444-4444-4444-4444-444444444444",
        ]
        authors_mapping = await self.repository.get_authors_in_bulk(id_list=id_list)
        for id_ in id_list:
            self.assertIn(id_, authors_mapping)
            self.assertIsNotNone(authors_mapping[id_])
            self.assertEqual(id_, authors_mapping[id_].id)

    async def test_get_authors_in_bulk__returns_empty_mapping_on_empty_id_list(
        self,
    ) -> None:
        authors_mapping = await self.repository.get_authors_in_bulk(id_list=[])
        self.assertEmpty(authors_mapping)

    async def test_get_authors_in_bulk__ignores_not_found(self) -> None:
        non_existent_id = str(uuid4())
        authors_mapping = await self.repository.get_authors_in_bulk(
            id_list=[non_existent_id]
        )
        self.assertNotIn(non_existent_id, authors_mapping)

    async def test_save__creates_if_does_not_exist(self) -> None:
        author = self._create_author()

        await self.repository.save(author)

        await self.session.flush()
        author_model_instance_from_get = await self.session.get(AuthorModel, author.id)
        self.assertIsNotNone(author_model_instance_from_get)
        self.assertAuthorAndModelAreCompletelyEqual(
            author, author_model_instance_from_get
        )

    async def test_save__updates_if_exists(self) -> None:
        author_model_instance = await self._populate_author()

        new_name = "Tim Gray"
        author = Author(id_=author_model_instance.id, name=new_name)
        await self.repository.save(author)

        await self.session.flush()
        author_model_instance_from_get = await self.session.get(AuthorModel, author.id)
        self.assertIsNotNone(author_model_instance_from_get)
        self.assertAuthorAndModelAreCompletelyEqual(
            author, author_model_instance_from_get
        )

    async def test_remove(self) -> None:
        author_model_instance = await self._populate_author()
        author = Author(id_=author_model_instance.id, name=author_model_instance.name)

        await self.repository.remove(author=author)

        await self.session.flush()
        await self.assertAuthorDoesNotExist(author.id)


class TortoiseDefaultAuthorRepositoryTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.repository = SQLAlchemyORMDefaultAuthorRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def test_get_default_author_id(self) -> None:
        user_id = str(uuid4())
        expected_author_id = str(uuid4())
        self.session.add(
            DefaultAuthorModel(user_id=user_id, author_id=expected_author_id)
        )
        await self.session.flush()

        returned_author_id = await self.repository.get_default_author_id(
            user_id=user_id
        )

        self.assertEqual(returned_author_id, expected_author_id)

    async def test_get_default_author_id__returns_null_if_never_set(self) -> None:
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

        await self.session.flush()
        saved_model_instance = await self.session.get(DefaultAuthorModel, user_id)
        self.assertIsNotNone(saved_model_instance)
        self.assertEqual(saved_model_instance.author_id, author_id)

    async def test_set_default_author_id__to_null(self) -> None:
        user_id = str(uuid4())
        await self.repository.set_default_author_id(user_id=user_id, author_id=None)

        await self.session.flush()
        saved_model_instance = await self.session.get(DefaultAuthorModel, user_id)
        self.assertIsNone(saved_model_instance)
