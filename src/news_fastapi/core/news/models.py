from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Protocol, runtime_checkable

from news_fastapi.core.authors.models import Author, AuthorReference
from news_fastapi.core.utils import NotLoadedType


@runtime_checkable
class NewsArticleReference(Protocol):
    id: str


@runtime_checkable
class NewsArticle(Protocol):
    id: str
    headline: str
    date_published: DateTime
    author: AuthorReference | Author | NotLoadedType
    text: str
    revoke_reason: str


@runtime_checkable
class NewsArticleListItem(Protocol):
    id: str
    headline: str
    date_published: DateTime
    author: AuthorReference | Author | NotLoadedType


@dataclass
class NewsArticleReferenceDataclass:
    id: str

    def __check_implements_protocol(self) -> NewsArticleReference:
        return self


@dataclass
class NewsArticleDataclass:
    id: str
    headline: str
    date_published: DateTime
    author: AuthorReference | Author | NotLoadedType
    text: str
    revoke_reason: str

    def __check_implements_protocol(self) -> NewsArticle:
        return self


@dataclass
class NewsArticleListItemDataclass:
    id: str
    headline: str
    date_published: DateTime
    author: AuthorReference | Author | NotLoadedType

    def __check_implements_protocol(self) -> NewsArticleListItem:
        return self
