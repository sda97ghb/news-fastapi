from datetime import datetime as DateTime
from inspect import isawaitable

from tortoise import Model
from tortoise.fields import (
    RESTRICT,
    DatetimeField,
    ForeignKeyField,
    TextField,
    ForeignKeyRelation,
)
from tortoise.signals import pre_save

from news_fastapi.core.authors.models import (
    Author,
    AuthorReference,
    AuthorReferenceDataclass,
)
from news_fastapi.core.news.models import NewsArticle
from news_fastapi.core.utils import NotLoadedType, NotLoaded, UndefinedType, Undefined


class AuthorTortoise(Model):
    id: str = TextField(pk=True)
    name: str = TextField()

    def __assert_implements_protocol(self) -> Author:
        return self


class NewsArticleTortoise(Model):
    id: str = TextField(pk=True)
    headline: str = TextField()
    date_published: DateTime = DatetimeField()
    author_id: str = TextField()
    text: str = TextField()
    revoke_reason: str = TextField()

    author_relation: ForeignKeyRelation[AuthorTortoise] = ForeignKeyField(
        "news.AuthorTortoise", related_name="news_article_relations", on_delete=RESTRICT
    )
    _author: Author | AuthorReference | NotLoadedType | UndefinedType = Undefined

    @property
    def author(self) -> AuthorReference | Author | NotLoadedType:
        if self._author is Undefined:
            self._author = self._populate_author()
        return self._author

    @author.setter
    def author(self, new_author: AuthorReference | Author | NotLoadedType) -> None:
        self._author = new_author

    def _populate_author(self) -> AuthorReference | Author | NotLoadedType:
        if isawaitable(self.author_relation):
            if isawaitable(self.author_id):
                return NotLoaded
            else:
                return AuthorReferenceDataclass(id=self.author_id)
        else:
            # noinspection PyTypeChecker
            return self.author_relation

    def __assert_implements_protocol(self) -> NewsArticle:
        return self


@pre_save(NewsArticleTortoise)
async def _update_news_article_author_if_changed(
    sender: type[NewsArticleTortoise],
    instance: NewsArticleTortoise,
    using_db,
    update_fields,
) -> None:
    if instance.author is not NotLoaded:
        instance.author_id = instance.author.id


# class DraftTortoise(Model):
#     id = TextField(pk=True)
#     news_article = ForeignKeyField(
#         "news.NewsArticleTortoise", related_name="drafts", on_delete=CASCADE
#     )
#     headline = TextField()
#     date_published = DatetimeField(null=True)
#     author = ForeignKeyField(
#         "news.AuthorTortoise", related_name="drafts", on_delete=RESTRICT
#     )
#     text = TextField()
#     create_by_user_id = TextField()
#     is_published = BooleanField()
#
#     def __assert_implements_protocol(self) -> Draft:
#         return self
