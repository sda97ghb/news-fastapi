from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AuthorsListItem:
    author_id: str
    name: str


@dataclass
class AuthorsListPage:
    offset: int
    limit: int
    items: list[AuthorsListItem]


class AuthorsListQueries(ABC):
    @abstractmethod
    async def get_page(self, offset: int = 0, limit: int = 10) -> AuthorsListPage:
        raise NotImplementedError


class AuthorsListService:
    _queries: AuthorsListQueries

    def __init__(self, authors_list_queries: AuthorsListQueries) -> None:
        self._queries = authors_list_queries

    async def get_page(self, offset: int = 0, limit: int = 10) -> AuthorsListPage:
        return await self._queries.get_page(offset=offset, limit=limit)


@dataclass
class AuthorDetails:
    author_id: str
    name: str


class AuthorDetailsQueries(ABC):
    @abstractmethod
    async def get_author(self, author_id: str) -> AuthorDetails:
        raise NotImplementedError


class AuthorDetailsService:
    _queries: AuthorDetailsQueries

    def __init__(self, author_details_queries: AuthorDetailsQueries) -> None:
        self._queries = author_details_queries

    async def get_author(self, author_id: str) -> AuthorDetails:
        return await self._queries.get_author(author_id=author_id)
