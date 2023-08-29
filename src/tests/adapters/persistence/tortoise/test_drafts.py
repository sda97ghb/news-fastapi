from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase, TestCase
from uuid import UUID, uuid4

from news_fastapi.adapters.persistence.tortoise.drafts import (
    TortoiseDraft,
    TortoiseDraftFactory,
    TortoiseDraftRepository,
)
from news_fastapi.domain.drafts import Draft
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, PREDICTABLE_IDS_B, TEXTS
from tests.utils import AssertMixin


class TortoiseDraftFactoryTests(TestCase):
    def setUp(self) -> None:
        self.factory = TortoiseDraftFactory()

    def test_create_draft(self) -> None:
        draft_id = "11111111-1111-1111-1111-111111111111"
        news_article_id = "22222222-2222-2222-2222-222222222222"
        headline = "The Headline"
        date_published = DateTime.fromisoformat("2023-01-01T12:00:00+0000")
        author_id = "33333333-3333-3333-3333-333333333333"
        text = "The text of the draft."
        user_id = "44444444-4444-4444-4444-444444444444"
        is_published = False
        draft = self.factory.create_draft(
            draft_id=draft_id,
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            text=text,
            created_by_user_id=user_id,
            is_published=is_published,
        )
        self.assertEqual(draft.id, draft_id)
        self.assertEqual(draft.news_article_id, news_article_id)
        self.assertEqual(draft.headline, headline)
        self.assertEqual(draft.date_published, date_published)
        self.assertEqual(draft.author_id, author_id)
        self.assertEqual(draft.text, text)
        self.assertEqual(draft.created_by_user_id, user_id)
        self.assertEqual(draft.is_published, is_published)


class TortoiseDraftRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = TortoiseDraftRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    def _create_valid_draft(self) -> TortoiseDraft:
        return TortoiseDraft(
            id="11111111-1111-1111-1111-111111111111",
            news_article_id="22222222-2222-2222-2222-222222222222",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="33333333-3333-3333-3333-333333333333",
            text="The text of the draft.",
            created_by_user_id="44444444-4444-4444-4444-444444444444",
            is_published=False,
        )

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
            draft = TortoiseDraft(
                id=draft_id,
                news_article_id=news_article_id,
                headline=headline,
                date_published=date_published,
                author_id=author_id,
                text=text,
                created_by_user_id=user_id,
                is_published=False,
            )
            await draft.save()

    def assertDraftsAreCompletelyEqual(self, draft_1: Draft, draft_2: Draft) -> None:
        self.assertEqual(draft_1.id, draft_2.id)
        self.assertEqual(draft_1.news_article_id, draft_2.news_article_id)
        self.assertEqual(draft_1.headline, draft_2.headline)
        self.assertEqual(draft_1.date_published, draft_2.date_published)
        self.assertEqual(draft_1.author_id, draft_2.author_id)
        self.assertEqual(draft_1.text, draft_2.text)
        self.assertEqual(draft_1.created_by_user_id, draft_2.created_by_user_id)
        self.assertEqual(draft_1.is_published, draft_2.is_published)

    async def test_next_identity(self) -> None:
        id_1 = await self.repository.next_identity()
        id_2 = await self.repository.next_identity()
        for id_ in [id_1, id_2]:
            try:
                UUID(id_)
            except ValueError:
                self.fail(f"next_identity returned badly formed UUID: {id_}")
        self.assertNotEqual(id_1, id_2)

    async def test_save_creates_if_does_not_exist(self) -> None:
        draft = self._create_valid_draft()
        await self.repository.save(draft)
        saved_draft = await TortoiseDraft.get(id=draft.id)
        self.assertDraftsAreCompletelyEqual(draft, saved_draft)

    async def test_save_updates_if_exists(self) -> None:
        draft = self._create_valid_draft()
        await draft.save()

        draft.headline = "NEW Headline"
        draft.date_published = DateTime.fromisoformat("2023-03-11T15:00:00+0000")
        draft.author_id = "77777777-7777-7777-7777-777777777777"
        draft.text = "NEW text."
        await self.repository.save(draft)

        saved_draft = await TortoiseDraft.get(id=draft.id)
        self.assertDraftsAreCompletelyEqual(saved_draft, draft)

    async def test_get_drafts_list(self) -> None:
        await self._populate_drafts()
        limit = 10
        drafts_list = await self.repository.get_drafts_list(offset=0, limit=limit)
        self.assertEqual(len(drafts_list), limit)

    async def test_get_drafts_list_too_big_offset_returns_empty_list(self) -> None:
        await self._populate_drafts()
        drafts_list = await self.repository.get_drafts_list(offset=10000, limit=10)
        self.assertEmpty(drafts_list)

    async def test_get_drafts_list_negative_offset_raises_value_error(self) -> None:
        await self._populate_drafts()
        with self.assertRaises(ValueError):
            await self.repository.get_drafts_list(offset=-1, limit=10)

    async def test_get_draft_by_id(self) -> None:
        saved_draft = self._create_valid_draft()
        await saved_draft.save()

        draft_id = saved_draft.id
        draft_from_db = await self.repository.get_draft_by_id(draft_id=draft_id)

        self.assertDraftsAreCompletelyEqual(draft_from_db, saved_draft)

    async def test_get_draft_by_id_raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_draft_by_id(draft_id=non_existent_draft_id)

    async def test_get_not_published_draft_by_news_id(self) -> None:
        draft = self._create_valid_draft()
        draft.news_article_id = "77777777-7777-7777-7777-777777777777"
        draft.is_published = False
        await draft.save()

        draft_from_db = await self.repository.get_not_published_draft_by_news_id(
            draft.news_article_id
        )

        self.assertDraftsAreCompletelyEqual(draft_from_db, draft)

    async def test_get_not_published_draft_by_news_id_raises_not_found(self) -> None:
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

    async def test_get_drafts_for_author_returns_empty_list_on_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        drafts_list = await self.repository.get_drafts_for_author(
            non_existent_author_id
        )
        self.assertEmpty(drafts_list)

    async def test_delete(self) -> None:
        draft = self._create_valid_draft()
        await draft.save()

        await self.repository.delete(draft)

        self.assertFalse(await TortoiseDraft.exists(id=draft.id))
