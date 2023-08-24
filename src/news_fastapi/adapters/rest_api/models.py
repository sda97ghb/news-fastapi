from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AuthorShort(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NewsShort(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class NewsLong(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort
    text: str

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
