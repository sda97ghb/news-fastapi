from collections.abc import Iterable, Mapping
from typing import Collection
from uuid import uuid4

from tortoise.exceptions import DoesNotExist
from tortoise.queryset import QuerySet

from news_fastapi.adapters.persistence.tortoise.models import (
    AuthorModel,
    NewsArticleModel,
)
from news_fastapi.core.news.queries import (
    NewsArticleDetails,
    NewsArticleDetailsAuthor,
    NewsArticleDetailsQueries,
    NewsArticlesListAuthor,
    NewsArticlesListItem,
    NewsArticlesListPage,
    NewsArticlesListQueries,
)
from news_fastapi.domain.news_article import (
    NewsArticle,
    NewsArticleListFilter,
    NewsArticleRepository,
)
from news_fastapi.domain.value_objects import Image
from news_fastapi.utils.exceptions import NotFoundError


class TortoiseNewsArticlesListQueries(NewsArticlesListQueries):
    async def get_page(
        self,
        offset: int = 0,
        limit: int = 50,
        filter_: NewsArticleListFilter | None = None,
    ) -> NewsArticlesListPage:
        if offset < 0:
            raise ValueError("Offset must be positive integer")
        model_instances_list = await self._fetch_news_article_list(
            offset, limit, filter_
        )
        author_model_mapping = await self._fetch_author_mapping(model_instances_list)
        items = [
            self._to_item(model_instance, author_model_mapping)
            for model_instance in model_instances_list
        ]
        return NewsArticlesListPage(
            offset=offset,
            limit=limit,
            items=items,
        )

    async def _fetch_news_article_list(
        self,
        offset: int,
        limit: int,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticleModel]:
        queryset = NewsArticleModel.all()
        if filter_ is not None:
            queryset = self._apply_filter_to_queryset(filter_, queryset)
        return await queryset.offset(offset).limit(limit)

    def _apply_filter_to_queryset(
        self, filter_: NewsArticleListFilter, queryset: QuerySet[NewsArticleModel]
    ) -> QuerySet[NewsArticleModel]:
        if filter_.revoked == "no_revoked":
            queryset = queryset.filter(revoke_reason__isnull=True)
        elif filter_.revoked == "only_revoked":
            queryset = queryset.filter(revoke_reason__isnull=False)
        return queryset

    async def _fetch_author_mapping(
        self, news_article_model_instances_list: Iterable[NewsArticleModel]
    ) -> Mapping[str, AuthorModel]:
        return await AuthorModel.in_bulk(
            id_list=(
                model_instance.author_id
                for model_instance in news_article_model_instances_list
            ),
            field_name="id",
        )

    def _to_item(
        self,
        news_article_model_instance: NewsArticleModel,
        author_model_mapping: Mapping[str, AuthorModel],
    ) -> NewsArticlesListItem:
        author_model_instance = author_model_mapping.get(
            news_article_model_instance.author_id
        )
        if author_model_instance is None:
            raise NotFoundError(
                f"News article '{news_article_model_instance.id}' contains "
                f"non-existent author ID '{news_article_model_instance.author_id}'"
            )
        return NewsArticlesListItem(
            news_article_id=news_article_model_instance.id,
            headline=news_article_model_instance.headline,
            date_published=news_article_model_instance.date_published,
            author=NewsArticlesListAuthor(
                author_id=author_model_instance.id,
                name=author_model_instance.name,
            ),
            revoke_reason=news_article_model_instance.revoke_reason,
        )


class TortoiseNewsArticleDetailsQueries(NewsArticleDetailsQueries):
    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        try:
            model_instance = await NewsArticleModel.get(id=news_article_id)
        except DoesNotExist as err:
            raise NotFoundError("News article not found") from err
        try:
            author_model_instance = await AuthorModel.get(id=model_instance.author_id)
        except DoesNotExist as err:
            raise NotFoundError(
                f"News article '{news_article_id}' contains"
                f"non-existent author ID '{model_instance.author_id}'"
            ) from err
        return NewsArticleDetails(
            news_article_id=model_instance.id,
            headline=model_instance.headline,
            date_published=model_instance.date_published,
            author=NewsArticleDetailsAuthor(
                author_id=author_model_instance.id,
                name=author_model_instance.name,
            ),
            image=Image(
                url=model_instance.image_url,
                description=model_instance.image_description,
                author=model_instance.image_author,
            ),
            text=model_instance.text,
            revoke_reason=model_instance.revoke_reason,
        )


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
        queryset = NewsArticleModel.select_for_update().all()
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
            model_instance = await NewsArticleModel.select_for_update().get(
                id=news_article_id
            )
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
