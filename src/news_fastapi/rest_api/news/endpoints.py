from typing import Annotated

from fastapi import APIRouter, Request, Path, Query, Body
from pydantic import BaseModel

from news_fastapi.rest_api.authors.models import AuthorShort
from news_fastapi.rest_api.news.container import NewsRequestContainer

router = APIRouter()


class NewsShort(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort


class NewsLong(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort
    text: str


@router.get(
    "/", response_model=list[NewsShort], tags=["News"], summary="Get a list of news"
)
def get_news_list(
    request: Request,
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
):
    container = NewsRequestContainer(request)
    news_service = container.news_service
    news_list = news_service.get_news_list(offset=offset, limit=limit)
    authors_service = container.authors_service
    authors_hash = authors_service.get_authors_in_bulk(
        id_list=[news.author_id for news in news_list]
    )
    author_short_hash = {
        author_id: AuthorShort(id=author.id, name=author.name)
        for author_id, author in authors_hash.items()
    }
    return [
        NewsShort(
            id=news.id,
            headline=news.headline,
            date_published=news.date_published.isoformat(),
            author=author_short_hash.get(news.author_id),
        )
        for news in news_list
    ]


@router.get("/{newsId}", response_model=NewsLong, tags=["News"], summary="Get single news article by ID")
def get_news(
    request: Request,
    news_id: Annotated[str, Path(
        description="ID of the news article", examples=["1234"]
    )],
):
    container = NewsRequestContainer(request)
    news_service = container.news_service
    news = news_service.get_news(news_id=news_id)
    return NewsLong(

    )
