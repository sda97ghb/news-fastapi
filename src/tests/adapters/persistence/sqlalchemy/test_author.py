from typing import Any, cast
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy import Row, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy.author import (
    SQLAlchemyAuthorDetailsQueries,
    SQLAlchemyAuthorRepository,
    SQLAlchemyAuthorsListQueries,
    SQLAlchemyDefaultAuthorRepository,
)
from news_fastapi.adapters.persistence.sqlalchemy.mappers import (
    dispose_orm_mappers,
    setup_orm_mappers,
)
from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    default_authors_table,
    metadata,
)
from news_fastapi.domain.author import Author
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.sqlalchemy.fixtures import DataFixtures
from tests.utils import AssertMixin


class SQLAlchemyAuthorsListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyAuthorsListQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_page(self) -> None:
        await self.data_fixtures.populate_authors()

        offset = 0
        limit = 50
        page = await self.queries.get_page(offset=offset, limit=limit)

        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page__too_big_offset_returns_empty_list(self) -> None:
        await self.data_fixtures.populate_authors()
        page = await self.queries.get_page(offset=10000, limit=50)
        self.assertEmpty(page.items)

    async def test_get_page__negative_offset_raises_values_error(self) -> None:
        await self.data_fixtures.populate_authors()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=50)


class SQLAlchemyAuthorDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyAuthorDetailsQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_author(self) -> None:
        saved_row = await self.data_fixtures.populate_author()
        details = await self.queries.get_author(author_id=saved_row["id"])
        self.assertEqual(details.author_id, saved_row["id"])
        self.assertEqual(details.name, saved_row["name"])

    async def test_get_author_raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_author(author_id=non_existent_author_id)


class SQLAlchemyAuthorRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        setup_orm_mappers()

    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.data_fixtures = DataFixtures(connection_or_session=self.session)
        self.repository = SQLAlchemyAuthorRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    @classmethod
    def tearDownClass(cls) -> None:
        dispose_orm_mappers()

    def assertAuthorAndRowAreCompletelyEqual(
        self, author: Author, row: dict[str, Any] | Row
    ) -> None:
        if isinstance(row, Row):
            row = {"id": row.id, "name": row.name}
        self.assertEqual(author.id, row["id"])
        self.assertEqual(author.name, row["name"])

    async def test_get_author_by_id(self) -> None:
        saved_row = await self.data_fixtures.populate_author()

        author_id = saved_row["id"]
        author_from_db = await self.repository.get_author_by_id(author_id=author_id)

        self.assertAuthorAndRowAreCompletelyEqual(author_from_db, saved_row)

    async def test_get_author_by_id__raises_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_author_by_id(non_existent_author_id)

    async def test_get_authors_list(self) -> None:
        await self.data_fixtures.populate_authors()
        limit = 50
        authors_list = await self.repository.get_authors_list(offset=0, limit=limit)
        self.assertEqual(len(authors_list), limit)

    async def test_get_authors_list__too_big_offset_returns_empty_list(self) -> None:
        await self.data_fixtures.populate_authors()
        authors_list = await self.repository.get_authors_list(offset=10000, limit=50)
        self.assertEmpty(authors_list)

    async def test_get_authors_list__negative_offset_raises_values_error(self) -> None:
        await self.data_fixtures.populate_authors()
        with self.assertRaises(ValueError):
            await self.repository.get_authors_list(offset=-1, limit=50)

    async def test_get_authors_in_bulk(self) -> None:
        await self.data_fixtures.populate_authors_with_ids(
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
        author = Author(id_=str(uuid4()), name="John Doe")
        await self.repository.save(author)

        await self.session.flush()
        result = await self.session.execute(
            select(authors_table).where(authors_table.c.id == author.id)
        )
        saved_row = result.one()
        self.assertAuthorAndRowAreCompletelyEqual(author, saved_row)

    async def test_save__updates_if_exists(self) -> None:
        saved_row = await self.data_fixtures.populate_author()
        author_id = cast(str, saved_row["id"])

        author = await self.repository.get_author_by_id(author_id)
        author.name = "NEW NAME"
        await self.repository.save(author)

        await self.session.flush()
        result = await self.session.execute(
            select(authors_table).where(authors_table.c.id == author_id)
        )
        updated_row = result.one()
        self.assertAuthorAndRowAreCompletelyEqual(author, updated_row)

    async def test_remove(self) -> None:
        await self.data_fixtures.populate_authors_with_ids(
            id_list=[
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            ]
        )

        author = await self.repository.get_author_by_id(
            author_id="11111111-1111-1111-1111-111111111111"
        )
        await self.repository.remove(author=author)

        await self.session.flush()
        result = await self.session.execute(
            select(authors_table).where(
                authors_table.c.id == "11111111-1111-1111-1111-111111111111"
            )
        )
        self.assertIsNone(result.one_or_none())
        result = await self.session.execute(
            select(authors_table).where(
                authors_table.c.id == "22222222-2222-2222-2222-222222222222"
            )
        )
        self.assertIsNotNone(result.one_or_none())


class SQLAlchemyDefaultAuthorRepositoryTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.repository = SQLAlchemyDefaultAuthorRepository(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_default_author_id(self) -> None:
        user_id = str(uuid4())
        expected_author_id = str(uuid4())
        await self.connection.execute(
            insert(default_authors_table).values(
                user_id=user_id, author_id=expected_author_id
            )
        )

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

        result = await self.connection.execute(
            select(default_authors_table.c.author_id).where(
                default_authors_table.c.user_id == user_id
            )
        )
        saved_author_id = result.scalar_one_or_none()
        self.assertEqual(saved_author_id, author_id)

    async def test_set_default_author_id__to_null(self) -> None:
        user_id = str(uuid4())
        await self.repository.set_default_author_id(user_id=user_id, author_id=None)

        result = await self.connection.execute(
            select(default_authors_table.c.author_id).where(
                default_authors_table.c.user_id == user_id
            )
        )
        saved_author_id = result.scalar_one_or_none()
        self.assertIsNone(saved_author_id)
