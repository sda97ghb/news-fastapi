from typing import Any, Collection, cast

from sqlalchemy import Row, select
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession
from sqlalchemy.sql.functions import count

from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    news_articles_table,
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
            news_articles_table, authors_table.c.name.label("author_name")
        ).select_from(
            news_articles_table.outerjoin(
                authors_table, news_articles_table.c.author_id == authors_table.c.id
            )
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
            where_clause_list.append(news_articles_table.c.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(news_articles_table.c.revoke_reason.is_not(None))
        return where_clause_list


class SQLAlchemyNewsArticleDetailsQueries(NewsArticleDetailsQueries):
    _connection: AsyncConnection

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def get_news_article(self, news_article_id: str) -> NewsArticleDetails:
        row = await self._fetch_news_article(news_article_id)
        author_row = await self._fetch_author(news_article_id, row.author_id)
        return NewsArticleDetails(
            news_article_id=row.id,
            headline=row.headline,
            date_published=row.date_published,
            author=NewsArticleDetailsAuthor(
                author_id=author_row.id,
                name=author_row.name,
            ),
            image=Image(
                url=row.image_url,
                description=row.image_description,
                author=row.image_author,
            ),
            text=row.text,
            revoke_reason=row.revoke_reason,
        )

    async def _fetch_news_article(self, news_article_id: str) -> Row:
        result = await self._connection.execute(
            select(news_articles_table).where(
                news_articles_table.c.id == news_article_id
            )
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError("News article not found")
        return row

    async def _fetch_author(self, news_article_id: str, author_id: str) -> Row:
        result = await self._connection.execute(
            select(authors_table).where(authors_table.c.id == author_id)
        )
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(
                f"News article '{news_article_id}' contains non-existent "
                f"author ID '{author_id}'"
            )
        return row


class SQLAlchemyNewsArticleRepository(NewsArticleRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, news_article: NewsArticle) -> None:
        self._session.add(news_article)

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        statement = select(NewsArticle)
        if filter_ is not None:
            if where_clause_list := self._where_clause_list_for_filter(filter_):
                statement = statement.where(*where_clause_list)
        statement = statement.offset(offset).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    def _where_clause_list_for_filter(
        self, filter_: NewsArticleListFilter
    ) -> list[Any]:
        where_clause_list = []
        if filter_.revoked == "no_revoked":
            where_clause_list.append(news_articles_table.c.revoke_reason.is_(None))
        if filter_.revoked == "only_revoked":
            where_clause_list.append(news_articles_table.c.revoke_reason.is_not(None))
        return where_clause_list

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        news_article = cast(
            NewsArticle | None, await self._session.get(NewsArticle, news_article_id)
        )
        if news_article is None:
            raise NotFoundError("News article not found")
        return news_article

    async def count_for_author(self, author_id: str) -> int:
        result = await self._session.execute(
            select(count())
            .select_from(NewsArticle)
            .where(news_articles_table.c.author_id == author_id)
        )
        return result.scalar_one()
