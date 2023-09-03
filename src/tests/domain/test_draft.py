from datetime import datetime as DateTime
from unittest import TestCase

from news_fastapi.domain.common import Image
from tests.domain.fixtures import TestDraftFactory, TestNewsArticle


class DraftFactoryTests(TestCase):
    def test_create_draft_from_scratch(self) -> None:
        factory = TestDraftFactory()
        draft_id = "11111111-1111-1111-1111-111111111111"
        user_id = "22222222-2222-2222-2222-222222222222"
        author_id = "33333333-3333-3333-3333-333333333333"
        draft = factory.create_draft_from_scratch(
            draft_id=draft_id, user_id=user_id, author_id=author_id
        )
        self.assertEqual(draft.id, draft_id)
        self.assertIsNone(draft.news_article_id)
        self.assertEqual(draft.headline, "")
        self.assertIsNone(draft.date_published)
        self.assertEqual(draft.author_id, author_id)
        self.assertIsNone(draft.image)
        self.assertEqual(draft.text, "")
        self.assertEqual(draft.created_by_user_id, user_id)
        self.assertFalse(draft.is_published)

    def test_create_draft_from_news_article(self) -> None:
        factory = TestDraftFactory()
        draft_id = "11111111-1111-1111-1111-111111111111"
        user_id = "22222222-2222-2222-2222-222222222222"
        author_id = "33333333-3333-3333-3333-333333333333"
        news_article_id = "44444444-4444-4444-4444-444444444444"
        news_article = TestNewsArticle(
            id=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id=author_id,
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the article.",
            revoke_reason=None,
        )
        draft = factory.create_draft_from_news_article(
            news_article=news_article,
            draft_id=draft_id,
            user_id=user_id,
        )
        self.assertEqual(draft.id, draft_id)
        self.assertEqual(draft.news_article_id, news_article.id)
        self.assertEqual(draft.headline, news_article.headline)
        self.assertEqual(draft.date_published, news_article.date_published)
        self.assertEqual(draft.author_id, news_article.author_id)
        self.assertEqual(draft.image, news_article.image)
        self.assertEqual(draft.text, news_article.text)
        self.assertEqual(draft.created_by_user_id, user_id)
        self.assertFalse(draft.is_published)
