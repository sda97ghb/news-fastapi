from dataclasses import dataclass
from datetime import datetime as DateTime
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import BooleanField, DatetimeField, TextField

from news_fastapi.domain.drafts import Draft, DraftFactory, DraftRepository
from news_fastapi.utils.exceptions import NotFoundError


@dataclass
class DraftDataclass:
    id: str  # pylint: disable=invalid-name
    news_article_id: str | None
    headline: str
    date_published: DateTime | None
    author_id: str
    text: str
    created_by_user_id: str
    is_published: bool

    def __assert_implements_protocol(self) -> Draft:
        # pylint: disable=unused-private-member
        return self


class TortoiseDraft(Model):
    id: str = TextField(pk=True)
    news_article_id: str | None = TextField(null=True)
    headline: str = TextField()
    date_published: DateTime | None = DatetimeField(null=True)
    author_id: str = TextField()
    text: str = TextField()
    created_by_user_id: str = TextField()
    is_published: bool = BooleanField()  # type: ignore[assignment]

    def __assert_implements_protocol(self) -> Draft:
        # pylint: disable=unused-private-member
        return self


class TortoiseDraftFactory(DraftFactory):
    def create_draft(
        self,
        draft_id: str,
        news_article_id: str | None,
        headline: str,
        date_published: DateTime | None,
        author_id: str,
        text: str,
        created_by_user_id: str,
        is_published: bool,
    ) -> Draft:
        return TortoiseDraft(
            id=draft_id,
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            text=text,
            created_by_user_id=created_by_user_id,
            is_published=is_published,
        )


class TortoiseDraftRepository(DraftRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, draft: Draft) -> None:
        if not isinstance(draft, TortoiseDraft):
            raise ValueError(
                "Tortoise based repository can't save not Tortoise based entity"
            )
        await draft.save()

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        try:
            return await TortoiseDraft.get(id=draft_id)
        except DoesNotExist as err:
            raise NotFoundError(f"Draft with id {draft_id} does not exist") from err

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        try:
            return await TortoiseDraft.get(is_published=False, news_id=news_article_id)
        except DoesNotExist as err:
            raise NotFoundError(
                f"There is no not published draft for news article {news_article_id}"
            ) from err

    async def delete(self, draft: Draft) -> None:
        await TortoiseDraft.filter(id=draft.id).delete()
