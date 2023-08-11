from abc import ABC, abstractmethod


class AuthorsAuth(ABC):
    @abstractmethod
    def can_create_author(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def can_update_author(self, author_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def can_delete_author(self, author_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_current_user_id(self) -> str:
        raise NotImplementedError


class SuperuserAuthorsAuth(AuthorsAuth):
    def can_create_author(self) -> bool:
        return True

    def can_update_author(self, author_id: str) -> bool:
        return True

    def can_delete_author(self, author_id: str) -> bool:
        return True

    def get_current_user_id(self) -> str:
        raise Exception("Superuser is not a concrete user and has not ID")
