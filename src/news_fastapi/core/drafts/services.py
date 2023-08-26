from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.drafts.exceptions import (
    CreateDraftConflictError,
    CreateDraftError,
    UpdateDraftError,
)
from news_fastapi.core.transaction import TransactionManager
from news_fastapi.domain.authors import (
    Author,
    AuthorRepository,
    DefaultAuthorRepository,
)
from news_fastapi.domain.drafts import Draft, DraftFactory, DraftRepository
from news_fastapi.domain.news import NewsArticle, NewsArticleRepository
from news_fastapi.domain.publish import PublishService
from news_fastapi.utils.exceptions import NotFoundError
from news_fastapi.utils.sentinels import Undefined, UndefinedType


@dataclass
class DraftListItem:
    draft: Draft


@dataclass
class DraftView:
    draft: Draft
    author: Author


class DraftsListService:
    _draft_repository: DraftRepository

    def __init__(self, draft_repository: DraftRepository) -> None:
        self._draft_repository = draft_repository

    async def get_page(self, offset: int, limit: int) -> list[DraftListItem]:
        drafts_list = await self._draft_repository.get_drafts_list(offset, limit)
        return [DraftListItem(draft=draft) for draft in drafts_list]


class DraftsService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _draft_factory: DraftFactory
    _draft_repository: DraftRepository
    _default_author_repository: DefaultAuthorRepository
    _news_article_repository: NewsArticleRepository
    _author_repository: AuthorRepository
    _publish_service: PublishService

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        draft_factory: DraftFactory,
        draft_repository: DraftRepository,
        default_author_repository: DefaultAuthorRepository,
        news_article_repository: NewsArticleRepository,
        author_repository: AuthorRepository,
        publish_service: PublishService,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._draft_factory = draft_factory
        self._draft_repository = draft_repository
        self._default_author_repository = default_author_repository
        self._news_article_repository = news_article_repository
        self._author_repository = author_repository
        self._publish_service = publish_service

    async def create_draft(self, news_article_id: str | None) -> Draft:
        self._auth.check_create_draft()
        if news_article_id is None:
            draft = await self._create_draft_from_scratch()
        else:
            draft = await self._create_draft_for_news_article(news_article_id)
        await self._draft_repository.save(draft)
        return draft

    async def _create_draft_from_scratch(self) -> Draft:
        current_user_id = self._auth.get_current_user_id()
        author_id = await self._default_author_repository.get_default_author_id(
            current_user_id
        )
        if author_id is None:
            raise CreateDraftError("User has no default author set")
        draft_id = await self._draft_repository.next_identity()
        draft = self._draft_factory.create_draft_from_scratch(
            draft_id=draft_id, user_id=current_user_id, author_id=author_id
        )
        return draft

    async def _create_draft_for_news_article(self, news_article_id: str) -> Draft:
        try:
            draft = await self._draft_repository.get_not_published_draft_by_news_id(
                news_article_id
            )
            raise CreateDraftConflictError(
                news_article_id=news_article_id,
                draft_id=draft.id,
                created_by_user_id=draft.created_by_user_id,
            )
        except NotFoundError:
            pass  # no conflicting draft
        current_user_id = self._auth.get_current_user_id()
        news_article = await self._news_article_repository.get_news_article_by_id(
            news_article_id
        )
        draft_id = await self._draft_repository.next_identity()
        draft = self._draft_factory.create_draft(
            draft_id=draft_id,
            news_article_id=news_article.id,
            headline=news_article.headline,
            date_published=news_article.date_published,
            author_id=news_article.author_id,
            text=news_article.text,
            created_by_user_id=current_user_id,
            is_published=False,
        )
        return draft

    async def get_draft(self, draft_id: str) -> DraftView:
        self._auth.check_get_draft(draft_id)
        draft = await self._draft_repository.get_draft_by_id(draft_id)
        author = await self._author_repository.get_author_by_id(draft.author_id)
        return DraftView(draft=draft, author=author)

    async def update_draft(
        self,
        draft_id: str,
        new_headline: str | UndefinedType = Undefined,
        new_date_published: DateTime | None | UndefinedType = Undefined,
        new_author_id: str | UndefinedType = Undefined,
        new_text: str | UndefinedType = Undefined,
    ) -> None:
        async with self._transaction_manager.in_transaction():
            self._auth.check_update_draft(draft_id)
            draft = await self._draft_repository.get_draft_by_id(draft_id)
            if draft.is_published:
                raise UpdateDraftError("Can't update published draft")
            if new_headline is not Undefined:
                draft.headline = new_headline
            if new_date_published is not Undefined:
                draft.date_published = new_date_published
            if new_author_id is not Undefined:
                draft.author_id = new_author_id
            if new_text is not Undefined:
                draft.text = new_text
            await self._draft_repository.save(draft)

    async def delete_draft(self, draft_id: str) -> None:
        async with self._transaction_manager.in_transaction():
            self._auth.check_delete_draft(draft_id)
            draft = await self._draft_repository.get_draft_by_id(draft_id)
            if draft.is_published:
                self._auth.check_delete_published_draft()
            await self._draft_repository.delete(draft)

    async def publish_draft(self, draft_id: str) -> NewsArticle:
        self._auth.check_publish_draft()
        async with self._transaction_manager.in_transaction():
            news_article = await self._publish_service.publish_draft(draft_id)
            return news_article

    async def delete_drafts_of_author(self, author_id: str) -> None:
        async with self._transaction_manager.in_transaction():
            drafts = await self._draft_repository.get_drafts_for_author(author_id)
            for draft in drafts:
                await self._draft_repository.delete(draft)
