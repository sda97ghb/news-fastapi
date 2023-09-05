from news_fastapi.adapters.auth.jwt import BaseJWTAuth
from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.exceptions import AuthenticationError


class SuperuserDraftsAuth(DraftsAuth):
    def can_create_draft(self) -> bool:
        return True

    def can_get_draft(self, draft_id: str) -> bool:
        return True

    def can_get_drafts_list(self) -> bool:
        return True

    def can_update_draft(self, draft_id: str) -> bool:
        return True

    def can_delete_draft(self, draft_id: str) -> bool:
        return True

    def can_delete_published_draft(self) -> bool:
        return True

    def can_publish_draft(self) -> bool:
        return True

    def get_current_user_id(self) -> str:
        raise AuthenticationError("Superuser is not a concrete user and has not ID")


class JWTDraftsAuth(DraftsAuth, BaseJWTAuth):
    def can_create_draft(self) -> bool:
        return "drafts:manage" in self.permissions

    def can_get_draft(self, draft_id: str) -> bool:
        return "drafts:manage" in self.permissions

    def can_get_drafts_list(self) -> bool:
        return "drafts:manage" in self.permissions

    def can_update_draft(self, draft_id: str) -> bool:
        return "drafts:manage" in self.permissions

    def can_delete_draft(self, draft_id: str) -> bool:
        return "drafts:manage" in self.permissions

    def can_delete_published_draft(self) -> bool:
        return "drafts:delete-published" in self.permissions

    def can_publish_draft(self) -> bool:
        return "drafts:publish" in self.permissions

    def get_current_user_id(self) -> str:
        return self.sub
