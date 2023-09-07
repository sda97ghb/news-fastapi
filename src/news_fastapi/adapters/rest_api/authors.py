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
from news_fastapi.core.authors.commands import (
    CreateAuthorService,
    DeleteAuthorService,
    UpdateAuthorService,
)
from news_fastapi.core.authors.default_author import DefaultAuthorService
from news_fastapi.core.authors.exceptions import DeleteAuthorError
from news_fastapi.core.authors.queries import AuthorDetailsService, AuthorsListService

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
            alias="user-id",
        ),
    ] = None,
    authors_auth: AuthorsAuth = Depends(Provide["authors_auth"]),
    default_authors_service: DefaultAuthorService = Depends(
        Provide["default_author_service"]
    ),
) -> GetDefaultAuthorResponseModel:
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    default_author_info = await default_authors_service.get_default_author(
        user_id=user_id
    )
    return GetDefaultAuthorResponseModel(
        author=Author(
            id=default_author_info.author.id, name=default_author_info.author.name
        )
        if default_author_info
        else None
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
    default_author_service: DefaultAuthorService = Depends(
        Provide["default_author_service"]
    ),
) -> None:
    if not user_id:
        user_id = authors_auth.get_current_user_id()
    await default_author_service.set_default_author(
        user_id=user_id, author_id=author_id
    )


class CreateAuthorResponseModel(BaseModel):
    author_id: str

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
    create_author_service: CreateAuthorService = Depends(
        Provide["create_author_service"]
    ),
) -> CreateAuthorResponseModel:
    result = await create_author_service.create_author(name=name)
    return CreateAuthorResponseModel(author_id=result.author.id)


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
    page = await authors_list_service.get_page(offset=offset, limit=limit)
    return [Author(id=item.author_id, name=item.name) for item in page.items]


@router.get(
    "/{authorId}",
    response_model=Author,
    tags=["Authors"],
    summary="Get an author by ID",
)
@inject
async def get_author_by_id(
    author_id: AuthorIdInPath,
    author_details_service: AuthorDetailsService = Depends(
        Provide["author_details_service"]
    ),
) -> Author:
    details = await author_details_service.get_author(author_id=author_id)
    return Author(id=details.author_id, name=details.name)


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
    update_author_service: UpdateAuthorService = Depends(
        Provide["update_author_service"]
    ),
) -> None:
    await update_author_service.update_author(author_id=author_id, new_name=name)


@router.delete(
    "/{authorId}",
    status_code=HTTP_204_NO_CONTENT,
    tags=["Authors"],
    summary="Delete the author with ID",
)
@inject
async def delete_author(
    author_id: AuthorIdInPath,
    delete_author_service: DeleteAuthorService = Depends(
        Provide["delete_author_service"]
    ),
) -> None:
    try:
        await delete_author_service.delete_author(author_id=author_id)
    except DeleteAuthorError as err:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail=str(err)) from err
