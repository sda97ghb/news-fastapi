from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Author(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Draft(BaseModel):
    id: str
    news_article_id: str | None
    headline: str
    date_published: str | None
    author: Author
    text: str
    created_by_user_id: str
    is_published: bool

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class DraftsListItem(BaseModel):
    id: str
    news_article_id: str | None
    headline: str
    created_by_user_id: str
    is_published: bool

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NewsArticle(BaseModel):
    id: str
    headline: str
    date_published: str
    author: Author
    text: str
    revoke_reason: str | None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NewsArticlesListItem(BaseModel):
    id: str
    headline: str
    date_published: str
    author: Author
    revoke_reason: str | None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
