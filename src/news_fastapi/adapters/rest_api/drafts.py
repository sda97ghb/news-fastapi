from datetime import datetime as DateTime
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from starlette.status import HTTP_204_NO_CONTENT, HTTP_409_CONFLICT

from news_fastapi.adapters.rest_api.models import Author, Draft, DraftsListItem
from news_fastapi.adapters.rest_api.parameters import (
    DraftIdInPath,
    LimitInQuery,
    OffsetInQuery,
)
from news_fastapi.core.drafts.exceptions import CreateDraftError, PublishDraftError
from news_fastapi.core.drafts.services import DraftsListService, DraftsService

router = APIRouter()


DEFAULT_DRAFTS_LIST_LIMIT = 10


@router.get(
    "/",
    response_model=list[DraftsListItem],
    tags=["Drafts"],
    summary="Get a list of drafts",
)
@inject
async def get_drafts_list(
    limit: LimitInQuery = None,
    offset: OffsetInQuery = None,
    drafts_list_service: DraftsListService = Depends(Provide["drafts_list_service"]),
) -> list[DraftsListItem]:
    if limit is None:
        limit = DEFAULT_DRAFTS_LIST_LIMIT
    if offset is None:
        offset = 0
    drafts_list = await drafts_list_service.get_page(offset, limit)
    return [
        DraftsListItem(
            id=item.draft.id,
            news_article_id=item.draft.news_article_id,
            headline=item.draft.headline,
            created_by_user_id=item.draft.created_by_user_id,
            is_published=item.draft.is_published,
        )
        for item in drafts_list
    ]


class CreateDraftResponse(BaseModel):
    draft_id: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.post(
    "/",
    response_model=CreateDraftResponse,
    tags=["Drafts"],
    summary="Create a draft for news article",
)
async def create_draft(
    news_article_id: Annotated[
        str | None,
        Body(
            embed=True,
            description="News article ID to modify article, null to create from scratch",
            examples=["11112222-3333-4444-5555-666677778888", None],
        ),
    ],
    drafts_service: DraftsService = Depends(Provide["drafts_service"]),
) -> CreateDraftResponse:
    try:
        draft = await drafts_service.create_draft(news_article_id)
    except CreateDraftError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err
    return CreateDraftResponse(draft_id=draft.id)


@router.get(
    "/{draftId}",
    response_model=Draft,
    tags=["Drafts"],
    summary="Get a draft by ID",
)
async def get_draft_by_id(
    draft_id: DraftIdInPath,
    drafts_service: DraftsService = Depends(Provide["drafts_service"]),
) -> Draft:
    draft = await drafts_service.get_draft(draft_id)
    return Draft(
        id=draft.draft.id,
        news_article_id=draft.draft.news_article_id,
        headline=draft.draft.headline,
        date_published=(
            draft.draft.date_published.isoformat()
            if draft.draft.date_published
            else None
        ),
        author=Author(
            id=draft.author.id,
            name=draft.author.name,
        ),
        text=draft.draft.text,
        created_by_user_id=draft.draft.created_by_user_id,
        is_published=draft.draft.is_published,
    )


@router.put(
    "/{draftId}",
    status_code=HTTP_204_NO_CONTENT,
    tags=["Drafts"],
    summary="Update the draft with ID",
)
async def update_draft(
    draft_id: DraftIdInPath,
    headline: Annotated[
        str,
        Body(
            embed=True,
            description="New headline",
            examples=["The Ultimate Cat Dresses Checklist"],
        ),
    ],
    date_published: Annotated[
        str | None,
        Body(
            embed=True,
            description=(
                "New date, if should be published at specific date, "
                "or null, if should be published ASAP"
            ),
            examples=["2022-01-01T15:00:00+0000"],
        ),
    ],
    author_id: Annotated[
        str,
        Body(
            embed=True,
            description="New author ID",
            examples=["11112222-3333-4444-5555-666677778888"],
        ),
    ],
    text: Annotated[
        str,
        Body(
            embed=True,
            description="New text",
            examples=["Full text of the news article..."],
        ),
    ],
    drafts_service: DraftsService = Depends(Provide["drafts_service"]),
) -> None:
    await drafts_service.update_draft(
        draft_id=draft_id,
        new_headline=headline,
        new_date_published=DateTime.fromisoformat(date_published)
        if date_published
        else None,
        new_author_id=author_id,
        new_text=text,
    )


@router.delete(
    "/{draftId}",
    status_code=HTTP_204_NO_CONTENT,
    tags=["Drafts"],
    summary="Delete the draft with ID",
)
async def delete_draft(
    draft_id: DraftIdInPath,
    drafts_service: DraftsService = Depends(Provide["drafts_service"]),
) -> None:
    await drafts_service.delete_draft(draft_id)


class PublishDraftResponse(BaseModel):
    news_article_id: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.post(
    "/{draftId}/publish",
    response_model=PublishDraftResponse,
    tags=["Drafts"],
    summary="Publish the draft with ID",
)
async def publish_draft(
    draft_id: DraftIdInPath,
    drafts_service: DraftsService = Depends(Provide["drafts_service"]),
) -> PublishDraftResponse | JSONResponse:
    try:
        news_article = await drafts_service.publish_draft(draft_id)
    except PublishDraftError as err:
        return JSONResponse(
            {
                "problems": [
                    {
                        "message": problem.message,
                        "userMessage": problem.user_message,
                    }
                    for problem in err.problems
                ]
            },
            status_code=HTTP_409_CONFLICT,
        )
    return PublishDraftResponse(news_article_id=news_article.id)
