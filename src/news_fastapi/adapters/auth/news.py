from news_fastapi.adapters.auth.jwt import BaseJWTAuth
from news_fastapi.core.news.auth import NewsAuth


class SuperuserNewsAuth(NewsAuth):
    def can_revoke(self) -> bool:
        return True


class JWTNewsAuth(NewsAuth, BaseJWTAuth):
    def can_revoke(self) -> bool:
        return "news:revoke" in self.permissions


class AnonymousNewsAuth(NewsAuth):
    def can_revoke(self) -> bool:
        return False
