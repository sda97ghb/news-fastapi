from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping
from typing import Protocol, runtime_checkable


@runtime_checkable
class Author(Protocol):
    id: str
    name: str


class AuthorFactory(ABC):
    @abstractmethod
    def create_author(self, author_id: str, name: str) -> Author:
        raise NotImplementedError


class AuthorRepository(ABC):
    @abstractmethod
    async def next_identity(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_author_by_id(self, author_id: str) -> Author:
        raise NotImplementedError

    @abstractmethod
    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        raise NotImplementedError

    @abstractmethod
    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, author: Author) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, author: Author) -> None:
        raise NotImplementedError


class DefaultAuthorRepository(ABC):
    @abstractmethod
    async def get_default_author_id(self, user_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        raise NotImplementedError
