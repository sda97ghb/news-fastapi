from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import datetime as DateTime
from typing import Protocol, runtime_checkable

from news_fastapi.domain.news import NewsArticle


@runtime_checkable
class Draft(Protocol):
    id: str
    news_article_id: str | None
    headline: str
    date_published: DateTime | None
    author_id: str
    text: str
    created_by_user_id: str
    is_published: bool


class DraftFactory(ABC):
    @abstractmethod
    def create_draft(
        self,
        draft_id: str,
        news_article_id: str | None,
        headline: str,
        date_published: DateTime | None,
        author_id: str,
        text: str,
        created_by_user_id: str,
        is_published: bool,
    ) -> Draft:
        raise NotImplementedError

    def create_draft_from_scratch(
        self, draft_id: str, user_id: str, author_id: str
    ) -> Draft:
        return self.create_draft(
            draft_id=draft_id,
            news_article_id=None,
            headline="",
            date_published=None,
            author_id=author_id,
            text="",
            created_by_user_id=user_id,
            is_published=False,
        )

    def create_draft_from_news_article(
        self, news_article: NewsArticle, draft_id: str, user_id: str
    ) -> Draft:
        return self.create_draft(
            draft_id=draft_id,
            news_article_id=news_article.id,
            headline=news_article.headline,
            date_published=news_article.date_published,
            author_id=news_article.author_id,
            text=news_article.text,
            created_by_user_id=user_id,
            is_published=False,
        )


class DraftRepository(ABC):
    @abstractmethod
    async def next_identity(self) -> str:
        raise NotImplementedError

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
