from datetime import datetime as DateTime

from tortoise import Model
from tortoise.fields import BooleanField, DatetimeField, TextField


class AuthorModel(Model):
    id: str = TextField(pk=True)
    name: str = TextField()

    class Meta:
        table = "authors"


class DefaultAuthorModel(Model):
    user_id: str = TextField()
    author_id: str = TextField()

    class Meta:
        table = "default_authors"


class DraftModel(Model):
    id: str = TextField(pk=True)
    news_article_id: str | None = TextField(null=True)
    headline: str = TextField()
    date_published: DateTime | None = DatetimeField(null=True)
    author_id: str = TextField()
    image_url: str | None = TextField(null=True)
    image_description: str | None = TextField(null=True)
    image_author: str | None = TextField(null=True)
    text: str = TextField()
    created_by_user_id: str = TextField()
    is_published: bool = BooleanField()  # type: ignore[assignment]

    class Meta:
        table = "drafts"


class NewsArticleModel(Model):
    id: str = TextField(pk=True)
    headline: str = TextField()
    date_published: DateTime = DatetimeField()
    author_id: str = TextField()
    image_url: str = TextField()
    image_description: str = TextField()
    image_author: str = TextField()
    text: str = TextField()
    revoke_reason: str | None = TextField(null=True)

    class Meta:
        table = "news_articles"
