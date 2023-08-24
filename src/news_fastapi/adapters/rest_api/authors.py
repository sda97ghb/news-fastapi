from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from starlette.status import HTTP_201_CREATED, HTTP_409_CONFLICT

from news_fastapi.adapters.rest_api.models import AuthorShort
from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)

router = APIRouter()


class CreateAuthorResponseModel(BaseModel):
    id: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.post(
    "/",
    response_model=CreateAuthorResponseModel,
    status_code=HTTP_201_CREATED,
    tags=["Authors"],
    summary="Create an author",
)
@inject
async def create_author(
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
):
    author_id = await authors_service.create_author(name=name)
    return {"id": author_id}


@router.get(
    "/",
    response_model=list[AuthorShort],
    tags=["Authors"],
    summary="List of authors",
)
@inject
async def get_list_of_authors(
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
    authors_list_service: AuthorsListService = Depends(Provide["authors_list_service"]),
):
    authors_list = await authors_list_service.get_page(offset=offset, limit=limit)
    return [AuthorShort(id=author.id, name=author.name) for author in authors_list]


@router.get(
    "/{authorId}",
    tags=["Authors"],
    summary="Get an author by ID",
)
@inject
async def get_author_by_id(
    author_id: Annotated[
        str, Path(description="ID of the author", examples=["1234"], alias="authorId")
    ],
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
):
    author = await authors_service.get_author(author_id)
    return AuthorShort(id=author.id, name=author.name)


@router.put(
    "/{authorId}",
    tags=["Authors"],
    summary="Update the author with ID",
)
@inject
async def update_author(
    author_id: Annotated[
        str, Path(description="ID of the author", examples=["1234"], alias="authorId")
    ],
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
):
    await authors_service.update_author(author_id=author_id, new_name=name)


@router.delete(
    "/{authorId}",
    tags=["Authors"],
    summary="Delete the author with ID",
)
@inject
async def delete_author(
    author_id: Annotated[
        str, Path(description="ID of the author", examples=["1234"], alias="authorId")
    ],
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
):
    try:
        await authors_service.delete_author(author_id=author_id)
    except DeleteAuthorError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err


class GetDefaultAuthorResponseModel(BaseModel):
    author: AuthorShort

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


@router.get(
    "/default",
    response_model=GetDefaultAuthorResponseModel,
    tags=["Authors"],
    summary="Default author for user",
)
@inject
async def get_default_author(
    user_id: Annotated[
        str | None,
        Query(
            description=(
                "ID of the user for which need to know default author. "
                "If this parameter is not set or is set to null, "
                "current user's ID will be used"
            ),
            examples=["1234"],
            alias="userId",
        ),
    ],
    authors_auth: AuthorsAuth = Depends(Provide["authors_auth"]),
    default_authors_service: DefaultAuthorsService = Depends(
        Provide["default_authors_service"]
    ),
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
@inject
async def set_default_author(
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
            alias="userId",
            validation_alias="userId",
        ),
    ],
    author_id: Annotated[
        str | None,
        Body(
            embed=True, examples=["1234"], alias="authorId", validation_alias="authorId"
        ),
    ],
    authors_auth: AuthorsAuth = Depends(Provide["authors_auth"]),
    default_authors_service: DefaultAuthorsService = Depends(
        Provide["default_authors_service"]
    ),
):
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    await default_authors_service.set_default_author(user_id, author_id)
