from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from news_fastapi.core.news.queries import NewsArticlesListService, \
    NewsArticleDetailsService
from news_fastapi.domain.news_article import NewsArticleListFilter


class NewsArticlesListServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.news_articles_list_queries=AsyncMock()
        self.service = NewsArticlesListService(
            news_articles_list_queries=self.news_articles_list_queries
        )

    async def test_get_page(self) -> None:
        page_mock = Mock()
        self.news_articles_list_queries.get_page.return_value = page_mock
        offset = 20
        limit = 10
        filter_ = NewsArticleListFilter(revoked="no_revoked")
        page = await self.service.get_page(offset=offset, limit=limit, filter_=filter_)
        self.news_articles_list_queries.get_page.assert_awaited_with(
            offset=offset, limit=limit, filter_=filter_)
        self.assertIs(page, page_mock)


class NewsArticleDetailsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.news_article_details_queries = AsyncMock()
        self.service = NewsArticleDetailsService(
            news_article_details_queries=self.news_article_details_queries
        )

    async def test_get_news_article(self) -> None:
        details_mock = Mock()
        self.news_article_details_queries.get_news_article.return_value = details_mock
        news_article_id = "11111111-1111-1111-1111-111111111111"
        details = await self.service.get_news_article(news_article_id=news_article_id)
        self.news_article_details_queries.get_news_article.assert_awaited_with(
            news_article_id=news_article_id)
        self.assertIs(details, details_mock)
