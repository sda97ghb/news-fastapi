from datetime import UTC, datetime as DateTime
from unittest import TestCase
from uuid import uuid4

from news_fastapi.domain.draft import Draft, DraftFactory, PublishedDraftEditError
from news_fastapi.domain.news_article import NewsArticleFactory
from news_fastapi.domain.value_objects import Image


class DraftTests(TestCase):
    def setUp(self) -> None:
        self.draft = Draft(
            id_="11111111-1111-1111-1111-111111111111",
            news_article_id="22222222-2222-2222-2222-222222222222",
            created_by_user_id="33333333-3333-3333-3333-333333333333",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="44444444-4444-4444-4444-444444444444",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the article.",
            is_published=False,
        )
        self.published_draft = Draft(
            id_="55555555-5555-5555-5555-555555555555",
            news_article_id="22222222-2222-2222-2222-222222222222",
            created_by_user_id="33333333-3333-3333-3333-333333333333",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="44444444-4444-4444-4444-444444444444",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the article.",
            is_published=True,
        )

    def test_set_headline(self) -> None:
        new_headline = "NEW Headline"
        self.draft.headline = new_headline
        self.assertEqual(self.draft.headline, new_headline)

    def test_set_headline_on_published_draft_raises_error(self) -> None:
        with self.assertRaises(PublishedDraftEditError):
            self.published_draft.headline = "NEW Headline"

    def test_set_date_published(self) -> None:
        new_date_published = DateTime.now(UTC)
        self.draft.date_published = new_date_published
        self.assertEqual(self.draft.date_published, new_date_published)

    def test_set_date_published_on_published_draft_raises_error(self) -> None:
        with self.assertRaises(PublishedDraftEditError):
            self.published_draft.date_published = DateTime.now(UTC)

    def test_set_author_id(self) -> None:
        new_author_id = str(uuid4())
        self.draft.author_id = new_author_id
        self.assertEqual(self.draft.author_id, new_author_id)

    def test_set_author_id_on_published_draft_raises_error(self) -> None:
        with self.assertRaises(PublishedDraftEditError):
            self.published_draft.author_id = str(uuid4())

    def test_set_image(self) -> None:
        new_image = Image(
            url="https://example.com/images/9999-NEW",
            description="NEW description of the image",
            author="NEW Author of the image",
        )
        self.draft.image = new_image
        self.assertEqual(self.draft.image, new_image)

    def test_set_image_on_published_draft_raises_error(self) -> None:
        with self.assertRaises(PublishedDraftEditError):
            self.published_draft.image = Image(
                url="https://example.com/images/9999-NEW",
                description="NEW description of the image",
                author="NEW Author of the image",
            )

    def test_set_text(self) -> None:
        new_text = "NEW text."
        self.draft.text = new_text
        self.assertEqual(self.draft.text, new_text)

    def test_mark_as_published(self) -> None:
        self.draft.mark_as_published()
        self.assertTrue(self.draft.is_published)


class DraftFactoryTests(TestCase):
    def setUp(self) -> None:
        self.factory = DraftFactory()
        self.news_article_factory = NewsArticleFactory()

    def test_create_draft_from_scratch(self) -> None:
        draft_id = "11111111-1111-1111-1111-111111111111"
        user_id = "22222222-2222-2222-2222-222222222222"
        author_id = "33333333-3333-3333-3333-333333333333"
        draft = self.factory.create_draft_from_scratch(
            draft_id=draft_id, user_id=user_id, author_id=author_id
        )
        self.assertEqual(draft.id, draft_id)
        self.assertIsNone(draft.news_article_id)
        self.assertEqual(draft.created_by_user_id, user_id)
        self.assertEqual(draft.headline, "")
        self.assertIsNone(draft.date_published)
        self.assertEqual(draft.author_id, author_id)
        self.assertIsNone(draft.image)
        self.assertEqual(draft.text, "")
        self.assertFalse(draft.is_published)

    def test_create_draft_from_news_article(self) -> None:
        author_id = "33333333-3333-3333-3333-333333333333"
        news_article_id = "44444444-4444-4444-4444-444444444444"
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
        draft_id = "11111111-1111-1111-1111-111111111111"
        user_id = "22222222-2222-2222-2222-222222222222"
        draft = self.factory.create_draft_from_news_article(
            news_article=news_article,
            draft_id=draft_id,
            user_id=user_id,
        )
        self.assertEqual(draft.id, draft_id)
        self.assertEqual(draft.news_article_id, news_article.id)
        self.assertEqual(draft.created_by_user_id, user_id)
        self.assertEqual(draft.headline, news_article.headline)
        self.assertEqual(draft.date_published, news_article.date_published)
        self.assertEqual(draft.author_id, news_article.author_id)
        self.assertEqual(draft.image, news_article.image)
        self.assertEqual(draft.text, news_article.text)
        self.assertFalse(draft.is_published)
