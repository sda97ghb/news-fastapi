from datetime import datetime as DateTime

from news_fastapi.application.drafts.auth import DraftsAuth
from news_fastapi.application.drafts.exceptions import (
    AlreadyPublishedError,
    CreateDraftConflictError,
    CreateDraftError,
    UpdateDraftError,
)
from news_fastapi.application.transaction import TransactionManager
from news_fastapi.domain.authors import DefaultAuthorRepository
from news_fastapi.domain.drafts import Draft, DraftFactory, DraftRepository
from news_fastapi.domain.news import (
    NewsArticle,
    NewsArticleFactory,
    NewsArticleRepository,
)
from news_fastapi.utils.exceptions import NotFoundError
from news_fastapi.utils.sentinels import Undefined, UndefinedType


class DraftsService:
    _auth: DraftsAuth
    _transaction_manager: TransactionManager
    _draft_factory: DraftFactory
    _draft_repository: DraftRepository
    _default_author_repository: DefaultAuthorRepository
    _news_article_factory: NewsArticleFactory
    _news_article_repository: NewsArticleRepository

    def __init__(
        self,
        auth: DraftsAuth,
        transaction_manager: TransactionManager,
        draft_factory: DraftFactory,
        draft_repository: DraftRepository,
        default_author_repository: DefaultAuthorRepository,
        news_article_factory: NewsArticleFactory,
        news_article_repository: NewsArticleRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._draft_factory = draft_factory
        self._draft_repository = draft_repository
        self._default_author_repository = default_author_repository
        self._news_article_factory = news_article_factory
        self._news_article_repository = news_article_repository

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

    async def get_draft(self, draft_id: str) -> Draft:
        self._auth.check_get_draft(draft_id)
        draft = await self._draft_repository.get_draft_by_id(draft_id)
        return draft

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
        async with self._transaction_manager.in_transaction():
            draft = await self._draft_repository.get_draft_by_id(draft_id)
            if draft.is_published:
                raise AlreadyPublishedError("The draft is already published")
            draft.is_published = True
            await self._draft_repository.save(draft)
            if draft.news_article_id is None:
                news_article = await self._create_news_article_from_scratch(draft)
            else:
                news_article = (
                    await self._news_article_repository.get_news_article_by_id(
                        draft.news_article_id
                    )
                )
                self._fill_news_article_from_draft(news_article, draft)
                news_article.revoke_reason = ""
            await self._news_article_repository.save(news_article)
            return news_article

    async def _create_news_article_from_scratch(self, draft: Draft) -> NewsArticle:
        news_article_id = await self._news_article_repository.next_identity()
        news_article = self._news_article_factory.create_news_article_from_scratch(
            news_article_id=news_article_id,
            headline=draft.headline,
            date_published=self._pick_date_published(draft.date_published),
            author_id=draft.author_id,
            text=draft.text,
        )
        return news_article

    def _fill_news_article_from_draft(
        self, news_article: NewsArticle, draft: Draft
    ) -> None:
        news_article.headline = draft.headline
        news_article.date_published = self._pick_date_published(draft.date_published)
        news_article.author_id = draft.author_id
        news_article.text = draft.text

    def _pick_date_published(
        self, date_published_from_draft: DateTime | None
    ) -> DateTime:
        if date_published_from_draft:
            return date_published_from_draft
        return DateTime.now()
