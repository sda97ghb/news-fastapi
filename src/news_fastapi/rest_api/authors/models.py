from pydantic import BaseModel


class AuthorShort(BaseModel):
    id: str
    name: str
