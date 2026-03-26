"""Deprecated compatibility shim for packages that still import `qcio`."""

from warnings import warn

from qcdata import *  # noqa: F403
from qcdata import __version__ as __version__

warn(
    "`qcio` has been renamed to `qcdata`. Update imports to use `qcdata`.",
    DeprecationWarning,
    stacklevel=2,
)
