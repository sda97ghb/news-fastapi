from abc import ABC, abstractmethod
from collections.abc import Iterable

from news_fastapi.core.authors.models import Author


class AuthorsDAO(ABC):
    @abstractmethod
    def get_authors_list(self, offset: int, limit: int) -> list[Author]:
        raise NotImplementedError

    @abstractmethod
    def save_author(self, author: Author) -> Author:
        raise NotImplementedError

    @abstractmethod
    def get_author_by_id(self, author_id: str) -> Author:
        raise NotImplementedError

    @abstractmethod
    def get_authors_in_bulk(self, id_list: Iterable[str]) -> dict[str, Author]:
        raise NotImplementedError

    @abstractmethod
    def delete_author(self, author_id: str) -> None:
        raise NotImplementedError


class DefaultAuthorsDAO(ABC):
    @abstractmethod
    def get_default_author_id(self, user_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        raise NotImplementedError
