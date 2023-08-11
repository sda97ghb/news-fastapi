from abc import ABC, abstractmethod

from news_fastapi.core.news.models import NewsOverview
from datetime import datetime as DateTime


class NewsDAO(ABC):
    @abstractmethod
    def get_news_overview_list(self, offset: int, limit: int) -> list[NewsOverview]:
        raise NotImplementedError

    @abstractmethod
    def get_news_overview_list_for_author(self, author_id: str) -> list[NewsOverview]:
        raise NotImplementedError


class MockNewsDAO(NewsDAO):
    def get_news_overview_list(self, offset: int, limit: int) -> list[NewsOverview]:
        return [
            NewsOverview(
                id="1234",
                headline="News 1",
                date_published=DateTime.fromisoformat("2022-01-01T15:00:00+0000"),
                author_id="1234",
            ),
            NewsOverview(
                id="5678",
                headline="News 2",
                date_published=DateTime.fromisoformat("2022-01-01T16:00:00+0000"),
                author_id="1234",
            ),
        ]

    def get_news_overview_list_for_author(self, author_id: str) -> list[NewsOverview]:
        return [
            NewsOverview(
                id="1234",
                headline="News 1",
                date_published=DateTime.fromisoformat("2022-01-01T15:00:00+0000"),
                author_id="1234",
            ),
            NewsOverview(
                id="5678",
                headline="News 2",
                date_published=DateTime.fromisoformat("2022-01-01T16:00:00+0000"),
                author_id="1234",
            ),
        ]
