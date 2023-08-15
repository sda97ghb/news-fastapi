from abc import ABC, abstractmethod

from news_fastapi.core.drafts.models import Draft, DraftReference
from news_fastapi.core.utils import LoadPolicy


class DraftsDAO(ABC):
    @abstractmethod
    def get_draft_references_for_author(self, author_id: str) -> list[DraftReference]:
        raise NotImplementedError

    @abstractmethod
    def get_draft_by_id(
        self,
        draft_id: str,
        load_news_article: LoadPolicy = LoadPolicy.REF,
        load_author: LoadPolicy = LoadPolicy.FULL,
    ) -> Draft:
        raise NotImplementedError

    @abstractmethod
    def get_not_published_draft_by_news_id(
        self,
        news_id: str,
        load_news_article: LoadPolicy = LoadPolicy.REF,
        load_author: LoadPolicy = LoadPolicy.REF,
    ) -> Draft:
        raise NotImplementedError

    @abstractmethod
    def delete_drafts(
        self,
        drafts: list[DraftReference | Draft] | None = None,
        draft_ids: list[str] | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_draft(self, draft: Draft) -> Draft:
        raise NotImplementedError
