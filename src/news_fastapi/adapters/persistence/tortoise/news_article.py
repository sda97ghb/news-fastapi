from collections.abc import Iterable
from datetime import datetime as DateTime
from typing import Collection
from uuid import uuid4

from tortoise import Model
from tortoise.exceptions import DoesNotExist
from tortoise.fields import DatetimeField, TextField
from tortoise.queryset import QuerySet

from news_fastapi.domain.news_article import (
    NewsArticle,
    NewsArticleListFilter,
    NewsArticleRepository,
)
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError


class NewsArticleModel(Model):
    id: str = TextField(pk=True)
    headline: str = TextField()
    date_published: DateTime = DatetimeField()
    author_id: str = TextField()
    image_url: str = TextField()
    image_description: str = TextField()
    image_author: str = TextField()
    text: str = TextField()
    revoke_reason: str | None = TextField(null=True)

    class Meta:
        table = "news_articles"


class TortoiseNewsArticleRepository(NewsArticleRepository):
    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, news_article: NewsArticle) -> None:
        image_url = None
        image_description = None
        image_author = None
        if news_article.image is not None:
            image_url = news_article.image.url
            image_description = news_article.image.description
            image_author = news_article.image.author
        await NewsArticleModel.update_or_create(
            {
                "headline": news_article.headline,
                "date_published": news_article.date_published,
                "author_id": news_article.author_id,
                "image_url": image_url,
                "image_description": image_description,
                "image_author": image_author,
                "text": news_article.text,
                "revoke_reason": news_article.revoke_reason,
            },
            id=news_article.id,
        )

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        if offset < 0:
            raise ValueError("Offset must be positive integer")
        queryset = NewsArticleModel.all()
        if filter_ is not None:
            queryset = self._apply_filter_to_queryset(filter_, queryset)
        model_instances_list = await queryset.offset(offset).limit(limit)
        return self._to_entity_list(model_instances_list)

    def _apply_filter_to_queryset(
        self, filter_: NewsArticleListFilter, queryset: QuerySet[NewsArticleModel]
    ) -> QuerySet[NewsArticleModel]:
        if filter_.revoked == "no_revoked":
            queryset = queryset.filter(revoke_reason__isnull=True)
        elif filter_.revoked == "only_revoked":
            queryset = queryset.filter(revoke_reason__isnull=False)
        return queryset

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        try:
            model_instance = await NewsArticleModel.get(id=news_article_id)
            return self._to_entity(model_instance)
        except DoesNotExist as err:
            raise NotFoundError(
                f"News article with id {news_article_id} does not exist"
            ) from err

    async def count_for_author(self, author_id: str) -> int:
        return await NewsArticleModel.filter(author_id=author_id).count()

    def _to_entity(self, model_instance: NewsArticleModel) -> NewsArticle:
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
        return NewsArticle(
            id_=model_instance.id,
            headline=model_instance.headline,
            date_published=model_instance.date_published,
            author_id=model_instance.author_id,
            image=image,
            text=model_instance.text,
            revoke_reason=model_instance.revoke_reason,
        )

    def _to_entity_list(
        self, model_instances_list: Iterable[NewsArticleModel]
    ) -> list[NewsArticle]:
        return [
            self._to_entity(model_instance) for model_instance in model_instances_list
        ]
