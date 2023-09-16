from datetime import UTC, datetime as DateTime
from typing import Any, Type

from sqlalchemy import DATETIME, Dialect
from sqlalchemy.types import TypeDecorator


class UTCDATETIME(TypeDecorator):  # pylint: disable=too-many-ancestors
    @property
    def python_type(self) -> Type[Any]:
        return DateTime

    impl = DATETIME
    LOCAL_TIMEZONE = DateTime.utcnow().astimezone().tzinfo

    def process_literal_param(self, value: Any | None, dialect: Dialect) -> str:
        if not isinstance(value, DateTime):
            raise ValueError("value must be datetime")
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)
        return value.astimezone(UTC).isoformat()

    def process_bind_param(self, value: Any | None, dialect: Dialect) -> Any:
        if not isinstance(value, DateTime):
            raise ValueError("value must be datetime")
        if value.tzinfo is None:
            value = value.astimezone(self.LOCAL_TIMEZONE)
        return value.astimezone(UTC)

    def process_result_value(self, value, dialect):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
