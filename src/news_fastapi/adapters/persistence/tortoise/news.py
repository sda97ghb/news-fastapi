from datetime import datetime as DateTime
from typing import Collection
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import DatetimeField, TextField
from tortoise.queryset import QuerySet

from news_fastapi.domain.common import Image
from news_fastapi.domain.news_article import (
    NewsArticle,
    NewsArticleFactory,
    NewsArticleListFilter,
    NewsArticleRepository,
)
from news_fastapi.utils.exceptions import NotFoundError


class TortoiseNewsArticle(Model):
    id: str = TextField(pk=True)
    headline: str = TextField()
    date_published: DateTime = DatetimeField()
    author_id: str = TextField()
    _image_url: str = TextField(source_field="image_url")
    _image_description: str = TextField(source_field="image_description")
    _image_author: str = TextField(source_field="image_author")
    text: str = TextField()
    revoke_reason: str | None = TextField(null=True)

    @property
    def image(self) -> Image:
        return Image(
            url=self._image_url,
            description=self._image_description,
            author=self._image_author,
        )

    @image.setter
    def image(self, new_image: Image) -> None:
        self._image_url = new_image.url
        self._image_description = new_image.description
        self._image_author = new_image.author

    def __assert_implements_protocol(self) -> NewsArticle:
        # pylint: disable=unused-private-member
        return self

    class Meta:
        table = "news_articles"


class TortoiseNewsArticleFactory(NewsArticleFactory):
    def create_news_article(
        self,
        news_article_id: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        image: Image,
        text: str,
        revoke_reason: str | None,
    ) -> NewsArticle:
        return TortoiseNewsArticle(
            id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            _image_url=image.url,
            _image_description=image.description,
            _image_author=image.author,
            text=text,
            revoke_reason=revoke_reason,
        )


class TortoiseNewsArticleRepository(NewsArticleRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, news_article: NewsArticle) -> None:
        if not isinstance(news_article, TortoiseNewsArticle):
            raise ValueError(
                "Tortoise based repository can't save not Tortoise based entity"
            )
        await news_article.save()

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        if offset < 0:
            raise ValueError("Offset must be positive integer")
        queryset = TortoiseNewsArticle.all()
        if filter_ is not None:
            queryset = self._apply_filter_to_queryset(filter_, queryset)
        return await queryset.offset(offset).limit(limit)

    def _apply_filter_to_queryset(
        self, filter_: NewsArticleListFilter, queryset: QuerySet[TortoiseNewsArticle]
    ) -> QuerySet[TortoiseNewsArticle]:
        if filter_.revoked == "no_revoked":
            queryset = queryset.filter(revoke_reason__isnull=True)
        elif filter_.revoked == "only_revoked":
            queryset = queryset.filter(revoke_reason__isnull=False)
        return queryset

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        try:
            return await TortoiseNewsArticle.get(id=news_article_id)
        except DoesNotExist as err:
            raise NotFoundError(
                f"News article with id {news_article_id} does not exist"
            ) from err

    async def count_for_author(self, author_id: str) -> int:
        return await TortoiseNewsArticle.filter(author_id=author_id).count()
