from abc import ABC, abstractmethod

from news_fastapi.core.exceptions import AuthorizationError


class AuthorsAuth(ABC):
    @abstractmethod
    def can_create_author(self) -> bool:
        raise NotImplementedError

    def check_create_author(self) -> None:
        if not self.can_create_author():
            raise AuthorizationError("User doesn't have permission to create an author")

    @abstractmethod
    def can_update_author(self, author_id: str) -> bool:
        raise NotImplementedError

    def check_update_author(self, author_id: str) -> None:
        if not self.can_update_author(author_id):
            raise AuthorizationError(
                "User doesn't have permission to update the author"
            )

    @abstractmethod
    def can_delete_author(self, author_id: str) -> bool:
        raise NotImplementedError

    def check_delete_author(self, author_id: str) -> None:
        if not self.can_delete_author(author_id):
            raise AuthorizationError(
                "User doesn't have permission to delete the author"
            )

    @abstractmethod
    def can_get_default_author(self) -> bool:
        raise NotImplementedError

    def check_get_default_author(self) -> None:
        if not self.can_get_default_author():
            raise AuthorizationError(
                "User doesn't have permission to get default author"
            )

    @abstractmethod
    def can_set_default_author(self) -> bool:
        raise NotImplementedError

    def check_set_default_author(self) -> None:
        if not self.can_set_default_author():
            raise AuthorizationError(
                "User doesn't have permission to set default author"
            )

    @abstractmethod
    def get_current_user_id(self) -> str:
        raise NotImplementedError
