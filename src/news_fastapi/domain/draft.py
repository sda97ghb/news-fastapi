from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import datetime as DateTime

from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.seed_work.entity import Entity, Repository
from news_fastapi.domain.value_objects import Image


class PublishedDraftEditError(Exception):
    def __init__(self) -> None:
        super().__init__("Published draft can not be edited")


class Draft(Entity):
    _news_article_id: str | None
    _created_by_user_id: str
    _headline: str
    _date_published: DateTime | None
    _author_id: str
    _image: Image | None
    _text: str
    _is_published: bool

    def __init__(
        self,
        id_: str,
        news_article_id: str | None,
        created_by_user_id: str,
        headline: str,
        date_published: DateTime | None,
        author_id: str,
        image: Image | None,
        text: str,
        is_published: bool,
    ) -> None:
        super().__init__(id_)
        self._news_article_id = news_article_id
        self._created_by_user_id = created_by_user_id
        self._headline = headline
        self._date_published = date_published
        self._author_id = author_id
        self._image = image
        self._text = text
        self._is_published = is_published

    @property
    def news_article_id(self) -> str | None:
        return self._news_article_id

    @property
    def created_by_user_id(self) -> str:
        return self._created_by_user_id

    @property
    def headline(self) -> str:
        return self._headline

    @headline.setter
    def headline(self, new_headline: str) -> None:
        if self.is_published:
            raise PublishedDraftEditError()
        self._headline = new_headline

    @property
    def date_published(self) -> DateTime | None:
        return self._date_published

    @date_published.setter
    def date_published(self, new_date_published: DateTime | None) -> None:
        if self.is_published:
            raise PublishedDraftEditError()
        self._date_published = new_date_published

    @property
    def author_id(self) -> str:
        return self._author_id

    @author_id.setter
    def author_id(self, new_author_id: str) -> None:
        if self.is_published:
            raise PublishedDraftEditError()
        self._author_id = new_author_id

    @property
    def image(self) -> Image | None:
        return self._image

    @image.setter
    def image(self, new_image: Image | None) -> None:
        if self.is_published:
            raise PublishedDraftEditError()
        self._image = new_image

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new_text: str) -> None:
        if self.is_published:
            raise PublishedDraftEditError()
        self._text = new_text

    @property
    def is_published(self) -> bool:
        return self._is_published

    def mark_as_published(self) -> None:
        self._is_published = True


class DraftFactory:
    def create_draft_from_scratch(
        self, draft_id: str, user_id: str, author_id: str
    ) -> Draft:
        return Draft(
            id_=draft_id,
            news_article_id=None,
            created_by_user_id=user_id,
            headline="",
            date_published=None,
            author_id=author_id,
            image=None,
            text="",
            is_published=False,
        )

    def create_draft_from_news_article(
        self, news_article: NewsArticle, draft_id: str, user_id: str
    ) -> Draft:
        return Draft(
            id_=draft_id,
            news_article_id=news_article.id,
            created_by_user_id=user_id,
            headline=news_article.headline,
            date_published=news_article.date_published,
            author_id=news_article.author_id,
            image=news_article.image,
            text=news_article.text,
            is_published=False,
        )


class DraftRepository(Repository, ABC):
    @abstractmethod
    async def save(self, draft: Draft) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_drafts_list(
        self,
        offset: int = 0,
        limit: int = 10,
    ) -> Collection[Draft]:
        raise NotImplementedError

    @abstractmethod
    async def get_draft_by_id(self, draft_id: str) -> Draft:
        raise NotImplementedError

    @abstractmethod
    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        raise NotImplementedError

    @abstractmethod
    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, draft: Draft) -> None:
        raise NotImplementedError
