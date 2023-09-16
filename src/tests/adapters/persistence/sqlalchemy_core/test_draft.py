from datetime import datetime as DateTime
from typing import Any
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy import RowMapping, insert, select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.functions import count

from news_fastapi.adapters.persistence.sqlalchemy_core.draft import (
    SQLAlchemyDraftDetailsQueries,
    SQLAlchemyDraftRepository,
    SQLAlchemyDraftsListQueries,
)
from news_fastapi.adapters.persistence.sqlalchemy_core.tables import (
    authors,
    drafts,
    metadata,
)
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, PREDICTABLE_IDS_B, TEXTS
from tests.utils import AssertMixin


class SQLAlchemyDraftsListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        self.connection = await self.engine.connect()
        await self.connection.run_sync(metadata.create_all)
        self.queries = SQLAlchemyDraftsListQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()

    async def _populate_drafts(
        self,
        author_id: str = "11111111-1111-1111-1111-111111111111",
        user_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> None:
        count = 30
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        await self.connection.execute(
            insert(drafts),
            [
                dict(
                    id=draft_id,
                    news_article_id=news_article_id,
                    headline=headline,
                    date_published=date_published,
                    author_id=author_id,
                    image_url="https://example.com/images/1234",
                    image_description="The description of the image",
                    image_author="Emma Brown",
                    text=text,
                    created_by_user_id=user_id,
                    is_published=False,
                )
                for draft_id, news_article_id, headline, text in zip(
                    PREDICTABLE_IDS_A[:count],
                    PREDICTABLE_IDS_B[:count],
                    HEADLINES[:count],
                    TEXTS[:count],
                )
            ],
        )

    async def test_get_page(self) -> None:
        await self._populate_drafts()
        offset = 0
        limit = 10
        page = await self.queries.get_page(offset=offset, limit=limit)
        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page_too_big_offset_returns_empty_list(self) -> None:
        await self._populate_drafts()
        page = await self.queries.get_page(offset=10000, limit=10)
        self.assertEmpty(page.items)

    async def test_get_page_negative_offset_raises_value_error(self) -> None:
        await self._populate_drafts()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=10)


class SQLAlchemyDraftDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        self.connection = await self.engine.connect()
        await self.connection.run_sync(metadata.create_all)
        self.queries = SQLAlchemyDraftDetailsQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()

    async def _populate_author(self) -> dict[str, Any]:
        row = {"id": str(uuid4()), "name": "John Doe"}
        await self.connection.execute(insert(authors), row)
        return row

    async def _populate_draft(self, author_id: str) -> dict[str, Any]:
        row = {
            "id": str(uuid4()),
            "news_article_id": str(uuid4()),
            "headline": "The Headline",
            "date_published": DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            "author_id": author_id,
            "image_url": "https://example.com/images/1234",
            "image_description": "Image description",
            "image_author": "Image author",
            "text": "The text of the article",
            "created_by_user_id": str(uuid4()),
            "is_published": False,
        }
        await self.connection.execute(insert(drafts), row)
        return row

    async def test_get_draft(self) -> None:
        saved_author_row = await self._populate_author()
        saved_draft_row = await self._populate_draft(author_id=saved_author_row["id"])

        draft_id = saved_draft_row["id"]
        details = await self.queries.get_draft(draft_id=draft_id)
        self.assertEqual(details.draft_id, draft_id)
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
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        self.connection = await self.engine.connect()
        await self.connection.run_sync(metadata.create_all)
        self.repository = SQLAlchemyDraftRepository(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()

    def _create_draft(self) -> Draft:
        return Draft(
            id_="11111111-1111-1111-1111-111111111111",
            news_article_id="22222222-2222-2222-2222-222222222222",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="33333333-3333-3333-3333-333333333333",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the draft.",
            created_by_user_id="44444444-4444-4444-4444-444444444444",
            is_published=False,
        )

    async def _populate_draft(
        self,
        author_id: str | None = None,
        news_article_id: str | None = None,
        is_published: bool = False,
    ) -> dict[str, Any]:
        if author_id is None:
            author_id = str(uuid4())
        if news_article_id is None:
            news_article_id = str(uuid4())
        row = {
            "id": str(uuid4()),
            "news_article_id": news_article_id,
            "headline": "The Headline",
            "date_published": DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            "author_id": author_id,
            "image_url": "https://example.com/images/1234",
            "image_description": "Image description",
            "image_author": "Image author",
            "text": "The text of the article",
            "created_by_user_id": str(uuid4()),
            "is_published": is_published,
        }
        await self.connection.execute(insert(drafts), row)
        return row

    async def _populate_drafts(
        self,
        author_id: str = "11111111-1111-1111-1111-111111111111",
        user_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> None:
        count = 30
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        await self.connection.execute(
            insert(drafts),
            [
                dict(
                    id=draft_id,
                    news_article_id=news_article_id,
                    headline=headline,
                    date_published=date_published,
                    author_id=author_id,
                    image_url="https://example.com/images/1234",
                    image_description="The description of the image",
                    image_author="Emma Brown",
                    text=text,
                    created_by_user_id=user_id,
                    is_published=False,
                )
                for draft_id, news_article_id, headline, text in zip(
                    PREDICTABLE_IDS_A[:count],
                    PREDICTABLE_IDS_B[:count],
                    HEADLINES[:count],
                    TEXTS[:count],
                )
            ],
        )

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
        result = await self.connection.execute(
            select(drafts).where(drafts.c.id == draft_id)
        )
        self.assertIsNone(result.one_or_none())

    async def test_save__creates_if_does_not_exist(self) -> None:
        draft = self._create_draft()
        await self.repository.save(draft)
        result = await self.connection.execute(
            select(drafts).where(drafts.c.id == draft.id)
        )
        saved_row = result.mappings().one()
        self.assertDraftAndRowAreCompletelyEqual(draft, saved_row)

    async def test_save__updates_if_exists(self) -> None:
        saved_row = await self._populate_draft()

        draft = Draft(
            id_=saved_row["id"],
            news_article_id=saved_row["news_article_id"],
            created_by_user_id=saved_row["created_by_user_id"],
            headline="NEW Headline",
            date_published=DateTime.fromisoformat("2023-03-11T15:00:00+0000"),
            author_id="77777777-7777-7777-7777-777777777777",
            image=Image(
                url="https://example.com/images/99999-NEW",
                description="NEW description of the image",
                author="NEW Author",
            ),
            text="NEW text.",
            is_published=saved_row["is_published"],
        )
        await self.repository.save(draft)

        result = await self.connection.execute(
            select(drafts).where(drafts.c.id == draft.id)
        )
        saved_row = result.mappings().one()
        self.assertDraftAndRowAreCompletelyEqual(draft, saved_row)

    async def test_get_drafts_list(self) -> None:
        await self._populate_drafts()
        limit = 10
        drafts_list = await self.repository.get_drafts_list(offset=0, limit=limit)
        self.assertEqual(len(drafts_list), limit)

    async def test_get_drafts_list_too_big_offset_returns_empty_list(self) -> None:
        await self._populate_drafts()
        drafts_list = await self.repository.get_drafts_list(offset=10000, limit=10)
        self.assertEmpty(drafts_list)

    async def test_get_drafts_list_negative_offset_raises_value_error(self) -> None:
        await self._populate_drafts()
        with self.assertRaises(ValueError):
            await self.repository.get_drafts_list(offset=-1, limit=10)

    async def test_get_draft_by_id(self) -> None:
        saved_row = await self._populate_draft()

        draft_id = saved_row["id"]
        draft_from_db = await self.repository.get_draft_by_id(draft_id=draft_id)

        self.assertDraftAndRowAreCompletelyEqual(draft_from_db, saved_row)

    async def test_get_draft_by_id_raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_draft_by_id(draft_id=non_existent_draft_id)

    async def test_get_not_published_draft_by_news_id(self) -> None:
        saved_row = await self._populate_draft(
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
        await self._populate_drafts(author_id=author_id)

        drafts_list = await self.repository.get_drafts_for_author(author_id=author_id)

        self.assertNotEmpty(drafts_list)
        for draft in drafts_list:
            self.assertEqual(draft.author_id, author_id)
        result = await self.connection.execute(
            select(count()).select_from(drafts).where(drafts.c.author_id == author_id)
        )
        self.assertEqual(len(drafts_list), result.scalar())

    async def test_get_drafts_for_author__returns_empty_list_on_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        drafts_list = await self.repository.get_drafts_for_author(
            non_existent_author_id
        )
        self.assertEmpty(drafts_list)

    async def test_delete(self) -> None:
        saved_row = await self._populate_draft()

        draft = await self.repository.get_draft_by_id(saved_row["id"])
        await self.repository.delete(draft)

        await self.assertDraftDoesNotExist(saved_row["id"])
