from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase, TestCase
from uuid import UUID, uuid4

from news_fastapi.adapters.persistence.tortoise.news import (
    TortoiseNewsArticle,
    TortoiseNewsArticleFactory,
    TortoiseNewsArticleRepository,
)
from news_fastapi.domain.news_article import NewsArticle, NewsArticleListFilter
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, TEXTS
from tests.utils import AssertMixin


class TortoiseNewsArticleFactoryTests(TestCase):
    def setUp(self) -> None:
        self.factory = TortoiseNewsArticleFactory()

    def test_create_news_article(self) -> None:
        news_article_id = "11111111-1111-1111-1111-111111111111"
        headline = "The Headline"
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        author_id = "22222222-2222-2222-2222-222222222222"
        image = Image(
            url="https://example.com/images/1234",
            description="The description of the image",
            author="Emma Brown",
        )
        text = "The text of the article."
        revoke_reason = "Fake"
        news_article = self.factory.create_news_article(
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            image=image,
            text=text,
            revoke_reason=revoke_reason,
        )
        self.assertEqual(news_article.id, news_article_id)
        self.assertEqual(news_article.headline, headline)
        self.assertEqual(news_article.date_published, date_published)
        self.assertEqual(news_article.author_id, author_id)
        self.assertEqual(news_article.image, image)
        self.assertEqual(news_article.text, text)
        self.assertEqual(news_article.revoke_reason, revoke_reason)


class TortoiseNewsArticleRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = TortoiseNewsArticleRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    def _create_valid_news_article(
        self, news_article_id: str = "11111111-1111-1111-1111-111111111111"
    ) -> TortoiseNewsArticle:
        news_article = TortoiseNewsArticle(
            id=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
            text="The text of the news article.",
            revoke_reason=None,
        )
        news_article.image = Image(
            url="https://example.com/images/1234",
            description="The description of the image",
            author="Emma Brown",
        )
        return news_article

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
            news_article = TortoiseNewsArticle(
                id=news_article_id if predictable_news_article_id else str(uuid4()),
                headline=headline,
                date_published=date_published,
                author_id=author_id,
                text=text,
                revoke_reason=None,
            )
            news_article.image = Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            )
            await news_article.save()

    async def _populate_good_news_article(self) -> TortoiseNewsArticle:
        published_news_article = self._create_valid_news_article(
            news_article_id=str(uuid4())
        )
        published_news_article.revoke_reason = None
        await published_news_article.save()
        return published_news_article

    async def _populate_revoked_news_article(self) -> TortoiseNewsArticle:
        revoked_news_article = self._create_valid_news_article(
            news_article_id=str(uuid4())
        )
        revoked_news_article.revoke_reason = "Fake"
        await revoked_news_article.save()
        return revoked_news_article

    def assertNewsArticlesAreCompletelyEqual(
        self, news_article_1: NewsArticle, news_article_2: NewsArticle
    ) -> None:
        self.assertEqual(news_article_1.id, news_article_2.id)
        self.assertEqual(news_article_1.headline, news_article_2.headline)
        self.assertEqual(news_article_1.date_published, news_article_2.date_published)
        self.assertEqual(news_article_1.author_id, news_article_2.author_id)
        self.assertEqual(news_article_1.text, news_article_2.text)
        self.assertEqual(news_article_1.revoke_reason, news_article_2.revoke_reason)

    async def test_next_identity(self) -> None:
        id_1 = await self.repository.next_identity()
        id_2 = await self.repository.next_identity()
        for id_ in [id_1, id_2]:
            try:
                UUID(id_)
            except ValueError:
                self.fail(f"next_identity returned badly formed UUID: {id_}")
        self.assertNotEqual(id_1, id_2)

    async def test_save_creates_if_does_not_exist(self) -> None:
        news_article = self._create_valid_news_article()
        await news_article.save()
        saved_news_article = await TortoiseNewsArticle.get(id=news_article.id)
        self.assertNewsArticlesAreCompletelyEqual(saved_news_article, news_article)

    async def test_save_updates_if_exists(self) -> None:
        news_article = self._create_valid_news_article()
        await news_article.save()

        news_article.headline = "NEW Headline"
        news_article.date_published = DateTime.fromisoformat("2023-05-15T15:00:00+0000")
        news_article.author_id = "77777777-7777-7777-7777-777777777777"
        news_article.image = Image(
            url="https://example.com/images/99999-NEW",
            description="NEW description of the image",
            author="NEW Author",
        )
        news_article.text = "NEW text."
        news_article.revoke_reason = "Fake"
        await self.repository.save(news_article)

        news_article_from_db = await TortoiseNewsArticle.get(id=news_article.id)
        self.assertNewsArticlesAreCompletelyEqual(news_article_from_db, news_article)

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
        good_news_article = await self._populate_good_news_article()
        revoked_news_article = await self._populate_revoked_news_article()

        filter_ = NewsArticleListFilter(revoked="no_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticlesAreCompletelyEqual(
            news_articles_list[0], good_news_article
        )

    async def test_get_news_articles_list_filter_only_revoked(self) -> None:
        good_news_article = await self._populate_good_news_article()
        revoked_news_article = await self._populate_revoked_news_article()

        filter_ = NewsArticleListFilter(revoked="only_revoked")
        news_articles_list = list(
            await self.repository.get_news_articles_list(
                offset=0, limit=10, filter_=filter_
            )
        )

        self.assertEqual(len(news_articles_list), 1)
        self.assertNewsArticlesAreCompletelyEqual(
            news_articles_list[0], revoked_news_article
        )

    async def test_get_news_article_by_id(self) -> None:
        saved_news_article = self._create_valid_news_article()
        await saved_news_article.save()

        news_article_id = saved_news_article.id
        news_article_from_db = await self.repository.get_news_article_by_id(
            news_article_id
        )

        self.assertNewsArticlesAreCompletelyEqual(
            news_article_from_db, saved_news_article
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
