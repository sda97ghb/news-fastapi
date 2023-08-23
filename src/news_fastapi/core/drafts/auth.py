from abc import ABC, abstractmethod

from news_fastapi.core.exceptions import AuthorizationError


class DraftsAuth(ABC):
    @abstractmethod
    def can_create_draft(self) -> bool:
        raise NotImplementedError

    def check_create_draft(self) -> None:
        if not self.can_create_draft():
            raise AuthorizationError("User doesn't have permission to create a draft")

    @abstractmethod
    def can_get_draft(self, draft_id: str) -> bool:
        raise NotImplementedError

    def check_get_draft(self, draft_id: str) -> None:
        if not self.can_get_draft(draft_id):
            raise AuthorizationError("User doesn't have permission to get a draft")

    @abstractmethod
    def can_update_draft(self, draft_id: str) -> bool:
        raise NotImplementedError

    def check_update_draft(self, draft_id: str) -> None:
        if not self.can_update_draft(draft_id):
            raise AuthorizationError("User doesn't have permission to update a draft")

    @abstractmethod
    def can_delete_draft(self, draft_id: str) -> bool:
        raise NotImplementedError

    def check_delete_draft(self, draft_id: str) -> None:
        if not self.can_delete_draft(draft_id):
            raise AuthorizationError("User doesn't have permission to delete a draft")

    @abstractmethod
    def can_delete_published_draft(self) -> bool:
        raise NotImplementedError

    def check_delete_published_draft(self) -> None:
        if not self.can_delete_published_draft():
            raise AuthorizationError(
                "User doesn't have permission to delete a *published* draft"
            )

    @abstractmethod
    def can_publish_draft(self) -> bool:
        raise NotImplementedError

    def check_publish_draft(self) -> None:
        if not self.can_publish_draft():
            raise AuthorizationError("User doesn't have permission to publish a draft")

    @abstractmethod
    def get_current_user_id(self) -> str:
        raise NotImplementedError
