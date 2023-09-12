from collections.abc import Iterable
from typing import Collection, Mapping
from uuid import uuid4

from tortoise.exceptions import DoesNotExist

from news_fastapi.adapters.persistence.tortoise.models import (
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


class TortoiseAuthorsListQueries(AuthorsListQueries):
    async def get_page(self, offset: int = 0, limit: int = 10) -> AuthorsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        model_instances_list = await AuthorModel.all().offset(offset).limit(limit)
        return AuthorsListPage(
            offset=offset,
            limit=limit,
            items=[
                AuthorsListItem(author_id=model_instance.id, name=model_instance.name)
                for model_instance in model_instances_list
            ],
        )


class TortoiseAuthorDetailsQueries(AuthorDetailsQueries):
    async def get_author(self, author_id: str) -> AuthorDetails:
        try:
            model_instance = await AuthorModel.get(id=author_id)
        except DoesNotExist as err:
            raise NotFoundError("Author not found") from err
        return AuthorDetails(
            author_id=model_instance.id,
            name=model_instance.name,
        )


class TortoiseAuthorRepository(AuthorRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def get_author_by_id(self, author_id: str) -> Author:
        try:
            model_instance = await AuthorModel.select_for_update().get(id=author_id)
            return self._to_entity(model_instance)
        except DoesNotExist as err:
            raise NotFoundError(f"Author with id {author_id} does not exist") from err

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        model_instances_list = (
            await AuthorModel.select_for_update().all().offset(offset).limit(limit)
        )
        return self._to_entity_list(model_instances_list)

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        model_instances_mapping = await AuthorModel.select_for_update().in_bulk(
            id_list=id_list, field_name="id"
        )
        return {
            id_: self._to_entity(model_instance)
            for id_, model_instance in model_instances_mapping.items()
        }

    async def save(self, author: Author) -> None:
        await AuthorModel.update_or_create({"name": author.name}, id=author.id)

    async def remove(self, author: Author) -> None:
        await AuthorModel.filter(id=author.id).delete()

    def _to_entity(self, model_instance: AuthorModel) -> Author:
        return Author(id_=model_instance.id, name=model_instance.name)

    def _to_entity_list(
        self, model_instances_list: Iterable[AuthorModel]
    ) -> list[Author]:
        return [
            self._to_entity(model_instance) for model_instance in model_instances_list
        ]


class TortoiseDefaultAuthorRepository(DefaultAuthorRepository):
    async def get_default_author_id(self, user_id: str) -> str | None:
        default_author = await DefaultAuthorModel.get_or_none(user_id=user_id)
        if default_author is None:
            return None
        return default_author.author_id

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        if author_id is None:
            await DefaultAuthorModel.filter(user_id=user_id).delete()
        else:
            default_author = await DefaultAuthorModel.select_for_update().get_or_none(
                user_id=user_id
            )
            if default_author is None:
                default_author = DefaultAuthorModel(user_id=user_id)
            default_author.author_id = author_id
            await default_author.save()
