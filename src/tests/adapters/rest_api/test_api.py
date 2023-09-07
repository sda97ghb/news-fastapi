from contextlib import asynccontextmanager
from typing import ClassVar
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from dependency_injector.containers import DeclarativeContainer, WiringConfiguration
from dependency_injector.providers import (
    Configuration,
    ContextLocalSingleton,
    Object,
    Singleton,
)
from fastapi import FastAPI
from httpx import AsyncClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from news_fastapi.adapters.auth.http_request import RequestHolder
from news_fastapi.adapters.rest_api.asgi import create_asgi_app
from news_fastapi.adapters.rest_api.authors import DEFAULT_AUTHORS_LIST_LIMIT
from news_fastapi.adapters.rest_api.drafts import DEFAULT_DRAFTS_LIST_LIMIT
from news_fastapi.adapters.rest_api.news import DEFAULT_NEWS_LIST_LIMIT
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.exceptions import AuthorizationError
from news_fastapi.core.news.commands import RevokeNewsArticleResult
from news_fastapi.utils.exceptions import NotFoundError
from tests.adapters.rest_api.fixtures import (
    AuthorDataFixture,
    AuthorsListDataFixture,
    CreateAuthorDataFixture,
    CreateDraftConflictDataFixture,
    CreateDraftDataFixture,
    DefaultAuthorDataFixture,
    DraftDataFixture,
    DraftsListDataFixture,
    NewsArticleDataFixture,
    NewsListDataFixture,
    PublishDraftDataFixture,
    PublishDraftWithValidationProblemsDataFixture,
    UpdateAuthorDataFixture,
    UpdateDraftDataFixture,
)


@asynccontextmanager
async def asgi_lifespan_fixture(app: FastAPI):
    yield


class DIContainer(DeclarativeContainer):
    wiring_config = WiringConfiguration(
        packages=[
            "news_fastapi.adapters",
        ],
        auto_wire=False,
    )

    config = Configuration()

    news_articles_list_service = ContextLocalSingleton(AsyncMock)
    news_article_details_service = ContextLocalSingleton(AsyncMock)
    revoke_news_article_service = ContextLocalSingleton(AsyncMock)

    drafts_list_service = ContextLocalSingleton(AsyncMock)
    draft_details_service = ContextLocalSingleton(AsyncMock)
    create_draft_service = ContextLocalSingleton(AsyncMock)
    update_draft_service = ContextLocalSingleton(AsyncMock)
    delete_draft_service = ContextLocalSingleton(AsyncMock)
    publish_draft_service = ContextLocalSingleton(AsyncMock)

    authors_list_service = ContextLocalSingleton(AsyncMock)
    author_details_service = ContextLocalSingleton(AsyncMock)
    create_author_service = ContextLocalSingleton(AsyncMock)
    update_author_service = ContextLocalSingleton(AsyncMock)
    delete_author_service = ContextLocalSingleton(AsyncMock)
    default_author_service = ContextLocalSingleton(AsyncMock)

    request_holder = ContextLocalSingleton(RequestHolder)

    authors_auth = ContextLocalSingleton(Mock)

    asgi_app = Singleton(
        create_asgi_app,
        config=config.fastapi,
        lifespan=Object(asgi_lifespan_fixture),
    )


class APITests(IsolatedAsyncioTestCase):
    di_container: ClassVar[DIContainer]
    app: ClassVar[FastAPI]

    @classmethod
    def setUpClass(cls) -> None:
        cls.di_container = DIContainer()
        cls.di_container.config.from_dict(
            {
                "fastapi": {
                    "debug": True,
                    "cors": {
                        "allow_origins": ["http://localhost:4000"],
                        "allow_credentials": True,
                        "allow_methods": ["*"],
                        "allow_headers": ["*"],
                    },
                },
            }
        )
        cls.di_container.wire()
        cls.app = cls.di_container.asgi_app()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app = None
        cls.di_container.unwire()

    def setUp(self) -> None:
        self.client = AsyncClient(
            app=self.app, base_url="http://testserver", follow_redirects=True
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()

    async def test_news__get(self) -> None:
        news_list_data = NewsListDataFixture()
        news_articles_list_service = self.di_container.news_articles_list_service()
        news_articles_list_service.get_page.return_value = (
            news_list_data.as__news_articles_list_service__get_page__return_value()
        )

        response = await self.client.get("/news")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), news_list_data.as__rest_api__news__get__json()
        )

        news_articles_list_service.get_page.assert_awaited_with(
            offset=0, limit=DEFAULT_NEWS_LIST_LIMIT, filter_=None
        )

    async def test_news__get__accepts_limit_in_query(self) -> None:
        news_articles_list_service = self.di_container.news_articles_list_service()

        limit = 42
        await self.client.get(f"/news?limit={limit}")

        news_articles_list_service.get_page.assert_awaited_with(
            offset=0, limit=limit, filter_=None
        )

    async def test_news__get__accepts_offset_in_query(self) -> None:
        news_articles_list_service = self.di_container.news_articles_list_service()

        offset = 42
        await self.client.get(f"/news?offset={offset}")

        news_articles_list_service.get_page.assert_awaited_with(
            offset=offset, limit=DEFAULT_NEWS_LIST_LIMIT, filter_=None
        )

    async def test_news__news_article_id__get(self) -> None:
        news_article_data = NewsArticleDataFixture(
            news_article_id="aaaaaaaa-aaaa-aaaa-0001-000000000001"
        )
        news_article_details_service = self.di_container.news_article_details_service()
        news_article_details_service.get_news_article.return_value = (
            news_article_data.as__news_article_details_service__get_news_article__return_value()
        )

        response = await self.client.get(f"/news/{news_article_data.news_article_id}")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(),
            news_article_data.as__rest_api__news__news_article_id__get__json(),
        )

    async def test_news__news_article_id__get__not_found(self) -> None:
        non_existent_news_article_id = str(uuid4())
        news_article_details_service = self.di_container.news_article_details_service()
        news_article_details_service.get_news_article.side_effect = NotFoundError(
            "News article not found"
        )

        response = await self.client.get(f"/news/{non_existent_news_article_id}")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_news__news_article_id__revoke__post(self) -> None:
        revoke_news_article_service = self.di_container.revoke_news_article_service()
        revoke_news_article_service.revoke_news_article.return_value = (
            RevokeNewsArticleResult(revoked_news_article=Mock())
        )

        news_article_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        reason = "Fake"
        request_body = {"reason": reason}
        response = await self.client.post(
            f"/news/{news_article_id}/revoke", json=request_body
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        revoke_news_article_service.revoke_news_article.assert_awaited_with(
            news_article_id=news_article_id, reason=reason
        )

    async def test_news__news_article_id__revoke__post__unauthorized(self) -> None:
        revoke_news_article_service = self.di_container.revoke_news_article_service()
        revoke_news_article_service.revoke_news_article.side_effect = (
            AuthorizationError("User has no required permissions")
        )

        news_article_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        request_body = {"reason": "Fake"}
        response = await self.client.post(
            f"/news/{news_article_id}/revoke", json=request_body
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_news__news_article_id__revoke__post__not_found(self) -> None:
        revoke_news_article_service = self.di_container.revoke_news_article_service()
        revoke_news_article_service.revoke_news_article.side_effect = NotFoundError(
            "News article not found"
        )

        news_article_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        request_body = {"reason": "Fake"}
        response = await self.client.post(
            f"/news/{news_article_id}/revoke", json=request_body
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_drafts__get(self) -> None:
        drafts_list_data = DraftsListDataFixture()
        drafts_list_service = self.di_container.drafts_list_service()
        drafts_list_service.get_page.return_value = (
            drafts_list_data.as__drafts_list_service__get_page__return_value()
        )

        response = await self.client.get("/drafts")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), drafts_list_data.as__rest_api__drafts__get__json()
        )

        drafts_list_service.get_page.assert_awaited_with(
            offset=0, limit=DEFAULT_DRAFTS_LIST_LIMIT
        )

    async def test_drafts__get__accept_offset_in_query(self) -> None:
        drafts_list_service = self.di_container.drafts_list_service()

        offset = 42
        await self.client.get("/drafts", params={"offset": offset})

        drafts_list_service.get_page.assert_awaited_with(
            offset=offset, limit=DEFAULT_DRAFTS_LIST_LIMIT
        )

    async def test_drafts__get__accept_limit_in_query(self) -> None:
        drafts_list_service = self.di_container.drafts_list_service()

        limit = 42
        await self.client.get("/drafts", params={"limit": limit})

        drafts_list_service.get_page.assert_awaited_with(offset=0, limit=limit)

    async def test_drafts__post__create_from_scratch(self) -> None:
        data_fixture = CreateDraftDataFixture(news_article_id=None)
        create_draft_service = self.di_container.create_draft_service()
        create_draft_service.create_draft.return_value = (
            data_fixture.as__create_draft_service__create_draft__return_value()
        )

        request_body = {"newsArticleId": data_fixture.news_article_id}
        response = await self.client.post("/drafts", json=request_body)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__drafts__post__json()
        )

        create_draft_service.create_draft.assert_awaited_with(
            news_article_id=data_fixture.news_article_id
        )

    async def test_drafts__post__create_from_news_article(self) -> None:
        data_fixture = CreateDraftDataFixture(
            news_article_id="bbbbbbbb-bbbb-bbbb-0001-000000000001"
        )
        create_draft_service = self.di_container.create_draft_service()
        create_draft_service.create_draft.return_value = (
            data_fixture.as__create_draft_service__create_draft__return_value()
        )

        request_body = {"newsArticleId": data_fixture.news_article_id}
        response = await self.client.post("/drafts", json=request_body)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__drafts__post__json()
        )

        create_draft_service.create_draft.assert_awaited_with(
            news_article_id=data_fixture.news_article_id
        )

    async def test_drafts__post__unauthorized(self) -> None:
        create_draft_service = self.di_container.create_draft_service()
        create_draft_service.create_draft.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        request_body = {"newsArticleId": None}
        response = await self.client.post("/drafts", json=request_body)

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_drafts__post__conflict(self) -> None:
        data_fixture = CreateDraftConflictDataFixture()
        create_draft_service = self.di_container.create_draft_service()
        create_draft_service.create_draft.side_effect = (
            data_fixture.as__create_draft_service__create_draft__side_effect()
        )

        request_body = {"newsArticleId": data_fixture.news_article_id}
        response = await self.client.post("/drafts", json=request_body)

        self.assertEqual(response.status_code, HTTP_409_CONFLICT)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__drafts__post__json()
        )

    async def test_drafts__draft_id__get(self) -> None:
        data_fixture = DraftDataFixture()
        draft_details_service = self.di_container.draft_details_service()
        draft_details_service.get_draft.return_value = (
            data_fixture.as__draft_details_service__get_draft()
        )

        response = await self.client.get(f"/drafts/{data_fixture.draft_id}")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__drafts__draft_id__get__json()
        )

    async def test_drafts__draft_id__get__unauthorized(self) -> None:
        draft_id = str(uuid4())
        draft_details_service = self.di_container.draft_details_service()
        draft_details_service.get_draft.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.get(f"/drafts/{draft_id}")

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_drafts__draft_id__get__not_found(self) -> None:
        non_existent_draft_id = str(uuid4())
        draft_details_service = self.di_container.draft_details_service()
        draft_details_service.get_draft.side_effect = NotFoundError("Draft not found")

        response = await self.client.get(f"/drafts/{non_existent_draft_id}")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_drafts__draft_id__put(self) -> None:
        data_fixture = UpdateDraftDataFixture()
        update_draft_service = self.di_container.update_draft_service()

        request_body = data_fixture.as__rest_api__drafts__draft_id__put__request_body()
        response = await self.client.put(
            f"/drafts/{data_fixture.draft_id}", json=request_body
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        update_draft_service.update_draft.assert_awaited_with(
            draft_id=data_fixture.draft_id,
            new_headline=data_fixture.new_headline,
            new_date_published=data_fixture.new_date_published,
            new_author_id=data_fixture.new_author_id,
            new_image=data_fixture.new_image,
            new_text=data_fixture.new_text,
        )

    async def test_drafts__draft_id__put__unauthorized(self) -> None:
        data_fixture = UpdateDraftDataFixture()
        update_draft_service = self.di_container.update_draft_service()
        update_draft_service.update_draft.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.put(
            f"/drafts/{data_fixture.draft_id}",
            json=data_fixture.as__rest_api__drafts__draft_id__put__request_body(),
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_drafts__draft_id__put__not_found(self) -> None:
        data_fixture = UpdateDraftDataFixture()
        update_draft_service = self.di_container.update_draft_service()
        update_draft_service.update_draft.side_effect = NotFoundError("Draft not found")

        response = await self.client.put(
            f"/drafts/{data_fixture.draft_id}",
            json=data_fixture.as__rest_api__drafts__draft_id__put__request_body(),
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_drafts__draft_id__delete(self) -> None:
        draft_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_draft_service = self.di_container.delete_draft_service()

        response = await self.client.delete(f"/drafts/{draft_id}")

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        delete_draft_service.delete_draft.assert_awaited_with(draft_id=draft_id)

    async def test_drafts__draft_id__delete__unauthorized(self) -> None:
        draft_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_draft_service = self.di_container.delete_draft_service()
        delete_draft_service.delete_draft.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.delete(f"/drafts/{draft_id}")

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_draft__draft_id__delete__not_found(self) -> None:
        draft_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_draft_service = self.di_container.delete_draft_service()
        delete_draft_service.delete_draft.side_effect = NotFoundError("Draft not found")

        response = await self.client.delete(f"/drafts/{draft_id}")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_drafts__draft_id__publish(self) -> None:
        data_fixture = PublishDraftDataFixture()
        publish_draft_service = self.di_container.publish_draft_service()
        publish_draft_service.publish_draft.return_value = (
            data_fixture.as__publish_draft_service__publish_draft__return_value()
        )

        response = await self.client.post(f"/drafts/{data_fixture.draft_id}/publish")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(),
            data_fixture.as__rest_api__drafts__draft_id__publish__json(),
        )

        publish_draft_service.publish_draft.assert_awaited_with(
            draft_id=data_fixture.draft_id
        )

    async def test_drafts__draft_id__publish__unauthorized(self) -> None:
        draft_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        publish_draft_service = self.di_container.publish_draft_service()
        publish_draft_service.publish_draft.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.post(f"/drafts/{draft_id}/publish")

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_drafts__draft_id__publish__not_found(self) -> None:
        draft_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        publish_draft_service = self.di_container.publish_draft_service()
        publish_draft_service.publish_draft.side_effect = NotFoundError(
            "Draft not found"
        )

        response = await self.client.post(f"/drafts/{draft_id}/publish")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test__draft__draft_id__publish__conflict(self) -> None:
        data_fixture = PublishDraftWithValidationProblemsDataFixture()
        publish_draft_service = self.di_container.publish_draft_service()
        publish_draft_service.publish_draft.side_effect = (
            data_fixture.as__publish_draft_service__publish_draft__side_effect()
        )

        response = await self.client.post(f"/drafts/{data_fixture.draft_id}/publish")

        self.assertEqual(response.status_code, HTTP_409_CONFLICT)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(),
            data_fixture.as__rest_api__drafts__draft_id__publish__json(),
        )

    async def test__authors__get(self) -> None:
        data_fixture = AuthorsListDataFixture()
        authors_list_service = self.di_container.authors_list_service()
        authors_list_service.get_page.return_value = (
            data_fixture.as__authors_list_service__get_page__return_value()
        )

        response = await self.client.get("/authors")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__authors__get__json()
        )

        authors_list_service.get_page.assert_awaited_with(
            offset=0, limit=DEFAULT_AUTHORS_LIST_LIMIT
        )

    async def test_authors__get__accepts_limit_in_query(self) -> None:
        authors_list_service = self.di_container.authors_list_service()

        limit = 42
        await self.client.get(f"/authors", params={"limit": limit})

        authors_list_service.get_page.assert_awaited_with(offset=0, limit=limit)

    async def test_authors__get__accepts_offset_in_query(self) -> None:
        authors_list_service = self.di_container.authors_list_service()

        offset = 42
        await self.client.get(f"/authors", params={"offset": offset})

        authors_list_service.get_page.assert_awaited_with(
            offset=offset, limit=DEFAULT_AUTHORS_LIST_LIMIT
        )

    async def test_authors__post(self) -> None:
        data_fixture = CreateAuthorDataFixture()
        create_author_service = self.di_container.create_author_service()
        create_author_service.create_author.return_value = (
            data_fixture.as__create_author_service__create_author__return_value()
        )

        response = await self.client.post(
            "/authors", json=data_fixture.as__rest_api__authors__post__request_json()
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__authors__post__json()
        )

        create_author_service.create_author.assert_awaited_with(name=data_fixture.name)

    async def test_authors__post__unauthorized(self) -> None:
        data_fixture = CreateAuthorDataFixture()
        create_author_service = self.di_container.create_author_service()
        create_author_service.create_author.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.post(
            "/authors", json=data_fixture.as__rest_api__authors__post__request_json()
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_authors__author_id__get(self) -> None:
        data_fixture = AuthorDataFixture()
        author_details_service = self.di_container.author_details_service()
        author_details_service.get_author.return_value = (
            data_fixture.as__author_details_service__get_author__return_value()
        )

        response = await self.client.get(f"/authors/{data_fixture.author_id}")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__authors__author_id__get__json()
        )

        author_details_service.get_author.assert_awaited_with(
            author_id=data_fixture.author_id
        )

    async def test_authors__author_id__get__not_found(self) -> None:
        author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        author_details_service = self.di_container.author_details_service()
        author_details_service.get_author.side_effect = NotFoundError(
            "Author not found"
        )

        response = await self.client.get(f"/authors/{author_id}")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_authors__author_id__put(self) -> None:
        data_fixture = UpdateAuthorDataFixture()
        update_author_service = self.di_container.update_author_service()
        update_author_service.update_author.return_value = (
            data_fixture.as__update_author_service__update_author__return_value()
        )

        response = await self.client.put(
            f"/authors/{data_fixture.author_id}",
            json=data_fixture.as__rest_api__authors__author_id__put__request_json(),
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        update_author_service.update_author.assert_awaited_with(
            author_id=data_fixture.author_id, new_name=data_fixture.new_name
        )

    async def test_authors__author_id__put__unauthorized(self) -> None:
        data_fixture = UpdateAuthorDataFixture()
        update_author_service = self.di_container.update_author_service()
        update_author_service.update_author.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.put(
            f"/authors/{data_fixture.author_id}",
            json=data_fixture.as__rest_api__authors__author_id__put__request_json(),
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_authors__author_id__put__not_found(self) -> None:
        data_fixture = UpdateAuthorDataFixture()
        update_author_service = self.di_container.update_author_service()
        update_author_service.update_author.side_effect = NotFoundError(
            "Author not found"
        )

        response = await self.client.put(
            f"/authors/{data_fixture.author_id}",
            json=data_fixture.as__rest_api__authors__author_id__put__request_json(),
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_authors__author_id__delete(self) -> None:
        author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_author_service = self.di_container.delete_author_service()

        response = await self.client.delete(f"/authors/{author_id}")

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        delete_author_service.delete_author.assert_awaited_with(author_id=author_id)

    async def test_authors__author_id__delete__unauthorized(self) -> None:
        author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_author_service = self.di_container.delete_author_service()
        delete_author_service.delete_author.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.delete(f"/authors/{author_id}")

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_authors__author_id__delete__not_found(self) -> None:
        author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_author_service = self.di_container.delete_author_service()
        delete_author_service.delete_author.side_effect = NotFoundError(
            "Author not found"
        )

        response = await self.client.delete(f"/authors/{author_id}")

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    async def test_authors__author_id__delete__conflict(self) -> None:
        author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        delete_author_service = self.di_container.delete_author_service()
        delete_author_service.delete_author.side_effect = DeleteAuthorError(
            "Can't delete an author with at least one published news article"
        )

        response = await self.client.delete(f"/authors/{author_id}")

        self.assertEqual(response.status_code, HTTP_409_CONFLICT)

    async def test_authors__default__get(self) -> None:
        data_fixture = DefaultAuthorDataFixture()
        authors_auth = self.di_container.authors_auth()
        authors_auth.get_current_user_id.return_value = data_fixture.user_id
        default_author_service = self.di_container.default_author_service()
        default_author_service.get_default_author.return_value = (
            data_fixture.as__default_author_service__get_default_author__return_value()
        )

        response = await self.client.get("/authors/default")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__authors__default__get__json()
        )

        default_author_service.get_default_author.assert_awaited_with(
            user_id=data_fixture.user_id
        )

    async def test_authors__default__get__default_author_is_not_set(self) -> None:
        default_author_service = self.di_container.default_author_service()
        default_author_service.get_default_author.return_value = None

        response = await self.client.get("/authors/default")

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(response.json(), {"author": None})

    async def test_authors__default__get__accepts_user_id_in_query(self) -> None:
        data_fixture = DefaultAuthorDataFixture()
        authors_auth = self.di_container.authors_auth()
        # current user is different user
        authors_auth.get_current_user_id.return_value = str(uuid4())
        default_author_service = self.di_container.default_author_service()
        default_author_service.get_default_author.return_value = (
            data_fixture.as__default_author_service__get_default_author__return_value()
        )

        response = await self.client.get(
            "/authors/default", params={"user-id": data_fixture.user_id}
        )

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(
            response.json(), data_fixture.as__rest_api__authors__default__get__json()
        )

        default_author_service.get_default_author.assert_awaited_with(
            user_id=data_fixture.user_id
        )

    async def test_authors__default__put(self) -> None:
        current_user_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        new_author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
        authors_auth = self.di_container.authors_auth()
        authors_auth.get_current_user_id.return_value = current_user_id
        default_author_service = self.di_container.default_author_service()

        response = await self.client.put(
            "/authors/default", json={"userId": None, "authorId": new_author_id}
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        default_author_service.set_default_author.assert_awaited_with(
            user_id=current_user_id, author_id=new_author_id
        )

    async def test_authors__default__put__accepts_user_id_in_query(self) -> None:
        current_user_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        user_id = "aaaaaaaa-aaaa-aaaa-0001-000000000003"
        new_author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
        authors_auth = self.di_container.authors_auth()
        authors_auth.get_current_user_id.return_value = current_user_id
        default_author_service = self.di_container.default_author_service()

        response = await self.client.put(
            "/authors/default", json={"userId": user_id, "authorId": new_author_id}
        )

        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)

        default_author_service.set_default_author.assert_awaited_with(
            user_id=user_id, author_id=new_author_id
        )

    async def test_authors__default__put__unauthorized(self) -> None:
        current_user_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        new_author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
        authors_auth = self.di_container.authors_auth()
        authors_auth.get_current_user_id.return_value = current_user_id
        default_author_service = self.di_container.default_author_service()
        default_author_service.set_default_author.side_effect = AuthorizationError(
            "User has no required permissions"
        )

        response = await self.client.put(
            "/authors/default", json={"userId": None, "authorId": new_author_id}
        )

        self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)

    async def test_authors__default__put__not_found(self) -> None:
        current_user_id = "aaaaaaaa-aaaa-aaaa-0001-000000000001"
        new_author_id = "aaaaaaaa-aaaa-aaaa-0001-000000000002"
        authors_auth = self.di_container.authors_auth()
        authors_auth.get_current_user_id.return_value = current_user_id
        default_author_service = self.di_container.default_author_service()
        default_author_service.set_default_author.side_effect = NotFoundError(
            "Author not found"
        )

        response = await self.client.put(
            "/authors/default", json={"userId": None, "authorId": new_author_id}
        )

        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
