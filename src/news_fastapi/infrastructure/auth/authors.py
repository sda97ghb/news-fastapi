from news_fastapi.application.authors.auth import AuthorsAuth
from news_fastapi.infrastructure.auth.jwt import BaseJWTAuth


class SuperuserAuthorsAuth(AuthorsAuth):
    def can_create_author(self) -> bool:
        return True

    def can_update_author(self, author_id: str) -> bool:
        return True

    def can_delete_author(self, author_id: str) -> bool:
        return True

    def get_current_user_id(self) -> str:
        raise TypeError("Superuser is not a concrete user and has no ID")


class JWTAuthorsAuth(AuthorsAuth, BaseJWTAuth):
    def can_create_author(self) -> bool:
        return "authors:create-author" in self.permissions

    def can_update_author(self, author_id: str) -> bool:
        return "authors:update-author" in self.permissions

    def can_delete_author(self, author_id: str) -> bool:
        return "authors:delete-author" in self.permissions

    def get_current_user_id(self) -> str:
        return self.sub
