from typing import Collection, Mapping, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from news_fastapi.adapters.persistence.sqlalchemy_orm.models import (
    AuthorModel,
    DefaultAuthorModel,
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


class SQLAlchemyORMAuthorsListQueries(AuthorsListQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_page(self, offset: int = 0, limit: int = 10) -> AuthorsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._session.execute(
            select(AuthorModel).offset(offset).limit(limit)
        )
        model_instances = cast(list[AuthorModel], result.scalars().all())
        return AuthorsListPage(
            offset=offset,
            limit=limit,
            items=[
                AuthorsListItem(
                    author_id=model_instance.id,
                    name=model_instance.name,
                )
                for model_instance in model_instances
            ],
        )


class SQLAlchemyORMAuthorDetailsQueries(AuthorDetailsQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_author(self, author_id: str) -> AuthorDetails:
        result = await self._session.execute(
            select(AuthorModel).where(AuthorModel.id == author_id)
        )
        model_instance = cast(AuthorModel | None, result.scalars().one_or_none())
        if model_instance is None:
            raise NotFoundError("Author not found")
        return AuthorDetails(author_id=model_instance.id, name=model_instance.name)


class SQLAlchemyORMAuthorRepository(AuthorRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_author_by_id(self, author_id: str) -> Author:
        model_instance = await self._session.get(
            AuthorModel, author_id, with_for_update=True
        )
        if model_instance is None:
            raise NotFoundError("Author not found")
        return Author(id_=model_instance.id, name=model_instance.name)

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._session.execute(
            select(AuthorModel).offset(offset).limit(limit).with_for_update()
        )
        model_instances_list = cast(list[AuthorModel], result.scalars().all())
        return self._to_entity_list(model_instances_list)

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        result = await self._session.execute(
            select(AuthorModel).where(AuthorModel.id.in_(id_list)).with_for_update()
        )
        model_instances_list = cast(list[AuthorModel], result.scalars().all())
        return {
            model_instance.id: self._to_entity(model_instance)
            for model_instance in model_instances_list
        }

    async def save(self, author: Author) -> None:
        model_instance = await self._session.get(
            AuthorModel, author.id, with_for_update=True
        )
        if model_instance is None:
            model_instance = AuthorModel(id=author.id, name=author.name)
            self._session.add(model_instance)
        else:
            model_instance.name = author.name

    async def remove(self, author: Author) -> None:
        model_instance = await self._session.get(
            AuthorModel, author.id, with_for_update=True
        )
        if model_instance is not None:
            await self._session.delete(model_instance)

    def _to_entity(self, model_instance: AuthorModel) -> Author:
        return Author(id_=model_instance.id, name=model_instance.name)

    def _to_entity_list(self, model_instances_list: list[AuthorModel]) -> list[Author]:
        return [
            self._to_entity(model_instance) for model_instance in model_instances_list
        ]


class SQLAlchemyORMDefaultAuthorRepository(DefaultAuthorRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_default_author_id(self, user_id: str) -> str | None:
        model_instance = await self._session.get(DefaultAuthorModel, user_id)
        if model_instance is None:
            return None
        return model_instance.author_id

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        model_instance = await self._session.get(
            DefaultAuthorModel, user_id, with_for_update=True
        )
        if author_id is None:
            if model_instance is not None:
                await self._session.delete(model_instance)
        else:
            if model_instance is None:
                model_instance = DefaultAuthorModel(
                    user_id=user_id, author_id=author_id
                )
                self._session.add(model_instance)
            else:
                model_instance.author_id = author_id
