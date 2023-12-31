from abc import ABC, abstractmethod

from news_fastapi.core.exceptions import AuthorizationError


class NewsAuth(ABC):
    @abstractmethod
    def can_revoke(self) -> bool:
        raise NotImplementedError

    def check_can_revoke(self) -> None:
        if not self.can_revoke():
            raise AuthorizationError(
                "User doesn't have permission to revoke a news article"
            )
