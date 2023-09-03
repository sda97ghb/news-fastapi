from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Collection, Literal, Protocol, runtime_checkable

from news_fastapi.domain.common import Image
from news_fastapi.utils.sentinels import Undefined, UndefinedType


@runtime_checkable
class NewsArticle(Protocol):
    id: str
    headline: str
    date_published: DateTime
    author_id: str
    image: Image
    text: str
    revoke_reason: str | None


class NewsArticleFactory(ABC):
    @abstractmethod
    def create_news_article(
        self,
        news_article_id: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        image: Image,
        text: str,
        revoke_reason: str | None,
    ) -> NewsArticle:
        raise NotImplementedError

    def create_news_article_from_scratch(
        self,
        news_article_id: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        image: Image,
        text: str,
    ) -> NewsArticle:
        return self.create_news_article(
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            image=image,
            text=text,
            revoke_reason=None,
        )


@dataclass
class NewsArticleListFilter:
    revoked: Literal["no_revoked", "only_revoked"] | UndefinedType = Undefined


class NewsArticleRepository(ABC):
    @abstractmethod
    async def next_identity(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def save(self, news_article: NewsArticle) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        raise NotImplementedError

    @abstractmethod
    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        raise NotImplementedError

    @abstractmethod
    async def count_for_author(self, author_id: str) -> int:
        raise NotImplementedError
