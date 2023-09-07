from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_204_NO_CONTENT

from news_fastapi.adapters.rest_api.models import (
    Author,
    Image,
    NewsArticle,
    NewsArticlesListItem,
)
from news_fastapi.adapters.rest_api.parameters import (
    LimitInQuery,
    NewsArticleIdInPath,
    OffsetInQuery,
)
from news_fastapi.core.news.commands import RevokeNewsArticleService
from news_fastapi.core.news.queries import (
    NewsArticleDetailsService,
    NewsArticlesListService,
)

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
    news_articles_list_service: NewsArticlesListService = Depends(
        Provide["news_articles_list_service"]
    ),
) -> list[NewsArticlesListItem]:
    if limit is None:
        limit = DEFAULT_NEWS_LIST_LIMIT
    if offset is None:
        offset = 0
    page = await news_articles_list_service.get_page(
        offset=offset, limit=limit, filter_=None
    )
    return [
        NewsArticlesListItem(
            id=item.news_article_id,
            headline=item.headline,
            date_published=item.date_published.isoformat(),
            author=Author(
                id=item.author.author_id,
                name=item.author.name,
            ),
            revoke_reason=item.revoke_reason,
        )
        for item in page.items
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
    news_article_details_service: NewsArticleDetailsService = Depends(
        Provide["news_article_details_service"]
    ),
) -> NewsArticle:
    details = await news_article_details_service.get_news_article(
        news_article_id=news_article_id
    )
    return NewsArticle(
        id=details.news_article_id,
        headline=details.headline,
        date_published=details.date_published.isoformat(),
        author=Author(
            id=details.author.author_id,
            name=details.author.name,
        ),
        image=Image(
            url=details.image.url,
            description=details.image.description,
            author=details.image.author,
        ),
        text=details.text,
        revoke_reason=details.revoke_reason,
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
    revoke_news_article_service: RevokeNewsArticleService = Depends(
        Provide["revoke_news_article_service"]
    ),
) -> None:
    await revoke_news_article_service.revoke_news_article(
        news_article_id=news_article_id, reason=reason
    )
