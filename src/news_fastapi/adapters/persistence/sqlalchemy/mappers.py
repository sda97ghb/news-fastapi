from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property, composite, registry

from news_fastapi.adapters.persistence.sqlalchemy.tables import (
    authors_table,
    drafts_table,
    metadata,
    news_articles_table,
)
from news_fastapi.domain.author import Author
from news_fastapi.domain.draft import Draft
from news_fastapi.domain.news_article import NewsArticle
from news_fastapi.domain.value_objects import Image

mapper_registry = registry(metadata=metadata)


def setup_orm_mappers():
    mapper_registry.map_imperatively(
        Author,
        authors_table,
        properties={
            "_id": column_property(authors_table.c.id),
            "_name": column_property(authors_table.c.name),
        },
    )
    mapper_registry.map_imperatively(
        Draft,
        drafts_table,
        properties={
            "_id": column_property(drafts_table.c.id),
            "_news_article_id": column_property(drafts_table.c.news_article_id),
            "_created_by_user_id": column_property(drafts_table.c.created_by_user_id),
            "_headline": column_property(drafts_table.c.headline),
            "_date_published": column_property(drafts_table.c.date_published),
            "_author_id": column_property(drafts_table.c.author_id),
            "_image_url": column_property(drafts_table.c.image_url),
            "_image_description": column_property(drafts_table.c.image_description),
            "_image_author": column_property(drafts_table.c.image_author),
            # composite doesn't work with nullable properties
            # "_image": composite(
            #     Image,
            #     drafts_table.c.image_url,
            #     drafts_table.c.image_description,
            #     drafts_table.c.image_author,
            # ),
            "_text": column_property(drafts_table.c.text),
            "_is_published": column_property(drafts_table.c.is_published),
        },
    )
    _patch_draft_image()
    mapper_registry.map_imperatively(
        NewsArticle,
        news_articles_table,
        properties={
            "_id": column_property(news_articles_table.c.id),
            "_headline": column_property(news_articles_table.c.headline),
            "_date_published": column_property(news_articles_table.c.date_published),
            "_author_id": column_property(news_articles_table.c.author_id),
            "_image": composite(
                Image,
                news_articles_table.c.image_url,
                news_articles_table.c.image_description,
                news_articles_table.c.image_author,
            ),
            "_text": column_property(news_articles_table.c.text),
            "_revoke_reason": column_property(news_articles_table.c.revoke_reason),
        },
    )


def _patch_draft_image() -> None:
    # pylint: disable=protected-access
    @hybrid_property
    def _image(self) -> Image | None:
        if (
            self._image_url is not None
            and self._image_description is not None
            and self._image_author is not None
        ):
            return Image(
                url=self._image_url,
                description=self._image_description,
                author=self._image_author,
            )
        return None

    @_image.setter  # type: ignore[no-redef]
    def _image(self, image: Image | None) -> None:
        if image is None:
            self._image_url = None
            self._image_description = None
            self._image_author = None
        else:
            self._image_url = image.url
            self._image_description = image.description
            self._image_author = image.author

    Draft._image = _image


def dispose_orm_mappers():
    mapper_registry.dispose()
