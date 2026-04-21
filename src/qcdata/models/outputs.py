"""Program output container objects."""

from __future__ import annotations

import sys
import warnings
from itertools import product
from typing import Any, Generic, Literal, get_args

from pydantic import model_validator
from typing_extensions import Self

from qcdata.helper_types import SerializableNDArray

from .base_models import Files, Provenance, QCDataBaseModel
from .data import (
    ConformerSearchData,
    Data,
    DataType,
    OptimizationData,
    ScanData,
    SinglePointData,
)
from .inputs import FileInput, Inputs, ProgramInput
from .inputs import InputType as ProgramInputType
from .structure import Structure
from .utils import deprecated_class

__all__ = ["ProgramOutput", "Results"]


class ProgramOutput(QCDataBaseModel, Generic[ProgramInputType, DataType]):
    """The core output object from a quantum chemistry calculation.

    Attributes:
        input_data: The input data for the calculation. Any of `qcdata.Inputs`.
        success: Whether the calculation was successful.
        data: The data from the calculation. Contains parsed values and files.
            Any of `qcdata.Data`.
        logs: The logs from the calculation.
        traceback: The traceback from the calculation, if it failed.
        provenance: The provenance information for the calculation.
        extras Dict[str, Any]: Additional information to bundle with the results. Use for
            schema development and scratch space.
        plogs str: `@property` Print the logs.
        ptraceback str: `@property` Print the traceback.
    """

    input_data: ProgramInputType
    success: Literal[True, False]
    data: DataType
    logs: str | None = None
    traceback: str | None = None
    provenance: Provenance

    @model_validator(mode="before")
    def _backwards_compatibility(cls, payload: dict[str, Any]) -> dict[str, Any]:
        """Backwards compatibility for renamed attributes."""
        if "stdout" in payload:
            warnings.warn(
                "The 'stdout' attribute has been renamed to 'logs'. Please update your "
                "code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            if "logs" not in payload:
                payload["logs"] = payload.pop("stdout")

        if "results" in payload:
            warnings.warn(
                "The 'results' attribute has been renamed to 'data'. Please update "
                "your code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            if isinstance(payload["results"], dict):
                payload["data"] = payload.pop("results")

        if "files" in payload:
            warnings.warn(
                "The 'files' attribute has been moved to 'data.files'. Please "
                "update your code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            if isinstance(payload["data"], dict):
                data_files_dict = payload["data"].get("files", {})
            else:
                data_files_dict = payload["data"].files

            data_files_dict.update(**payload.pop("files"))

        return payload

    def model_post_init(self, __context) -> None:
        """Parameterize the class (if not set explicitly)."""
        if self.__class__ in {ProgramOutput, Results}:
            input_type = type(self.input_data)
            results_type = type(self.data)
            self.__class__ = self.__class__[input_type, results_type]  # type: ignore[index]

    @property
    def results(self) -> DataType:
        """Return the data attribute."""
        warnings.warn(
            ".results has been renamed to .data. Please update your code accordingly.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.data

    @property
    def stdout(self) -> str | None:
        """Backwards compatibility for .stdout attribute."""
        warnings.warn(
            ".stdout has been renamed to .logs. Please update your code accordingly.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.logs

    @model_validator(mode="after")
    def ensure_traceback_on_failure(self) -> Self:
        if self.success is False:
            assert self.traceback is not None, (
                "A traceback must be provided for failed calculations."
            )
        return self

    @model_validator(mode="after")
    def _ensure_structured_results_on_success(self) -> Self:
        """Ensure structured results are provided for successful, non FileInputs."""
        if self.success is True and isinstance(self.input_data, ProgramInput):
            assert type(self.data) is not Files, (
                "Structured results must be provided for successful, non FileInput "
                "calculations."
            )
        return self

    @model_validator(mode="after")
    def ensure_primary_result_on_success(self) -> Self:
        if type(self.data) is SinglePointData:
            calctype_val = self.input_data.calctype.value  # type: ignore
            assert getattr(self.data, calctype_val) is not None, (
                f"Missing the primary result: {calctype_val}."
            )
        return self

    @property
    def plogs(self) -> None:
        """Print the logs."""
        print(self.logs)

    @property
    def pstdout(self) -> None:
        """Print the logs."""
        warnings.warn(
            ".pstdout has been renamed to .plogs. Please update your code accordingly.",
            category=FutureWarning,
            stacklevel=2,
        )
        print(self.logs)

    @property
    def ptraceback(self) -> None:
        """Print the traceback."""
        print(self.traceback)

    def __repr_args__(self) -> list[tuple[str, Any]]:
        """Exclude stdout and traceback from the repr and ensure success is first."""
        args = super().__repr_args__()
        filtered_args = [
            (key, value if key not in {"stdout", "traceback"} else "<...>")
            for key, value in args
        ]
        success_arg = [(key, value) for key, value in filtered_args if key == "success"]
        other_args = [(key, value) for key, value in filtered_args if key != "success"]
        return success_arg + other_args

    @property
    def files(self) -> dict[str, str | bytes]:
        """Return the files attribute."""
        warnings.warn(
            ".files has been moved to .data.files. "
            "Please access it there going forward.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.data.files

    @property
    def return_result(self) -> float | SerializableNDArray | Structure | None:
        """Return the primary result of the calculation."""
        warnings.warn(
            ".return_result is being deprecated and will be removed in a future. "
            "Please access data directly at .data instead.",
            category=FutureWarning,
            stacklevel=2,
        )
        assert self.data is not None, "No data exist on this ProgramOutput object."
        assert type(self.input_data) is not FileInput, "FileInputs have no data."
        return self.data.return_result(self.input_data.calctype)  # type: ignore


@deprecated_class("ProgramOutput")
class Results(ProgramOutput[ProgramInputType, DataType]):
    """This class is deprecated and will be removed in a future release. Please use
    `ProgramOutput` instead."""


ProgramOutput.model_rebuild()
Results.model_rebuild()
OptimizationData.model_rebuild()
ConformerSearchData.model_rebuild()
ScanData.model_rebuild()

def _register_program_output_classes():
    """Required so that pickle can find the concrete classes for serialization."""
    for spec_type, data_type in product(get_args(Inputs), get_args(Data)):
        for class_type in [ProgramOutput, Results]:
            _class = class_type[spec_type, data_type]
            name = _class.__name__
            this_module = sys.modules[__name__]
            if name not in this_module.__dict__:
                setattr(this_module, name, _class)


_register_program_output_classes()
