from collections.abc import Iterable
from typing import Collection

from sqlalchemy import Row, delete, insert, select, update
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncConnection

from news_fastapi.adapters.persistence.sqlalchemy_core.tables import authors, drafts
from news_fastapi.core.drafts.queries import (
    DraftDetails,
    DraftDetailsAuthor,
    DraftDetailsQueries,
    DraftsListItem,
    DraftsListPage,
    DraftsListQueries,
)
from news_fastapi.domain.draft import Draft, DraftRepository
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError


class SQLAlchemyDraftsListQueries(DraftsListQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_page(self, offset: int, limit: int) -> DraftsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._connection.execute(
            select(drafts).offset(offset).limit(limit)
        )
        return DraftsListPage(
            offset=offset,
            limit=limit,
            items=[
                DraftsListItem(
                    draft_id=row.id,
                    news_article_id=row.news_article_id,
                    headline=row.headline,
                    created_by_user_id=row.created_by_user_id,
                    is_published=row.is_published,
                )
                for row in result.fetchall()
            ],
        )


class SQLAlchemyDraftDetailsQueries(DraftDetailsQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_draft(self, draft_id: str) -> DraftDetails:
        row = await self._fetch_draft(draft_id)
        author_row = await self._fetch_author(draft_id, row.author_id)
        image = self._image(row)
        return DraftDetails(
            draft_id=row.id,
            news_article_id=row.news_article_id,
            created_by_user_id=row.created_by_user_id,
            headline=row.headline,
            date_published=row.date_published,
            author=DraftDetailsAuthor(
                author_id=author_row.id,
                name=author_row.name,
            ),
            image=image,
            text=row.text,
            is_published=row.is_published,
        )

    async def _fetch_draft(self, draft_id: str) -> Row:
        result = await self._connection.execute(
            select(drafts).where(drafts.c.id == draft_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Draft not found")
        return row

    async def _fetch_author(self, draft_id: str, author_id: str) -> Row:
        result = await self._connection.execute(
            select(authors).where(authors.c.id == author_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(
                f"Draft '{draft_id}' contains non-existent author ID '{author_id}'"
            )
        return row

    def _image(self, row: Row) -> Image | None:
        if (
            row.image_url is not None
            and row.image_description is not None
            and row.image_author is not None
        ):
            return Image(
                url=row.image_url,
                description=row.image_description,
                author=row.image_author,
            )
        return None


class SQLAlchemyDraftRepository(DraftRepository):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def save(self, draft: Draft) -> None:
        image_url = None
        image_description = None
        image_author = None
        if draft.image is not None:
            image_url = draft.image.url
            image_description = draft.image.description
            image_author = draft.image.author
        result = await self._connection.execute(
            update(drafts)
            .where(drafts.c.id == draft.id)
            .values(
                news_article_id=draft.news_article_id,
                headline=draft.headline,
                date_published=draft.date_published,
                author_id=draft.author_id,
                image_url=image_url,
                image_description=image_description,
                image_author=image_author,
                text=draft.text,
                created_by_user_id=draft.created_by_user_id,
                is_published=draft.is_published,
            )
        )
        if result.rowcount == 1:
            return
        if result.rowcount != 0:
            raise InvalidRequestError(
                f"Update affected {result.rowcount} rows when saving one object"
            )
        await self._connection.execute(
            insert(drafts).values(
                id=draft.id,
                news_article_id=draft.news_article_id,
                headline=draft.headline,
                date_published=draft.date_published,
                author_id=draft.author_id,
                image_url=image_url,
                image_description=image_description,
                image_author=image_author,
                text=draft.text,
                created_by_user_id=draft.created_by_user_id,
                is_published=draft.is_published,
            )
        )

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._connection.execute(
            select(drafts).offset(offset).limit(limit).with_for_update()
        )
        drafts_list = result.fetchall()
        return self._to_entity_list(drafts_list)

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        result = await self._connection.execute(
            select(drafts).where(drafts.c.id == draft_id).with_for_update()
        )
        draft = result.one_or_none()
        if draft is None:
            raise NotFoundError("Draft not found")
        return self._to_entity(draft)

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        result = await self._connection.execute(
            select(drafts)
            .where(
                drafts.c.is_published.is_(False),
                drafts.c.news_article_id == news_article_id,
            )
            .with_for_update()
        )
        draft = result.one_or_none()
        if draft is None:
            raise NotFoundError("Draft not found")
        return self._to_entity(draft)

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        result = await self._connection.execute(
            select(drafts).where(drafts.c.author_id == author_id).with_for_update()
        )
        drafts_list = result.fetchall()
        return self._to_entity_list(drafts_list)

    async def delete(self, draft: Draft) -> None:
        await self._connection.execute(delete(drafts).where(drafts.c.id == draft.id))

    def _to_entity(self, row: Row) -> Draft:
        image = None
        if (
            row.image_url is not None
            and row.image_description is not None
            and row.image_author is not None
        ):
            image = Image(
                url=row.image_url,
                description=row.image_description,
                author=row.image_author,
            )
        return Draft(
            id_=row.id,
            news_article_id=row.news_article_id,
            created_by_user_id=row.created_by_user_id,
            headline=row.headline,
            date_published=row.date_published,
            author_id=row.author_id,
            image=image,
            text=row.text,
            is_published=row.is_published,
        )

    def _to_entity_list(self, rows_list: Iterable[Row]) -> list[Draft]:
        return [self._to_entity(row) for row in rows_list]
