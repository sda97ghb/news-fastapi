from contextlib import asynccontextmanager

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.core.transaction import TransactionContextManager, TransactionManager


class AuthorsAuthFixture(AuthorsAuth):
    _current_user_id: str
    _can_create_author: bool
    _can_update_author: bool
    _can_delete_author: bool

    def __init__(self, current_user_id: str) -> None:
        self._current_user_id = current_user_id
        self._can_create_author = True
        self._can_update_author = True
        self._can_delete_author = True

    def can_create_author(self) -> bool:
        return self._can_create_author

    def forbid_create_author(self) -> None:
        self._can_create_author = False

    def can_update_author(self, author_id: str) -> bool:
        return self._can_update_author

    def forbid_update_author(self) -> None:
        self._can_update_author = False

    def can_delete_author(self, author_id: str) -> bool:
        return self._can_delete_author

    def forbid_delete_author(self) -> None:
        self._can_delete_author = False

    def can_get_default_author(self) -> bool:
        return True

    def can_set_default_author(self) -> bool:
        return True

    def get_current_user_id(self) -> str:
        return self._current_user_id


class DraftsAuthFixture(DraftsAuth):
    _current_user_id: str
    _can_get_draft: bool
    _can_get_drafts_list: bool
    _can_create_draft: bool
    _can_update_draft: bool
    _can_delete_draft: bool
    _can_delete_published_draft: bool
    _can_publish_draft: bool

    def __init__(self, current_user_id: str) -> None:
        self._current_user_id = current_user_id
        self._can_get_draft = True
        self._can_get_drafts_list = True
        self._can_create_draft = True
        self._can_update_draft = True
        self._can_delete_draft = True
        self._can_delete_published_draft = True
        self._can_publish_draft = True

    def can_get_draft(self, draft_id: str) -> bool:
        return self._can_get_draft

    def forbid_get_draft(self) -> None:
        self._can_get_draft = False

    def can_get_drafts_list(self) -> bool:
        return self._can_get_drafts_list

    def forbid_get_drafts_list(self) -> None:
        self._can_get_drafts_list = False

    def can_create_draft(self) -> bool:
        return self._can_create_draft

    def forbid_create_draft(self) -> None:
        self._can_create_draft = False

    def can_update_draft(self, draft_id: str) -> bool:
        return self._can_update_draft

    def forbid_update_draft(self) -> None:
        self._can_update_draft = False

    def can_delete_draft(self, draft_id: str) -> bool:
        return self._can_delete_draft

    def forbid_delete_draft(self) -> None:
        self._can_delete_draft = False

    def can_delete_published_draft(self) -> bool:
        return self._can_delete_published_draft

    def can_publish_draft(self) -> bool:
        return self._can_publish_draft

    def get_current_user_id(self) -> str:
        return self._current_user_id


class NewsAuthFixture(NewsAuth):
    _can_revoke: bool

    def __init__(self) -> None:
        self._can_revoke = True

    def can_revoke(self) -> bool:
        return self._can_revoke

    def forbid_revoke(self) -> None:
        self._can_revoke = False


class TransactionManagerFixture(TransactionManager):
    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        yield
