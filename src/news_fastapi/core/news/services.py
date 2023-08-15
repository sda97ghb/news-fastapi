from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.core.news.dao import NewsArticleListFilter, NewsDAO
from news_fastapi.core.news.models import NewsArticle, NewsArticleListItem
from news_fastapi.core.utils import LoadPolicy


class NewsListService:
    _dao: NewsDAO

    def get_page(self, offset: int = 0, limit: int = 50) -> list[NewsArticleListItem]:
        return self._dao.get_news_article_list(
            offset, limit, filter_=NewsArticleListFilter(revoked="no_revoked")
        )


class NewsService:
    _auth: NewsAuth
    _dao: NewsDAO

    def __init__(self, auth: NewsAuth, news_dao: NewsDAO) -> None:
        self._auth = auth
        self._dao = news_dao

    def get_news_article(self, news_id: str) -> NewsArticle:
        return self._dao.get_news_article(news_id)

    def revoke_news_article(self, news_id: str, reason: str) -> None:
        self._auth.check_can_revoke()
        news_article = self._dao.get_news_article(news_id, load_author=LoadPolicy.NO)
        news_article.revoke_reason = reason
        self._dao.save_news_article(news_article)
