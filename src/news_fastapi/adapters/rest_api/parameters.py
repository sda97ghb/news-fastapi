from typing import Annotated

from fastapi import Path, Query

NewsArticleIdInPath = Annotated[
    str,
    Path(
        description="ID of the news article",
        examples=["11112222-3333-4444-5555-666677778888"],
        alias="newsArticleId",
    ),
]

DraftIdInPath = Annotated[
    str,
    Path(
        description="ID of the draft",
        examples=["11112222-3333-4444-5555-666677778888"],
        alias="draftId",
    ),
]

AuthorIdInPath = Annotated[
    str,
    Path(
        description="ID of the author",
        examples=["11112222-3333-4444-5555-666677778888"],
        alias="authorId",
    ),
]

LimitInQuery = Annotated[
    int | None,
    Query(
        description="Max number of returned items, a.k.a. page size",
        examples=[10],
        alias="limit",
    ),
]

OffsetInQuery = Annotated[
    int | None,
    Query(
        description="Skip that many items before beginning to return items",
        examples=[30],
        alias="offset",
    ),
]
