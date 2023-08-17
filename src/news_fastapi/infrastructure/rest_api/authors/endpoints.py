from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query, Request
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_409_CONFLICT

from news_fastapi.application.authors.exceptions import DeleteAuthorError
from news_fastapi.infrastructure.rest_api.authors.container import (
    AuthorsRequestContainer,
)
from news_fastapi.infrastructure.rest_api.authors.models import AuthorShort

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
def create_author(
    request: Request,
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
):
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    author = authors_service.create_author(name=name)
    return {"id": author.id}


@router.get(
    "/",
    response_model=list[AuthorShort],
    tags=["Authors"],
    summary="List of authors",
)
def get_list_of_authors(
    request: Request,
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
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    authors_list = authors_service.get_authors_list(offset=offset, limit=limit)
    return [AuthorShort(id=author.id, name=author.name) for author in authors_list]


@router.put(
    "/{authorId}",
    tags=["Authors"],
    summary="Update the author with ID",
)
def update_author(
    request: Request,
    author_id: Annotated[str, Path(description="ID of the author", examples=["1234"])],
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
):
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    authors_service.update_author(author_id=author_id, new_name=name)


@router.delete(
    "/{authorId}",
    tags=["Authors"],
    summary="Delete the author with ID",
)
def delete_author(
    request: Request,
    author_id: Annotated[str, Path(description="ID of the author", examples=["1234"])],
):
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    try:
        authors_service.delete_author(author_id=author_id)
    except DeleteAuthorError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err))


class GetDefaultAuthorResponseModel(BaseModel):
    author: AuthorShort


@router.get(
    "/default",
    response_model=GetDefaultAuthorResponseModel,
    tags=["Authors"],
    summary="Default author for user",
)
def get_default_author(
    request: Request,
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
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    if not user_id:
        auth = container.auth
        user_id = auth.get_current_user_id()
    author = authors_service.get_default_author(user_id)
    return {"author": {"id": author.id, "name": author.name} if author else None}


@router.put(
    "/default",
    tags=["Authors"],
    summary="Set default author for user",
)
def set_default_author(
    request: Request,
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
    container = AuthorsRequestContainer(request)
    authors_service = container.authors_service
    if not user_id:
        auth = container.auth
        user_id = auth.get_current_user_id()
    authors_service.set_default_author(user_id, author_id)
