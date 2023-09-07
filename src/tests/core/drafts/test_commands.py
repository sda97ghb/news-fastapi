from datetime import datetime as DateTime
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock
from uuid import uuid4

from news_fastapi.core.drafts.commands import (
    CreateDraftService,
    DeleteDraftService,
    PublishDraftService,
    UpdateDraftService,
)
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.domain.draft import DraftFactory
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError
from tests.core.drafts.mixins import DraftsTestsMixin
from tests.core.fixtures import DraftsAuthFixture, TransactionManagerFixture
from tests.domain.fixtures import (
    DefaultAuthorRepositoryFixture,
    DraftRepositoryFixture,
    NewsArticleRepositoryFixture,
)
from tests.utils import AssertMixin


class CreateDraftServiceTests(DraftsTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.current_user_id = "11111111-1111-1111-1111-111111111111"
        self.author_id = "22222222-2222-2222-2222-222222222222"
        self.auth = DraftsAuthFixture(current_user_id=self.current_user_id)
        self.transaction_manager = TransactionManagerFixture()
        self.draft_factory = DraftFactory()
        self.draft_repository = DraftRepositoryFixture()
        self.default_author_repository = DefaultAuthorRepositoryFixture()
        self.news_article_repository = NewsArticleRepositoryFixture()
        self.service = CreateDraftService(
            auth=self.auth,
            transaction_manager=self.transaction_manager,
            draft_factory=self.draft_factory,
            draft_repository=self.draft_repository,
            default_author_repository=self.default_author_repository,
            news_article_repository=self.news_article_repository,
        )

    async def asyncSetUp(self) -> None:
        await self.default_author_repository.set_default_author_id(
            user_id=self.current_user_id, author_id=self.author_id
        )

    async def test_create_draft_from_scratch(self) -> None:
        result = await self.service.create_draft(news_article_id=None)

        self.assertIsNone(result.draft.news_article_id)
        self.assertEqual(result.draft.created_by_user_id, self.current_user_id)
        self.assertEqual(result.draft.author_id, self.author_id)

        draft = await self.draft_repository.get_draft_by_id(result.draft.id)
        self.assertIsNone(draft.news_article_id)
        self.assertEqual(draft.created_by_user_id, self.current_user_id)
        self.assertEqual(draft.author_id, self.author_id)

    async def test_create_draft_from_news_article(self) -> None:
        news_article = await self._populate_news_article()

        result = await self.service.create_draft(news_article_id=news_article.id)

        self.assertEqual(result.draft.news_article_id, news_article.id)
        self.assertEqual(result.draft.author_id, news_article.author_id)
        self.assertEqual(result.draft.created_by_user_id, self.current_user_id)

        draft = await self.draft_repository.get_draft_by_id(result.draft.id)
        self.assertEqual(draft.news_article_id, news_article.id)
        self.assertEqual(draft.author_id, news_article.author_id)
        self.assertEqual(draft.created_by_user_id, self.current_user_id)

    async def test_create_draft_requires_authorization(self) -> None:
        self.auth.forbid_create_draft()
        with self.assertRaises(AuthorizationError):
            await self.service.create_draft(news_article_id=None)


class UpdateDraftServiceTests(DraftsTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.current_user_id = "11111111-1111-1111-1111-111111111111"
        self.auth = DraftsAuthFixture(current_user_id=self.current_user_id)
        self.transaction_manager = TransactionManagerFixture()
        self.draft_repository = DraftRepositoryFixture()
        self.service = UpdateDraftService(
            auth=self.auth,
            transaction_manager=self.transaction_manager,
            draft_repository=self.draft_repository,
        )

    async def test_update_draft(self) -> None:
        draft = await self._populate_draft()
        result = await self.service.update_draft(draft_id=draft.id)
        self.assertEqual(result.updated_draft.id, draft.id)

    async def test_update_draft_new_headline(self) -> None:
        draft = await self._populate_draft()

        new_headline = "NEW Headline"
        result = await self.service.update_draft(
            draft_id=draft.id, new_headline=new_headline
        )

        self.assertEqual(result.updated_draft.headline, new_headline)

        draft = await self.draft_repository.get_draft_by_id(draft_id=draft.id)
        self.assertEqual(draft.headline, new_headline)

    async def test_update_draft_new_date_published(self) -> None:
        draft = await self._populate_draft()

        new_date_published = DateTime.now()
        result = await self.service.update_draft(
            draft_id=draft.id, new_date_published=new_date_published
        )

        self.assertEqual(result.updated_draft.date_published, new_date_published)

        draft = await self.draft_repository.get_draft_by_id(draft_id=draft.id)
        self.assertEqual(draft.date_published, new_date_published)

    async def test_update_draft_new_author_id(self) -> None:
        draft = await self._populate_draft()

        new_author_id = str(uuid4())
        result = await self.service.update_draft(
            draft_id=draft.id, new_author_id=new_author_id
        )

        self.assertEqual(result.updated_draft.author_id, new_author_id)

        draft = await self.draft_repository.get_draft_by_id(draft_id=draft.id)
        self.assertEqual(draft.author_id, new_author_id)

    async def test_update_draft_new_image(self) -> None:
        draft = await self._populate_draft()

        new_image = Image(
            url="https://example.com/images/99999-NEW",
            description="NEW image description",
            author="NEW image author",
        )
        result = await self.service.update_draft(draft_id=draft.id, new_image=new_image)

        self.assertEqual(result.updated_draft.image, new_image)

        draft = await self.draft_repository.get_draft_by_id(draft_id=draft.id)
        self.assertEqual(draft.image, new_image)

    async def test_update_draft_new_text(self) -> None:
        draft = await self._populate_draft()

        new_text = "NEW text."
        result = await self.service.update_draft(draft_id=draft.id, new_text=new_text)

        self.assertEqual(result.updated_draft.text, new_text)

        draft = await self.draft_repository.get_draft_by_id(draft_id=draft.id)
        self.assertEqual(draft.text, new_text)

    async def test_update_draft_requires_authorization(self) -> None:
        draft = await self._populate_draft()
        self.auth.forbid_update_draft()
        with self.assertRaises(AuthorizationError):
            await self.service.update_draft(draft_id=draft.id)


class DeleteDraftServiceTests(DraftsTestsMixin, AssertMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.current_user_id = "11111111-1111-1111-1111-111111111111"
        self.auth = DraftsAuthFixture(current_user_id=self.current_user_id)
        self.transaction_manager = TransactionManagerFixture()
        self.draft_repository = DraftRepositoryFixture()
        self.service = DeleteDraftService(
            auth=self.auth,
            transaction_manager=self.transaction_manager,
            draft_repository=self.draft_repository,
        )

    async def test_delete_draft(self) -> None:
        draft = await self._populate_draft()
        result = await self.service.delete_draft(draft_id=draft.id)
        self.assertEqual(result.deleted_draft_id, draft.id)
        with self.assertRaises(NotFoundError):
            await self.draft_repository.get_draft_by_id(draft_id=draft.id)

    async def test_delete_draft_requires_authorization(self) -> None:
        draft = await self._populate_draft()
        self.auth.forbid_delete_draft()
        with self.assertRaises(AuthorizationError):
            await self.service.delete_draft(draft_id=draft.id)

    async def test_delete_drafts_of_author(self) -> None:
        author_id_1 = str(uuid4())
        author_id_2 = str(uuid4())
        await self._populate_draft(author_id=author_id_1)
        await self._populate_draft(author_id=author_id_1)
        await self._populate_draft(author_id=author_id_2)
        await self.assertAuthorHasNDrafts(author_id_1, 2)
        await self.assertAuthorHasNDrafts(author_id_2, 1)

        await self.service.delete_drafts_of_author(author_id=author_id_1)

        await self.assertAuthorHasNDrafts(author_id_1, 0)
        await self.assertAuthorHasNDrafts(author_id_2, 1)

    async def assertAuthorHasNDrafts(self, author_id: str, expected_count: int) -> None:
        drafts = await self.draft_repository.get_drafts_for_author(author_id=author_id)
        self.assertEqual(len(drafts), expected_count)


class PublishDraftServiceTests(DraftsTestsMixin, IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.current_user_id = "11111111-1111-1111-1111-111111111111"
        self.auth = DraftsAuthFixture(current_user_id=self.current_user_id)
        self.transaction_manager = TransactionManagerFixture()
        self.draft_repository = DraftRepositoryFixture()
        self.news_article_repository = NewsArticleRepositoryFixture()
        self.publish_service_mock = AsyncMock()
        self.service = PublishDraftService(
            auth=self.auth,
            transaction_manager=self.transaction_manager,
            publish_service=self.publish_service_mock,
        )

    async def asyncSetUp(self) -> None:
        self.published_news_article_fixture = await self._populate_news_article()
        self.publish_service_mock.publish_draft.return_value = (
            self.published_news_article_fixture
        )

    async def test_publish_draft(self) -> None:
        draft = await self._populate_draft()

        result = await self.service.publish_draft(draft_id=draft.id)

        self.publish_service_mock.publish_draft.assert_awaited_with(draft.id)
        self.assertEqual(
            result.published_news_article, self.published_news_article_fixture
        )
