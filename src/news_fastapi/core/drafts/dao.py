from abc import ABC, abstractmethod

from news_fastapi.core.drafts.models import DraftOverview


class DraftsDAO(ABC):
    @abstractmethod
    def get_draft_overview_list_for_author(self, author_id: str) -> list[DraftOverview]:
        raise NotImplementedError

    @abstractmethod
    def delete_drafts(self, draft_ids: list[str]) -> None:
        raise NotImplementedError


class MockDraftsDAO(DraftsDAO):
    def get_draft_overview_list_for_author(self, author_id: str) -> list[DraftOverview]:
        return [DraftOverview(id="1234")]

    def delete_drafts(self, draft_ids: list[str]) -> None:
        pass
