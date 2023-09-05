from collections.abc import Iterable
from typing import Collection
from uuid import uuid4

from tortoise.exceptions import DoesNotExist

from news_fastapi.adapters.persistence.tortoise.models import AuthorModel, DraftModel
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


class TortoiseDraftsListQueries(DraftsListQueries):
    async def get_page(self, offset: int, limit: int) -> DraftsListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        model_instances_list = await DraftModel.all().offset(offset).limit(limit)
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
                for model_instance in model_instances_list
            ],
        )


class TortoiseDraftDetailsQueries(DraftDetailsQueries):
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
                author_id=author_model_instance.id, name=author_model_instance.name
            ),
            image=image,
            text=draft_model_instance.text,
            is_published=draft_model_instance.is_published,
        )

    async def _fetch_draft(self, draft_id: str) -> DraftModel:
        try:
            return await DraftModel.get(id=draft_id)
        except DoesNotExist as err:
            raise NotFoundError("Draft not found") from err

    async def _fetch_author(self, draft_id: str, author_id: str) -> AuthorModel:
        try:
            return await AuthorModel.get(id=author_id)
        except DoesNotExist as err:
            raise NotFoundError(
                f"Draft '{draft_id}' contains non-existent author ID '{author_id}'"
            ) from err

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


class TortoiseDraftRepository(DraftRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, draft: Draft) -> None:
        image_url = None
        image_description = None
        image_author = None
        if draft.image is not None:
            image_url = draft.image.url
            image_description = draft.image.description
            image_author = draft.image.author
        await DraftModel.update_or_create(
            {
                "news_article_id": draft.news_article_id,
                "headline": draft.headline,
                "date_published": draft.date_published,
                "author_id": draft.author_id,
                "image_url": image_url,
                "image_description": image_description,
                "image_author": image_author,
                "text": draft.text,
                "created_by_user_id": draft.created_by_user_id,
                "is_published": draft.is_published,
            },
            id=draft.id,
        )

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        model_instances_list = await DraftModel.all().offset(offset).limit(limit)
        return self._to_entity_list(model_instances_list)

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        try:
            model_instance = await DraftModel.get(id=draft_id)
            return self._to_entity(model_instance)
        except DoesNotExist as err:
            raise NotFoundError(f"Draft with id {draft_id} does not exist") from err

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        try:
            model_instance = await DraftModel.get(
                is_published=False, news_article_id=news_article_id
            )
            return self._to_entity(model_instance)
        except DoesNotExist as err:
            raise NotFoundError(
                f"There is no not published draft for news article {news_article_id}"
            ) from err

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        model_instances_list = await DraftModel.filter(author_id=author_id)
        return self._to_entity_list(model_instances_list)

    async def delete(self, draft: Draft) -> None:
        await DraftModel.filter(id=draft.id).delete()

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
