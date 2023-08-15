from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from news_fastapi.core.news.models import (
    NewsArticle,
    NewsArticleListItem,
    NewsArticleReference,
)
from news_fastapi.core.utils import LoadPolicy, Undefined, UndefinedType


@dataclass
class NewsArticleListFilter:
    revoked: Literal["no_revoked", "only_revoked"] | UndefinedType = Undefined


class NewsDAO(ABC):
    @abstractmethod
    def get_news_article_references_for_author(
        self, author_id: str
    ) -> list[NewsArticleReference]:
        raise NotImplementedError

    @abstractmethod
    def get_news_article_list(
        self,
        offset: int,
        limit: int,
        load_author: LoadPolicy = LoadPolicy.FULL,
        filter_: NewsArticleListFilter | None = None,
    ) -> list[NewsArticleListItem]:
        raise NotImplementedError

    @abstractmethod
    def get_news_article(
        self, news_id: str, load_author: LoadPolicy = LoadPolicy.FULL
    ) -> NewsArticle:
        raise NotImplementedError

    @abstractmethod
    def save_news_article(self, news_article: NewsArticle) -> NewsArticle:
        raise NotImplementedError
