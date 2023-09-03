from typing import Any


class Entity:
    _id: str

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        return self._id

    def __init__(self, id_: str) -> None:
        self._id = id_

    def __eq__(self, other: Any) -> bool:
        if other is None or not isinstance(other, Entity):
            return False
        if other is self:
            return True
        if type(other) != type(self):  # pylint: disable=unidiomatic-typecheck
            return False
        return other.id == self.id
