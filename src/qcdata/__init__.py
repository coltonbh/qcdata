import importlib
import warnings
from importlib import metadata
from types import ModuleType
from typing import Any

from .models import *  # noqa: F403
from .models.utils import to_multi_xyz
from .utils import json_dumps

__version__ = metadata.version(__name__)


__all__ = [  # noqa: F405
    # Core Models
    "CalcType",
    "Model",
    "Provenance",
    "Structure",
    "Molecule",
    "Files",
    "FileInput",
    "ProgramInput",
    "ProgramOutput",
    "Results",
    "DualProgramInput",
    "SinglePointData",
    "OptimizationData",
    "ConformerSearchData",
    "SinglePointResults",
    "OptimizationResults",
    "ConformerSearchResults",
    "Wavefunction",
    "ProgramArgs",
    "ProgramArgsSub",
    "json_dumps",
    "to_multi_xyz",
    "LengthUnit",
]

# Map of deprecated symbols → new fully-qualified path
_DEPRECATED: dict[str, str] = {
    "rmsd": "qcinf.rmsd",
    "align": "qcinf.align",
}


def __getattr__(name: str) -> Any:  # PEP 562
    """Redirect old qcdata symbols to qcinf (with helpful message)."""
    if name not in _DEPRECATED:
        raise AttributeError(f"module 'qcdata' has no attribute '{name}'")

    new_path = _DEPRECATED[name]
    mod_path, func_name = new_path.rsplit(".", 1)

    try:
        module: ModuleType = importlib.import_module(mod_path)
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            f"`qcinf` is not installed, so `qcdata.{name}` can no longer be "
            "used. Install the dependency with either:\n\n"
            "    python -m pip install qcinf\n"
            "or\n"
            "    python -m pip install 'qcinf[all]'\n\n"
            "and then import the new function location:\n\n"
            f"    from {mod_path} import {func_name}",
        ) from exc

    else:
        # Emit a FutureWarning so it's shown by default
        warnings.warn(
            f"`qcdata.{name}` has moved to `{new_path}`.\n"
            "Please update your import to:\n\n"
            f"    from qcinf import {name}",
            FutureWarning,
            stacklevel=2,
        )
    return getattr(module, func_name)
