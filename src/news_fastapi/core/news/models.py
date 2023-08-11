from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Protocol


@dataclass
class NewsOverview:
    id: str
    headline: str
    date_published: DateTime
    author_id: str


class NewsArticleListItem(Protocol):
    id: str
    headline: str
    date_published: DateTime
    author: Author


class NewsArticleDetails(Protocol):
    id: str
    headline: str
    date_published: DateTime
    author: Author
    text: str
