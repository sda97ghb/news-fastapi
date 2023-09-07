from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from news_fastapi.core.drafts.queries import DraftDetailsService, DraftsListService
from news_fastapi.core.exceptions import AuthorizationError
from tests.core.fixtures import DraftsAuthFixture


class DraftsListServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.auth = DraftsAuthFixture(current_user_id=str(uuid4()))
        self.draft_list_queries = AsyncMock()
        self.service = DraftsListService(
            drafts_auth=self.auth, draft_list_queries=self.draft_list_queries
        )

    async def test_get_page(self) -> None:
        page_mock = Mock()
        self.draft_list_queries.get_page.return_value = page_mock
        offset = 20
        limit = 10
        page = await self.service.get_page(offset=offset, limit=limit)
        self.draft_list_queries.get_page.assert_awaited_with(offset=offset, limit=limit)
        self.assertIs(page, page_mock)

    async def test_get_page_requires_authorization(self) -> None:
        self.auth.forbid_get_drafts_list()
        with self.assertRaises(AuthorizationError):
            await self.service.get_page(offset=0, limit=10)


class DraftDetailsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.auth = DraftsAuthFixture(current_user_id=str(uuid4()))
        self.draft_details_queries = AsyncMock()
        self.service = DraftDetailsService(
            auth=self.auth, draft_details_queries=self.draft_details_queries
        )

    async def test_get_draft(self) -> None:
        details_mock = Mock()
        self.draft_details_queries.get_draft.return_value = details_mock
        draft_id = "11111111-1111-1111-1111-111111111111"
        details = await self.service.get_draft(draft_id=draft_id)
        self.draft_details_queries.get_draft.assert_awaited_with(draft_id=draft_id)
        self.assertIs(details, details_mock)

    async def test_get_draft_requires_authorization(self) -> None:
        self.auth.forbid_get_draft()
        with self.assertRaises(AuthorizationError):
            await self.service.get_draft(draft_id=str(uuid4()))
