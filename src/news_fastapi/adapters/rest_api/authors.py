from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT

from news_fastapi.adapters.rest_api.models import Author
from news_fastapi.adapters.rest_api.parameters import (
    AuthorIdInPath,
    LimitInQuery,
    OffsetInQuery,
)
from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.authors.services import (
    AuthorsListService,
    AuthorsService,
    DefaultAuthorsService,
)

router = APIRouter()


DEFAULT_AUTHORS_LIST_LIMIT = 50


class GetDefaultAuthorResponseModel(BaseModel):
    author: Author | None

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
    ] = None,
    authors_auth: AuthorsAuth = Depends(Provide["authors_auth"]),
    default_authors_service: DefaultAuthorsService = Depends(
        Provide["default_authors_service"]
    ),
) -> GetDefaultAuthorResponseModel:
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    author = await default_authors_service.get_default_author(user_id)
    return GetDefaultAuthorResponseModel(
        author=Author(id=author.id, name=author.name) if author else None
    )


@router.put(
    "/default",
    tags=["Authors"],
    summary="Set default author for user",
    status_code=HTTP_204_NO_CONTENT,
)
@inject
async def set_default_author(
    author_id: Annotated[
        str | None,
        Body(
            embed=True, examples=["1234"], alias="authorId", validation_alias="authorId"
        ),
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
            alias="userId",
            validation_alias="userId",
        ),
    ] = None,
    authors_auth: AuthorsAuth = Depends(Provide["authors_auth"]),
    default_authors_service: DefaultAuthorsService = Depends(
        Provide["default_authors_service"]
    ),
) -> None:
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    await default_authors_service.set_default_author(user_id, author_id)


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
) -> CreateAuthorResponseModel:
    author_id = await authors_service.create_author(name=name)
    return CreateAuthorResponseModel(id=author_id)


@router.get(
    "/",
    response_model=list[Author],
    tags=["Authors"],
    summary="List of authors",
)
@inject
async def get_list_of_authors(
    limit: LimitInQuery = None,
    offset: OffsetInQuery = None,
    authors_list_service: AuthorsListService = Depends(Provide["authors_list_service"]),
) -> list[Author]:
    if limit is None:
        limit = DEFAULT_AUTHORS_LIST_LIMIT
    if offset is None:
        offset = 0
    authors_list = await authors_list_service.get_page(offset=offset, limit=limit)
    return [Author(id=author.id, name=author.name) for author in authors_list]


@router.get(
    "/{authorId}",
    response_model=Author,
    tags=["Authors"],
    summary="Get an author by ID",
)
@inject
async def get_author_by_id(
    author_id: AuthorIdInPath,
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
) -> Author:
    author = await authors_service.get_author(author_id)
    return Author(id=author.id, name=author.name)


@router.put(
    "/{authorId}",
    status_code=HTTP_204_NO_CONTENT,
    tags=["Authors"],
    summary="Update the author with ID",
)
@inject
async def update_author(
    author_id: AuthorIdInPath,
    name: Annotated[str, Body(embed=True, examples=["John Doe"])],
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
) -> None:
    await authors_service.update_author(author_id=author_id, new_name=name)


@router.delete(
    "/{authorId}",
    status_code=HTTP_204_NO_CONTENT,
    tags=["Authors"],
    summary="Delete the author with ID",
)
@inject
async def delete_author(
    author_id: AuthorIdInPath,
    authors_service: AuthorsService = Depends(Provide["authors_service"]),
) -> None:
    try:
        await authors_service.delete_author(author_id=author_id)
    except DeleteAuthorError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err
