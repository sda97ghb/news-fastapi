from dataclasses import dataclass

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.domain.author import Author, AuthorRepository, DefaultAuthorRepository


@dataclass
class DefaultAuthorInfo:
    user_id: str
    author: Author


class DefaultAuthorService:
    _auth: AuthorsAuth
    _default_author_repository: DefaultAuthorRepository
    _author_repository: AuthorRepository

    def __init__(
        self,
        auth: AuthorsAuth,
        default_author_repository: DefaultAuthorRepository,
        author_repository: AuthorRepository,
    ) -> None:
        self._auth = auth
        self._default_author_repository = default_author_repository
        self._author_repository = author_repository

    async def get_default_author(self, user_id: str) -> DefaultAuthorInfo | None:
        self._auth.check_get_default_author()
        author_id = await self._default_author_repository.get_default_author_id(user_id)
        if author_id is None:
            return None
        author = await self._author_repository.get_author_by_id(author_id)
        return DefaultAuthorInfo(user_id=user_id, author=author)

    async def set_default_author(self, user_id: str, author_id: str | None) -> None:
        self._auth.check_set_default_author()
        await self._default_author_repository.set_default_author_id(user_id, author_id)
