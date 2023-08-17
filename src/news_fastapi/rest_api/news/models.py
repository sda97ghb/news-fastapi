from pydantic import BaseModel

from news_fastapi.rest_api.authors.models import AuthorShort


class NewsShort(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort


class NewsLong(BaseModel):
    id: str
    headline: str
    date_published: str
    author: AuthorShort
    text: str
