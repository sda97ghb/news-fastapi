from datetime import datetime as DateTime
from typing import Any
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy import RowMapping, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.sql.functions import count

from news_fastapi.adapters.persistence.sqlalchemy.draft import (
    SQLAlchemyDraftDetailsQueries,
    SQLAlchemyDraftRepository,
    SQLAlchemyDraftsListQueries,
)
from news_fastapi.adapters.persistence.sqlalchemy.mappers import (
    dispose_orm_mappers,
    setup_orm_mappers,
)
from news_fastapi.adapters.persistence.sqlalchemy.tables import drafts_table, metadata
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.sqlalchemy.fixtures import DataFixtures
from tests.utils import AssertMixin


class SQLAlchemyDraftsListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyDraftsListQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_page(self) -> None:
        await self.data_fixtures.populate_drafts()

        offset = 0
        limit = 10
        page = await self.queries.get_page(offset=offset, limit=limit)

        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page_too_big_offset_returns_empty_list(self) -> None:
        await self.data_fixtures.populate_drafts()
        page = await self.queries.get_page(offset=10000, limit=10)
        self.assertEmpty(page.items)

    async def test_get_page_negative_offset_raises_value_error(self) -> None:
        await self.data_fixtures.populate_drafts()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=10)


class SQLAlchemyDraftDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyDraftDetailsQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_draft(self) -> None:
        saved_author_row = await self.data_fixtures.populate_author()
        saved_draft_row = await self.data_fixtures.populate_draft(
            author_id=saved_author_row["id"]
        )

        details = await self.queries.get_draft(draft_id=saved_draft_row["id"])

        self.assertEqual(details.draft_id, saved_draft_row["id"])
        self.assertEqual(details.news_article_id, saved_draft_row["news_article_id"])
        self.assertEqual(
            details.created_by_user_id, saved_draft_row["created_by_user_id"]
        )
        self.assertEqual(details.headline, saved_draft_row["headline"])
        self.assertEqual(details.date_published, saved_draft_row["date_published"])
        self.assertEqual(details.author.author_id, saved_author_row["id"])
        self.assertEqual(details.author.name, saved_author_row["name"])
        self.assertEqual(details.image.url, saved_draft_row["image_url"])
        self.assertEqual(
            details.image.description, saved_draft_row["image_description"]
        )
        self.assertEqual(details.image.author, saved_draft_row["image_author"])
        self.assertEqual(details.text, saved_draft_row["text"])
        self.assertEqual(details.is_published, saved_draft_row["is_published"])

    async def test_get_draft_raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_draft(draft_id=non_existent_draft_id)


class SQLAlchemyDraftRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
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
        self.repository = SQLAlchemyDraftRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    @classmethod
    def tearDownClass(cls) -> None:
        dispose_orm_mappers()

    def assertDraftAndRowAreCompletelyEqual(
        self, draft: Draft, row: dict[str, Any] | RowMapping
    ) -> None:
        self.assertEqual(draft.id, row["id"])
        self.assertEqual(draft.news_article_id, row["news_article_id"])
        self.assertEqual(draft.headline, row["headline"])
        self.assertEqual(draft.date_published, row["date_published"])
        self.assertEqual(draft.author_id, row["author_id"])
        if draft.image is None:
            self.assertIsNone(row["image_url"])
            self.assertIsNone(row["image_description"])
            self.assertIsNone(row["image_author"])
        else:
            self.assertEqual(draft.image.url, row["image_url"])
            self.assertEqual(draft.image.description, row["image_description"])
            self.assertEqual(draft.image.author, row["image_author"])
        self.assertEqual(draft.text, row["text"])
        self.assertEqual(draft.created_by_user_id, row["created_by_user_id"])
        self.assertEqual(draft.is_published, row["is_published"])

    async def assertDraftDoesNotExist(self, draft_id: str) -> None:
        self.assertIsNone(await self.session.get(Draft, draft_id))

    async def test_save__creates_if_does_not_exist(self) -> None:
        draft = self.data_fixtures.create_draft_entity()

        await self.repository.save(draft)

        await self.session.flush()
        result = await self.session.execute(
            select(drafts_table).where(drafts_table.c.id == draft.id)
        )
        saved_row = result.mappings().one()
        self.assertDraftAndRowAreCompletelyEqual(draft, saved_row)

    async def test_save__updates_if_exists(self) -> None:
        saved_row = await self.data_fixtures.populate_draft()

        draft = await self.repository.get_draft_by_id(draft_id=saved_row["id"])
        draft.headline = "NEW Headline"
        draft.date_published = DateTime.fromisoformat("2023-03-11T15:00:00+0000")
        draft.author_id = "77777777-7777-7777-7777-777777777777"
        draft.image = Image(
            url="https://example.com/images/99999-NEW",
            description="NEW description of the image",
            author="NEW Author",
        )
        draft.text = "NEW text."
        await self.repository.save(draft)

        await self.session.flush()
        result = await self.session.execute(
            select(drafts_table).where(drafts_table.c.id == draft.id)
        )
        saved_row = result.mappings().one()
        self.assertDraftAndRowAreCompletelyEqual(draft, saved_row)

    async def test_get_drafts_list(self) -> None:
        await self.data_fixtures.populate_drafts()
        limit = 10
        drafts_list = await self.repository.get_drafts_list(offset=0, limit=limit)
        self.assertEqual(len(drafts_list), limit)

    async def test_get_drafts_list__too_big_offset_returns_empty_list(self) -> None:
        await self.data_fixtures.populate_drafts()
        drafts_list = await self.repository.get_drafts_list(offset=10000, limit=10)
        self.assertEmpty(drafts_list)

    async def test_get_drafts_list__negative_offset_raises_value_error(self) -> None:
        await self.data_fixtures.populate_drafts()
        with self.assertRaises(ValueError):
            await self.repository.get_drafts_list(offset=-1, limit=10)

    async def test_get_draft_by_id(self) -> None:
        saved_row = await self.data_fixtures.populate_draft()

        draft_from_db = await self.repository.get_draft_by_id(draft_id=saved_row["id"])

        self.assertDraftAndRowAreCompletelyEqual(draft_from_db, saved_row)

    async def test_get_draft_by_id__raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_draft_by_id(draft_id=non_existent_draft_id)

    async def test_get_not_published_draft_by_news_id(self) -> None:
        saved_row = await self.data_fixtures.populate_draft(
            news_article_id="77777777-7777-7777-7777-777777777777", is_published=False
        )
        draft_from_db = await self.repository.get_not_published_draft_by_news_id(
            news_article_id=saved_row["news_article_id"]
        )
        self.assertDraftAndRowAreCompletelyEqual(draft_from_db, saved_row)

    async def test_get_not_published_draft_by_news_id__raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_not_published_draft_by_news_id(
                non_existent_news_article_id
            )

    async def test_get_drafts_for_author(self) -> None:
        author_id = "11111111-1111-1111-1111-111111111111"
        await self.data_fixtures.populate_drafts(author_id=author_id)

        drafts_list = await self.repository.get_drafts_for_author(author_id=author_id)

        self.assertNotEmpty(drafts_list)
        for draft in drafts_list:
            self.assertEqual(draft.author_id, author_id)
        result = await self.session.execute(
            select(count())
            .select_from(drafts_table)
            .where(drafts_table.c.author_id == author_id)
        )
        self.assertEqual(len(drafts_list), result.scalar())

    async def test_get_drafts_for_author__returns_empty_list_on_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        drafts_list = await self.repository.get_drafts_for_author(
            non_existent_author_id
        )
        self.assertEmpty(drafts_list)

    async def test_delete(self) -> None:
        saved_row = await self.data_fixtures.populate_draft()
        draft = await self.repository.get_draft_by_id(saved_row["id"])

        await self.repository.delete(draft)

        await self.session.flush()
        await self.assertDraftDoesNotExist(saved_row["id"])
