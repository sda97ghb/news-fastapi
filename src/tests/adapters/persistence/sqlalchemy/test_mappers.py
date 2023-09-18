from datetime import datetime as DateTime
from typing import TypedDict, cast
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy.mappers import (
    dispose_orm_mappers,
    setup_orm_mappers,
)
from news_fastapi.adapters.persistence.sqlalchemy.tables import metadata
from news_fastapi.domain.author import Author
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.value_objects import Image


class SaveAndLoadTests(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        setup_orm_mappers()

    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(metadata.create_all)
        self.session = AsyncSession(self.engine)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    @classmethod
    def tearDownClass(cls) -> None:
        dispose_orm_mappers()

    async def test_author(self) -> None:
        id_ = str(uuid4())
        name = "John Doe"

        async with self.session.begin():
            author = Author(id_=id_, name=name)
            self.session.add(author)

        self.session.expunge_all()

        async with self.session.begin():
            author = await self.session.get(Author, id_)
            self.assertIsNotNone(author)
            self.assertEqual(author.id, id_)
            self.assertEqual(author.name, name)

    class DraftKwargs(TypedDict):
        id_: str
        news_article_id: str | None
        created_by_user_id: str
        headline: str
        date_published: DateTime | None
        author_id: str
        image: Image | None
        text: str
        is_published: bool

    def _valid_draft_kwargs(self) -> DraftKwargs:
        return dict(
            id_=str(uuid4()),
            news_article_id=str(uuid4()),
            created_by_user_id=str(uuid4()),
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author_id=str(uuid4()),
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="The author of the image",
            ),
            text="The text of the article",
            is_published=False,
        )

    async def test_draft(self) -> None:
        kwargs = self._valid_draft_kwargs()

        async with self.session.begin():
            draft = Draft(**kwargs)
            self.session.add(draft)

        self.session.expunge_all()

        async with self.session.begin():
            draft = cast(Draft | None, await self.session.get(Draft, kwargs["id_"]))
            self.assertIsNotNone(draft)
            self.assertEqual(draft.id, kwargs["id_"])
            self.assertEqual(draft.news_article_id, kwargs["news_article_id"])
            self.assertEqual(draft.created_by_user_id, kwargs["created_by_user_id"])
            self.assertEqual(draft.headline, kwargs["headline"])
            self.assertEqual(draft.date_published, kwargs["date_published"])
            self.assertEqual(draft.author_id, kwargs["author_id"])
            self.assertEqual(draft.image, kwargs["image"])
            self.assertEqual(draft.text, kwargs["text"])
            self.assertEqual(draft.is_published, kwargs["is_published"])

    # @skip
    async def test_draft__with_null_values(self) -> None:
        kwargs = self._valid_draft_kwargs()
        kwargs["news_article_id"] = None
        kwargs["date_published"] = None
        kwargs["image"] = None

        async with self.session.begin():
            draft = Draft(**kwargs)
            self.session.add(draft)

        self.session.expunge_all()

        async with self.session.begin():
            draft = await self.session.get(Draft, kwargs["id_"])
            self.assertIsNotNone(draft)
            self.assertIsNone(draft.news_article_id)
            self.assertIsNone(draft.date_published)
            self.assertIsNone(draft.image)

    class NewsArticleKwargs(TypedDict):
        id_: str
        headline: str
        date_published: DateTime
        author_id: str
        image: Image
        text: str
        revoke_reason: str | None

    def _valid_news_article_kwargs(self) -> NewsArticleKwargs:
        return dict(
            id_=str(uuid4()),
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+00:00"),
            author_id=str(uuid4()),
            image=Image(
                url="https://example.com/images/1234",
                description="The description of the image",
                author="The author of the image",
            ),
            text="The text of the article",
            revoke_reason="Fake",
        )

    async def test_news_article(self) -> None:
        kwargs = self._valid_news_article_kwargs()

        async with self.session.begin():
            news_article = NewsArticle(**kwargs)
            self.session.add(news_article)

        self.session.expunge_all()

        async with self.session.begin():
            news_article = await self.session.get(NewsArticle, kwargs["id_"])
            self.assertIsNotNone(news_article)
            self.assertEqual(news_article.id, kwargs["id_"])
            self.assertEqual(news_article.headline, kwargs["headline"])
            self.assertEqual(news_article.date_published, kwargs["date_published"])
            self.assertEqual(news_article.author_id, kwargs["author_id"])
            self.assertEqual(news_article.image, kwargs["image"])
            self.assertEqual(news_article.text, kwargs["text"])
            self.assertEqual(news_article.revoke_reason, kwargs["revoke_reason"])

    async def test_news_article__with_null_values(self) -> None:
        kwargs = self._valid_news_article_kwargs()
        kwargs["revoke_reason"] = None

        async with self.session.begin():
            news_article = NewsArticle(**kwargs)
            self.session.add(news_article)

        self.session.expunge_all()

        async with self.session.begin():
            news_article = await self.session.get(NewsArticle, kwargs["id_"])
            self.assertIsNotNone(news_article)
            self.assertIsNone(news_article.revoke_reason)
