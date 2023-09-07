from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from news_fastapi.core.authors.queries import AuthorDetailsService, AuthorsListService


class AuthorsListServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.authors_list_queries = AsyncMock()
        self.service = AuthorsListService(
            authors_list_queries=self.authors_list_queries
        )

    async def test_get_page(self) -> None:
        page_mock = Mock()
        self.authors_list_queries.get_page.return_value = page_mock
        offset = 20
        limit = 10
        page = await self.service.get_page(offset=offset, limit=limit)
        self.authors_list_queries.get_page.assert_awaited_with(
            offset=offset, limit=limit
        )
        self.assertIs(page, page_mock)


class AuthorDetailsServiceTests(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.author_details_queries = AsyncMock()
        self.service = AuthorDetailsService(
            author_details_queries=self.author_details_queries
        )

    async def test_get_author(self) -> None:
        details_mock = Mock()
        self.author_details_queries.get_author.return_value = details_mock
        author_id = "11111111-1111-1111-1111-111111111111"
        details = await self.service.get_author(author_id=author_id)
        self.author_details_queries.get_author.assert_awaited_with(author_id=author_id)
        self.assertIs(details, details_mock)
