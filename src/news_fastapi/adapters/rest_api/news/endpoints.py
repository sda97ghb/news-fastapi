from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Path, Query
from starlette.status import HTTP_204_NO_CONTENT

from news_fastapi.adapters.rest_api.authors.models import AuthorShort
from news_fastapi.adapters.rest_api.news.models import NewsLong, NewsShort
from news_fastapi.core.news.services import NewsListService, NewsService

router = APIRouter()


@router.get(
    "/", response_model=list[NewsShort], tags=["News"], summary="Get a list of news"
)
@inject
async def get_news_list(
    limit: Annotated[
        int,
        Query(
            description="How many news can be returned on one page of the list?",
            examples=[10],
        ),
    ] = 10,
    offset: Annotated[
        int,
        Query(
            description="How many news should be skipped before the page?",
            examples=[30],
        ),
    ] = 0,
    news_list_service: NewsListService = Depends(Provide["news_list_service"]),
):
    news_list = await news_list_service.get_page(offset=offset, limit=limit)
    return [
        NewsShort(
            id=news_list_item.news_article.id,
            headline=news_list_item.news_article.headline,
            date_published=news_list_item.news_article.date_published.isoformat(),
            author=AuthorShort(
                id=news_list_item.author.id,
                name=news_list_item.author.name,
            ),
        )
        for news_list_item in news_list
    ]


@router.get(
    "/{news_article_id}",
    response_model=NewsLong,
    tags=["News"],
    summary="Get single news article by ID",
)
@inject
async def get_news_article(
    news_article_id: Annotated[
        str, Path(description="ID of the news article", examples=["1234"])
    ],
    news_service: NewsService = Depends(Provide["news_service"]),
):
    news_article = await news_service.get_news_article(news_article_id=news_article_id)
    return NewsLong(
        id=news_article.news_article.id,
        headline=news_article.news_article.headline,
        date_published=news_article.news_article.date_published.isoformat(),
        author=AuthorShort(
            id=news_article.author.id,
            name=news_article.author.name,
        ),
        text=news_article.news_article.text,
    )


@router.post(
    "/{newsId}/revoke",
    status_code=HTTP_204_NO_CONTENT,
    tags=["News"],
    summary="Revoke the news article, i.e. hide it",
)
@inject
async def revoke_news_article(
    news_article_id: Annotated[
        str, Path(description="ID of the news article", examples=["1234"])
    ],
    reason: Annotated[
        str,
        Body(
            embed=True,
            description="Why this article need to be revoked?",
            examples=["1234"],
        ),
    ],
    news_service: NewsService = Depends(Provide["news_service"]),
):
    await news_service.revoke_news_article(
        news_article_id=news_article_id, reason=reason
    )
