from news_fastapi.domain.news_article import NewsArticleRepository


async def can_delete_author(
    author_id: str, news_article_repository: NewsArticleRepository
) -> bool:
    news_for_author = await news_article_repository.count_for_author(author_id)
    has_author_published_news = news_for_author > 0
    return not has_author_published_news
