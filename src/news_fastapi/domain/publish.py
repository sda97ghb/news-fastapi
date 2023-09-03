from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Self

from news_fastapi.domain.draft import Draft, DraftRepository
from news_fastapi.domain.news_article import (
    NewsArticle,
    NewsArticleFactory,
    NewsArticleRepository,
)


@dataclass
class DraftValidationProblem:
    message: str
    user_message: str


@dataclass
class EmptyHeadlineProblem(DraftValidationProblem):
    message: str = "Empty headline"
    user_message: str = "Заголовок не заполнен"


@dataclass
class TooLongHeadlineProblem(DraftValidationProblem):
    current_length: int
    max_length: int

    @classmethod
    def create(cls, current_length: int, max_length: int) -> Self:
        return cls(
            message="Too long headline",
            user_message=(
                f"Заголовок слишком длинный (сейчас {current_length} "
                f"символов, должен быть не больше {max_length} "
                "символов)"
            ),
            current_length=current_length,
            max_length=max_length,
        )


@dataclass
class NoImageProblem(DraftValidationProblem):
    message: str = "No image set"
    user_message: str = "Не задано изображение"


@dataclass
class EmptyImageURLProblem(DraftValidationProblem):
    message: str = "Empty image url"
    user_message: str = "Не задан URL изображения"


@dataclass
class EmptyImageDescriptionProblem(DraftValidationProblem):
    message: str = "Empty image description"
    user_message: str = "Подпись под изображением не заполнена"


@dataclass
class TooLongImageDescriptionProblem(DraftValidationProblem):
    current_length: int
    max_length: int

    @classmethod
    def create(cls, current_length: int, max_length: int) -> Self:
        return cls(
            message="Too long image description",
            user_message=(
                f"Подпись под изображением слишком длинная (сейчас {current_length} "
                f"символов, должна быть не больше {max_length} символов)"
            ),
            current_length=current_length,
            max_length=max_length,
        )


@dataclass
class EmptyImageAuthorProblem(DraftValidationProblem):
    message: str = "Empty image author"
    user_message: str = "Не указан автор изображения"


@dataclass
class EmptyTextProblem(DraftValidationProblem):
    message: str = "Empty text"
    user_message: str = "Текст не заполнен"


class DraftValidator:
    _draft: Draft
    _problems: list[DraftValidationProblem]
    _max_headline_length: int
    _max_image_description_length: int

    def __init__(
        self,
        draft: Draft,
        max_headline_length: int = 60,
        max_image_description_length: int = 200,
    ) -> None:
        self._draft = draft
        self._problems = []
        self._max_headline_length = max_headline_length
        self._max_image_description_length = max_image_description_length

    def _append_problem(self, problem: DraftValidationProblem) -> None:
        self._problems.append(problem)

    def validate(self) -> list[DraftValidationProblem]:
        self._problems = []
        self._validate_headline()
        self._validate_image()
        self._validate_text()
        return self._problems

    def _validate_headline(self) -> None:
        headline = self._draft.headline.strip()
        headline_length = len(headline)
        if headline_length == 0:
            self._append_problem(EmptyHeadlineProblem())
        if headline_length > self._max_headline_length:
            self._append_problem(
                TooLongHeadlineProblem.create(
                    current_length=headline_length, max_length=self._max_headline_length
                )
            )

    def _validate_image(self) -> None:
        image = self._draft.image
        if image is None:
            self._append_problem(NoImageProblem())
            return
        if image.url == "":
            self._append_problem(EmptyImageURLProblem())
        description_length = len(image.description)
        if description_length == 0:
            self._append_problem(EmptyImageDescriptionProblem())
        if description_length > self._max_image_description_length:
            self._append_problem(
                TooLongImageDescriptionProblem.create(
                    current_length=description_length,
                    max_length=self._max_image_description_length,
                )
            )
        if image.author == "":
            self._append_problem(EmptyImageAuthorProblem())

    def _validate_text(self) -> None:
        if len(self._draft.text.strip()) == 0:
            self._append_problem(EmptyTextProblem())


class PublishDraftError(Exception):
    pass


class DraftAlreadyPublishedError(PublishDraftError):
    pass


class InvalidDraftError(Exception):
    problems: list[DraftValidationProblem]

    def __init__(self, problems: list[DraftValidationProblem]) -> None:
        self.problems = problems


def pick_date_published(date_published_from_draft: DateTime | None) -> DateTime:
    if date_published_from_draft:
        return date_published_from_draft
    return DateTime.now()


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
        draft.mark_as_published()
        await self._draft_repository.save(draft)
        return draft

    def _validate_draft(self, draft: Draft) -> None:
        problems = DraftValidator(draft).validate()
        if problems:
            raise InvalidDraftError(problems)

    async def _create_news_article_from_scratch(self, draft: Draft) -> NewsArticle:
        news_article_id = await self._news_article_repository.next_identity()
        if draft.image is None:
            raise ValueError("Draft with no image can not be published")
        news_article = self._news_article_factory.create_news_article_from_scratch(
            news_article_id=news_article_id,
            headline=draft.headline,
            date_published=pick_date_published(draft.date_published),
            author_id=draft.author_id,
            image=draft.image,
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
        if news_article.is_revoked:
            news_article.cancel_revoke()
        return news_article

    def _fill_news_article_from_draft(
        self, news_article: NewsArticle, draft: Draft
    ) -> None:
        if draft.image is None:
            raise ValueError("Draft with no image can not be published")
        news_article.headline = draft.headline
        news_article.date_published = pick_date_published(draft.date_published)
        news_article.author_id = draft.author_id
        news_article.image = draft.image
        news_article.text = draft.text
