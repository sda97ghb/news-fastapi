from collections.abc import Iterable
from typing import Collection, Mapping
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import TextField

from news_fastapi.domain.author import Author, AuthorRepository, DefaultAuthorRepository
from news_fastapi.utils.exceptions import NotFoundError


class AuthorModel(Model):
    id: str = TextField(pk=True)
    name: str = TextField()

    class Meta:
        table = "authors"


class TortoiseAuthorRepository(AuthorRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def get_author_by_id(self, author_id: str) -> Author:
        try:
            model_instance = await AuthorModel.get(id=author_id)
            return self._to_entity(model_instance)
        except DoesNotExist as err:
            raise NotFoundError(f"Author with id {author_id} does not exist") from err

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        model_instances_list = await AuthorModel.all().offset(offset).limit(limit)
        return self._to_entity_list(model_instances_list)

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        model_instances_mapping = await AuthorModel.in_bulk(
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


class DefaultAuthor(Model):
    user_id: str = TextField()
    author_id: str = TextField()

    class Meta:
        table = "default_authors"


class TortoiseDefaultAuthorRepository(DefaultAuthorRepository):
    async def get_default_author_id(self, user_id: str) -> str | None:
        default_author = await DefaultAuthor.get_or_none(user_id=user_id)
        if default_author is None:
            return None
        return default_author.author_id

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        if author_id is None:
            await DefaultAuthor.filter(user_id=user_id).delete()
        else:
            default_author = await DefaultAuthor.get_or_none(user_id=user_id)
            if default_author is None:
                default_author = DefaultAuthor(user_id=user_id)
            default_author.author_id = author_id
            await default_author.save()
