from abc import ABC, abstractmethod
from datetime import datetime as DateTime
from typing import Protocol, runtime_checkable


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


class DraftRepository(ABC):
    @abstractmethod
    async def next_identity(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def save(self, draft: Draft) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_draft_by_id(self, draft_id: str) -> Draft:
        raise NotImplementedError

    @abstractmethod
    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, draft: Draft) -> None:
        raise NotImplementedError
