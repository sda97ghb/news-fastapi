from news_fastapi.adapters.auth.jwt import BaseJWTAuth
from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.exceptions import AuthenticationError


class SuperuserAuthorsAuth(AuthorsAuth):
    def can_create_author(self) -> bool:
        return True

    def can_update_author(self, author_id: str) -> bool:
        return True

    def can_delete_author(self, author_id: str) -> bool:
        return True

    def get_current_user_id(self) -> str:
        raise AuthenticationError("Superuser is not a concrete user and has no ID")


class JWTAuthorsAuth(AuthorsAuth, BaseJWTAuth):
    def can_create_author(self) -> bool:
        return "authors:create-author" in self.permissions

    def can_update_author(self, author_id: str) -> bool:
        return "authors:update-author" in self.permissions

    def can_delete_author(self, author_id: str) -> bool:
        return "authors:delete-author" in self.permissions

    def get_current_user_id(self) -> str:
        return self.sub


class AnonymousAuthorsAuth(AuthorsAuth):
    def can_create_author(self) -> bool:
        return False

    def can_update_author(self, author_id: str) -> bool:
        return False

    def can_delete_author(self, author_id: str) -> bool:
        return False

    def get_current_user_id(self) -> str:
        raise AuthenticationError("Anonymous user is not a concrete user and has no ID")
