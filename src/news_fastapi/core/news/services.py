from dataclasses import dataclass

from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.domain.author import Author, AuthorRepository
from news_fastapi.domain.news_article import (
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

    def __init__(
        self,
        news_article_repository: NewsArticleRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._news_article_repository = news_article_repository
        self._author_repository = author_repository

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


@dataclass
class NewsArticleView:
    news_article: NewsArticle
    author: Author


class NewsService:
    _auth: NewsAuth
    _news_article_repository: NewsArticleRepository
    _author_repository: AuthorRepository

    def __init__(
        self,
        auth: NewsAuth,
        news_article_repository: NewsArticleRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._auth = auth
        self._news_article_repository = news_article_repository
        self._author_repository = author_repository

    async def get_news_article(self, news_article_id: str) -> NewsArticleView:
        news_article = await self._news_article_repository.get_news_article_by_id(
            news_article_id
        )
        author = await self._author_repository.get_author_by_id(news_article.author_id)
        return NewsArticleView(news_article=news_article, author=author)

    async def revoke_news_article(self, news_article_id: str, reason: str) -> None:
        self._auth.check_can_revoke()
        news_article = await self._news_article_repository.get_news_article_by_id(
            news_article_id=news_article_id
        )
        news_article.revoke(reason=reason)
        await self._news_article_repository.save(news_article)
