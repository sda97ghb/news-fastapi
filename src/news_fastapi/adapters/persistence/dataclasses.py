from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.domain.authors import Author, AuthorFactory
from news_fastapi.domain.drafts import Draft
from news_fastapi.domain.news import NewsArticle


@dataclass
class AuthorDataclass:
    id: str  # pylint: disable=invalid-name
    name: str

    def __assert_implements_protocol(self) -> Author:
        # pylint: disable=unused-private-member
        return self


class DataclassesAuthorFactory(AuthorFactory):
    def create_author(self, author_id: str, name: str) -> Author:
        return AuthorDataclass(id=author_id, name=name)


@dataclass
class DraftDataclass:
    id: str  # pylint: disable=invalid-name
    news_article_id: str | None
    headline: str
    date_published: DateTime | None
    author_id: str
    text: str
    created_by_user_id: str
    is_published: bool

    def __assert_implements_protocol(self) -> Draft:
        # pylint: disable=unused-private-member
        return self


@dataclass
class NewsArticleDataclass:
    id: str  # pylint: disable=invalid-name
    headline: str
    date_published: DateTime
    author_id: str
    text: str
    revoke_reason: str | None

    def __assert_implements_protocol(self) -> NewsArticle:
        # pylint: disable=unused-private-member
        return self
