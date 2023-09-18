from datetime import datetime as DateTime
from typing import Any
from uuid import uuid4

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    drafts_table,
    news_articles_table,
)
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.sentinels import Undefined, UndefinedType
from tests.fixtures import (
    HEADLINES,
    HUMAN_NAMES,
    PREDICTABLE_IDS_A,
    PREDICTABLE_IDS_B,
    TEXTS,
)


class DataFixtures:
    connection_or_session: AsyncConnection | AsyncSession

    def __init__(self, connection_or_session: AsyncConnection | AsyncSession) -> None:
        self.connection_or_session = connection_or_session

    async def flush(self) -> None:
        if hasattr(self.connection_or_session, "flush"):
            await self.connection_or_session.flush()

    async def populate_author(self) -> dict[str, Any]:
        row = {"id": str(uuid4()), "name": "John Doe"}
        await self.connection_or_session.execute(insert(authors_table), row)
        await self.flush()
        return row

    async def populate_authors(self) -> None:
        await self.connection_or_session.execute(
            insert(authors_table),
            [{"id": str(uuid4()), "name": name} for name in HUMAN_NAMES],
        )
        await self.flush()

    async def populate_authors_with_ids(self, id_list: list[str]) -> None:
        await self.connection_or_session.execute(
            insert(authors_table),
            [{"id": id_, "name": name} for id_, name in zip(id_list, HUMAN_NAMES)],
        )
        await self.flush()

    def create_draft_entity(self) -> Draft:
        return Draft(
            id_="11111111-1111-1111-1111-111111111111",
            news_article_id="22222222-2222-2222-2222-222222222222",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="33333333-3333-3333-3333-333333333333",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the draft.",
            created_by_user_id="44444444-4444-4444-4444-444444444444",
            is_published=False,
        )

    async def populate_draft(
        self,
        author_id: str | UndefinedType = Undefined,
        news_article_id: str | UndefinedType = Undefined,
        is_published: bool = False,
    ) -> dict[str, Any]:
        if author_id is Undefined:
            author_id = str(uuid4())
        if news_article_id is Undefined:
            news_article_id = str(uuid4())
        row = {
            "id": str(uuid4()),
            "news_article_id": news_article_id,
            "headline": "The Headline",
            "date_published": DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            "author_id": author_id,
            "image_url": "https://example.com/images/1234",
            "image_description": "Image description",
            "image_author": "Image author",
            "text": "The text of the article",
            "created_by_user_id": str(uuid4()),
            "is_published": is_published,
        }
        await self.connection_or_session.execute(insert(drafts_table), row)
        await self.flush()
        return row

    async def populate_drafts(
        self,
        author_id: str = "11111111-1111-1111-1111-111111111111",
        user_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> None:
        count = 30
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        await self.connection_or_session.execute(
            insert(drafts_table),
            [
                dict(
                    id=draft_id,
                    news_article_id=news_article_id,
                    headline=headline,
                    date_published=date_published,
                    author_id=author_id,
                    image_url="https://example.com/images/1234",
                    image_description="The description of the image",
                    image_author="Emma Brown",
                    text=text,
                    created_by_user_id=user_id,
                    is_published=False,
                )
                for draft_id, news_article_id, headline, text in zip(
                    PREDICTABLE_IDS_A[:count],
                    PREDICTABLE_IDS_B[:count],
                    HEADLINES[:count],
                    TEXTS[:count],
                )
            ],
        )
        await self.flush()

    def create_news_article_entity(
        self, news_article_id: str = "11111111-1111-1111-1111-111111111111"
    ) -> NewsArticle:
        return NewsArticle(
            id_=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="22222222-2222-2222-2222-222222222222",
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="Emma Brown",
            ),
            text="The text of the news article.",
            revoke_reason=None,
        )

    async def populate_news_article(
        self, author_id: str | None = None, revoke_reason: str | None = None
    ) -> dict[str, Any]:
        if author_id is None:
            author_id = str(uuid4())
        row = {
            "id": str(uuid4()),
            "headline": "The Headline",
            "date_published": DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            "author_id": author_id,
            "image_url": "https://example.com/images/1234",
            "image_description": "The image description",
            "image_author": "The image author",
            "text": "The text of the news article",
            "revoke_reason": revoke_reason,
        }
        await self.connection_or_session.execute(insert(news_articles_table), row)
        await self.flush()
        return row

    async def populate_not_revoked_news_article(self, author_id: str) -> dict[str, Any]:
        return await self.populate_news_article(author_id=author_id, revoke_reason=None)

    async def populate_revoked_news_article(self, author_id: str) -> dict[str, Any]:
        return await self.populate_news_article(
            author_id=author_id, revoke_reason="Fake"
        )

    async def populate_news_articles(
        self,
        count: int = 30,
        author_id="22222222-2222-2222-2222-222222222222",
        predictable_news_article_id: bool = True,
    ) -> None:
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        await self.connection_or_session.execute(
            insert(news_articles_table),
            [
                dict(
                    id=news_article_id if predictable_news_article_id else str(uuid4()),
                    headline=headline,
                    date_published=date_published,
                    author_id=author_id,
                    image_url="https://example.com/images/1234",
                    image_description="The description of the image",
                    image_author="Emma Brown",
                    text=text,
                    revoke_reason=None,
                )
                for news_article_id, headline, text in zip(
                    PREDICTABLE_IDS_A[:count], HEADLINES[:count], TEXTS[:count]
                )
            ],
        )
        await self.flush()
