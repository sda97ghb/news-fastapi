from contextlib import asynccontextmanager

from news_fastapi.core.authors.auth import AuthorsAuth
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


class TransactionManagerFixture(TransactionManager):
    def in_transaction(self) -> TransactionContextManager:
        return self._in_transaction()

    @asynccontextmanager
    async def _in_transaction(self):
        yield
