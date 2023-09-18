from sqlalchemy import BOOLEAN, TEXT, Column, MetaData, Table

from news_fastapi.adapters.persistence.sqlalchemy.data_types import UTCDATETIME

metadata = MetaData()

authors_table = Table(
    "authors",
    metadata,
    Column("id", TEXT(), primary_key=True),
    Column("name", TEXT()),
)

default_authors_table = Table(
    "default_authors",
    metadata,
    Column("user_id", TEXT()),
    Column("author_id", TEXT()),
)

drafts_table = Table(
    "drafts",
    metadata,
    Column("id", TEXT(), primary_key=True),
    Column("news_article_id", TEXT(), nullable=True),
    Column("headline", TEXT()),
    Column("date_published", UTCDATETIME(timezone=True), nullable=True),
    Column("author_id", TEXT()),
    Column("image_url", TEXT(), nullable=True),
    Column("image_description", TEXT(), nullable=True),
    Column("image_author", TEXT(), nullable=True),
    Column("text", TEXT()),
    Column("created_by_user_id", TEXT()),
    Column("is_published", BOOLEAN()),
)

news_articles_table = Table(
    "news_articles",
    metadata,
    Column("id", TEXT(), primary_key=True),
    Column("headline", TEXT()),
    Column("date_published", UTCDATETIME(timezone=True)),
    Column("author_id", TEXT()),
    Column("image_url", TEXT()),
    Column("image_description", TEXT()),
    Column("image_author", TEXT()),
    Column("text", TEXT()),
    Column("revoke_reason", TEXT(), nullable=True),
)
