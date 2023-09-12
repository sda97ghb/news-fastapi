from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase, TestCase
from uuid import UUID, uuid4

from news_fastapi.adapters.persistence.tortoise.models import (
    AuthorModel,
    NewsArticleModel,
)
from news_fastapi.adapters.persistence.tortoise.news_article import (
    TortoiseNewsArticleDetailsQueries,
    TortoiseNewsArticleRepository,
    TortoiseNewsArticlesListQueries,
)
from news_fastapi.domain.news_article import NewsArticle, NewsArticleListFilter
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, TEXTS
from tests.utils import AssertMixin


class NewsArticleTestsMixin:
    def _create_valid_news_article_model_instance(
        self,
        news_article_id: str = "11111111-1111-1111-1111-111111111111",
        author_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> NewsArticleModel:
        return NewsArticleModel(
            id=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id=author_id,
            image_url="https://example.com/images/1234",
            image_description="The description of the image",
            image_author="Emma Brown",
            text="The text of the news article.",
            revoke_reason=None,
        )

    async def _populate_news_article(self) -> NewsArticleModel:
        model_instance = self._create_valid_news_article_model_instance()
        await model_instance.save()
        return model_instance

    async def _populate_news_articles(
        self,
        count: int = 30,
        author_id="22222222-2222-2222-2222-222222222222",
        predictable_news_article_id: bool = True,
    ) -> None:
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        for news_article_id, headline, text in zip(
            PREDICTABLE_IDS_A[:count], HEADLINES[:count], TEXTS[:count]
        ):
            news_article = NewsArticleModel(
                id=news_article_id if predictable_news_article_id else str(uuid4()),
                headline=headline,
                date_published=date_published,
                author_id=author_id,
                image_url="https://example.com/images/1234",
                image_description="The description of the image",
                image_author="Emma Brown",
                text=text,
                revoke_reason=None,
            )
            await news_article.save()

    async def _populate_good_news_article(
        self, author_id: str | None = None
    ) -> NewsArticleModel:
        published_model_instance = self._create_valid_news_article_model_instance(
            news_article_id=str(uuid4()),
            author_id=author_id if author_id else str(uuid4()),
        )
        published_model_instance.revoke_reason = None
        await published_model_instance.save()
        return published_model_instance

    async def _populate_revoked_news_article(
        self, author_id: str | None = None
    ) -> NewsArticleModel:
        revoked_model_instance = self._create_valid_news_article_model_instance(
            news_article_id=str(uuid4()),
            author_id=author_id if author_id else str(uuid4()),
        )
        revoked_model_instance.revoke_reason = "Fake"
        await revoked_model_instance.save()
        return revoked_model_instance

    async def _populate_author(self, author_id: str | None = None) -> AuthorModel:
        if author_id is None:
            author_id = str(uuid4())
        author_model_instance = AuthorModel(id=author_id, name="Lauren Brown")
        await author_model_instance.save()
        return author_model_instance


class TortoiseNewsArticlesListQueriesTests(
    NewsArticleTestsMixin, AssertMixin, IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.queries = TortoiseNewsArticlesListQueries()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_get_page(self) -> None:
        author_model_instance = await self._populate_author()
        await self._populate_news_articles(author_id=author_model_instance.id)
        offset = 0
        limit = 10
        page = await self.queries.get_page(offset=offset, limit=limit)
        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page_too_big_offset_returns_empty_list(
        self,
    ) -> None:
        author_model_instance = await self._populate_author()
        await self._populate_news_articles(author_id=author_model_instance.id)
        page = await self.queries.get_page(offset=10000, limit=10)
        self.assertEmpty(page.items)

    async def test_get_page_negative_offset_raises_value_error(
        self,
    ) -> None:
        author_model_instance = await self._populate_author()
        await self._populate_news_articles(author_id=author_model_instance.id)
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=10)

    async def test_get_page_filter_no_revoked(self) -> None:
        author_model_instance = await self._populate_author()
        all_authors = await AuthorModel.all()
        authors_in_bulk = await AuthorModel.in_bulk(
            id_list=[author_model_instance.id], field_name="id"
        )
        good_news_article_model_instance = await self._populate_good_news_article(
            author_id=author_model_instance.id
        )
        revoked_news_article_model_instance = await self._populate_revoked_news_article(
            author_id=author_model_instance.id
        )

        filter_ = NewsArticleListFilter(revoked="no_revoked")
        page = await self.queries.get_page(offset=0, limit=10, filter_=filter_)

        self.assertCountEqual(
            (item.news_article_id for item in page.items),
            [good_news_article_model_instance.id],
        )

    async def test_get_page_filter_only_revoked(self) -> None:
        author_model_instance = await self._populate_author()
        good_news_article_model_instance = await self._populate_good_news_article(
            author_id=author_model_instance.id
        )
        revoked_news_article_model_instance = await self._populate_revoked_news_article(
            author_id=author_model_instance.id
        )

        filter_ = NewsArticleListFilter(revoked="only_revoked")
        page = await self.queries.get_page(offset=0, limit=10, filter_=filter_)

        self.assertCountEqual(
            (item.news_article_id for item in page.items),
            [revoked_news_article_model_instance.id],
        )


class TortoiseNewsArticleDetailsQueriesTests(
    NewsArticleTestsMixin, IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.queries = TortoiseNewsArticleDetailsQueries()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    async def test_get_news_article(self) -> None:
        saved_model_instance = await self._populate_news_article()
        saved_author_model_instance = await self._populate_author(
            author_id=saved_model_instance.author_id
        )

        news_article_id = saved_model_instance.id
        details = await self.queries.get_news_article(news_article_id=news_article_id)

        self.assertEqual(details.news_article_id, saved_model_instance.id)
        self.assertEqual(details.headline, saved_model_instance.headline)
        self.assertEqual(details.date_published, saved_model_instance.date_published)
        self.assertEqual(details.author.author_id, saved_author_model_instance.id)
        self.assertEqual(details.author.name, saved_author_model_instance.name)
        self.assertEqual(details.image.url, saved_model_instance.image_url)
        self.assertEqual(
            details.image.description, saved_model_instance.image_description
        )
        self.assertEqual(details.image.author, saved_model_instance.image_author)
        self.assertEqual(details.text, saved_model_instance.text)
        self.assertEqual(details.revoke_reason, saved_model_instance.revoke_reason)

    async def test_get_news_article_by_id_raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_news_article(
                news_article_id=non_existent_news_article_id
            )


class TortoiseNewsArticleRepositoryTests(
    NewsArticleTestsMixin, AssertMixin, IsolatedAsyncioTestCase
):
    def setUp(self) -> None:
        self.repository = TortoiseNewsArticleRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    def _create_news_article(
        self, news_article_id: str = "11111111-1111-1111-1111-111111111111"
    ) -> NewsArticle:
        return NewsArticle(
            id_=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the news article.",
            revoke_reason=None,
        )

    def assertNewsArticlesAreCompletelyEqual(
        self, news_article_1: NewsArticle, news_article_2: NewsArticle
    ) -> None:
        self.assertEqual(news_article_1.id, news_article_2.id)
        self.assertEqual(news_article_1.headline, news_article_2.headline)
        self.assertEqual(news_article_1.date_published, news_article_2.date_published)
        self.assertEqual(news_article_1.author_id, news_article_2.author_id)
        self.assertEqual(news_article_1.text, news_article_2.text)
        self.assertEqual(news_article_1.revoke_reason, news_article_2.revoke_reason)

    def assertNewsArticleAndModelAreCompletelyEqual(
        self, news_article: NewsArticle, model_instance: NewsArticleModel
    ) -> None:
        self.assertEqual(news_article.id, model_instance.id)
        self.assertEqual(news_article.headline, model_instance.headline)
        self.assertEqual(news_article.date_published, model_instance.date_published)
        self.assertEqual(news_article.author_id, model_instance.author_id)
        self.assertEqual(news_article.image.url, model_instance.image_url)
        self.assertEqual(
            news_article.image.description, model_instance.image_description
        )
        self.assertEqual(news_article.image.author, model_instance.image_author)
        self.assertEqual(news_article.text, model_instance.text)
        self.assertEqual(news_article.revoke_reason, model_instance.revoke_reason)

    async def test_save_creates_if_does_not_exist(self) -> None:
        news_article = self._create_news_article()
        await self.repository.save(news_article)
        saved_news_article_model_instance = await NewsArticleModel.get(
            id=news_article.id
        )
        self.assertNewsArticleAndModelAreCompletelyEqual(
            news_article, saved_news_article_model_instance
        )

    async def test_save_updates_if_exists(self) -> None:
        news_article_model_instance = await self._populate_news_article()

        news_article = NewsArticle(
            id_=news_article_model_instance.id,
            headline="NEW Headline",
            date_published=DateTime.fromisoformat("2023-05-15T15:00:00+0000"),
            author_id="77777777-7777-7777-7777-777777777777",
            image=Image(
                url="https://example.com/images/99999-NEW",
                description="NEW description of the image",
                author="NEW Author",
            ),
            text="NEW text.",
            revoke_reason="Fake",
        )
        await self.repository.save(news_article)

        model_instance_from_db = await NewsArticleModel.get(id=news_article.id)
        self.assertNewsArticleAndModelAreCompletelyEqual(
            news_article, model_instance_from_db
        )

    async def test_get_news_articles_list(self) -> None:
        await self._populate_news_articles()
        limit = 10
        news_articles_list = await self.repository.get_news_articles_list(
            offset=0, limit=limit
        )
        self.assertEqual(len(news_articles_list), limit)

    async def test_get_news_articles_list_too_big_offset_returns_empty_list(
        self,
    ) -> None:
        await self._populate_news_articles()
        news_articles_list = await self.repository.get_news_articles_list(
            offset=10000, limit=10
        )
        self.assertEmpty(news_articles_list)

    async def test_get_news_articles_list_negative_offset_raises_value_error(
        self,
    ) -> None:
        await self._populate_news_articles()
        with self.assertRaises(ValueError):
            await self.repository.get_news_articles_list(offset=-1, limit=10)

    async def test_get_news_articles_list_filter_no_revoked(self) -> None:
        good_news_article_model_instance = await self._populate_good_news_article()
        revoked_news_article_model_instance = (
            await self._populate_revoked_news_article()
        )

        filter_ = NewsArticleListFilter(revoked="no_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticleAndModelAreCompletelyEqual(
            news_articles_list[0], good_news_article_model_instance
        )

    async def test_get_news_articles_list_filter_only_revoked(self) -> None:
        good_news_article_model_instance = await self._populate_good_news_article()
        revoked_news_article_model_instance = (
            await self._populate_revoked_news_article()
        )

        filter_ = NewsArticleListFilter(revoked="only_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticleAndModelAreCompletelyEqual(
            news_articles_list[0], revoked_news_article_model_instance
        )

    async def test_get_news_article_by_id(self) -> None:
        saved_model_instance = await self._populate_news_article()

        news_article_id = saved_model_instance.id
        news_article = await self.repository.get_news_article_by_id(news_article_id)

        self.assertNewsArticleAndModelAreCompletelyEqual(
            news_article, saved_model_instance
        )

    async def test_get_news_article_by_id_raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_news_article_by_id(
                news_article_id=non_existent_news_article_id
            )

    async def test_count_for_author(self) -> None:
        author_id = "11111111-1111-1111-1111-111111111111"
        another_author_id = "22222222-2222-2222-2222-222222222222"
        expected_count = 3
        await self._populate_news_articles(
            count=expected_count, author_id=author_id, predictable_news_article_id=False
        )
        await self._populate_news_articles(
            count=3, author_id=another_author_id, predictable_news_article_id=False
        )
        actual_count = await self.repository.count_for_author(author_id=author_id)
        self.assertEqual(actual_count, expected_count)

    async def test_count_for_author_returns_0_if_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        count = await self.repository.count_for_author(author_id=non_existent_author_id)
        self.assertEqual(count, 0)
