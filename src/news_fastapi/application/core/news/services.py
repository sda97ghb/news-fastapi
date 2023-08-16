from dataclasses import dataclass

from news_fastapi.application.core.news.auth import NewsAuth
from news_fastapi.domain.authors import Author, AuthorRepository
from news_fastapi.domain.news import (
    NewsArticle,
    NewsArticleListFilter,
    NewsArticleRepository,
)


@dataclass
class NewsArticleListItem:
    news_article: NewsArticle
    author: Author


class NewsListService:
    _news_article_repository: NewsArticleRepository
    _author_repository: AuthorRepository

    async def get_page(
        self, offset: int = 0, limit: int = 50
    ) -> list[NewsArticleListItem]:
        news_list = await self._news_article_repository.get_news_articles_list(
            offset=offset,
            limit=limit,
            filter_=NewsArticleListFilter(revoked="no_revoked"),
        )
        author_id_list = [news_article.author_id for news_article in news_list]
        authors = await self._author_repository.get_authors_in_bulk(author_id_list)
        return [
            NewsArticleListItem(
                news_article=news_article, author=authors[news_article.author_id]
            )
            for news_article in news_list
        ]


class NewsService:
    _auth: NewsAuth
    _news_article_repository: NewsArticleRepository

    def __init__(
        self, auth: NewsAuth, news_article_repository: NewsArticleRepository
    ) -> None:
        self._auth = auth
        self._news_article_repository = news_article_repository

    async def get_news_article(self, news_id: str) -> NewsArticle:
        return await self._news_article_repository.get_news_article_by_id(news_id)

    async def revoke_news_article(self, news_id: str, reason: str) -> None:
        self._auth.check_can_revoke()
        news_article = await self._news_article_repository.get_news_article_by_id(
            news_article_id=news_id
        )
        news_article.revoke_reason = reason
        await self._news_article_repository.save(news_article)
