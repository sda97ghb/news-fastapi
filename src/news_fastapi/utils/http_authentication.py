from dataclasses import dataclass

from starlette.requests import Request


@dataclass
class AuthorizationHeader:
    scheme: str
    parameters: str


@dataclass
class BearerAuthorizationHeader(AuthorizationHeader):
    token: str


def parse_authorization_header(header_value: str) -> AuthorizationHeader:
    scheme_separator_position = header_value.index(" ")
    scheme = header_value[:scheme_separator_position]
    parameters = header_value[scheme_separator_position + 1 :]
    if scheme == "Bearer":
        return BearerAuthorizationHeader(
            scheme=scheme, parameters=parameters, token=parameters
        )
    return AuthorizationHeader(scheme=scheme, parameters=parameters)


def get_authorization_header(request: Request) -> AuthorizationHeader | None:
    header_value = request.headers.get("Authorization")
    if header_value is None:
        return None
    return parse_authorization_header(header_value)
