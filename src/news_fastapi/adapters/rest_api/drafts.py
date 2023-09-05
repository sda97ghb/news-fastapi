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
from news_fastapi.core.drafts.commands import (
    CreateDraftService,
    DeleteDraftService,
    PublishDraftService,
    UpdateDraftService,
)
from news_fastapi.core.drafts.exceptions import CreateDraftError
from news_fastapi.core.drafts.queries import DraftDetailsService, DraftsListService
from news_fastapi.domain.publish import DraftAlreadyPublishedError, InvalidDraftError

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
    page = await drafts_list_service.get_page(offset, limit)
    return [
        DraftsListItem(
            id=item.draft_id,
            news_article_id=item.news_article_id,
            headline=item.headline,
            created_by_user_id=item.created_by_user_id,
            is_published=item.is_published,
        )
        for item in page.items
    ]


class CreateDraftResponseModel(BaseModel):
    draft_id: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.post(
    "/",
    response_model=CreateDraftResponseModel,
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
    create_draft_service: CreateDraftService = Depends(Provide["create_draft_service"]),
) -> CreateDraftResponseModel:
    try:
        result = await create_draft_service.create_draft(news_article_id)
    except CreateDraftError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err
    return CreateDraftResponseModel(draft_id=result.draft.id)


@router.get(
    "/{draftId}",
    response_model=Draft,
    tags=["Drafts"],
    summary="Get a draft by ID",
)
async def get_draft_by_id(
    draft_id: DraftIdInPath,
    draft_details_service: DraftDetailsService = Depends(
        Provide["draft_details_service"]
    ),
) -> Draft:
    details = await draft_details_service.get_draft(draft_id)
    return Draft(
        id=details.draft_id,
        news_article_id=details.news_article_id,
        headline=details.headline,
        date_published=(
            details.date_published.isoformat() if details.date_published else None
        ),
        author=Author(
            id=details.author.author_id,
            name=details.author.name,
        ),
        text=details.text,
        created_by_user_id=details.created_by_user_id,
        is_published=details.is_published,
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
    update_draft_service: UpdateDraftService = Depends(Provide["update_draft_service"]),
) -> None:
    await update_draft_service.update_draft(
        draft_id=draft_id,
        new_headline=headline,
        new_date_published=(
            DateTime.fromisoformat(date_published) if date_published else None
        ),
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
    delete_draft_service: DeleteDraftService = Depends(Provide["delete_draft_service"]),
) -> None:
    await delete_draft_service.delete_draft(draft_id)


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
    publish_draft_service: PublishDraftService = Depends(
        Provide["publish_draft_service"]
    ),
) -> PublishDraftResponse | JSONResponse:
    try:
        result = await publish_draft_service.publish_draft(draft_id)
    except DraftAlreadyPublishedError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err
    except InvalidDraftError as err:
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
    return PublishDraftResponse(news_article_id=result.published_news_article.id)
