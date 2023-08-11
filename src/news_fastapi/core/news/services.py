from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.core.news.dao import NewsDAO
from news_fastapi.core.news.models import NewsOverview


class NewsService:
    _auth: NewsAuth
    _dao: NewsDAO

    def __init__(self, auth: NewsAuth, news_dao: NewsDAO) -> None:
        self._auth = auth
        self._dao = news_dao

    def get_news_list(self, offset: int = 0, limit: int = 10) -> list[NewsOverview]:
        return self._dao.get_news_overview_list(offset, limit)
