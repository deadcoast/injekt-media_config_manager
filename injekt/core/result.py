"""Result types for operation outcomes."""

from dataclasses import dataclass
from typing import TypeVar, Generic, Union

T = TypeVar('T')


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful operation result."""
    value: T


@dataclass(frozen=True)
class Failure:
    """Represents a failed operation result."""
    error: Exception


Result = Union[Success[T], Failure]


def is_success(result: Result) -> bool:
    """Check if result is a success."""
    return isinstance(result, Success)


def is_failure(result: Result) -> bool:
    """Check if result is a failure."""
    return isinstance(result, Failure)
