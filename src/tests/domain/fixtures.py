from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime as DateTime
from typing import Collection, Mapping
from uuid import uuid4

from news_fastapi.domain.authors import (
    Author,
    AuthorFactory,
    AuthorRepository,
    DefaultAuthorRepository,
)
from news_fastapi.domain.drafts import Draft, DraftFactory, DraftRepository
from news_fastapi.domain.events.models import DomainEvent
from news_fastapi.domain.events.publisher import DomainEventIdGenerator
from news_fastapi.domain.events.store import DomainEventStore
from news_fastapi.domain.news import (
    NewsArticle,
    NewsArticleFactory,
    NewsArticleListFilter,
    NewsArticleRepository,
)
from news_fastapi.utils.exceptions import NotFoundError


@dataclass
class TestDraft:
    id: str
    news_article_id: str | None
    headline: str
    date_published: DateTime | None
    author_id: str
    text: str
    created_by_user_id: str
    is_published: bool


class TestDraftFactory(DraftFactory):
    def create_draft(
        self,
        draft_id: str,
        news_article_id: str | None,
        headline: str,
        date_published: DateTime | None,
        author_id: str,
        text: str,
        created_by_user_id: str,
        is_published: bool,
    ) -> Draft:
        return TestDraft(
            id=draft_id,
            news_article_id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            text=text,
            created_by_user_id=created_by_user_id,
            is_published=is_published,
        )


class TestDraftRepository(DraftRepository):
    _data: dict[str, Draft]

    def __init__(self, initial_drafts: Iterable[Draft] = ()) -> None:
        self._data = {}
        for draft in initial_drafts:
            self._data[draft.id] = draft

    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, draft: Draft) -> None:
        self._data[draft.id] = draft

    async def get_drafts_list(
        self, offset: int = 0, limit: int = 10
    ) -> Collection[Draft]:
        return list(self._data.values())[offset : offset + limit]

    async def get_draft_by_id(self, draft_id: str) -> Draft:
        try:
            return self._data[draft_id]
        except KeyError as err:
            raise NotFoundError("Draft not found") from err

    async def get_not_published_draft_by_news_id(self, news_article_id: str) -> Draft:
        for draft in self._data.values():
            if not draft.is_published and draft.news_article_id == news_article_id:
                return draft
        raise NotFoundError("Draft not found")

    async def get_drafts_for_author(self, author_id: str) -> Collection[Draft]:
        return [draft for draft in self._data.values() if draft.author_id == author_id]

    async def delete(self, draft: Draft) -> None:
        try:
            del self._data[draft.id]
        except KeyError:
            pass


@dataclass
class TestNewsArticle:
    id: str
    headline: str
    date_published: DateTime
    author_id: str
    text: str
    revoke_reason: str | None


class TestNewsArticleFactory(NewsArticleFactory):
    def create_news_article(
        self,
        news_article_id: str,
        headline: str,
        date_published: DateTime,
        author_id: str,
        text: str,
        revoke_reason: str | None,
    ) -> NewsArticle:
        return TestNewsArticle(
            id=news_article_id,
            headline=headline,
            date_published=date_published,
            author_id=author_id,
            text=text,
            revoke_reason=revoke_reason,
        )


class TestNewsArticleRepository(NewsArticleRepository):
    _data: dict[str, NewsArticle]

    def __init__(self) -> None:
        self._data = {}

    async def next_identity(self) -> str:
        return str(uuid4())

    async def save(self, news_article: NewsArticle) -> None:
        self._data[news_article.id] = news_article

    async def get_news_articles_list(
        self,
        offset: int = 0,
        limit: int = 10,
        filter_: NewsArticleListFilter | None = None,
    ) -> Collection[NewsArticle]:
        return [
            news_article
            for news_article in self._data.values()
            if self._matches_filter(news_article, filter_)
        ]

    def _matches_filter(
        self, news_article: NewsArticle, filter_: NewsArticleListFilter | None
    ) -> bool:
        if filter_ is None:
            return True
        if filter_.revoked == "no_revoked" and news_article.revoke_reason is not None:
            return False
        if filter_.revoked == "only_revoked" and news_article.revoke_reason is None:
            return False
        return True

    async def get_news_article_by_id(self, news_article_id: str) -> NewsArticle:
        try:
            return self._data[news_article_id]
        except KeyError as err:
            raise NotFoundError("News article not found") from err

    async def count_for_author(self, author_id: str) -> int:
        counter = 0
        for news_article in self._data.values():
            if news_article.author_id == author_id:
                counter += 1
        return counter


@dataclass
class TestAuthor:
    id: str
    name: str


class TestAuthorFactory(AuthorFactory):
    def create_author(self, author_id: str, name: str) -> Author:
        return TestAuthor(id=author_id, name=name)


class TestDefaultAuthorRepository(DefaultAuthorRepository):
    _data: dict[str, str | None]

    def __init__(self) -> None:
        self._data = {}

    async def get_default_author_id(self, user_id: str) -> str | None:
        return self._data.get(user_id)

    async def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        self._data[user_id] = author_id


class TestAuthorRepository(AuthorRepository):
    _data: dict[str, Author]

    def __init__(self) -> None:
        self._data = {}

    async def next_identity(self) -> str:
        return str(uuid4())

    async def get_author_by_id(self, author_id: str) -> Author:
        try:
            return self._data[author_id]
        except KeyError as err:
            raise NotFoundError("Author not found") from err

    async def get_authors_list(
        self, offset: int = 0, limit: int = 50
    ) -> Collection[Author]:
        return list(self._data.values())[offset : offset + limit]

    async def get_authors_in_bulk(self, id_list: list[str]) -> Mapping[str, Author]:
        return {
            author_id: author
            for author_id, author in self._data.items()
            if author_id in id_list
        }

    async def save(self, author: Author) -> None:
        self._data[author.id] = author

    async def remove(self, author: Author) -> None:
        try:
            del self._data[author.id]
        except KeyError:
            pass


HUMAN_NAMES = [
    "Katherine Abraham",
    "Charles Allan",
    "Stewart Alsop",
    "Cameron Anderson",
    "Carl Arnold",
    "Carol Avery",
    "Maria Bailey",
    "Jennifer Baker",
    "Jane Ball",
    "Caroline Bell",
    "Ryan Berry",
    "Dominic Black",
    "Lauren Blake",
    "Max Bond",
    "Piers Bower",
    "Emma Brown",
    "Irene Buckland",
    "Fiona Burgess",
    "Bella Butler",
    "Penelope Cameron",
    "Hannah Campbell",
    "Heather Carr",
    "Frank Chapman",
    "Owen Churchill",
    "Pippa Clark",
    "Andrew Clarkson",
    "Gavin Coleman",
    "Dan Cornish",
    "Joseph Davidson",
    "Felicity Davies",
    "Sam Dickens",
    "Sophie Dowd",
    "Brian Duncan",
    "Ella Dyer",
    "Natalie Edmunds",
    "Anna Ellison",
    "Jonathan Ferguson",
    "Claire Fisher",
    "Audrey Forsyth",
    "Ruth Fraser",
    "Alexander Gibson",
    "Grace Gill",
    "Brandon Glover",
    "Emily Graham",
    "Wendy Grant",
    "Tim Gray",
    "Sonia Greene",
    "John Hamilton",
    "Steven Hardacre",
    "Amy Harris",
    "Gabrielle Hart",
    "Michael Hemmings",
    "Jan Henderson",
    "Rachel Hill",
    "Christopher Hodges",
    "Connor Howard",
    "William Hudson",
    "Phil Hughes",
    "Zoe Hunter",
    "Edward Ince",
    "Faith Jackson",
    "Leah James",
    "Kylie Johnston",
    "Paul Jones",
    "Leonard Kelly",
    "Liam Kerr",
    "Theresa King",
    "Richard Knox",
    "Amanda Lambert",
    "Vanessa Langdon",
    "Virginia Lawrence",
    "Joanne Lee",
    "Lily Lewis",
    "Victor Lyman",
    "Bernadette MacDonald",
    "Anne Mackay",
    "Gordon Mackenzie",
    "Christian MacLeod",
    "Madeleine Manning",
    "Dylan Marshall",
    "Thomas Martin",
    "Melanie Mathis",
    "Kimberly May",
    "Jacob McDonald",
    "Wanda McLean",
    "Warren McGrath",
    "Adrian Metcalfe",
    "Oliver Miller",
    "Luke Mills",
    "Sebastian Mitchell",
    "Nicholas Morgan",
    "Stephanie Morrison",
    "Simon Murray",
    "Harry Nash",
    "Rebecca Newman",
    "Lillian Nolan",
    "Tracey North",
    "Diane Ogden",
    "Yvonne Oliver",
    "Carolyn Paige",
    "Nathan Parr",
    "Una Parsons",
    "Keith Paterson",
    "Nicola Payne",
    "Joe Peake",
    "Trevor Peters",
    "Isaac Piper",
    "Anthony Poole",
    "Eric Powell",
    "Donna Pullman",
    "Angela Quinn",
    "James Rampling",
    "Dorothy Randall",
    "Michelle Rees",
    "Jake Reid",
    "Amelia Roberts",
    "Alison Robertson",
    "Mary Ross",
    "Justin Russell",
    "Joan Rutherford",
    "Rose Sanderson",
    "Jason Scott",
    "Jack Sharp",
    "Stephen Short",
    "Ava Simpson",
    "Sarah Skinner",
    "Molly Slater",
    "Lucas Smith",
    "Kevin Springer",
    "Benjamin Stewart",
    "Ian Sutherland",
    "Andrea Taylor",
    "Chloe Terry",
    "Evan Thomson",
    "Matt Tucker",
    "Karen Turner",
    "Abigail Underwood",
    "Lisa Vance",
    "Sean Vaughan",
    "Deirdre Walker",
    "Austin Wallace",
    "Sally Walsh",
    "Neil Watson",
    "Adam Welch",
    "Jessica White",
    "Blake Wilkins",
    "David Wilson",
    "Alexandra Wright",
    "Jasmine Young",
]


class TestDomainEventIdGenerator(DomainEventIdGenerator):
    async def next_event_id(self) -> str:
        return str(uuid4())


class TestDomainEventStore(DomainEventStore):
    _data: list[DomainEvent]

    def __init__(self) -> None:
        self._data = []

    async def append(self, event: DomainEvent) -> None:
        self._data.append(event)

    async def get_not_sent_events(self) -> Collection[DomainEvent]:
        raise NotImplementedError

    async def ack_event_send(self, event: DomainEvent) -> None:
        raise NotImplementedError