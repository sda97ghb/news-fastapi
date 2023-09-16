from datetime import datetime as DateTime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from news_fastapi.adapters.persistence.sqlalchemy_core.utils import UTCDATETIME


class Model(DeclarativeBase):
    pass


class AuthorModel(Model):
    __tablename__ = "authors"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]


class DefaultAuthorModel(Model):
    __tablename__ = "default_authors"

    user_id: Mapped[str] = mapped_column(primary_key=True)
    author_id: Mapped[str]


class DraftModel(Model):
    __tablename__ = "drafts"

    id: Mapped[str] = mapped_column(primary_key=True)
    news_article_id: Mapped[str | None]
    headline: Mapped[str]
    date_published: Mapped[DateTime | None] = mapped_column(type_=UTCDATETIME)
    author_id: Mapped[str]
    image_url: Mapped[str | None]
    image_description: Mapped[str | None]
    image_author: Mapped[str | None]
    text: Mapped[str]
    created_by_user_id: Mapped[str]
    is_published: Mapped[bool]


class NewsArticleModel(Model):
    __tablename__ = "news_articles"

    id: Mapped[str] = mapped_column(primary_key=True)
    headline: Mapped[str]
    date_published: Mapped[DateTime] = mapped_column(type_=UTCDATETIME)
    author_id: Mapped[str]
    image_url: Mapped[str]
    image_description: Mapped[str]
    image_author: Mapped[str]
    text: Mapped[str]
    revoke_reason: Mapped[str | None]
