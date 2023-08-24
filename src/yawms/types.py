from pathlib import Path
from typing import Any, Callable, TypeVar

from optree.typing import PyTree as _PyTree

T = TypeVar("T")
PyTree = T | list[T] | dict[Any, T] | _PyTree[T]
PathLike = Path | str
PathLikeOrCallable = PyTree[PathLike | Callable[[dict[str, str]], PyTree[PathLike]]]
