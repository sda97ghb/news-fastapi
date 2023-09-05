from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.drafts.exceptions import (
    CreateDraftConflictError,
    CreateDraftError,
    UpdateDraftError,
)
from news_fastapi.core.transaction import TransactionManager
from news_fastapi.domain.author import DefaultAuthorRepository
from news_fastapi.domain.draft import Draft, DraftFactory, DraftRepository
from news_fastapi.domain.news_article import NewsArticle, NewsArticleRepository
from news_fastapi.domain.publish import PublishService
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from news_fastapi.utils.sentinels import Undefined, UndefinedType


@dataclass
class CreateDraftResult:
    draft: Draft


class CreateDraftService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _draft_factory: DraftFactory
    _draft_repository: DraftRepository
    _default_author_repository: DefaultAuthorRepository
    _news_article_repository: NewsArticleRepository

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        draft_factory: DraftFactory,
        draft_repository: DraftRepository,
        default_author_repository: DefaultAuthorRepository,
        news_article_repository: NewsArticleRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._draft_factory = draft_factory
        self._draft_repository = draft_repository
        self._default_author_repository = default_author_repository
        self._news_article_repository = news_article_repository

    async def create_draft(self, news_article_id: str | None) -> CreateDraftResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_create_draft()
            if news_article_id is None:
                draft = await self._create_draft_from_scratch()
            else:
                draft = await self._create_draft_for_news_article(news_article_id)
            await self._draft_repository.save(draft)
            return CreateDraftResult(draft=draft)

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
        draft = self._draft_factory.create_draft_from_news_article(
            news_article=news_article, draft_id=draft_id, user_id=current_user_id
        )
        return draft


@dataclass
class UpdateDraftResult:
    updated_draft: Draft


class UpdateDraftService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _draft_repository: DraftRepository

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        draft_repository: DraftRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._draft_repository = draft_repository

    async def update_draft(
        self,
        draft_id: str,
        new_headline: str | UndefinedType = Undefined,
        new_date_published: DateTime | None | UndefinedType = Undefined,
        new_author_id: str | UndefinedType = Undefined,
        new_image: Image | None | UndefinedType = Undefined,
        new_text: str | UndefinedType = Undefined,
    ) -> UpdateDraftResult:
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
            if new_image is not Undefined:
                draft.image = new_image
            if new_text is not Undefined:
                draft.text = new_text
            await self._draft_repository.save(draft)
            return UpdateDraftResult(updated_draft=draft)


@dataclass
class DeleteDraftResult:
    deleted_draft_id: str


class DeleteDraftService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _draft_repository: DraftRepository

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        draft_repository: DraftRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._draft_repository = draft_repository

    async def delete_draft(self, draft_id: str) -> DeleteDraftResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_delete_draft(draft_id)
            draft = await self._draft_repository.get_draft_by_id(draft_id)
            if draft.is_published:
                self._auth.check_delete_published_draft()
            await self._draft_repository.delete(draft)
            return DeleteDraftResult(deleted_draft_id=draft_id)

    async def delete_drafts_of_author(self, author_id: str) -> None:
        async with self._transaction_manager.in_transaction():
            drafts = await self._draft_repository.get_drafts_for_author(author_id)
            for draft in drafts:
                await self._draft_repository.delete(draft)


@dataclass
class PublishDraftResult:
    published_news_article: NewsArticle


class PublishDraftService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _publish_service: PublishService

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        publish_service: PublishService,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._publish_service = publish_service

    async def publish_draft(self, draft_id: str) -> PublishDraftResult:
        self._auth.check_publish_draft()
        async with self._transaction_manager.in_transaction():
            news_article = await self._publish_service.publish_draft(draft_id)
            return PublishDraftResult(published_news_article=news_article)
