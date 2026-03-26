"""Utility functions for working with qcdata objects."""

from __future__ import annotations

import json

import numpy as np
from pydantic import BaseModel

from .models import Structure

# Helper Structures
water = Structure(
    symbols=["O", "H", "H"],
    geometry=np.array(
        [
            [0.0253397, 0.01939466, -0.00696322],
            [0.22889176, 1.84438441, 0.16251426],
            [1.41760224, -0.62610794, -1.02954938],
        ]
    ),
    charge=0,
    multiplicity=1,
    connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
    identifiers={"name": "water"},
)


def json_dumps(
    obj: BaseModel | list[BaseModel],
    exclude_unset: bool = True,
    **model_dump_kwargs,
) -> str:
    """Serialization helper for lists of pydantic objects.

    Args:
        obj: The object to serialize. Either a single pydantic object or a list of pydantic
            objects.
        exclude_unset: Whether to exclude unset fields from the serialized output.
        **model_dump_kwargs: Additional keyword arguments to pass to model_dump.
    """
    if isinstance(obj, list):
        return json.dumps(
            [
                o.model_dump(exclude_unset=exclude_unset, **model_dump_kwargs)
                for o in obj
            ]
        )
    return obj.model_dump_json(exclude_unset=exclude_unset, **model_dump_kwargs)
