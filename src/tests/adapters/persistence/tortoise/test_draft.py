from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase
from uuid import UUID, uuid4

from news_fastapi.adapters.persistence.tortoise.draft import (
    DraftModel,
    TortoiseDraftRepository,
)
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.persistence.tortoise.fixtures import tortoise_orm_lifespan
from tests.fixtures import HEADLINES, PREDICTABLE_IDS_A, PREDICTABLE_IDS_B, TEXTS
from tests.utils import AssertMixin


class TortoiseDraftRepositoryTests(AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.repository = TortoiseDraftRepository()

    async def asyncSetUp(self) -> None:
        await self.enterAsyncContext(tortoise_orm_lifespan())

    def _create_valid_draft_model_instance(self) -> DraftModel:
        return DraftModel(
            id="11111111-1111-1111-1111-111111111111",
            news_article_id="22222222-2222-2222-2222-222222222222",
            headline="The Headline",
            date_published=DateTime.fromisoformat("2023-01-01T12:00:00+0000"),
            author_id="33333333-3333-3333-3333-333333333333",
            image_url="https://example.com/images/1234",
            image_description="The description of the image",
            image_author="Emma Brown",
            text="The text of the draft.",
            created_by_user_id="44444444-4444-4444-4444-444444444444",
            is_published=False,
        )

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

    async def _populate_draft(self) -> DraftModel:
        draft_model_instance = self._create_valid_draft_model_instance()
        await draft_model_instance.save()
        return draft_model_instance

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
            await draft_model_instance.save()

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
        self.assertFalse(await DraftModel.exists(id=draft_id))

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
        draft = self._create_draft()
        await self.repository.save(draft)
        saved_draft_model_instance = await DraftModel.get(id=draft.id)
        self.assertDraftAndModelAreCompletelyEqual(draft, saved_draft_model_instance)

    async def test_save_updates_if_exists(self) -> None:
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

        saved_draft_model_instance = await DraftModel.get(id=draft.id)
        self.assertDraftAndModelAreCompletelyEqual(draft, saved_draft_model_instance)

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
        saved_draft_model_instance = await self._populate_draft()

        draft_id = saved_draft_model_instance.id
        draft_from_db = await self.repository.get_draft_by_id(draft_id=draft_id)

        self.assertDraftAndModelAreCompletelyEqual(
            draft_from_db, saved_draft_model_instance
        )

    async def test_get_draft_by_id_raises_not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        with self.assertRaises(NotFoundError):
            await self.repository.get_draft_by_id(draft_id=non_existent_draft_id)

    async def test_get_not_published_draft_by_news_id(self) -> None:
        draft_model_instance = self._create_valid_draft_model_instance()
        draft_model_instance.news_article_id = "77777777-7777-7777-7777-777777777777"
        draft_model_instance.is_published = False
        await draft_model_instance.save()

        draft_from_db = await self.repository.get_not_published_draft_by_news_id(
            draft_model_instance.news_article_id
        )

        self.assertDraftAndModelAreCompletelyEqual(draft_from_db, draft_model_instance)

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
        self.assertEqual(
            len(drafts_list), await DraftModel.filter(author_id=author_id).count()
        )

    async def test_get_drafts_for_author_returns_empty_list_on_not_found(self) -> None:
        non_existent_author_id = str(uuid4())
        drafts_list = await self.repository.get_drafts_for_author(
            non_existent_author_id
        )
        self.assertEmpty(drafts_list)

    async def test_delete(self) -> None:
        draft_model_instance = await self._populate_draft()

        draft = await self.repository.get_draft_by_id(draft_model_instance.id)
        await self.repository.delete(draft)

        await self.assertDraftDoesNotExist(draft_model_instance.id)
