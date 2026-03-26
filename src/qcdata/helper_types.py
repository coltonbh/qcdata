from pathlib import Path
from typing import Annotated

import numpy as np
from pydantic import BeforeValidator, GetPydanticSchema, PlainSerializer, SkipValidation
from pydantic_core import core_schema

StrOrPath = Annotated[str | Path, PlainSerializer(lambda x: str(x))]

# Create the annotated type for numpy array
SerializableNDArray = Annotated[
    SkipValidation[np.ndarray],
    # Coerce values to float64 numpy array. Not required. Creates consistency.
    BeforeValidator(lambda x: np.array(x, dtype=np.float64)),
    # Serializes the numpy array to a list
    PlainSerializer(lambda x: np.array(x).tolist()),
    # Describe json schema as a list of floats (numbers). Required for ChemCloud docs.
    GetPydanticSchema(
        lambda tp, handler: core_schema.with_default_schema(handler(list[float]))
    ),
]
