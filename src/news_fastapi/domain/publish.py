from dataclasses import dataclass
from datetime import datetime as DateTime

from news_fastapi.domain.drafts import Draft, DraftRepository
from news_fastapi.domain.news import (
    NewsArticle,
    NewsArticleFactory,
    NewsArticleRepository,
)


@dataclass
class DraftValidationProblem:
    message: str
    user_message: str


class DraftValidator:
    _draft: Draft
    _problems: list[DraftValidationProblem]

    def __init__(self, draft: Draft) -> None:
        self._draft = draft
        self._problems = []

    def validate(self) -> list[DraftValidationProblem]:
        self._problems = []
        self._validate_not_published()
        self._validate_headline()
        self._validate_text()
        return self._problems

    def _validate_not_published(self) -> None:
        if self._draft.is_published:
            self._problems.append(
                DraftValidationProblem(
                    message="The draft is already published",
                    user_message="Этот черновик уже был опубликован, создайте новый",
                )
            )

    def _validate_headline(self) -> None:
        headline = self._draft.headline.strip()
        headline_length = len(headline)
        if headline_length == 0:
            self._problems.append(
                DraftValidationProblem(
                    message="Empty headline",
                    user_message="Заголовок не заполнен",
                )
            )
        max_headline_length = 60
        if headline_length > max_headline_length:
            self._problems.append(
                DraftValidationProblem(
                    message="Too long headline",
                    user_message=(
                        f"Заголовок слишком длинный (сейчас {headline_length} "
                        f"символов, должен быть не больше {max_headline_length} "
                        "символов)"
                    ),
                )
            )

    def _validate_text(self) -> None:
        if len(self._draft.text.strip()) == 0:
            self._problems.append(
                DraftValidationProblem(
                    message="Empty text",
                    user_message="Текст не заполнен",
                )
            )


class PublishDraftError(Exception):
    pass


class DraftAlreadyPublishedError(PublishDraftError):
    pass


class InvalidDraftError(Exception):
    problems: list[DraftValidationProblem]

    def __init__(self, problems: list[DraftValidationProblem]) -> None:
        self.problems = problems


class PublishService:
    _draft_repository: DraftRepository
    _news_article_factory: NewsArticleFactory
    _news_article_repository: NewsArticleRepository

    def __init__(
        self,
        draft_repository: DraftRepository,
        news_article_factory: NewsArticleFactory,
        news_article_repository: NewsArticleRepository,
    ) -> None:
        self._draft_repository = draft_repository
        self._news_article_factory = news_article_factory
        self._news_article_repository = news_article_repository

    async def publish_draft(self, draft_id: str) -> NewsArticle:
        draft = await self._load_draft_for_publishing(draft_id)
        self._validate_draft(draft)
        if draft.news_article_id is None:
            news_article = await self._create_news_article_from_scratch(draft)
        else:
            news_article = await self._update_existing_news_article(
                draft, draft.news_article_id
            )
        await self._news_article_repository.save(news_article)
        return news_article

    async def _load_draft_for_publishing(self, draft_id: str) -> Draft:
        draft = await self._draft_repository.get_draft_by_id(draft_id)
        if draft.is_published:
            raise DraftAlreadyPublishedError("The draft is already published")
        draft.is_published = True
        await self._draft_repository.save(draft)
        return draft

    def _validate_draft(self, draft: Draft) -> None:
        problems = DraftValidator(draft).validate()
        if problems:
            raise InvalidDraftError(problems)

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

    async def _update_existing_news_article(
        self, draft: Draft, news_article_id: str
    ) -> NewsArticle:
        news_article = await self._news_article_repository.get_news_article_by_id(
            news_article_id
        )
        self._fill_news_article_from_draft(news_article, draft)
        news_article.revoke_reason = None
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
