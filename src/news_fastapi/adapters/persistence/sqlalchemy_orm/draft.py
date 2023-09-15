from collections.abc import Iterable
from typing import Collection, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from news_fastapi.adapters.persistence.sqlalchemy_orm.models import (
    AuthorModel,
    DraftModel,
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


class SQLAlchemyORMDraftsListQueries(DraftsListQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_page(self, offset: int, limit: int) -> DraftsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        result = await self._session.execute(
            select(DraftModel).offset(offset).limit(limit)
        )
        model_instances = cast(list[DraftModel], result.scalars().all())
        return DraftsListPage(
            offset=offset,
            limit=limit,
            items=[
                DraftsListItem(
                    draft_id=model_instance.id,
                    news_article_id=model_instance.news_article_id,
                    headline=model_instance.headline,
                    created_by_user_id=model_instance.created_by_user_id,
                    is_published=model_instance.is_published,
                )
                for model_instance in model_instances
            ],
        )


class SQLAlchemyORMDraftDetailsQueries(DraftDetailsQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_draft(self, draft_id: str) -> DraftDetails:
        draft_model_instance = await self._fetch_draft(draft_id)
        author_model_instance = await self._fetch_author(
            draft_id, draft_model_instance.author_id
        )
        image = self._image(draft_model_instance)
        return DraftDetails(
            draft_id=draft_model_instance.id,
            news_article_id=draft_model_instance.news_article_id,
            created_by_user_id=draft_model_instance.created_by_user_id,
            headline=draft_model_instance.headline,
            date_published=draft_model_instance.date_published,
            author=DraftDetailsAuthor(
                author_id=author_model_instance.id,
                name=author_model_instance.name,
            ),
            image=image,
            text=draft_model_instance.text,
            is_published=draft_model_instance.is_published,
        )

    async def _fetch_draft(self, draft_id: str) -> DraftModel:
        model_instance = await self._session.get(DraftModel, draft_id)
        if model_instance is None:
            raise NotFoundError("Draft not found")
        return model_instance

    async def _fetch_author(self, draft_id: str, author_id: str) -> AuthorModel:
        model_instance = await self._session.get(AuthorModel, author_id)
        if model_instance is None:
            raise NotFoundError(
                f"Draft '{draft_id}' contains non-existent author ID '{author_id}'"
            )
        return model_instance

    def _image(self, draft_model_instance: DraftModel) -> Image | None:
        if (
            draft_model_instance.image_url is not None
            and draft_model_instance.image_description is not None
            and draft_model_instance.image_author is not None
        ):
            return Image(
                url=draft_model_instance.image_url,
                description=draft_model_instance.image_description,
                author=draft_model_instance.image_author,
            )
        return None


class SQLAlchemyORMDraftRepository(DraftRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, draft: Draft) -> None:
        image_url = None
        image_description = None
        image_author = None
        if draft.image is not None:
            image_url = draft.image.url
            image_description = draft.image.description
            image_author = draft.image.author
        model_instance = await self._session.get(
            DraftModel, draft.id, with_for_update=True
        )
        if model_instance is None:
            model_instance = DraftModel(
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
            self._session.add(model_instance)
        else:
            model_instance.news_article_id = draft.news_article_id
            model_instance.headline = draft.headline
            model_instance.date_published = draft.date_published
            model_instance.author_id = draft.author_id
            model_instance.image_url = image_url
            model_instance.image_description = image_description
            model_instance.image_author = image_author
            model_instance.text = draft.text
            model_instance.created_by_user_id = draft.created_by_user_id
            model_instance.is_published = draft.is_published

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        result = await self._session.execute(
            select(DraftModel).offset(offset).limit(limit).with_for_update()
        )
        model_instances_list = result.scalars().all()
        return self._to_entity_list(model_instances_list)

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        model_instance = await self._session.get(
            DraftModel, draft_id, with_for_update=True
        )
        if model_instance is None:
            raise NotFoundError("Draft not found")
        return self._to_entity(model_instance)

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        result = await self._session.execute(
            select(DraftModel)
            .where(
                DraftModel.is_published.is_(False),
                DraftModel.news_article_id == news_article_id,
            )
            .with_for_update()
        )
        model_instance = result.scalars().one_or_none()
        if model_instance is None:
            raise NotFoundError(
                f"There is no not published draft for news article {news_article_id}"
            )
        return self._to_entity(model_instance)

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        result = await self._session.execute(
            select(DraftModel)
            .where(DraftModel.author_id == author_id)
            .with_for_update()
        )
        return self._to_entity_list(result.scalars().all())

    async def delete(self, draft: Draft) -> None:
        model_instance = await self._session.get(
            DraftModel, draft.id, with_for_update=True
        )
        if model_instance is not None:
            await self._session.delete(model_instance)

    def _to_entity(self, model_instance: DraftModel) -> Draft:
        image = None
        if (
            model_instance.image_url is not None
            and model_instance.image_description is not None
            and model_instance.image_author is not None
        ):
            image = Image(
                url=model_instance.image_url,
                description=model_instance.image_description,
                author=model_instance.image_author,
            )
        return Draft(
            id_=model_instance.id,
            news_article_id=model_instance.news_article_id,
            created_by_user_id=model_instance.created_by_user_id,
            headline=model_instance.headline,
            date_published=model_instance.date_published,
            author_id=model_instance.author_id,
            image=image,
            text=model_instance.text,
            is_published=model_instance.is_published,
        )

    def _to_entity_list(
        self, model_instances_list: Iterable[DraftModel]
    ) -> list[Draft]:
        return [
            self._to_entity(model_instance) for model_instance in model_instances_list
        ]
