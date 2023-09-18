from collections.abc import Collection, Mapping
from typing import cast

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    default_authors_table,
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
        result = await self._connection.execute(
            select(authors_table).offset(offset).limit(limit)
        )
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
        result = await self._connection.execute(
            select(authors_table).where(authors_table.c.id == author_id)
        )
        author = result.one_or_none()
        if author is None:
            raise NotFoundError("Author not found")
        return AuthorDetails(
            author_id=author.id,
            name=author.name,
        )


class SQLAlchemyAuthorRepository(AuthorRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_author_by_id(self, author_id: str) -> Author:
        author = cast(
            Author | None,
            await self._session.get(Author, author_id, with_for_update=True),
        )
        if author is None:
            raise NotFoundError("Author not found")
        return author

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._session.execute(
            select(Author).offset(offset).limit(limit).with_for_update()
        )
        return result.scalars().all()

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        result = await self._session.execute(
            select(Author).where(authors_table.c.id.in_(id_list)).with_for_update()
        )
        authors_list = cast(list[Author], result.scalars().all())
        return {author.id: author for author in authors_list}

    async def save(self, author: Author) -> None:
        self._session.add(author)

    async def remove(self, author: Author) -> None:
        await self._session.delete(author)


class SQLAlchemyDefaultAuthorRepository(DefaultAuthorRepository):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_default_author_id(self, user_id: str) -> str | None:
        result = await self._connection.execute(
            select(default_authors_table.c.author_id).where(
                default_authors_table.c.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        if author_id is None:
            await self._connection.execute(
                delete(default_authors_table).where(
                    default_authors_table.c.user_id == user_id
                )
            )
        else:
            result = await self._connection.execute(
                select(default_authors_table.c.author_id)
                .where(default_authors_table.c.user_id == user_id)
                .with_for_update()
            )
            if result.scalar_one_or_none() is not None:
                await self._connection.execute(
                    update(default_authors_table)
                    .values(author_id=author_id)
                    .where(default_authors_table.c.user_id == user_id)
                    .returning()
                )
            else:
                await self._connection.execute(
                    insert(default_authors_table).values(
                        user_id=user_id, author_id=author_id
                    )
                )
