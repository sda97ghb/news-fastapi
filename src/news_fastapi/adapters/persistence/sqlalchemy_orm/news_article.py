from collections.abc import Iterable
from typing import Any, Collection, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import join
from sqlalchemy.sql.functions import count

from news_fastapi.adapters.persistence.sqlalchemy_orm.models import (
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


class SQLAlchemyORMNewsArticlesListQueries(NewsArticlesListQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_page(
        self,
        offset: int = 0,
        limit: int = 50,
        filter_: NewsArticleListFilter | None = None,
    ) -> NewsArticlesListPage:
        if offset < 0:
            raise ValueError("Offset must be positive integer")
        statement = select(NewsArticleModel, AuthorModel.name).select_from(
            join(
                NewsArticleModel,
                AuthorModel,
                NewsArticleModel.author_id == AuthorModel.id,
                isouter=True,
            )
        )
        if filter_ is not None:
            if where_clause_list := self._where_clause_list_for_filter(filter_):
                statement = statement.where(*where_clause_list)
        statement = statement.offset(offset).limit(limit)
        result = await self._session.execute(statement)
        rows_list = cast(list[tuple[NewsArticleModel, str]], result.all())
        return NewsArticlesListPage(
            offset=offset,
            limit=limit,
            items=[
                NewsArticlesListItem(
                    news_article_id=model_instance.id,
                    headline=model_instance.headline,
                    date_published=model_instance.date_published,
                    author=NewsArticlesListAuthor(
                        author_id=model_instance.author_id,
                        name=author_name,
                    ),
                    revoke_reason=model_instance.revoke_reason,
                )
                for model_instance, author_name in rows_list
            ],
        )

    def _where_clause_list_for_filter(
        self, filter_: NewsArticleListFilter
    ) -> list[Any]:
        where_clause_list = []
        if filter_.revoked == "no_revoked":
            where_clause_list.append(NewsArticleModel.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(NewsArticleModel.revoke_reason.is_not(None))
        return where_clause_list


class SQLAlchemyORMNewsArticleDetailsQueries(NewsArticleDetailsQueries):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        news_article_model_instance = await self._fetch_news_article(news_article_id)
        author_model_instance = await self._fetch_author(
            news_article_id, news_article_model_instance.author_id
        )
        return NewsArticleDetails(
            news_article_id=news_article_model_instance.id,
            headline=news_article_model_instance.headline,
            date_published=news_article_model_instance.date_published,
            author=NewsArticleDetailsAuthor(
                author_id=author_model_instance.id,
                name=author_model_instance.name,
            ),
            image=Image(
                url=news_article_model_instance.image_url,
                description=news_article_model_instance.image_description,
                author=news_article_model_instance.image_author,
            ),
            text=news_article_model_instance.text,
            revoke_reason=news_article_model_instance.revoke_reason,
        )

    async def _fetch_news_article(self, news_article_id: str) -> NewsArticleModel:
        model_instance = await self._session.get(NewsArticleModel, news_article_id)
        if model_instance is None:
            raise NotFoundError("News article not found")
        return model_instance

    async def _fetch_author(self, news_article_id: str, author_id: str) -> AuthorModel:
        model_instance = await self._session.get(AuthorModel, author_id)
        if model_instance is None:
            raise NotFoundError(
                f"News article '{news_article_id}' contains non-existent "
                f"author ID '{author_id}'"
            )
        return model_instance


class SQLAlchemyORMNewsArticleRepository(NewsArticleRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, news_article: NewsArticle) -> None:
        model_instance = await self._session.get(NewsArticleModel, news_article.id)
        if model_instance is None:
            model_instance = NewsArticleModel(
                id=news_article.id,
                headline=news_article.headline,
                date_published=news_article.date_published,
                author_id=news_article.author_id,
                image_url=news_article.image.url,
                image_description=news_article.image.description,
                image_author=news_article.image.author,
                text=news_article.text,
                revoke_reason=news_article.revoke_reason,
            )
            self._session.add(model_instance)
        else:
            model_instance.headline = news_article.headline
            model_instance.date_published = news_article.date_published
            model_instance.author_id = news_article.author_id
            model_instance.image_url = news_article.image.url
            model_instance.image_description = news_article.image.description
            model_instance.image_author = news_article.image.author
            model_instance.text = news_article.text
            model_instance.revoke_reason = news_article.revoke_reason

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        statement = select(NewsArticleModel)
        if filter_ is not None:
            if where_clause_list := self._where_clause_list_for_filter(filter_):
                statement = statement.where(*where_clause_list)
        statement = statement.offset(offset).limit(limit)
        result = await self._session.execute(statement)
        model_instances_list = result.scalars().all()
        return self._to_entity_list(model_instances_list)

    def _where_clause_list_for_filter(
        self, filter_: NewsArticleListFilter
    ) -> list[Any]:
        where_clause_list = []
        if filter_.revoked == "no_revoked":
            where_clause_list.append(NewsArticleModel.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(NewsArticleModel.revoke_reason.is_not(None))
        return where_clause_list

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        model_instance = await self._session.get(NewsArticleModel, news_article_id)
        if model_instance is None:
            raise NotFoundError("News article not found")
        return self._to_entity(model_instance)

    async def count_for_author(self, author_id: str) -> int:
        result = await self._session.execute(
            select(count())
            .select_from(NewsArticleModel)
            .where(NewsArticleModel.author_id == author_id)
        )
        return result.scalar_one()

    def _to_entity(self, news_article_model_instance: NewsArticleModel) -> NewsArticle:
        return NewsArticle(
            id_=news_article_model_instance.id,
            headline=news_article_model_instance.headline,
            date_published=news_article_model_instance.date_published,
            author_id=news_article_model_instance.author_id,
            image=Image(
                url=news_article_model_instance.image_url,
                description=news_article_model_instance.image_description,
                author=news_article_model_instance.image_author,
            ),
            text=news_article_model_instance.text,
            revoke_reason=news_article_model_instance.revoke_reason,
        )

    def _to_entity_list(
        self, model_instances_list: Iterable[NewsArticleModel]
    ) -> list[NewsArticle]:
        return [
            self._to_entity(model_instance) for model_instance in model_instances_list
        ]
