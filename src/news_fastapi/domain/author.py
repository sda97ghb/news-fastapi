from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

from news_fastapi.domain.seed_work.entity import Entity, Repository
from news_fastapi.domain.seed_work.events import DomainEvent
from news_fastapi.utils.format_callable import format_callable_call


class Author(Entity):
    _name: str

    def __init__(self, id_: str, name: str) -> None:
        super().__init__(id_=id_)
        self._name = name

    def __repr__(self) -> str:
        return format_callable_call("Author", id=self.id, name=self.name)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        new_name = new_name.strip()
        if new_name == "":
            raise ValueError("Author name can not be empty")
        self._name = new_name


class AuthorFactory:
    def create_author(self, author_id: str, name: str) -> Author:
        return Author(id_=author_id, name=name)


class AuthorRepository(Repository, ABC):
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


@dataclass(kw_only=True, frozen=True)
class AuthorDeleted(DomainEvent):
    author_id: str

    def _to_json_extra_fields(self) -> dict[str, Any]:
        return {"author_id": self.author_id}
