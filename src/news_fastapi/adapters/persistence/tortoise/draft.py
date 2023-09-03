from collections.abc import Iterable
from datetime import datetime as DateTime
from typing import Collection
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import BooleanField, DatetimeField, TextField

from news_fastapi.domain.draft import Draft, DraftRepository
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError


class DraftModel(Model):
    id: str = TextField(pk=True)
    news_article_id: str | None = TextField(null=True)
    headline: str = TextField()
    date_published: DateTime | None = DatetimeField(null=True)
    author_id: str = TextField()
    image_url: str | None = TextField(null=True)
    image_description: str | None = TextField(null=True)
    image_author: str | None = TextField(null=True)
    text: str = TextField()
    created_by_user_id: str = TextField()
    is_published: bool = BooleanField()  # type: ignore[assignment]

    class Meta:
        table = "drafts"


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
