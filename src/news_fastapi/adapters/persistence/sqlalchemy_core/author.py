from collections.abc import Iterable
from typing import Collection, Mapping
from uuid import uuid4

from sqlalchemy import Row, delete, insert, select, update
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncConnection

from news_fastapi.adapters.persistence.sqlalchemy_core.tables import (
    authors,
    default_authors,
)
from news_fastapi.core.authors.queries import (
    AuthorDetails,
    AuthorDetailsQueries,
    AuthorsListItem,
    AuthorsListPage,
    AuthorsListQueries,
)
from news_fastapi.domain.author import Author, AuthorRepository, DefaultAuthorRepository
from news_fastapi.utils.exceptions import NotFoundError


class SQLAlchemyAuthorsListQueries(AuthorsListQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_page(self, offset: int = 0, limit: int = 10) -> AuthorsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        statement = select(authors).offset(offset).limit(limit)
        result = await self._connection.execute(statement=statement)
        authors_list = result.fetchall()
        return AuthorsListPage(
            offset=offset,
            limit=limit,
            items=[
                AuthorsListItem(
                    author_id=author.id,
                    name=author.name,
                )
                for author in authors_list
            ],
        )


class SQLAlchemyAuthorDetailsQueries(AuthorDetailsQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_author(self, author_id: str) -> AuthorDetails:
        statement = select(authors).where(authors.c.id == author_id)
        result = await self._connection.execute(statement)
        author = result.one_or_none()
        if author is None:
            raise NotFoundError("Author not found")
        return AuthorDetails(
            author_id=author.id,
            name=author.name,
        )


class SQLAlchemyAuthorRepository(AuthorRepository):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def next_identity(self) -> str:
        return str(uuid4())

    async def get_author_by_id(self, author_id: str) -> Author:
        result = await self._connection.execute(
            select(authors).where(authors.c.id == author_id).with_for_update()
        )
        author = result.one_or_none()
        if author is None:
            raise NotFoundError("Author not found")
        return self._to_entity(author)

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._connection.execute(
            select(authors).offset(offset).limit(limit).with_for_update()
        )
        authors_list = result.fetchall()
        return self._to_entity_list(authors_list)

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        result = await self._connection.execute(
            select(authors).where(authors.c.id.in_(id_list)).with_for_update()
        )
        authors_list = result.fetchall()
        return {author.id: self._to_entity(author) for author in authors_list}

    async def save(self, author: Author) -> None:
        result = await self._connection.execute(
            update(authors).where(authors.c.id == author.id).values(name=author.name)
        )
        if result.rowcount == 1:
            return
        if result.rowcount != 0:
            raise InvalidRequestError(
                f"Update affected {result.rowcount} rows when saving one object"
            )
        await self._connection.execute(
            insert(authors).values(id=author.id, name=author.name)
        )

    async def remove(self, author: Author) -> None:
        await self._connection.execute(delete(authors).where(authors.c.id == author.id))

    def _to_entity(self, author: Row) -> Author:
        return Author(
            id_=author.id,
            name=author.name,
        )

    def _to_entity_list(self, authors_list: Iterable[Row]) -> list[Author]:
        return [self._to_entity(author) for author in authors_list]


class SQLAlchemyDefaultAuthorRepository(DefaultAuthorRepository):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_default_author_id(self, user_id: str) -> str | None:
        result = await self._connection.execute(
            select(default_authors.c.author_id).where(
                default_authors.c.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        if author_id is None:
            await self._connection.execute(
                delete(default_authors).where(default_authors.c.user_id == user_id)
            )
        else:
            result = await self._connection.execute(
                select(default_authors.c.author_id)
                .where(default_authors.c.user_id == user_id)
                .with_for_update()
            )
            if result.scalar_one_or_none() is not None:
                await self._connection.execute(
                    update(default_authors)
                    .values(author_id=author_id)
                    .where(default_authors.c.user_id == user_id)
                )
            else:
                await self._connection.execute(
                    insert(default_authors).values(user_id=user_id, author_id=author_id)
                )
