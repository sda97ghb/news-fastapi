from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.domain.value_objects import Image


@dataclass
class DraftsListItem:
    draft_id: str
    news_article_id: str | None
    headline: str
    created_by_user_id: str
    is_published: bool


@dataclass
class DraftsListPage:
    offset: int
    limit: int
    items: list[DraftsListItem]


class DraftsListQueries(ABC):
    @abstractmethod
    async def get_page(self, offset: int, limit: int) -> DraftsListPage:
        raise NotImplementedError


class DraftsListService:
    _auth: DraftsAuth
    _queries: DraftsListQueries

    def __init__(
        self, drafts_auth: DraftsAuth, draft_list_queries: DraftsListQueries
    ) -> None:
        self._auth = drafts_auth
        self._queries = draft_list_queries

    async def get_page(self, offset: int, limit: int) -> DraftsListPage:
        self._auth.check_get_drafts_list()
        return await self._queries.get_page(offset=offset, limit=limit)


@dataclass
class DraftDetailsAuthor:
    author_id: str
    name: str


@dataclass
class DraftDetails:
    draft_id: str
    news_article_id: str | None
    created_by_user_id: str
    headline: str
    date_published: DateTime | None
    author: DraftDetailsAuthor
    image: Image | None
    text: str
    is_published: bool


class DraftDetailsQueries(ABC):
    @abstractmethod
    async def get_draft(self, draft_id: str) -> DraftDetails:
        raise NotImplementedError


class DraftDetailsService:
    _auth: DraftsAuth
    _draft_details_queries: DraftDetailsQueries

    def __init__(
        self, auth: DraftsAuth, draft_details_queries: DraftDetailsQueries
    ) -> None:
        self._auth = auth
        self._draft_details_queries = draft_details_queries

    async def get_draft(self, draft_id: str) -> DraftDetails:
        self._auth.check_get_draft(draft_id)
        details = await self._draft_details_queries.get_draft(draft_id=draft_id)
        return details
