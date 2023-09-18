from datetime import datetime as DateTime
from typing import Any
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy import RowMapping, insert, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy.mappers import (
    dispose_orm_mappers,
    setup_orm_mappers,
)
from news_fastapi.adapters.persistence.sqlalchemy.news_article import (
    SQLAlchemyNewsArticleDetailsQueries,
    SQLAlchemyNewsArticleRepository,
    SQLAlchemyNewsArticlesListQueries,
)
from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    metadata,
    news_articles_table,
)
from news_fastapi.domain.news_article import NewsArticle, NewsArticleListFilter
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.sqlalchemy.fixtures import DataFixtures
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, TEXTS
from tests.utils import AssertMixin


class TortoiseNewsArticlesListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyNewsArticlesListQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_page(self) -> None:
        saved_author_row = await self.data_fixtures.populate_author()
        await self.data_fixtures.populate_news_articles(
            author_id=saved_author_row["id"]
        )

        offset = 0
        limit = 10
        page = await self.queries.get_page(offset=offset, limit=limit)

        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page__too_big_offset_returns_empty_list(
        self,
    ) -> None:
        saved_author_row = await self.data_fixtures.populate_author()
        await self.data_fixtures.populate_news_articles(
            author_id=saved_author_row["id"]
        )

        page = await self.queries.get_page(offset=10000, limit=10)

        self.assertEmpty(page.items)

    async def test_get_page__negative_offset_raises_value_error(
        self,
    ) -> None:
        saved_author_row = await self.data_fixtures.populate_author()
        await self.data_fixtures.populate_news_articles(
            author_id=saved_author_row["id"]
        )
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=10)

    async def test_get_page__filter_no_revoked(self) -> None:
        author_row = await self.data_fixtures.populate_author()
        good_news_article_row = (
            await self.data_fixtures.populate_not_revoked_news_article(
                author_id=author_row["id"]
            )
        )
        revoked_news_article_row = (
            await self.data_fixtures.populate_revoked_news_article(
                author_id=author_row["id"]
            )
        )

        filter_ = NewsArticleListFilter(revoked="no_revoked")
        page = await self.queries.get_page(offset=0, limit=10, filter_=filter_)

        self.assertCountEqual(
            (item.news_article_id for item in page.items),
            [good_news_article_row["id"]],
        )

    async def test_get_page__filter_only_revoked(self) -> None:
        author_row = await self.data_fixtures.populate_author()
        good_news_article_row = (
            await self.data_fixtures.populate_not_revoked_news_article(
                author_id=author_row["id"]
            )
        )
        revoked_news_article_row = (
            await self.data_fixtures.populate_revoked_news_article(
                author_id=author_row["id"]
            )
        )

        filter_ = NewsArticleListFilter(revoked="only_revoked")
        page = await self.queries.get_page(offset=0, limit=10, filter_=filter_)

        self.assertCountEqual(
            (item.news_article_id for item in page.items),
            [revoked_news_article_row["id"]],
        )


class TortoiseNewsArticleDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.connection = await self.engine.connect()
        self.data_fixtures = DataFixtures(connection_or_session=self.connection)
        self.queries = SQLAlchemyNewsArticleDetailsQueries(connection=self.connection)

    async def asyncTearDown(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def test_get_news_article(self) -> None:
        saved_author_row = await self.data_fixtures.populate_author()
        saved_row = await self.data_fixtures.populate_news_article(
            author_id=saved_author_row["id"]
        )

        details = await self.queries.get_news_article(news_article_id=saved_row["id"])

        self.assertEqual(details.news_article_id, saved_row["id"])
        self.assertEqual(details.headline, saved_row["headline"])
        self.assertEqual(details.date_published, saved_row["date_published"])
        self.assertEqual(details.author.author_id, saved_author_row["id"])
        self.assertEqual(details.author.name, saved_author_row["name"])
        self.assertEqual(details.image.url, saved_row["image_url"])
        self.assertEqual(details.image.description, saved_row["image_description"])
        self.assertEqual(details.image.author, saved_row["image_author"])
        self.assertEqual(details.text, saved_row["text"])
        self.assertEqual(details.revoke_reason, saved_row["revoke_reason"])

    async def test_get_news_article__raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_news_article(
                news_article_id=non_existent_news_article_id
            )


class TortoiseNewsArticleRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
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
        self.repository = SQLAlchemyNewsArticleRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    @classmethod
    def tearDownClass(cls) -> None:
        dispose_orm_mappers()

    def assertNewsArticleAndRowAreCompletelyEqual(
        self, news_article: NewsArticle, row: dict[str, Any] | RowMapping
    ) -> None:
        self.assertEqual(news_article.id, row["id"])
        self.assertEqual(news_article.headline, row["headline"])
        self.assertEqual(news_article.date_published, row["date_published"])
        self.assertEqual(news_article.author_id, row["author_id"])
        self.assertEqual(news_article.image.url, row["image_url"])
        self.assertEqual(news_article.image.description, row["image_description"])
        self.assertEqual(news_article.image.author, row["image_author"])
        self.assertEqual(news_article.text, row["text"])
        self.assertEqual(news_article.revoke_reason, row["revoke_reason"])

    async def test_save__creates_if_does_not_exist(self) -> None:
        news_article = self.data_fixtures.create_news_article_entity()

        await self.repository.save(news_article)

        await self.session.flush()
        result = await self.session.execute(
            select(news_articles_table).where(
                news_articles_table.c.id == news_article.id
            )
        )
        saved_row = result.mappings().one()
        self.assertNewsArticleAndRowAreCompletelyEqual(news_article, saved_row)

    async def test_save__updates_if_exists(self) -> None:
        saved_row = await self.data_fixtures.populate_news_article()

        news_article = await self.repository.get_news_article_by_id(
            news_article_id=saved_row["id"]
        )
        news_article.headline = "NEW Headline"
        news_article.date_published = DateTime.fromisoformat("2023-05-15T15:00:00+0000")
        news_article.author_id = "77777777-7777-7777-7777-777777777777"
        news_article.image = Image(
            url="https://example.com/images/99999-NEW",
            description="NEW description of the image",
            author="NEW Author",
        )
        news_article.text = "NEW text."
        news_article.revoke(reason="Fake")
        await self.repository.save(news_article)

        await self.session.flush()
        result = await self.session.execute(
            select(news_articles_table).where(
                news_articles_table.c.id == news_article.id
            )
        )
        saved_row = result.mappings().one()
        self.assertNewsArticleAndRowAreCompletelyEqual(news_article, saved_row)

    async def test_get_news_articles_list(self) -> None:
        await self.data_fixtures.populate_news_articles()

        limit = 10
        news_articles_list = await self.repository.get_news_articles_list(
            offset=0, limit=limit
        )

        self.assertEqual(len(news_articles_list), limit)

    async def test_get_news_articles_list_too_big_offset_returns_empty_list(
        self,
    ) -> None:
        await self.data_fixtures.populate_news_articles()
        news_articles_list = await self.repository.get_news_articles_list(
            offset=10000, limit=10
        )
        self.assertEmpty(news_articles_list)

    async def test_get_news_articles_list_negative_offset_raises_value_error(
        self,
    ) -> None:
        await self.data_fixtures.populate_news_articles()
        with self.assertRaises(ValueError):
            await self.repository.get_news_articles_list(offset=-1, limit=10)

    async def test_get_news_articles_list_filter_no_revoked(self) -> None:
        author_id = str(uuid4())
        good_news_article_row = (
            await self.data_fixtures.populate_not_revoked_news_article(
                author_id=author_id
            )
        )
        revoked_news_article_row = (
            await self.data_fixtures.populate_revoked_news_article(author_id=author_id)
        )

        filter_ = NewsArticleListFilter(revoked="no_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticleAndRowAreCompletelyEqual(
            news_articles_list[0], good_news_article_row
        )

    async def test_get_news_articles_list_filter_only_revoked(self) -> None:
        author_id = str(uuid4())
        good_news_article_row = (
            await self.data_fixtures.populate_not_revoked_news_article(
                author_id=author_id
            )
        )
        revoked_news_article_row = (
            await self.data_fixtures.populate_revoked_news_article(author_id=author_id)
        )

        filter_ = NewsArticleListFilter(revoked="only_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticleAndRowAreCompletelyEqual(
            news_articles_list[0], revoked_news_article_row
        )

    async def test_get_news_article_by_id(self) -> None:
        saved_row = await self.data_fixtures.populate_news_article()

        news_article = await self.repository.get_news_article_by_id(
            news_article_id=saved_row["id"]
        )

        self.assertNewsArticleAndRowAreCompletelyEqual(news_article, saved_row)

    async def test_get_news_article_by_id__raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_news_article_by_id(
                news_article_id=non_existent_news_article_id
            )

    async def test_count_for_author(self) -> None:
        author_id = "11111111-1111-1111-1111-111111111111"
        another_author_id = "22222222-2222-2222-2222-222222222222"
        expected_count = 3
        await self.data_fixtures.populate_news_articles(
            count=expected_count, author_id=author_id, predictable_news_article_id=False
        )
        await self.data_fixtures.populate_news_articles(
            count=3, author_id=another_author_id, predictable_news_article_id=False
        )
        actual_count = await self.repository.count_for_author(author_id=author_id)
        self.assertEqual(actual_count, expected_count)

    async def test_count_for_author_returns_0_if_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        count = await self.repository.count_for_author(author_id=non_existent_author_id)
        self.assertEqual(count, 0)
