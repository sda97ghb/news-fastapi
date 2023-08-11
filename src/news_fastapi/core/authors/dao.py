from abc import ABC, abstractmethod
from collections.abc import Iterable

from news_fastapi.core.authors.models import AuthorDetails, AuthorOverview


class AuthorsDAO(ABC):
    @abstractmethod
    def get_author_overview_by_id(self, author_id: str) -> AuthorOverview:
        raise NotImplementedError

    @abstractmethod
    def get_author_details_by_id(self, author_id: str) -> AuthorDetails:
        raise NotImplementedError

    @abstractmethod
    def save_author_details(self, author_details: AuthorDetails) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_author_overview_list(self, offset: int, limit: int) -> list[AuthorOverview]:
        raise NotImplementedError

    @abstractmethod
    def get_author_overview_in_bulk(
        self, id_list: Iterable[str]
    ) -> dict[str, AuthorOverview]:
        raise NotImplementedError

    @abstractmethod
    def delete_author(self, author_id: str) -> None:
        raise NotImplementedError


class MockAuthorsDAO(AuthorsDAO):
    def get_author_overview_by_id(self, author_id: str) -> AuthorOverview:
        return AuthorOverview(id="1234", name="John Doe")

    def get_author_details_by_id(self, author_id: str) -> AuthorDetails:
        return AuthorDetails(id="1234", name="John Doe")

    def save_author_details(self, author_details: AuthorDetails) -> None:
        pass

    def get_author_overview_list(self, offset: int, limit: int) -> list[AuthorOverview]:
        return [
            AuthorOverview(id="1234", name="John Doe"),
            AuthorOverview(id="5678", name="Jane Smith"),
        ]

    def get_author_overview_in_bulk(
        self, id_list: Iterable[str]
    ) -> dict[str, AuthorOverview]:
        return {
            "1234": AuthorOverview(id="1234", name="John Doe"),
            "5678": AuthorOverview(id="5678", name="Jane Smith"),
        }

    def delete_author(self, author_id: str) -> None:
        pass


class DefaultAuthorsDAO(ABC):
    @abstractmethod
    def get_default_author_id(self, user_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        raise NotImplementedError


class MockDefaultAuthorsDAO(DefaultAuthorsDAO):
    def get_default_author_id(self, user_id: str) -> str | None:
        return "1234"

    def set_default_author_id(self, user_id: str, author_id: str | None) -> None:
        pass
