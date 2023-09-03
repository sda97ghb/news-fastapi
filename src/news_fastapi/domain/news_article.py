from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from datetime import datetime as DateTime
from typing import Collection, Literal

from news_fastapi.domain.seed_work.entity import Entity
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.sentinels import Undefined, UndefinedType


class NewsArticle(Entity):
    _headline: str
    _date_published: DateTime
    _author_id: str
    _image: Image
    _text: str
    _revoke_reason: str | None

    def __init__(
        self,
        id_: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        image: Image,
        text: str,
        revoke_reason: str | None,
    ) -> None:
        super().__init__(id_)
        self._headline = headline
        self._date_published = date_published
        self._author_id = author_id
        self._image = image
        self._text = text
        self._revoke_reason = revoke_reason

    @property
    def headline(self) -> str:
        return self._headline

    @headline.setter
    def headline(self, new_headline: str) -> None:
        new_headline = new_headline.strip()
        if new_headline == "":
            raise ValueError("Can not set empty headline to news article")
        self._headline = new_headline

    @property
    def date_published(self) -> DateTime:
        return self._date_published

    @date_published.setter
    def date_published(self, new_date_published: DateTime) -> None:
        self._date_published = new_date_published

    @property
    def author_id(self) -> str:
        return self._author_id

    @author_id.setter
    def author_id(self, new_author_id: str) -> None:
        self._author_id = new_author_id

    @property
    def image(self) -> Image:
        return self._image

    @image.setter
    def image(self, new_image: Image) -> None:
        new_image = replace(
            new_image,
            description=new_image.description.strip(),
            author=new_image.author.strip(),
        )
        if new_image.url == "":
            raise ValueError("Can not set image with empty URL")
        if new_image.description == "":
            raise ValueError("Can not set image with empty description")
        if new_image.author == "":
            raise ValueError("Can not set image with empty author")
        self._image = new_image

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_text: str) -> None:
        new_text = new_text.strip()
        if new_text == "":
            raise ValueError("Can not set empty text to news article")
        self._text = new_text

    @property
    def revoke_reason(self) -> str | None:
        return self._revoke_reason

    @property
    def is_revoked(self) -> bool:
        return self._revoke_reason is not None

    def revoke(self, reason: str) -> None:
        self._revoke_reason = reason

    def cancel_revoke(self) -> None:
        self._revoke_reason = None


class NewsArticleFactory:
    def create_news_article_from_scratch(
        self,
        news_article_id: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        image: Image,
        text: str,
    ) -> NewsArticle:
        return NewsArticle(
            id_=news_article_id,
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
