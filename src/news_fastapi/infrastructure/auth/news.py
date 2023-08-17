from news_fastapi.application.news.auth import NewsAuth
from news_fastapi.infrastructure.auth.jwt import BaseJWTAuth


class SuperuserNewsAuth(NewsAuth):
    def can_revoke(self) -> bool:
        return True


class JWTNewsAuth(NewsAuth, BaseJWTAuth):
    def can_revoke(self) -> bool:
        return "news:revoke" in self.permissions
