"""Utility functions for the models module."""

import warnings
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from qcdata import Structure


def deprecated_function(new_name: str):
    """Notify users that a function is deprecated and will be removed in the future.
    Works equally well on functions and methods.

    Usage:
        @deprecated("new_name")
        def old_name():
            pass
    """

    def decorator(func):
        def wrapped(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed in future "
                f"versions. Please use {new_name} instead.",
                FutureWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapped

    return decorator


def deprecated_class(new_name: str):
    """Notify users that a class is deprecated and will be removed in the future.
    Works only on Pydantic models since it relies on the model_post_init method.

    Usage:
        @deprecated_class("new_name")
        class OldName:
            pass
    """

    def class_decorator(cls):
        orig_init = cls.__init__

        def new_init(self, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} is deprecated and will be removed in a future "
                f"release. Please use '{new_name}' instead.",
                category=FutureWarning,
                stacklevel=2,
            )
            orig_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return class_decorator


def renamed_class(new_cls: Any):
    """Notify users that a class is deprecated and has been renamed.

    Usage:
        @renamed_class(NewClass)
        class OldClass:
            pass
    """

    def decorator(cls):
        def return_new_cls(cls, *args, **kwargs):
            warnings.warn(
                f"{cls.__name__} is deprecated and and will be removed in a future "
                f"release. Please use '{new_cls.__name__}' instead.",
                category=FutureWarning,
                stacklevel=2,
            )
            return new_cls(*args, **kwargs)

        cls.__new__ = return_new_cls
        return cls

    return decorator


def to_multi_xyz(structures: Iterable["Structure"]) -> str:
    """Create a multi-structure XYZ string from a list of structures.

    Args:
        structures: An Iterable of Structure objects.

    Returns:
        The multi-structure XYZ string.
    """
    return "".join(struct.to_xyz() for struct in structures)
