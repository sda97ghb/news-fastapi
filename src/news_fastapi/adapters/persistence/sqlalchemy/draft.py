from collections.abc import Collection
from typing import cast

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    drafts_table,
)
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
            select(drafts_table).offset(offset).limit(limit)
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
            select(drafts_table).where(drafts_table.c.id == draft_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("Draft not found")
        return row

    async def _fetch_author(self, draft_id: str, author_id: str) -> Row:
        result = await self._connection.execute(
            select(authors_table).where(authors_table.c.id == author_id)
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
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, draft: Draft) -> None:
        self._session.add(draft)

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        result = await self._session.execute(
            select(Draft).offset(offset).limit(limit).with_for_update()
        )
        return result.scalars().all()

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        draft = cast(
            Draft | None, await self._session.get(Draft, draft_id, with_for_update=True)
        )
        if draft is None:
            raise NotFoundError("Draft not found")
        return draft

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        result = await self._session.execute(
            select(Draft)
            .where(
                drafts_table.c.is_published.is_(False),
                drafts_table.c.news_article_id == news_article_id,
            )
            .with_for_update()
        )
        draft = result.scalars().one_or_none()
        if draft is None:
            raise NotFoundError(
                f"There is no not published draft for news article {news_article_id}"
            )
        return draft

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        result = await self._session.execute(
            select(Draft).where(drafts_table.c.author_id == author_id).with_for_update()
        )
        return result.scalars().all()

    async def delete(self, draft: Draft) -> None:
        await self._session.delete(draft)
