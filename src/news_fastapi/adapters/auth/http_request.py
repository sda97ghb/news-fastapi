from starlette.requests import Request

from news_fastapi.adapters.auth.authors import AnonymousAuthorsAuth, JWTAuthorsAuth
from news_fastapi.adapters.auth.drafts import JWTDraftsAuth
from news_fastapi.adapters.auth.jwt import JWTConfig, authenticate_jwt
from news_fastapi.adapters.auth.news import AnonymousNewsAuth, JWTNewsAuth
from news_fastapi.core.authors.auth import AuthorsAuth
from news_fastapi.core.drafts.auth import DraftsAuth
from news_fastapi.core.exceptions import AuthenticationError
from news_fastapi.core.news.auth import NewsAuth
from news_fastapi.utils.http_authentication import (
    AuthorizationHeader,
    BearerAuthorizationHeader,
    get_authorization_header,
)


class UnsupportedAuthorizationSchemeError(AuthenticationError):
    def __init__(self, scheme: str) -> None:
        super().__init__(f"Unsupported Authorization header scheme '{scheme}'")


class NoAuthenticationInfoError(AuthenticationError):
    def __init__(self, supported_info: list[str]) -> None:
        super().__init__(
            "No acceptable authentication information provided, "
            "use one of the following: " + ",".join(supported_info) + "."
        )


class RequestHolder:
    _request: Request | None

    def __init__(self) -> None:
        self._request = None

    def get(self) -> Request | None:
        return self._request

    def set(self, request: Request) -> None:
        self._request = request


class RequestAuthFactory:
    _request_holder: RequestHolder
    _jwt_config: JWTConfig
    _cached_authorization_header: AuthorizationHeader | None

    def __init__(self, request_holder: RequestHolder, jwt_config: JWTConfig) -> None:
        self._request_holder = request_holder
        self._jwt_config = jwt_config
        self._cached_authorization_header = None

    def get_authorization_header(self) -> AuthorizationHeader | None:
        request = self._request_holder.get()
        if request is None:
            raise ValueError("Request is None. Did you forget to set it in middleware?")
        if self._cached_authorization_header is None:
            self._cached_authorization_header = get_authorization_header(request)
        return self._cached_authorization_header

    def authors_auth(self) -> AuthorsAuth:
        authorization_header = self.get_authorization_header()
        if authorization_header:
            if isinstance(authorization_header, BearerAuthorizationHeader):
                jwt_str = authorization_header.token
                authentication_result = authenticate_jwt(jwt_str, self._jwt_config)
                return JWTAuthorsAuth(authentication_result.jwt_claims)
            raise UnsupportedAuthorizationSchemeError(authorization_header.scheme)
        return AnonymousAuthorsAuth()

    def drafts_auth(self) -> DraftsAuth:
        authorization_header = self.get_authorization_header()
        if authorization_header:
            if isinstance(authorization_header, BearerAuthorizationHeader):
                jwt_str = authorization_header.token
                authentication_result = authenticate_jwt(jwt_str, self._jwt_config)
                return JWTDraftsAuth(authentication_result.jwt_claims)
            raise UnsupportedAuthorizationSchemeError(authorization_header.scheme)
        raise NoAuthenticationInfoError(
            supported_info=["Authorization header with Bearer scheme"]
        )

    def news_auth(self) -> NewsAuth:
        authorization_header = self.get_authorization_header()
        if authorization_header:
            if isinstance(authorization_header, BearerAuthorizationHeader):
                jwt_str = authorization_header.token
                authentication_result = authenticate_jwt(jwt_str, self._jwt_config)
                return JWTNewsAuth(authentication_result.jwt_claims)
            raise UnsupportedAuthorizationSchemeError(authorization_header.scheme)
        return AnonymousNewsAuth()
