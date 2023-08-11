from collections.abc import Iterable
from uuid import uuid4

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.dao import AuthorsDAO, DefaultAuthorsDAO
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.authors.models import AuthorDetails, AuthorOverview
from news_fastapi.core.drafts.dao import DraftsDAO
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.core.news.dao import NewsDAO


class AuthorsService:
    _auth: AuthorsAuth
    _dao: AuthorsDAO
    _news_dao: NewsDAO
    _drafts_dao: DraftsDAO
    _default_authors_dao: DefaultAuthorsDAO

    def __init__(
        self,
        auth: AuthorsAuth,
        dao: AuthorsDAO,
        news_dao: NewsDAO,
        drafts_dao: DraftsDAO,
        default_authors_dao: DefaultAuthorsDAO,
    ) -> None:
        self._auth = auth
        self._dao = dao
        self._news_dao = news_dao
        self._drafts_dao = drafts_dao
        self._default_authors_dao = default_authors_dao

    def create_author(self, name: str) -> AuthorOverview:
        if not self._auth.can_create_author():
            raise AuthorizationError("User doesn't have permission to create an author")
        author = AuthorDetails(id=str(uuid4()), name=name)
        self._dao.save_author_details(author)
        return AuthorOverview(id=author.id, name=author.name)

    def get_authors_list(self, offset: int, limit: int) -> list[AuthorOverview]:
        return self._dao.get_author_overview_list(offset, limit)

    def get_authors_in_bulk(self, id_list: Iterable[str]) -> dict[str, AuthorOverview]:
        return self._dao.get_author_overview_in_bulk(id_list)

    def update_author(self, author_id: str, new_name: str) -> None:
        if not self._auth.can_update_author(author_id):
            raise AuthorizationError(
                "User doesn't have permission to update the author"
            )
        author = self._dao.get_author_details_by_id(author_id)
        author.name = new_name
        self._dao.save_author_details(author)

    def delete_author(self, author_id: str) -> None:
        if not self._auth.can_delete_author(author_id):
            raise AuthorizationError(
                "User doesn't have permission to delete the author"
            )
        news_list = self._news_dao.get_news_overview_list_for_author(author_id)
        has_author_published_news = len(news_list) > 0
        if has_author_published_news:
            raise DeleteAuthorError(
                "Can't delete an author with at least one published news article"
            )
        drafts_list = self._drafts_dao.get_draft_overview_list_for_author(author_id)
        self._drafts_dao.delete_drafts(draft_ids=[draft.id for draft in drafts_list])
        self._dao.delete_author(author_id)

    def get_default_author(self, user_id: str) -> AuthorOverview | None:
        author_id = self._default_authors_dao.get_default_author_id(user_id)
        if author_id is None:
            return None
        author = self._dao.get_author_overview_by_id(author_id)
        return author

    def set_default_author(self, user_id: str, author_id: str | None) -> None:
        self._default_authors_dao.set_default_author_id(user_id, author_id)
