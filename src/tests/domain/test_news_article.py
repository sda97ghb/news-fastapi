from datetime import datetime as DateTime
from unittest import TestCase

from news_fastapi.domain.news_article import NewsArticle, NewsArticleFactory
from news_fastapi.domain.value_objects import Image


class NewsArticleTests(TestCase):
    def setUp(self) -> None:
        self.news_article = NewsArticle(
            id_="11111111-1111-1111-1111-111111111111",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the article.",
            revoke_reason=None,
        )

    def test_set_headline(self) -> None:
        new_headline = "NEW Headline"
        self.news_article.headline = new_headline
        self.assertEqual(self.news_article.headline, new_headline)

    def test_set_headline_to_empty_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.news_article.headline = ""

    def test_set_image(self) -> None:
        new_image = Image(
            url="https://example.com/images/9999-NEW",
            description="NEW description of the image",
            author="NEW Author of the image",
        )
        self.news_article.image = new_image
        self.assertEqual(self.news_article.image, new_image)

    def test_set_image_with_empty_url_raises(self) -> None:
        new_image = Image(
            url="",
            description="NEW description of the image",
            author="NEW Author of the image",
        )
        with self.assertRaises(ValueError):
            self.news_article.image = new_image

    def test_set_image_with_empty_description_raises(self) -> None:
        new_image = Image(
            url="https://example.com/images/9999-NEW",
            description="",
            author="NEW Author of the image",
        )
        with self.assertRaises(ValueError):
            self.news_article.image = new_image

    def test_set_image_with_empty_author_raises(self) -> None:
        new_image = Image(
            url="https://example.com/images/9999-NEW",
            description="NEW description of the image",
            author="",
        )
        with self.assertRaises(ValueError):
            self.news_article.image = new_image

    def test_set_text(self) -> None:
        new_text = "NEW text."
        self.news_article.text = new_text
        self.assertEqual(self.news_article.text, new_text)

    def test_set_text_to_empty_string_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.news_article.text = ""

    def test_revoke(self) -> None:
        reason = "Fake"
        self.news_article.revoke(reason=reason)
        self.assertTrue(self.news_article.is_revoked)
        self.assertEqual(self.news_article.revoke_reason, reason)

    def test_cancel_revoke(self) -> None:
        self.news_article.revoke(reason="Fake")
        self.news_article.cancel_revoke()
        self.assertFalse(self.news_article.is_revoked)
        self.assertIsNone(self.news_article.revoke_reason)


class NewsArticleFactoryTests(TestCase):
    def setUp(self) -> None:
        self.factory = NewsArticleFactory()

    def test_create_news_article_from_scratch(self) -> None:
        news_article_id = "11111111-1111-1111-1111-111111111111"
        headline = "The Headline"
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        author_id = "22222222-2222-2222-2222-222222222222"
        image = Image(
            url="https://example.com/images/1234",
            description="The description of the image",
            author="Emma Brown",
        )
        text = "The text of the article."
        news_article = self.factory.create_news_article_from_scratch(
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            image=image,
            text=text,
        )
        self.assertEqual(news_article.id, news_article_id)
        self.assertEqual(news_article.headline, headline)
        self.assertEqual(news_article.date_published, date_published)
        self.assertEqual(news_article.author_id, author_id)
        self.assertEqual(news_article.image, image)
        self.assertEqual(news_article.text, text)
        self.assertIsNone(news_article.revoke_reason)
