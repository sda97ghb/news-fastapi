from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_204_NO_CONTENT

from news_fastapi.adapters.rest_api.models import (
    Author,
    NewsArticle,
    NewsArticlesListItem,
)
from news_fastapi.adapters.rest_api.parameters import (
    LimitInQuery,
    NewsArticleIdInPath,
    OffsetInQuery,
)
from news_fastapi.core.news.services import NewsListService, NewsService

router = APIRouter()


DEFAULT_NEWS_LIST_LIMIT = 10


@router.get(
    "/",
    response_model=list[NewsArticlesListItem],
    tags=["News"],
    summary="Get a list of news articles",
)
@inject
async def get_news_list(
    limit: LimitInQuery = None,
    offset: OffsetInQuery = None,
    news_list_service: NewsListService = Depends(Provide["news_list_service"]),
) -> list[NewsArticlesListItem]:
    if limit is None:
        limit = DEFAULT_NEWS_LIST_LIMIT
    if offset is None:
        offset = 0
    news_list = await news_list_service.get_page(offset=offset, limit=limit)
    return [
        NewsArticlesListItem(
            id=news_list_item.news_article.id,
            headline=news_list_item.news_article.headline,
            date_published=news_list_item.news_article.date_published.isoformat(),
            author=Author(
                id=news_list_item.author.id,
                name=news_list_item.author.name,
            ),
            revoke_reason=news_list_item.news_article.revoke_reason,
        )
        for news_list_item in news_list
    ]


@router.get(
    "/{newsArticleId}",
    response_model=NewsArticle,
    tags=["News"],
    summary="Get single news article by ID",
)
@inject
async def get_news_article(
    news_article_id: NewsArticleIdInPath,
    news_service: NewsService = Depends(Provide["news_service"]),
) -> NewsArticle:
    news_article = await news_service.get_news_article(news_article_id=news_article_id)
    return NewsArticle(
        id=news_article.news_article.id,
        headline=news_article.news_article.headline,
        date_published=news_article.news_article.date_published.isoformat(),
        author=Author(
            id=news_article.author.id,
            name=news_article.author.name,
        ),
        text=news_article.news_article.text,
        revoke_reason=news_article.news_article.revoke_reason,
    )


@router.post(
    "/{newsArticleId}/revoke",
    status_code=HTTP_204_NO_CONTENT,
    tags=["News"],
    summary="Revoke the news article, i.e. hide it",
)
@inject
async def revoke_news_article(
    news_article_id: NewsArticleIdInPath,
    reason: Annotated[
        str,
        Body(
            embed=True,
            description="Why this article need to be revoked?",
            examples=["Fake"],
        ),
    ],
    news_service: NewsService = Depends(Provide["news_service"]),
) -> None:
    await news_service.revoke_news_article(
        news_article_id=news_article_id, reason=reason
    )
