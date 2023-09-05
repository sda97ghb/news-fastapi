from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.core.news.commands import RevokeNewsArticleService
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.value_objects import Image
from tests.core.fixtures import NewsAuthFixture, TransactionManagerFixture
from tests.domain.fixtures import NewsArticleRepositoryFixture


class RevokeNewsArticleServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.auth = NewsAuthFixture()
        self.transaction_manager = TransactionManagerFixture()
        self.news_article_repository = NewsArticleRepositoryFixture()
        self.service = RevokeNewsArticleService(
            auth=self.auth,
            transaction_manager=self.transaction_manager,
            news_article_repository=self.news_article_repository,
        )

    async def _populate_news_article(self) -> NewsArticle:
        news_article = NewsArticle(
            id_=str(uuid4()),
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author_id=str(uuid4()),
            image=Image(
                url="https://example.com/images/1234",
                description="Description of the image",
                author="Author of the image",
            ),
            text="Text of the news article.",
            revoke_reason=None,
        )
        await self.news_article_repository.save(news_article)
        return news_article

    async def test_revoke_news_article(self) -> None:
        news_article = await self._populate_news_article()

        revoke_reason = "Fake"
        result = await self.service.revoke_news_article(
            news_article_id=news_article.id, reason=revoke_reason
        )

        self.assertEqual(result.revoked_news_article.id, news_article.id)
        self.assertTrue(result.revoked_news_article.is_revoked)
        self.assertEqual(result.revoked_news_article.revoke_reason, revoke_reason)

        news_article = await self.news_article_repository.get_news_article_by_id(
            news_article_id=news_article.id
        )
        self.assertTrue(news_article.is_revoked)
        self.assertEqual(news_article.revoke_reason, revoke_reason)

    async def test_revoke_news_article_requires_authorization(self) -> None:
        news_article = await self._populate_news_article()
        self.auth.forbid_revoke()
        with self.assertRaises(AuthorizationError):
            await self.service.revoke_news_article(
                news_article_id=news_article.id, reason="Fake"
            )
