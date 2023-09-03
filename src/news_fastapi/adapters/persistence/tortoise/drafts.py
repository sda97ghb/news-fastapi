from datetime import datetime as DateTime
from typing import Collection
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import BooleanField, DatetimeField, TextField

from news_fastapi.domain.draft import Draft, DraftFactory, DraftRepository
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError


class TortoiseDraft(Model):
    id: str = TextField(pk=True)
    news_article_id: str | None = TextField(null=True)
    headline: str = TextField()
    date_published: DateTime | None = DatetimeField(null=True)
    author_id: str = TextField()
    _image_url: str | None = TextField(source_field="image_url", null=True)
    _image_description: str | None = TextField(
        source_field="image_description", null=True
    )
    _image_author: str | None = TextField(source_field="image_author", null=True)
    text: str = TextField()
    created_by_user_id: str = TextField()
    is_published: bool = BooleanField()  # type: ignore[assignment]

    @property
    def image(self) -> Image | None:
        if self._image_url and self._image_description and self._image_author:
            return Image(
                url=self._image_url,
                description=self._image_description,
                author=self._image_author,
            )
        return None

    @image.setter
    def image(self, new_image: Image | None) -> None:
        if new_image is None:
            self._image_url = None
            self._image_description = None
            self._image_author = None
        else:
            self._image_url = new_image.url
            self._image_description = new_image.description
            self._image_author = new_image.author

    def __assert_implements_protocol(self) -> Draft:
        # pylint: disable=unused-private-member
        return self

    class Meta:
        table = "drafts"


class TortoiseDraftFactory(DraftFactory):
    def _create_draft(
        self,
        draft_id: str,
        news_article_id: str | None,
        headline: str,
        date_published: DateTime | None,
        author_id: str,
        image: Image | None,
        text: str,
        created_by_user_id: str,
        is_published: bool,
    ) -> Draft:
        draft = TortoiseDraft(
            id=draft_id,
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            text=text,
            created_by_user_id=created_by_user_id,
            is_published=is_published,
        )
        draft.image = image
        return draft


class TortoiseDraftRepository(DraftRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, draft: Draft) -> None:
        if not isinstance(draft, TortoiseDraft):
            raise ValueError(
                "Tortoise based repository can't save not Tortoise based entity"
            )
        await draft.save()

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        return await TortoiseDraft.all().offset(offset).limit(limit)

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        try:
            return await TortoiseDraft.get(id=draft_id)
        except DoesNotExist as err:
            raise NotFoundError(f"Draft with id {draft_id} does not exist") from err

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        try:
            return await TortoiseDraft.get(
                is_published=False, news_article_id=news_article_id
            )
        except DoesNotExist as err:
            raise NotFoundError(
                f"There is no not published draft for news article {news_article_id}"
            ) from err

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        return await TortoiseDraft.filter(author_id=author_id)

    async def delete(self, draft: Draft) -> None:
        await TortoiseDraft.filter(id=draft.id).delete()
