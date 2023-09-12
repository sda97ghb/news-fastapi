from collections.abc import Iterable
from typing import Any, Collection

from sqlalchemy import Row, insert, select, update
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.functions import count

from news_fastapi.adapters.persistence.sqlalchemy.tables import authors, news_articles
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


class SQLAlchemyNewsArticlesListQueries(NewsArticlesListQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_page(
        self,
        offset: int = 0,
        limit: int = 50,
        filter_: NewsArticleListFilter | None = None,
    ) -> NewsArticlesListPage:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        statement = select(
            news_articles, authors.c.name.label("author_name")
        ).select_from(
            news_articles.outerjoin(authors, news_articles.c.author_id == authors.c.id)
        )
        if filter_ is not None:
            if where_clause_list := self._where_clause_list_for_filter(filter_):
                statement = statement.where(*where_clause_list)
        statement = statement.offset(offset).limit(limit)
        result = await self._connection.execute(statement)
        return NewsArticlesListPage(
            offset=offset,
            limit=limit,
            items=[
                NewsArticlesListItem(
                    news_article_id=row.id,
                    headline=row.headline,
                    date_published=row.date_published,
                    author=NewsArticlesListAuthor(
                        author_id=row.author_id,
                        name=row.author_name,
                    ),
                    revoke_reason=row.revoke_reason,
                )
                for row in result.fetchall()
            ],
        )

    def _where_clause_list_for_filter(
        self, filter_: NewsArticleListFilter
    ) -> list[Any]:
        where_clause_list = []
        if filter_.revoked == "no_revoked":
            where_clause_list.append(news_articles.c.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(news_articles.c.revoke_reason.is_not(None))
        return where_clause_list


class SQLAlchemyNewsArticleDetailsQueries(NewsArticleDetailsQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        row = await self._fetch_news_article(news_article_id)
        author_row = await self._fetch_author(news_article_id, row.author_id)
        image = self._image(row)
        return NewsArticleDetails(
            news_article_id=row.id,
            headline=row.headline,
            date_published=row.date_published,
            author=NewsArticleDetailsAuthor(
                author_id=author_row.id,
                name=author_row.name,
            ),
            image=image,
            text=row.text,
            revoke_reason=row.revoke_reason,
        )

    async def _fetch_news_article(self, news_article_id: str) -> Row:
        result = await self._connection.execute(
            select(news_articles).where(news_articles.c.id == news_article_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("News article not found")
        return row

    async def _fetch_author(self, news_article_id: str, author_id: str) -> Row:
        result = await self._connection.execute(
            select(authors).where(authors.c.id == author_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(
                f"News article '{news_article_id}' contains non-existent "
                f"author ID '{author_id}'"
            )
        return row

    def _image(self, row: Row) -> Image:
        return Image(
            url=row.image_url,
            description=row.image_description,
            author=row.image_author,
        )


class SQLAlchemyNewsArticleRepository(NewsArticleRepository):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def save(self, news_article: NewsArticle) -> None:
        result = await self._connection.execute(
            update(news_articles)
            .where(news_articles.c.id == news_article.id)
            .values(
                headline=news_article.headline,
                date_published=news_article.date_published,
                author_id=news_article.author_id,
                image_url=news_article.image.url,
                image_description=news_article.image.description,
                image_author=news_article.image.author,
                text=news_article.text,
                revoke_reason=news_article.revoke_reason,
            )
        )
        if result.rowcount == 1:
            return
        if result.rowcount != 0:
            raise InvalidRequestError(
                f"Update affected {result.rowcount} rows when saving one object"
            )
        await self._connection.execute(
            insert(news_articles).values(
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
        )

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        if offset < 0:
            raise ValueError("Offset must be non-negative integer")
        statement = select(news_articles)
        if filter_ is not None:
            if where_clause_list := self._where_clause_list_for_filter(filter_):
                statement = statement.where(*where_clause_list)
        statement = statement.offset(offset).limit(limit)
        result = await self._connection.execute(statement)
        rows_list = result.fetchall()
        return self._to_entity_list(rows_list)

    def _where_clause_list_for_filter(
        self, filter_: NewsArticleListFilter
    ) -> list[Any]:
        where_clause_list = []
        if filter_.revoked == "no_revoked":
            where_clause_list.append(news_articles.c.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(news_articles.c.revoke_reason.is_not(None))
        return where_clause_list

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        result = await self._connection.execute(
            select(news_articles)
            .where(news_articles.c.id == news_article_id)
            .with_for_update()
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("News article not found")
        return self._to_entity(row)

    async def count_for_author(self, author_id: str) -> int:
        result = await self._connection.execute(
            select(count())
            .select_from(news_articles)
            .where(news_articles.c.author_id == author_id)
        )
        return result.scalar_one()

    def _to_entity(self, row: Row) -> NewsArticle:
        return NewsArticle(
            id_=row.id,
            headline=row.headline,
            date_published=row.date_published,
            author_id=row.author_id,
            image=Image(
                url=row.image_url,
                description=row.image_description,
                author=row.image_author,
            ),
            text=row.text,
            revoke_reason=row.revoke_reason,
        )

    def _to_entity_list(self, rows_list: Iterable[Row]) -> list[NewsArticle]:
        return [self._to_entity(row) for row in rows_list]
