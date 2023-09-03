from datetime import datetime as DateTime
from unittest import TestCase

from news_fastapi.domain.common import Image
from tests.domain.fixtures import TestNewsArticleFactory


class NewsArticleFactoryTests(TestCase):
    def test_create_news_article_from_scratch(self) -> None:
        factory = TestNewsArticleFactory()
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
        news_article = factory.create_news_article_from_scratch(
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
