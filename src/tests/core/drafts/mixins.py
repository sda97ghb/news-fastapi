from datetime import datetime as DateTime
from uuid import uuid4

from news_fastapi.domain.draft import Draft
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.value_objects import Image


class DraftsTestsMixin:
    async def _populate_news_article(self) -> NewsArticle:
        news_article = NewsArticle(
            id_=str(uuid4()),
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author_id=str(uuid4()),
            image=Image(
                url="https://example.com/images/1234",
                description="Description of the image",
                author="Author of the image",
            ),
            text="Text of the news article.",
            revoke_reason=None,
        )
        await self.news_article_repository.save(news_article)
        return news_article

    async def _populate_draft(self, author_id: str | None = None) -> Draft:
        if author_id is None:
            author_id = str(uuid4())
        draft = Draft(
            id_=str(uuid4()),
            news_article_id=None,
            created_by_user_id=self.current_user_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author_id=author_id,
            image=Image(
                url="https://example.com/images/1234",
                description="Description of the image",
                author="Author of the image",
            ),
            text="Text of the news article.",
            is_published=False,
        )
        await self.draft_repository.save(draft)
        return draft
