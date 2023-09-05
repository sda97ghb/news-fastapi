from dataclasses import dataclass

from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.core.transaction import TransactionManager
from news_fastapi.domain.news_article import NewsArticle, NewsArticleRepository


@dataclass
class RevokeNewsArticleResult:
    revoked_news_article: NewsArticle


class RevokeNewsArticleService:
    _auth: NewsAuth
    _transaction_manager: TransactionManager
    _news_article_repository: NewsArticleRepository

    def __init__(
        self,
        auth: NewsAuth,
        transaction_manager: TransactionManager,
        news_article_repository: NewsArticleRepository,
    ) -> None:
        self._auth = auth
        self._transaction_manager = transaction_manager
        self._news_article_repository = news_article_repository

    async def revoke_news_article(
        self, news_article_id: str, reason: str
    ) -> RevokeNewsArticleResult:
        async with self._transaction_manager.in_transaction():
            self._auth.check_can_revoke()
            news_article = await self._news_article_repository.get_news_article_by_id(
                news_article_id=news_article_id
            )
            news_article.revoke(reason=reason)
            await self._news_article_repository.save(news_article)
            return RevokeNewsArticleResult(revoked_news_article=news_article)
