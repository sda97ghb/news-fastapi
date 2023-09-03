from dataclasses import replace
from datetime import datetime as DateTime, timedelta as TimeDelta
from unittest import IsolatedAsyncioTestCase, TestCase

from news_fastapi.domain.common import Image
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.publish import (
    DraftValidationProblem,
    DraftValidator,
    EmptyHeadlineProblem,
    EmptyImageAuthorProblem,
    EmptyImageDescriptionProblem,
    EmptyImageURLProblem,
    EmptyTextProblem,
    NoImageProblem,
    PublishService,
    TooLongHeadlineProblem,
    TooLongImageDescriptionProblem,
    pick_date_published,
)
from tests.domain.fixtures import (
    TestDraft,
    TestDraftFactory,
    TestDraftRepository,
    TestNewsArticleFactory,
    TestNewsArticleRepository,
)
from tests.utils import AssertMixin


class DraftValidatorTests(AssertMixin, TestCase):
    def setUp(self) -> None:
        self.max_headline_length = 100
        self.max_image_description_length = 200

    def create_valid_draft(self) -> TestDraft:
        return TestDraft(
            id="11111111-1111-1111-1111-111111111111",
            news_article_id=None,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The news article's text.",
            created_by_user_id="33333333-3333-3333-3333-333333333333",
            is_published=False,
        )

    def validate_draft(self, draft: Draft) -> list[DraftValidationProblem]:
        validator = DraftValidator(
            draft=draft,
            max_headline_length=self.max_headline_length,
            max_image_description_length=self.max_image_description_length,
        )
        problems = validator.validate()
        return problems

    def assertProblemFound(
        self,
        problems_list: list[DraftValidationProblem],
        problem_class: type[DraftValidationProblem],
        **kwargs,
    ) -> None:
        for problem in problems_list:
            if isinstance(problem, problem_class):
                if all(
                    getattr(problem, attr_name) == expected_value
                    for attr_name, expected_value in kwargs.items()
                ):
                    return
        self.fail(
            f"Problem not found {problem_class}({kwargs}). "
            f"Found problems: {problems_list}"
        )

    def test_validate(self) -> None:
        valid_draft = self.create_valid_draft()
        problems_list = self.validate_draft(valid_draft)
        self.assertEmpty(problems_list)

    def test_validate_empty_headline_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.headline = ""
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, EmptyHeadlineProblem)

    def test_validate_too_long_headline_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.headline = "A" * 1000
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(
            problems_list,
            TooLongHeadlineProblem,
            current_length=1000,
            max_length=self.max_headline_length,
        )

    def test_validate_no_image_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.image = None
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, NoImageProblem)

    def test_validate_empty_image_url_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.image = replace(draft.image, url="")
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, EmptyImageURLProblem)

    def test_validate_empty_image_description_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.image = replace(draft.image, description="")
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, EmptyImageDescriptionProblem)

    def test_validate_too_long_image_description_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.image = replace(draft.image, description="A" * 1000)
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(
            problems_list,
            TooLongImageDescriptionProblem,
            current_length=1000,
            max_length=self.max_image_description_length,
        )

    def test_validate_empty_image_author_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.image = replace(draft.image, author="")
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, EmptyImageAuthorProblem)

    def test_validate_empty_text_problem(self) -> None:
        draft = self.create_valid_draft()
        draft.text = ""
        problems_list = self.validate_draft(draft)
        self.assertProblemFound(problems_list, EmptyTextProblem)


class PickDatePublishedTests(TestCase):
    def test_pick_set_date_as_is(self) -> None:
        date_published_from_draft = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        date_published = pick_date_published(date_published_from_draft)
        self.assertEqual(date_published, date_published_from_draft)

    def test_pick_not_set_date_as_current_date(self) -> None:
        date_published_from_draft = None
        date_published = pick_date_published(date_published_from_draft)
        self.assertAlmostEqual(
            date_published, DateTime.now(), delta=TimeDelta(seconds=10)
        )


class PublishServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.draft_factory = TestDraftFactory()
        self.draft_repository = TestDraftRepository()
        self.news_article_factory = TestNewsArticleFactory()
        self.news_article_repository = TestNewsArticleRepository()
        self.publish_service = PublishService(
            draft_repository=self.draft_repository,
            news_article_factory=self.news_article_factory,
            news_article_repository=self.news_article_repository,
        )

    async def test_publish_create_from_scratch(self) -> None:
        draft = await self._create_draft_from_scratch()
        published_news_article = await self.publish_service.publish_draft(draft.id)
        self._assert_news_article_matches_draft(published_news_article, draft)

    async def test_publish_update_previously_published(self) -> None:
        news_article = await self._create_news_article()
        draft = await self._create_draft_from_news_article(news_article)
        published_news_article = await self.publish_service.publish_draft(draft.id)
        self._assert_news_article_matches_draft(published_news_article, draft)

    def _assert_news_article_matches_draft(
        self, news_article: NewsArticle, draft: Draft
    ) -> None:
        self.assertEqual(news_article.headline, draft.headline)
        self.assertEqual(news_article.author_id, draft.author_id)
        self.assertEqual(news_article.image, draft.image)
        self.assertEqual(news_article.text, draft.text)

    async def _create_news_article(self) -> NewsArticle:
        news_article_id = "11111111-1111-1111-1111-111111111111"
        author_id = "22222222-2222-2222-2222-222222222222"
        news_article = self.news_article_factory.create_news_article_from_scratch(
            news_article_id=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id=author_id,
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the article.",
        )
        await self.news_article_repository.save(news_article)
        return news_article

    async def _create_draft_from_scratch(self) -> Draft:
        draft_id = await self.draft_repository.next_identity()
        user_id = "11111111-1111-1111-1111-111111111111"
        author_id = "22222222-2222-2222-2222-222222222222"
        draft = self.draft_factory.create_draft_from_scratch(
            draft_id=draft_id, user_id=user_id, author_id=author_id
        )
        draft.headline = "The Headline"
        draft.image = Image(
            url="https://example.com/images/1234",
            description="The description of the image",
            author="Emma Brown",
        )
        draft.text = "The text of the article."
        await self.draft_repository.save(draft)
        return draft

    async def _create_draft_from_news_article(self, news_article: NewsArticle) -> Draft:
        draft_id = "33333333-3333-3333-3333-333333333333"
        user_id = "44444444-4444-4444-4444-444444444444"
        draft = self.draft_factory.create_draft_from_news_article(
            news_article=news_article, draft_id=draft_id, user_id=user_id
        )
        draft.headline = "NEW Headline"
        draft.image = Image(
            url="https://example.com/images/9999999-NEW",
            description="NEW description of the image",
            author="NEW image author",
        )
        draft.text = "NEW text."
        draft.author_id = "77777777-7777-7777-7777-777777777777"
        await self.draft_repository.save(draft)
        return draft
