from datetime import datetime as DateTime
from typing import cast
from uuid import uuid4

from news_fastapi.core.authors.dao import DefaultAuthorsDAO
from news_fastapi.core.authors.models import AuthorReferenceDataclass
from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.drafts.dao import DraftsDAO
from news_fastapi.core.drafts.exceptions import (
    AlreadyPublishedError,
    CreateDraftConflictError,
    CreateDraftError,
    UpdateDraftError,
)
from news_fastapi.core.drafts.models import Draft, DraftDataclass
from news_fastapi.core.exceptions import NotFoundError
from news_fastapi.core.news.dao import NewsDAO
from news_fastapi.core.news.models import NewsArticle, NewsArticleDataclass
from news_fastapi.core.utils import LoadPolicy, NotLoaded, Undefined, UndefinedType


class DraftsService:
    _auth: DraftsAuth
    _news_dao: NewsDAO
    _drafts_dao: DraftsDAO
    _default_authors_dao: DefaultAuthorsDAO

    def __init__(
        self,
        auth: DraftsAuth,
        news_dao: NewsDAO,
        drafts_dao: DraftsDAO,
        default_authors_dao: DefaultAuthorsDAO,
    ) -> None:
        self._auth = auth
        self._news_dao = news_dao
        self._drafts_dao = drafts_dao
        self._default_authors_dao = default_authors_dao

    def create_draft(self, news_id: str | None) -> Draft:
        self._auth.check_create_draft()
        if news_id is None:
            draft = self._create_draft_from_scratch()
        else:
            draft = self._create_draft_for_news_article(news_id)
        return draft

    def _create_draft_from_scratch(self) -> Draft:
        current_user_id = self._auth.get_current_user_id()
        author_id = self._default_authors_dao.get_default_author_id(current_user_id)
        if author_id is None:
            raise CreateDraftError("User has no default author set")
        draft: Draft = DraftDataclass(
            id=str(uuid4()),
            news_article=None,
            headline="",
            date_published=None,
            author=AuthorReferenceDataclass(id=author_id),
            text="",
            created_by_user_id=current_user_id,
            is_published=False,
        )
        draft = self._drafts_dao.save_draft(draft)
        return draft

    def _create_draft_for_news_article(self, news_id: str) -> Draft:
        try:
            draft = self._drafts_dao.get_not_published_draft_by_news_id(news_id)
            raise CreateDraftConflictError(
                news_id=news_id,
                draft_id=draft.id,
                created_by_user_id=draft.created_by_user_id,
            )
        except NotFoundError:
            pass  # no conflicting draft
        news_article = self._news_dao.get_news_article(news_id)
        draft = DraftDataclass(
            id=str(uuid4()),
            news_article=news_article,
            headline=news_article.headline,
            date_published=news_article.date_published,
            author=news_article.author,
            text=news_article.text,
            created_by_user_id=self._auth.get_current_user_id(),
            is_published=False,
        )
        draft = self._drafts_dao.save_draft(draft)
        return draft

    def get_draft(self, draft_id: str) -> Draft:
        self._auth.check_get_draft(draft_id)
        draft = self._drafts_dao.get_draft_by_id(draft_id)
        return draft

    def update_draft(
        self,
        draft_id: str,
        new_headline: str | UndefinedType = Undefined,
        new_date_published: DateTime | None | UndefinedType = Undefined,
        new_author_id: str | UndefinedType = Undefined,
        new_text: str | UndefinedType = Undefined,
    ) -> None:
        self._auth.check_update_draft(draft_id)
        draft = self._drafts_dao.get_draft_by_id(draft_id)
        if draft.is_published:
            raise UpdateDraftError("Can't update published draft")
        if new_headline is not Undefined:
            draft.headline = new_headline
        if new_date_published is not Undefined:
            draft.date_published = new_date_published
        if new_author_id is not Undefined:
            draft.author = AuthorReferenceDataclass(id=new_author_id)
        if new_text is not Undefined:
            draft.text = new_text
        self._drafts_dao.save_draft(draft)

    def delete_draft(self, draft_id: str) -> None:
        self._auth.check_delete_draft(draft_id)
        draft = self._drafts_dao.get_draft_by_id(draft_id)
        if draft.is_published:
            self._auth.check_delete_published_draft()
        self._drafts_dao.delete_drafts([draft])

    def publish_draft(self, draft_id: str) -> NewsArticle:
        draft = self._drafts_dao.get_draft_by_id(
            draft_id, load_news_article=LoadPolicy.FULL
        )
        if draft.is_published:
            raise AlreadyPublishedError("The draft is already published")
        draft.is_published = True
        self._drafts_dao.save_draft(draft)
        if draft.news_article is None:
            news_article = self._create_news_article_from_scratch(draft)
        else:
            news_article = self._update_news_article(draft)
        return news_article

    def _create_news_article_from_scratch(self, draft: Draft) -> NewsArticle:
        if draft.date_published is None:
            date_published = DateTime.now()
        else:
            date_published = draft.date_published
        news_article: NewsArticle = NewsArticleDataclass(
            id=str(uuid4()),
            headline=draft.headline,
            date_published=date_published,
            author=draft.author,
            text=draft.text,
            revoke_reason="",
        )
        news_article = self._news_dao.save_news_article(news_article)
        return news_article

    def _update_news_article(self, draft: Draft) -> NewsArticle:
        news_article = self._get_news_article_from_draft(draft)
        news_article.headline = draft.headline
        news_article.date_published = (
            DateTime.now() if draft.date_published is None else draft.date_published
        )
        news_article.author = draft.author
        news_article.text = draft.text
        news_article.revoke_reason = ""
        news_article = self._news_dao.save_news_article(news_article)
        return news_article

    def _get_news_article_from_draft(self, draft: Draft) -> NewsArticle:
        if isinstance(draft.news_article, NewsArticle):
            return draft.news_article
        draft = self._drafts_dao.get_draft_by_id(
            draft.id, load_news_article=LoadPolicy.FULL
        )
        return cast(NewsArticle, draft.news_article)
