from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Any
from unittest.mock import Mock

from news_fastapi.core.authors.commands import CreateAuthorResult
from news_fastapi.core.authors.default_author import DefaultAuthorInfo
from news_fastapi.core.authors.queries import (
    AuthorDetails,
    AuthorsListItem,
    AuthorsListPage,
)
from news_fastapi.core.drafts.exceptions import CreateDraftConflictError
from news_fastapi.core.drafts.queries import (
    DraftDetails,
    DraftDetailsAuthor,
    DraftsListItem,
    DraftsListPage,
)
from news_fastapi.core.news.queries import (
    NewsArticleDetails,
    NewsArticleDetailsAuthor,
    NewsArticlesListAuthor,
    NewsArticlesListItem,
    NewsArticlesListPage,
)
from news_fastapi.domain.publish import DraftValidationProblem, InvalidDraftError
from news_fastapi.domain.value_objects import Image


class NewsListDataFixture:
    def as__news_articles_list_service__get_page__return_value(
        self, offset: int = 0, limit: int = 10
    ) -> NewsArticlesListPage:
        return NewsArticlesListPage(
            offset=offset,
            limit=limit,
            items=[
                NewsArticlesListItem(
                    news_article_id="aaaaaaaa-aaaa-aaaa-0001-000000000001",
                    headline="The Headline One",
                    date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
                    author=NewsArticlesListAuthor(
                        author_id="aaaaaaaa-aaaa-aaaa-0001-000000000002",
                        name="John Doe",
                    ),
                    revoke_reason=None,
                ),
                NewsArticlesListItem(
                    news_article_id="aaaaaaaa-aaaa-aaaa-0002-000000000001",
                    headline="The Headline Two",
                    date_published=DateTime.fromisoformat("2023-01-01T12:10:00+00:00"),
                    author=NewsArticlesListAuthor(
                        author_id="aaaaaaaa-aaaa-aaaa-0002-000000000002",
                        name="Sarah Gray",
                    ),
                    revoke_reason="Fake",
                ),
            ],
        )

    def as__rest_api__news__get__json(self) -> Any:
        return [
            {
                "id": "aaaaaaaa-aaaa-aaaa-0001-000000000001",
                "headline": "The Headline One",
                "datePublished": "2023-01-01T12:00:00+00:00",
                "author": {
                    "id": "aaaaaaaa-aaaa-aaaa-0001-000000000002",
                    "name": "John Doe",
                },
                "revokeReason": None,
            },
            {
                "id": "aaaaaaaa-aaaa-aaaa-0002-000000000001",
                "headline": "The Headline Two",
                "datePublished": "2023-01-01T12:10:00+00:00",
                "author": {
                    "id": "aaaaaaaa-aaaa-aaaa-0002-000000000002",
                    "name": "Sarah Gray",
                },
                "revokeReason": "Fake",
            },
        ]


class NewsArticleDataFixture:
    news_article_id: str

    def __init__(self, news_article_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"):
        self.news_article_id = news_article_id

    def as__news_article_details_service__get_news_article__return_value(
        self,
    ) -> NewsArticleDetails:
        return NewsArticleDetails(
            news_article_id=self.news_article_id,
            headline="The Healine One",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author=NewsArticleDetailsAuthor(
                author_id="aaaaaaaa-aaaa-aaaa-0001-000000000002",
                name="John Doe",
            ),
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="The author of the image",
            ),
            text="The text of the news article.",
            revoke_reason=None,
        )

    def as__rest_api__news__news_article_id__get__json(self) -> Any:
        return {
            "id": self.news_article_id,
            "headline": "The Healine One",
            "datePublished": "2023-01-01T12:00:00+00:00",
            "author": {
                "id": "aaaaaaaa-aaaa-aaaa-0001-000000000002",
                "name": "John Doe",
            },
            "image": {
                "url": "https://example.com/images/1234",
                "description": "The description of the image",
                "author": "The author of the image",
            },
            "text": "The text of the news article.",
            "revokeReason": None,
        }


class DraftsListDataFixture:
    def as__drafts_list_service__get_page__return_value(
        self, offset: int = 0, limit: int = 10
    ) -> DraftsListPage:
        return DraftsListPage(
            offset=offset,
            limit=limit,
            items=[
                DraftsListItem(
                    draft_id="aaaaaaaa-aaaa-aaaa-0001-000000000001",
                    news_article_id=None,
                    headline="The Headline One",
                    created_by_user_id="aaaaaaaa-aaaa-aaaa-0001-000000000003",
                    is_published=False,
                ),
                DraftsListItem(
                    draft_id="aaaaaaaa-aaaa-aaaa-0002-000000000001",
                    news_article_id="aaaaaaaa-aaaa-aaaa-0002-000000000002",
                    headline="The Headline Two",
                    created_by_user_id="aaaaaaaa-aaaa-aaaa-0002-000000000003",
                    is_published=True,
                ),
            ],
        )

    def as__rest_api__drafts__get__json(self) -> Any:
        return [
            {
                "id": "aaaaaaaa-aaaa-aaaa-0001-000000000001",
                "newsArticleId": None,
                "headline": "The Headline One",
                "createdByUserId": "aaaaaaaa-aaaa-aaaa-0001-000000000003",
                "isPublished": False,
            },
            {
                "id": "aaaaaaaa-aaaa-aaaa-0002-000000000001",
                "newsArticleId": "aaaaaaaa-aaaa-aaaa-0002-000000000002",
                "headline": "The Headline Two",
                "createdByUserId": "aaaaaaaa-aaaa-aaaa-0002-000000000003",
                "isPublished": True,
            },
        ]


class DraftDataFixture:
    draft_id: str

    def __init__(self, draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001") -> None:
        self.draft_id = draft_id

    def as__draft_details_service__get_draft(self) -> Any:
        return DraftDetails(
            draft_id=self.draft_id,
            news_article_id="aaaaaaaa-aaaa-aaaa-0001-000000000002",
            created_by_user_id="aaaaaaaa-aaaa-aaaa-0001-000000000003",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author=DraftDetailsAuthor(
                author_id="aaaaaaaa-aaaa-aaaa-0001-000000000004",
                name="John Doe",
            ),
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="The author of the image",
            ),
            text="The text of the draft.",
            is_published=False,
        )

    def as__rest_api__drafts__draft_id__get__json(self) -> Any:
        return {
            "id": self.draft_id,
            "newsArticleId": "aaaaaaaa-aaaa-aaaa-0001-000000000002",
            "headline": "The Headline",
            "datePublished": "2023-01-01T12:00:00+00:00",
            "author": {
                "id": "aaaaaaaa-aaaa-aaaa-0001-000000000004",
                "name": "John Doe",
            },
            "image": {
                "url": "https://example.com/images/1234",
                "description": "The description of the image",
                "author": "The author of the image",
            },
            "text": "The text of the draft.",
            "createdByUserId": "aaaaaaaa-aaaa-aaaa-0001-000000000003",
            "isPublished": False,
        }


class CreateDraftDataFixture:
    draft_id: str
    news_article_id: str | None

    def __init__(
        self,
        draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001",
        news_article_id: str | None = None,
    ):
        self.draft_id = draft_id
        self.news_article_id = news_article_id

    def as__create_draft_service__create_draft__return_value(self) -> Any:
        result = Mock()
        result.draft.id = self.draft_id
        return result

    def as__rest_api__drafts__post__json(self) -> Any:
        return {"draftId": self.draft_id}


class CreateDraftConflictDataFixture:
    draft_id: str
    news_article_id: str
    created_by_user_id: str

    def __init__(
        self,
        draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001",
        news_article_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000002",
        created_by_user_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000003",
    ) -> None:
        self.draft_id = draft_id
        self.news_article_id = news_article_id
        self.created_by_user_id = created_by_user_id

    def as__create_draft_service__create_draft__side_effect(
        self,
    ) -> CreateDraftConflictError:
        return CreateDraftConflictError(
            news_article_id=self.news_article_id,
            draft_id=self.draft_id,
            created_by_user_id=self.created_by_user_id,
        )

    def as__rest_api__drafts__post__json(self) -> Any:
        return {
            "draftId": self.draft_id,
            "createdBy": {"userId": self.created_by_user_id},
        }


@dataclass
class UpdateDraftDataFixture:
    draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    new_headline: str = "NEW headline"
    new_date_published: DateTime = DateTime.fromisoformat("2023-01-01T12:00:00+00:00")
    new_author_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
    new_image: Image = Image(
        url="https://example.com/images/99999-NEW",
        description="NEW image description",
        author="NEW image author",
    )
    new_text: str = "NEW text"

    def as__rest_api__drafts__draft_id__put__request_body(self) -> Any:
        return {
            "headline": self.new_headline,
            "datePublished": self.new_date_published.isoformat(),
            "authorId": self.new_author_id,
            "image": {
                "url": self.new_image.url,
                "description": self.new_image.description,
                "author": self.new_image.author,
            },
            "text": self.new_text,
        }


@dataclass
class PublishDraftDataFixture:
    draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    news_article_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000002"

    def as__publish_draft_service__publish_draft__return_value(self) -> Any:
        result = Mock()
        result.published_news_article.id = self.news_article_id
        return result

    def as__rest_api__drafts__draft_id__publish__json(self) -> Any:
        return {"newsArticleId": self.news_article_id}


@dataclass
class PublishDraftWithValidationProblemsDataFixture:
    draft_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    problem_1_message: str = "Empty headline"
    problem_1_user_message: str = "Заголовок не заполнен"
    problem_2_message: str = "Empty text"
    problem_2_user_message: str = "Текст не заполнен"

    def as__publish_draft_service__publish_draft__side_effect(self) -> Any:
        return InvalidDraftError(
            problems=[
                DraftValidationProblem(
                    message=self.problem_1_message,
                    user_message=self.problem_1_user_message,
                ),
                DraftValidationProblem(
                    message=self.problem_2_message,
                    user_message=self.problem_2_user_message,
                ),
            ]
        )

    def as__rest_api__drafts__draft_id__publish__json(self) -> Any:
        return {
            "problems": [
                {
                    "message": self.problem_1_message,
                    "userMessage": self.problem_1_user_message,
                },
                {
                    "message": self.problem_2_message,
                    "userMessage": self.problem_2_user_message,
                },
            ],
        }


class AuthorsListDataFixture:
    def as__authors_list_service__get_page__return_value(
        self, offset: int = 10, limit: int = 50
    ) -> Any:
        return AuthorsListPage(
            offset=offset,
            limit=limit,
            items=[
                AuthorsListItem(
                    author_id="aaaaaaaa-aaaa-aaaa-0001-000000000001",
                    name="Jim Blue",
                ),
                AuthorsListItem(
                    author_id="aaaaaaaa-aaaa-aaaa-0002-000000000001",
                    name="Ophelia Green",
                ),
            ],
        )

    def as__rest_api__authors__get__json(self) -> Any:
        return [
            {
                "id": "aaaaaaaa-aaaa-aaaa-0001-000000000001",
                "name": "Jim Blue",
            },
            {
                "id": "aaaaaaaa-aaaa-aaaa-0002-000000000001",
                "name": "Ophelia Green",
            },
        ]


@dataclass
class CreateAuthorDataFixture:
    name: str = "John Doe"
    author_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"

    def as__create_author_service__create_author__return_value(self) -> Any:
        author = Mock()
        author.id = self.author_id
        return CreateAuthorResult(author=author)

    def as__rest_api__authors__post__request_json(self) -> Any:
        return {"name": self.name}

    def as__rest_api__authors__post__json(self) -> Any:
        return {"authorId": self.author_id}


@dataclass
class AuthorDataFixture:
    author_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    name: str = "John Doe"

    def as__author_details_service__get_author__return_value(self) -> Any:
        return AuthorDetails(author_id=self.author_id, name=self.name)

    def as__rest_api__authors__author_id__get__json(self) -> Any:
        return {"id": self.author_id, "name": self.name}


@dataclass
class UpdateAuthorDataFixture:
    author_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    new_name: str = "Joe Smith"

    def as__update_author_service__update_author__return_value(self) -> Any:
        result = Mock()
        result.updated_author.id = self.author_id
        result.updated_author.name = self.new_name
        return result

    def as__rest_api__authors__author_id__put__request_json(self) -> Any:
        return {"name": self.new_name}


@dataclass
class DefaultAuthorDataFixture:
    user_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
    author_id: str = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
    name: str = "John Doe"

    def as__default_author_service__get_default_author__return_value(self) -> Any:
        author = Mock()
        author.id = self.author_id
        author.name = self.name
        return DefaultAuthorInfo(user_id=self.user_id, author=author)

    def as__rest_api__authors__default__get__json(self) -> Any:
        return {
            "author": {
                "id": self.author_id,
                "name": self.name,
            },
        }
