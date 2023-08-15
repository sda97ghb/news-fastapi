from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Protocol, runtime_checkable

from news_fastapi.core.authors.models import Author, AuthorReference
from news_fastapi.core.news.models import NewsArticle, NewsArticleReference
from news_fastapi.core.utils import NotLoadedType


@runtime_checkable
class DraftReference(Protocol):
    id: str


@runtime_checkable
class Draft(Protocol):
    id: str
    news_article: NewsArticleReference | NewsArticle | None | NotLoadedType
    headline: str
    date_published: DateTime | None
    author: AuthorReference | Author | NotLoadedType
    text: str
    created_by_user_id: str
    is_published: bool


@dataclass
class DraftReferenceDataclass:
    id: str

    def __check_implements_protocol(self) -> DraftReference:
        return self


@dataclass
class DraftDataclass:
    id: str
    news_article: NewsArticleReference | NewsArticle | None | NotLoadedType
    headline: str
    date_published: DateTime | None
    author: AuthorReference | Author | NotLoadedType
    text: str
    created_by_user_id: str
    is_published: bool

    def __check_implements_protocol(self) -> Draft:
        return self
