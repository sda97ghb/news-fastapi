from abc import ABC, abstractmethod

from news_fastapi.application.exceptions import AuthorizationError


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
    def get_current_user_id(self) -> str:
        raise NotImplementedError
