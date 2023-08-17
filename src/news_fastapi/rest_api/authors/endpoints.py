from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_409_CONFLICT

from news_fastapi.application.authors.auth import AuthorsAuth
from news_fastapi.application.authors.exceptions import DeleteAuthorError
from news_fastapi.application.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)
from news_fastapi.rest_api.authors.models import AuthorShort
from news_fastapi.rest_api.dependencies import (
    authors_auth_provider,
    authors_list_service_provider,
    authors_service_provider,
    default_authors_service_provider,
)

router = APIRouter()


class CreateAuthorResponseModel(BaseModel):
    id: str


@router.post(
    "/",
    response_model=CreateAuthorResponseModel,
    status_code=HTTP_201_CREATED,
    tags=["Authors"],
    summary="Create an author",
)
async def create_author(
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
    authors_service: Annotated[AuthorsService, Depends(authors_service_provider)],
):
    author_id = await authors_service.create_author(name=name)
    return {"id": author_id}


@router.get(
    "/",
    response_model=list[AuthorShort],
    tags=["Authors"],
    summary="List of authors",
)
async def get_list_of_authors(
    authors_list_service: Annotated[
        AuthorsListService, Depends(authors_list_service_provider)
    ],
    limit: Annotated[
        int, Query(description="How many items fit on one page?", examples=[50])
    ] = 50,
    offset: Annotated[
        int,
        Query(
            description="How many items should be skipped before the page?",
            examples=[150],
        ),
    ] = 0,
):
    authors_list = await authors_list_service.get_page(offset=offset, limit=limit)
    return [AuthorShort(id=author.id, name=author.name) for author in authors_list]


@router.put(
    "/{authorId}",
    tags=["Authors"],
    summary="Update the author with ID",
)
async def update_author(
    authors_service: Annotated[AuthorsService, Depends(authors_service_provider)],
    author_id: Annotated[str, Path(description="ID of the author", examples=["1234"])],
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
):
    await authors_service.update_author(author_id=author_id, new_name=name)


@router.delete(
    "/{authorId}",
    tags=["Authors"],
    summary="Delete the author with ID",
)
async def delete_author(
    authors_service: Annotated[AuthorsService, Depends(authors_service_provider)],
    author_id: Annotated[str, Path(description="ID of the author", examples=["1234"])],
):
    try:
        await authors_service.delete_author(author_id=author_id)
    except DeleteAuthorError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err


class GetDefaultAuthorResponseModel(BaseModel):
    author: AuthorShort


@router.get(
    "/default",
    response_model=GetDefaultAuthorResponseModel,
    tags=["Authors"],
    summary="Default author for user",
)
async def get_default_author(
    authors_auth: Annotated[AuthorsAuth, Depends(authors_auth_provider)],
    default_authors_service: Annotated[
        DefaultAuthorsService, Depends(default_authors_service_provider)
    ],
    user_id: Annotated[
        str | None,
        Query(
            description=(
                "ID of the user for which need to know default author. "
                "If this parameter is not set or is set to null, "
                "current user's ID will be used"
            ),
            examples=["1234"],
        ),
    ],
):
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    author = await default_authors_service.get_default_author(user_id)
    return {"author": {"id": author.id, "name": author.name} if author else None}


@router.put(
    "/default",
    tags=["Authors"],
    summary="Set default author for user",
)
async def set_default_author(
    authors_auth: Annotated[AuthorsAuth, Depends(authors_auth_provider)],
    default_authors_service: Annotated[
        DefaultAuthorsService, Depends(default_authors_service_provider)
    ],
    user_id: Annotated[
        str | None,
        Body(
            embed=True,
            description=(
                "ID of the user for which need to set default author. "
                "If this parameter is not set or is set to null, "
                "current user's ID will be used"
            ),
            examples=["1234"],
        ),
    ],
    author_id: Annotated[str | None, Body(embed=True, examples=["1234"])],
):
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    await default_authors_service.set_default_author(user_id, author_id)
