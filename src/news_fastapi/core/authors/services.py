from uuid import uuid4

from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.dao import AuthorsDAO, DefaultAuthorsDAO
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.authors.models import Author, AuthorDataclass
from news_fastapi.core.drafts.dao import DraftsDAO
from news_fastapi.core.news.dao import NewsDAO
from news_fastapi.core.utils import Undefined, UndefinedType


class AuthorsListService:
    _dao: AuthorsDAO

    def get_page(self, offset: int = 0, limit: int = 50) -> list[Author]:
        return self._dao.get_authors_list(offset, limit)


class AuthorsService:
    _auth: AuthorsAuth
    _dao: AuthorsDAO
    _news_dao: NewsDAO
    _drafts_dao: DraftsDAO

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

    def create_author(self, name: str) -> Author:
        self._auth.check_create_author()
        author: Author = AuthorDataclass(id=str(uuid4()), name=name)
        author = self._dao.save_author(author)
        return author

    def update_author(
        self, author_id: str, new_name: str | UndefinedType = Undefined
    ) -> None:
        self._auth.check_update_author(author_id)
        author = self._dao.get_author_by_id(author_id)
        if new_name is not Undefined:
            author.name = new_name
        self._dao.save_author(author)

    def delete_author(self, author_id: str) -> None:
        self._auth.check_delete_author(author_id)
        news_ref_list = self._news_dao.get_news_article_references_for_author(author_id)
        has_author_published_news = len(news_ref_list) > 0
        if has_author_published_news:
            raise DeleteAuthorError(
                "Can't delete an author with at least one published news article"
            )
        draft_ref_list = self._drafts_dao.get_draft_references_for_author(author_id)
        self._drafts_dao.delete_drafts(draft_ref_list)
        self._dao.delete_author(author_id)


class DefaultAuthorsService:
    _authors_dao: AuthorsDAO
    _default_authors_dao: DefaultAuthorsDAO

    def __init__(
        self, authors_dao: AuthorsDAO, default_authors_dao: DefaultAuthorsDAO
    ) -> None:
        self._authors_dao = authors_dao
        self._default_authors_dao = default_authors_dao

    def get_default_author(self, user_id: str) -> Author | None:
        author_id = self._default_authors_dao.get_default_author_id(user_id)
        if author_id is None:
            return None
        author = self._authors_dao.get_author_by_id(author_id)
        return author

    def set_default_author(self, user_id: str, author_id: str | None) -> None:
        self._default_authors_dao.set_default_author_id(user_id, author_id)
