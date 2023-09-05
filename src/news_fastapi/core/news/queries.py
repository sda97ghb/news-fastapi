from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.domain.news_article import NewsArticleListFilter
from news_fastapi.domain.value_objects import Image


@dataclass
class NewsArticlesListAuthor:
    author_id: str
    name: str


@dataclass
class NewsArticlesListItem:
    news_article_id: str
    headline: str
    date_published: DateTime
    author: NewsArticlesListAuthor
    revoke_reason: str | None


@dataclass
class NewsArticlesListPage:
    offset: int
    limit: int
    items: list[NewsArticlesListItem]


class NewsArticlesListQueries(ABC):
    @abstractmethod
    async def get_page(
        self,
        offset: int = 0,
        limit: int = 50,
        filter_: NewsArticleListFilter | None = None,
    ) -> NewsArticlesListPage:
        raise NotImplementedError


class NewsArticlesListService:
    _queries: NewsArticlesListQueries

    def __init__(self, news_articles_list_queries: NewsArticlesListQueries) -> None:
        self._queries = news_articles_list_queries

    async def get_page(
        self,
        offset: int = 0,
        limit: int = 50,
        filter_: NewsArticleListFilter | None = None,
    ) -> NewsArticlesListPage:
        return await self._queries.get_page(offset=offset, limit=limit, filter_=filter_)


@dataclass
class NewsArticleDetailsAuthor:
    author_id: str
    name: str


@dataclass
class NewsArticleDetails:
    news_article_id: str
    headline: str
    date_published: DateTime
    author: NewsArticleDetailsAuthor
    image: Image
    text: str
    revoke_reason: str | None


class NewsArticleDetailsQueries(ABC):
    @abstractmethod
    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        raise NotImplementedError


class NewsArticleDetailsService:
    _queries: NewsArticleDetailsQueries

    def __init__(self, news_article_details_queries: NewsArticleDetailsQueries) -> None:
        self._queries = news_article_details_queries

    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        return await self._queries.get_news_article(news_article_id=news_article_id)
