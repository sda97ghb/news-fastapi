from collections.abc import Collection, Mapping
from dataclasses import dataclass
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import TextField

from news_fastapi.domain.authors import (
    Author,
    AuthorFactory,
    AuthorRepository,
    DefaultAuthorRepository,
)
from news_fastapi.utils.exceptions import NotFoundError


@dataclass
class AuthorDataclass:
    id: str  # pylint: disable=invalid-name
    name: str

    def __assert_implements_protocol(self) -> Author:
        # pylint: disable=unused-private-member
        return self


class DataclassesAuthorFactory(AuthorFactory):
    def create_author(self, author_id: str, name: str) -> Author:
        return AuthorDataclass(id=author_id, name=name)


class TortoiseAuthor(Model):
    id: str = TextField(pk=True)
    name: str = TextField()

    def __assert_implements_protocol(self) -> Author:
        # pylint: disable=unused-private-member
        return self


class TortoiseAuthorFactory(AuthorFactory):
    def create_author(self, author_id: str, name: str) -> Author:
        return TortoiseAuthor(id=id, name=name)


class TortoiseAuthorRepository(AuthorRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def get_author_by_id(self, author_id: str) -> Author:
        try:
            return await TortoiseAuthor.get(id=author_id)
        except DoesNotExist as err:
            raise NotFoundError(f"Author with id {author_id} does not exist") from err

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        return await TortoiseAuthor.all().offset(offset).limit(limit)

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        return await TortoiseAuthor.in_bulk(id_list=id_list, field_name="id")

    async def save(self, author: Author) -> None:
        if isinstance(author, TortoiseAuthor):
            await author.save()
        else:
            raise ValueError(
                "Tortoise based repository doesn't support saving of "
                "not Tortoise based entities."
            )

    async def remove(self, author: Author) -> None:
        if not isinstance(author, TortoiseAuthor):
            raise ValueError(
                "Tortoise based repository doesn't support removing of "
                "not Tortoise based entities."
            )
        await author.delete()


class DefaultAuthor(Model):
    user_id: str = TextField()
    author_id: str = TextField()


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
            await DefaultAuthor.filter(user_id=user_id).update(author_id=author_id)
