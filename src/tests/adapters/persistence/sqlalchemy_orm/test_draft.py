from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from news_fastapi.adapters.persistence.sqlalchemy_orm.draft import (
    SQLAlchemyORMDraftDetailsQueries,
    SQLAlchemyORMDraftRepository,
    SQLAlchemyORMDraftsListQueries,
)
from news_fastapi.adapters.persistence.sqlalchemy_orm.models import (
    AuthorModel,
    DraftModel,
    Model,
)
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from news_fastapi.utils.sentinels import Undefined, UndefinedType
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, PREDICTABLE_IDS_B, TEXTS
from tests.utils import AssertMixin


class TortoiseDraftsListQueriesTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.queries = SQLAlchemyORMDraftsListQueries(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _populate_drafts(
        self,
        author_id: str = "11111111-1111-1111-1111-111111111111",
        user_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> None:
        count = 30
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        for draft_id, news_article_id, headline, text in zip(
            PREDICTABLE_IDS_A[:count],
            PREDICTABLE_IDS_B[:count],
            HEADLINES[:count],
            TEXTS[:count],
        ):
            draft_model_instance = DraftModel(
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
            self.session.add(draft_model_instance)
        await self.session.flush()

    async def test_get_page(self) -> None:
        await self._populate_drafts()
        offset = 0
        limit = 10
        page = await self.queries.get_page(offset=offset, limit=limit)
        self.assertEqual(page.offset, offset)
        self.assertEqual(page.limit, limit)
        self.assertEqual(len(page.items), limit)

    async def test_get_page__too_big_offset_returns_empty_list(self) -> None:
        await self._populate_drafts()
        page = await self.queries.get_page(offset=10000, limit=10)
        self.assertEmpty(page.items)

    async def test_get_page__negative_offset_raises_value_error(self) -> None:
        await self._populate_drafts()
        with self.assertRaises(ValueError):
            await self.queries.get_page(offset=-1, limit=10)


class TortoiseDraftDetailsQueriesTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.queries = SQLAlchemyORMDraftDetailsQueries(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    async def _populate_author(self) -> AuthorModel:
        model_instance = AuthorModel(id=str(uuid4()), name="John Doe")
        self.session.add(model_instance)
        await self.session.flush()
        return model_instance

    async def _populate_draft(self, author_id: str | None = None) -> DraftModel:
        if author_id is None:
            author_id = str(uuid4())
        model_instance = DraftModel(
            id=str(uuid4()),
            news_article_id=str(uuid4()),
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id=author_id,
            image_url="https://example.com/images/1234",
            image_description="The description of the image",
            image_author="Emma Brown",
            text="The text of the draft.",
            created_by_user_id=str(uuid4()),
            is_published=False,
        )
        self.session.add(model_instance)
        await self.session.flush()
        return model_instance

    async def test_get_draft(self) -> None:
        saved_author_model_instance = await self._populate_author()
        saved_draft_model_instance = await self._populate_draft(
            author_id=saved_author_model_instance.id
        )

        details = await self.queries.get_draft(draft_id=saved_draft_model_instance.id)

        self.assertEqual(details.draft_id, saved_draft_model_instance.id)
        self.assertEqual(
            details.news_article_id, saved_draft_model_instance.news_article_id
        )
        self.assertEqual(
            details.created_by_user_id, saved_draft_model_instance.created_by_user_id
        )
        self.assertEqual(details.headline, saved_draft_model_instance.headline)
        self.assertEqual(
            details.date_published, saved_draft_model_instance.date_published
        )
        self.assertEqual(details.author.author_id, saved_author_model_instance.id)
        self.assertEqual(details.author.name, saved_author_model_instance.name)
        self.assertEqual(details.image.url, saved_draft_model_instance.image_url)
        self.assertEqual(
            details.image.description, saved_draft_model_instance.image_description
        )
        self.assertEqual(details.image.author, saved_draft_model_instance.image_author)
        self.assertEqual(details.text, saved_draft_model_instance.text)
        self.assertEqual(details.is_published, saved_draft_model_instance.is_published)

    async def test_get_draft__raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.queries.get_draft(draft_id=non_existent_draft_id)


class TortoiseDraftRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_async_engine("sqlite+aiosqlite://")

    async def asyncSetUp(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Model.metadata.create_all)
        self.session = AsyncSession(self.engine)
        self.repository = SQLAlchemyORMDraftRepository(session=self.session)

    async def asyncTearDown(self) -> None:
        await self.session.close()
        await self.engine.dispose()

    def _create_draft(self) -> Draft:
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

    async def _populate_draft(
        self,
        author_id: str | None = None,
        news_article_id: str | UndefinedType = Undefined,
        is_published: bool = False,
    ) -> DraftModel:
        if author_id is None:
            author_id = str(uuid4())
        if news_article_id is Undefined:
            news_article_id = str(uuid4())
        model_instance = DraftModel(
            id=str(uuid4()),
            news_article_id=news_article_id,
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id=author_id,
            image_url="https://example.com/images/1234",
            image_description="The description of the image",
            image_author="Emma Brown",
            text="The text of the draft.",
            created_by_user_id=str(uuid4()),
            is_published=is_published,
        )
        self.session.add(model_instance)
        await self.session.flush()
        return model_instance

    async def _populate_drafts(
        self,
        author_id: str = "11111111-1111-1111-1111-111111111111",
        user_id: str = "22222222-2222-2222-2222-222222222222",
    ) -> None:
        count = 30
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        for draft_id, news_article_id, headline, text in zip(
            PREDICTABLE_IDS_A[:count],
            PREDICTABLE_IDS_B[:count],
            HEADLINES[:count],
            TEXTS[:count],
        ):
            draft_model_instance = DraftModel(
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
            self.session.add(draft_model_instance)
        await self.session.flush()

    def assertDraftAndModelAreCompletelyEqual(
        self, draft: Draft, model_instance: DraftModel
    ) -> None:
        self.assertEqual(draft.id, model_instance.id)
        self.assertEqual(draft.news_article_id, model_instance.news_article_id)
        self.assertEqual(draft.headline, model_instance.headline)
        self.assertEqual(draft.date_published, model_instance.date_published)
        self.assertEqual(draft.author_id, model_instance.author_id)
        if draft.image is None:
            self.assertIsNone(model_instance.image_url)
            self.assertIsNone(model_instance.image_description)
            self.assertIsNone(model_instance.image_author)
        else:
            self.assertEqual(draft.image.url, model_instance.image_url)
            self.assertEqual(draft.image.description, model_instance.image_description)
            self.assertEqual(draft.image.author, model_instance.image_author)
        self.assertEqual(draft.text, model_instance.text)
        self.assertEqual(draft.created_by_user_id, model_instance.created_by_user_id)
        self.assertEqual(draft.is_published, model_instance.is_published)

    async def assertDraftDoesNotExist(self, draft_id: str) -> None:
        await self.session.flush()
        self.assertIsNone(await self.session.get(DraftModel, draft_id))

    async def test_save__creates_if_does_not_exist(self) -> None:
        draft = self._create_draft()

        await self.repository.save(draft)

        await self.session.flush()
        saved_draft_model_instance = await self.session.get(DraftModel, draft.id)
        self.assertIsNotNone(saved_draft_model_instance)
        self.assertDraftAndModelAreCompletelyEqual(draft, saved_draft_model_instance)

    async def test_save__updates_if_exists(self) -> None:
        draft_model_instance = await self._populate_draft()

        draft = Draft(
            id_=draft_model_instance.id,
            news_article_id=draft_model_instance.news_article_id,
            created_by_user_id=draft_model_instance.created_by_user_id,
            headline="NEW Headline",
            date_published=DateTime.fromisoformat("2023-03-11T15:00:00+0000"),
            author_id="77777777-7777-7777-7777-777777777777",
            image=Image(
                url="https://example.com/images/99999-NEW",
                description="NEW description of the image",
                author="NEW Author",
            ),
            text="NEW text.",
            is_published=draft_model_instance.is_published,
        )
        await self.repository.save(draft)

        await self.session.flush()
        saved_draft_model_instance = await self.session.get(DraftModel, draft.id)
        self.assertIsNotNone(saved_draft_model_instance)
        self.assertDraftAndModelAreCompletelyEqual(draft, saved_draft_model_instance)

    async def test_get_drafts_list(self) -> None:
        await self._populate_drafts()
        limit = 10
        drafts_list = await self.repository.get_drafts_list(offset=0, limit=limit)
        self.assertEqual(len(drafts_list), limit)

    async def test_get_drafts_list__too_big_offset_returns_empty_list(self) -> None:
        await self._populate_drafts()
        drafts_list = await self.repository.get_drafts_list(offset=10000, limit=10)
        self.assertEmpty(drafts_list)

    async def test_get_drafts_list__negative_offset_raises_value_error(self) -> None:
        await self._populate_drafts()
        with self.assertRaises(ValueError):
            await self.repository.get_drafts_list(offset=-1, limit=10)

    async def test_get_draft_by_id(self) -> None:
        saved_draft_model_instance = await self._populate_draft()

        draft_id = saved_draft_model_instance.id
        draft_from_db = await self.repository.get_draft_by_id(draft_id=draft_id)

        self.assertDraftAndModelAreCompletelyEqual(
            draft_from_db, saved_draft_model_instance
        )

    async def test_get_draft_by_id__raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_draft_by_id(draft_id=non_existent_draft_id)

    async def test_get_not_published_draft_by_news_id(self) -> None:
        draft_model_instance = await self._populate_draft(
            news_article_id="77777777-7777-7777-7777-777777777777", is_published=False
        )

        draft_from_db = await self.repository.get_not_published_draft_by_news_id(
            draft_model_instance.news_article_id
        )

        self.assertDraftAndModelAreCompletelyEqual(draft_from_db, draft_model_instance)

    async def test_get_not_published_draft_by_news_id__raises_not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_not_published_draft_by_news_id(
                non_existent_news_article_id
            )

    async def test_get_drafts_for_author(self) -> None:
        author_id = "11111111-1111-1111-1111-111111111111"
        await self._populate_drafts(author_id=author_id)

        drafts_list = await self.repository.get_drafts_for_author(author_id=author_id)

        self.assertNotEmpty(drafts_list)
        for draft in drafts_list:
            self.assertEqual(draft.author_id, author_id)
        result = await self.session.execute(
            select(DraftModel).where(DraftModel.author_id == author_id)
        )
        self.assertEqual(len(drafts_list), len(result.scalars().all()))

    async def test_get_drafts_for_author__returns_empty_list_on_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        drafts_list = await self.repository.get_drafts_for_author(
            non_existent_author_id
        )
        self.assertEmpty(drafts_list)

    async def test_delete(self) -> None:
        draft_model_instance = await self._populate_draft()

        draft = await self.repository.get_draft_by_id(draft_model_instance.id)
        await self.repository.delete(draft)

        await self.session.flush()
        await self.assertDraftDoesNotExist(draft_model_instance.id)
