import warnings
from enum import Enum, StrEnum
from typing import Literal


class _NotLoadedType(Enum):
    NOT_LOADED = object()

    @property
    def value(self) -> "_NotLoadedType":  # pylint: disable=invalid-overridden-method
        return _NotLoadedType.NOT_LOADED

    def __repr__(self) -> str:
        return "NotLoaded"

    def __str__(self) -> str:
        return "NotLoaded"

    def __bool__(self) -> bool:
        raise TypeError("Can't determine if not loaded value is True or False")

    def __eq__(self, other) -> bool:
        raise NotImplementedError(
            "Impossible to compare not loaded value. Did you mean 'is NotLoaded'?"
        )


NotLoaded = _NotLoadedType.NOT_LOADED
NotLoadedType = Literal[_NotLoadedType.NOT_LOADED]


class LoadPolicy(StrEnum):
    NO = "no"  # don't load anything, i.e. return NotLoaded
    REF = "ref"  # load only reference
    FULL = "full"  # load full object


class _UndefinedType(Enum):
    UNDEFINED = object()

    @property
    def value(self) -> "_UndefinedType":  # pylint: disable=invalid-overridden-method
        return _UndefinedType.UNDEFINED

    def __repr__(self) -> str:
        return "Undefined"

    def __str__(self) -> str:
        return "Undefined"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other) -> bool:
        warnings.warn(
            "Undefined is never equal to anything else. "
            "Did you mean 'is Undefined'?",
            category=SyntaxWarning,
            stacklevel=2,
        )
        return False

    def __hash__(self) -> int:
        return id(_UndefinedType.UNDEFINED)


Undefined = _UndefinedType.UNDEFINED
UndefinedType = Literal[_UndefinedType.UNDEFINED]
