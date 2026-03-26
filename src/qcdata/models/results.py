"""End user results and data objects."""

from __future__ import annotations

import sys
import warnings
from itertools import product
from pathlib import Path
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    Union,
    get_args,
)

import numpy as np
from pydantic import BaseModel, ValidationInfo, field_validator, model_validator
from typing_extensions import Self

from qcdata.helper_types import SerializableNDArray

from .base_models import CalcType, Files, Provenance, QCDataBaseModel
from .inputs import (
    FileInput,
    Inputs,
    ProgramInput,
)
from .inputs import (
    InputType as ProgramInputType,
)
from .structure import Structure
from .utils import deprecated_class, to_multi_xyz

__all__ = [
    "SinglePointData",
    "Wavefunction",
    "OptimizationData",
    "Results",
    "StructuredData",
    "StructuredDataType",
    "DataType",
    "Data",
    "ConformerSearchData",
    "SinglePointResults",
    "OptimizationResults",
    "ConformerSearchResults",
    "Results",
    "ProgramOutput",
]


class Wavefunction(QCDataBaseModel):
    """The wavefunction for a single point calculation.

    Attributes:
        scf_eigenvalues_a: The SCF alpha-spin orbital eigenvalues.
        scf_eigenvalues_b: The SCF beta-spin orbital eigenvalues.
        scf_occupations_a: The SCF alpha-spin orbital occupations.
        scf_occupations_b: The SCF beta-spin orbital occupations.
    """

    scf_eigenvalues_a: SerializableNDArray | None = None
    scf_eigenvalues_b: SerializableNDArray | None = None
    scf_occupations_a: SerializableNDArray | None = None
    scf_occupations_b: SerializableNDArray | None = None

    @field_validator(
        "scf_eigenvalues_a",
        "scf_eigenvalues_b",
        "scf_occupations_a",
        "scf_occupations_b",
    )
    @classmethod
    def to_numpy(cls, val, _info) -> np.ndarray | None:
        return np.asarray(val) if val is not None else None


class CalcInfoData(BaseModel):
    """Mixin for calcinfo attributes.

    Attributes:
        calcinfo_natoms: The number of atoms as computed by the program.
        calcinfo_nalpha: The number of alpha electrons as computed by the program.
        calcinfo_nbeta: The number of beta electrons as computed by the program.
        calcinfo_nbasis: The number of basis functions in the calculation.
        calcinfo_nmo: The number of molecular orbitals in the calculation.
    """

    # calcinfo contains general information about the calculation
    calcinfo_natoms: int | None = None
    calcinfo_nalpha: int | None = None
    calcinfo_nbeta: int | None = None
    calcinfo_nbasis: int | None = None
    calcinfo_nmo: int | None = None


class SinglePointData(Files, CalcInfoData):
    """The computed data from a single point calculation.

    Attributes:
        energy: The electronic energy of the structure in `Hartrees`.
        gradient: The gradient of the structure in `Hartrees/Bohr`.
        hessian: The hessian of the structure in `Hartrees/Bohr^2`.
        nuclear_repulsion_energy: The nuclear repulsion energy of the structure in
            Hartrees.

        wavefunction: Wavefunction data from the calculation.

        freqs_wavenumber: The frequencies of the structure in wavenumbers.
        normal_modes_cartesian: 3D n_vibmodes x n_atoms x 3 array containing
            un-mass-weighted Cartesian displacements of each normal mode in Bohr.
        gibbs_free_energy: Gibbs free energy (i.e. thermochemical analysis) in Hartrees
            of a system where translation / rotation / vibration degrees of freedom are
            approximated using ideal gas / rigid rotor / harmonic oscillator
            respectively.
        scf_dipole_moment: The x, y, z component of the dipole moment of the structure
            in units of e a0 (NOT Debye!).

    """

    # Core properties
    energy: float | None = None
    gradient: SerializableNDArray | None = None  # Coerced to 2D array
    hessian: SerializableNDArray | None = None  # Coerced to 2D array
    nuclear_repulsion_energy: float | None = None

    # Wavefunction data
    wavefunction: Wavefunction | None = None

    # Frequency data
    freqs_wavenumber: list[float] = []
    normal_modes_cartesian: SerializableNDArray | None = None  # Coerced to 3D array
    gibbs_free_energy: float | None = None

    # SCF results
    scf_dipole_moment: list[float] | None = None

    @field_validator("normal_modes_cartesian")
    @classmethod
    def _validate_normal_modes_cartesian_shape(
        cls, v: SerializableNDArray, info: ValidationInfo
    ):
        if v is not None:
            # Array must have length of the number of normal modes
            freqs = info.data.get("freqs_wavenumber")
            # Fallback to len(v) if we must
            n_normal_modes = len(freqs) if freqs else len(v)
            return np.asarray(v).reshape(n_normal_modes, -1, 3)
        return v

    @field_validator("gradient")
    @classmethod
    def _validate_gradient_shape(cls, v: SerializableNDArray):
        """Validate gradient is n x 3"""
        if v is not None:
            return np.asarray(v).reshape(-1, 3)

    @field_validator("hessian")
    @classmethod
    def _validate_hessian_shape(cls, v: SerializableNDArray):
        """Validate hessian is square"""
        if v is not None:
            v = np.asarray(v)
            n = int(np.sqrt(v.size))
            return v.reshape((n, n))

    def return_result(self, calctype: CalcType) -> float | SerializableNDArray:
        """Return the primary result of the calculation."""
        return getattr(self, calctype.value)

    @model_validator(mode="after")
    def _ensure_results(self) -> Self:
        """Ensure that at least one result is present."""
        if all(
            result is None
            for result in [
                self.energy,
                self.gradient,
                self.hessian,
            ]
        ):
            raise ValueError(
                "SinglePointResults requires either an energy, gradient, or hessian "
                "value."
            )
        return self


class OptimizationData(Files, CalcInfoData):
    """Computed data for an optimization (may be for a minimum or transition state).

    Attributes:
        energies: The energies for each step of the optimization.
        structures: The Structure objects for each step of the optimization.
        final_structure: The final, optimized Structure.
        trajectory: The Results objects for each step of the optimization.
    """

    trajectory: list[
        (Results[ProgramInput, SinglePointData] | Results[ProgramInput, Files])
    ] = []

    @property
    def final_structure(self) -> Structure:
        """The final Structure in the optimization."""
        return self.structures[-1]

    @property
    def final_molecule(self) -> Structure:
        warnings.warn(
            ".final_molecule is being deprecated and will be removed in a future. "
            "Please use .final_structure instead.",
            category=FutureWarning,
            stacklevel=2,
        )
        return self.final_structure

    @property
    def final_energy(self) -> float | None:  # Optional for np.nan
        """
        The final energy in the optimization. Is `np.nan` if final calculation failed.
        """
        return self.energies[-1]

    @property
    def energies(self) -> np.ndarray:
        """The energies for each step of the optimization."""
        return np.array(
            [
                # ensure_structured_results_on_success validator ensures .results
                # is not Files if success is True so # type: ignore
                output.data.energy if output.success else np.nan  # type: ignore
                for output in self.trajectory
            ],
            dtype=float,
        )

    @property
    def structures(self) -> list[Structure]:
        """The Structure objects for each step of the optimization."""
        return [output.input_data.structure for output in self.trajectory]

    def return_result(self, calctype: CalcType) -> Structure | None:
        """Return the primary result of the calculation."""
        return self.final_structure

    def __repr_args__(self):
        """Custom repr to avoid printing the entire collection of objects."""
        return [
            ("final_structure", f"{self.final_structure}"),
            ("trajectory", "[...]"),
            ("energies", "[...]"),
            ("structures", "[...]"),
        ]

    def to_xyz(self) -> str:
        """Return the trajectory as an `xyz` string."""
        return to_multi_xyz(
            prog_output.input_data.structure for prog_output in self.trajectory
        )

    def save(
        self,
        filepath: Path | str,
        exclude_none: bool = True,
        exclude_unset: bool = True,
        indent: int = 4,
        **kwargs: dict[str, Any],
    ) -> None:
        """Save an OptimizationOutput to a file.

        Args:
            filepath: The path to save the molecule to.
            exclude_none: If True, attributes with a value of None will not be written
                to the file.
            exclude_unset: If True, attributes that have not been set will not be
                written to the file.
            **kwargs: Additional keyword arguments to pass to the json serializer.

        Note:
            If the filepath has a `.xyz` extension, the trajectory will be saved to a
            multi-structure `xyz` file.
        """
        filepath = Path(filepath)
        if filepath.suffix == ".xyz":
            filepath.write_text(self.to_xyz())
            return
        super().save(filepath, exclude_none, exclude_unset, indent, **kwargs)


class ConformerSearchData(Files):
    """Data from a conformer search calculation.

    Conformers and rotamers are sorted by energy.

    Attributes:
        conformers: The conformers found in the search.
        conformer_energies: The energies for each conformer.
        rotamers: The rotamers found in the search.
        rotamer_energies: The energies for each rotamer.
    """

    conformers: list[Structure] = []
    conformer_energies: SerializableNDArray = np.array([])
    rotamers: list[Structure] = []
    rotamer_energies: SerializableNDArray = np.array([])

    @model_validator(mode="after")
    def _energies_size(self) -> ConformerSearchData:
        """Ensure the energies are the same size as the conformers and rotamers."""
        if self.conformer_energies.size > 0 and (
            self.conformer_energies.size != len(self.conformers)
        ):
            raise ValueError(
                "The number of conformer energies must match the number of conformers."
            )
        if self.rotamer_energies.size > 0 and (
            self.rotamer_energies.size != len(self.rotamers)
        ):
            raise ValueError(
                "The number of rotamer energies must match the number of rotamers."
            )
        return self

    @model_validator(mode="after")
    def _sort_by_energy(self) -> ConformerSearchData:
        """Sort conformers and rotamers by energy."""

        # Sort conformers and their energies together
        if self.conformer_energies.size > 0:
            sorted_indices = np.argsort(self.conformer_energies)
            self.conformers[:] = [self.conformers[i] for i in sorted_indices]
            self.conformer_energies[:] = self.conformer_energies[sorted_indices]

        # Sort rotamers and their energies together
        if self.rotamer_energies.size > 0:
            sorted_indices = np.argsort(self.rotamer_energies)
            self.rotamers[:] = [self.rotamers[i] for i in sorted_indices]
            self.rotamer_energies[:] = self.rotamer_energies[sorted_indices]

        return self

    @property
    def conformer_energies_relative(self) -> np.ndarray:
        """The relative energies for each conformer in the search."""
        if self.conformer_energies.size == 0:
            return np.array([])
        return self.conformer_energies - self.conformer_energies.min()

    @property
    def rotamer_energies_relative(self) -> np.ndarray:
        """The relative energies for each rotamer in the search."""
        if self.rotamer_energies.size == 0:
            return np.array([])
        return self.rotamer_energies - self.rotamer_energies.min()

    def conformers_filtered(
        self,
        threshold: float = 1.0,
        **rmsd_kwargs,
    ) -> tuple[list[Structure], SerializableNDArray]:
        """
        !!! warning "Moved since *qcdata* 0.15.0"
            This convenience method has moved to
            [`qcinf.filter_conformers`][qcinf.filter_conformers]
            and this stub will be **removed** from *qcdata* in a future release.

            ```python
            from qcinf import filter_conformers

            filtered_csr = filter_conformers(
                conformers=csr
                threshold=1.0,          # Bohr
                backend="qcinf",      # or "rdkit",
                **rmsd_kwargs,
            )
            ```
        """

        warnings.warn(
            "`ConformerSearchResults.conformers_filtered()` is deprecated. "
            "Install *qcinf* and use `qcinf.filter_conformers` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        raise NotImplementedError(
            "Method removed.  Replace with:\n\n"
            "    from qcinf import filter_conformers\n\n"
            "    filtered_csr = filter_conformers(\n"
            "        prog_output.results,\n"
            "        threshold=1.0,\n"
            "        backend='qcinf',\n"
            "        **rmsd_kwargs\n"
            "    )"
        )


StructuredData = Union[SinglePointData, OptimizationData, ConformerSearchData]
StructuredDataType = TypeVar("StructuredDataType", bound=StructuredData)
Data = Union[Files, StructuredData]
DataType = TypeVar("DataType", bound=Data)


class Results(QCDataBaseModel, Generic[ProgramInputType, DataType]):
    """The core results object from a quantum chemistry calculation.

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

        # Backwards compatibility for .stdout attribute:
        if "stdout" in payload:
            warnings.warn(
                "The 'stdout' attribute has been renamed to 'logs'. Please update your "
                "code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            if "logs" not in payload:
                payload["logs"] = payload.pop("stdout")

        # Backwards compatibility for .results attribute:
        if "results" in payload:
            warnings.warn(
                "The 'results' attribute has been renamed to 'data'. Please update "
                "your code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            if isinstance(payload["results"], dict):
                payload["data"] = payload.pop("results")

        # Backwards compatibility for .files attribute:
        if "files" in payload:
            warnings.warn(
                "The 'files' attribute has been moved to 'data.files'. Please "
                "update your code accordingly.",
                category=FutureWarning,
                stacklevel=2,
            )
            # This moves files from the top level to the data attribute
            if isinstance(payload["data"], dict):
                data_files_dict = payload["data"].get("files", {})
            else:  # data["data"] is Files, SinglePointData, OptimizationData
                data_files_dict = payload["data"].files

            data_files_dict.update(**payload.pop("files"))

        return payload

    def model_post_init(self, __context) -> None:
        """Parameterize the class (if not set explicitly)."""
        # Check if the current class is still generic, do not override if explicitly set
        if self.__class__ is Results:
            input_type = type(self.input_data)
            results_type = type(self.data)
            self.__class__ = Results[input_type, results_type]  # type: ignore # noqa 501

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
        # Covers case of ProgramInput and DualProgramInput
        if self.success is True and isinstance(self.input_data, ProgramInput):
            assert type(self.data) is not Files, (
                "Structured results must be provided for successful, non FileInput "
                "calculations."
            )

        return self

    @model_validator(mode="after")
    def ensure_primary_result_on_success(self) -> Self:
        if type(self.data) is SinglePointData:
            # Ensure the primary calctype result is present
            calctype_val = self.input_data.calctype.value  # type: ignore
            assert getattr(self.data, calctype_val) is not None, (
                f"Missing the primary result: {calctype_val}."
            )

        return self

    @property
    def plogs(self) -> None:
        """Print the logs"""
        print(self.logs)

    @property
    def pstdout(self) -> None:
        """Print the logs"""
        warnings.warn(
            ".pstdout has been renamed to .plogs. Please update your code accordingly.",
            category=FutureWarning,
            stacklevel=2,
        )
        print(self.logs)

    @property
    def ptraceback(self) -> None:
        """Print the traceback"""
        print(self.traceback)

    def __repr_args__(self) -> list[tuple[str, Any]]:
        """Exclude stdout and traceback from the repr and ensure success is first"""
        args = super().__repr_args__()

        # Replace stdout and traceback with "<...>"
        filtered_args = [
            (key, value if key not in {"stdout", "traceback"} else "<...>")
            for key, value in args
        ]
        # Ensure success is first
        success_arg = [(key, value) for key, value in filtered_args if key == "success"]
        other_args = [(key, value) for key, value in filtered_args if key != "success"]
        return success_arg + other_args

    @property
    def files(self) -> dict[str, str | bytes]:
        """Return the files attribute."""
        # Depreciation warning
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
        # For mypy
        assert self.data is not None, "No data exist on this Results object."
        assert type(self.input_data) is not FileInput, "FileInputs have no data."
        return self.data.return_result(self.input_data.calctype)  # type: ignore


### Backwards compatibility classes ###
@deprecated_class("Results")
class ProgramOutput(Results):
    """This class is deprecated and will be removed in a future release. Please use
    `Results` instead."""

    pass


@deprecated_class("SinglePointData")
class SinglePointResults(SinglePointData):
    """This class is deprecated and will be removed in a future release. Please use
    `SinglePointData` instead."""

    pass


@deprecated_class("OptimizationData")
class OptimizationResults(OptimizationData):
    """This class is deprecated and will be removed in a future release. Please use
    `OptimizationData` instead."""

    pass


@deprecated_class("ConformerSearchData")
class ConformerSearchResults(ConformerSearchData):
    """This class is deprecated and will be removed in a future release. Please use
    `ConformerSearchData` instead."""

    pass


### End backwards compatibility classes ###


# Register the concrete classes for serialization
def _register_program_output_classes():
    """Required so that pickle can find the concrete classes for serialization."""
    for spec_type, data_type in product(get_args(Inputs), get_args(Data)):
        # TODO: Remove ProgramOutput when compatibility is no longer needed
        for ClassType in [Results, ProgramOutput]:
            _class = ClassType[spec_type, data_type]
            name = _class.__name__
            this_module = sys.modules[__name__]
            if name not in this_module.__dict__:
                # Directly declare the type to ensure it is registered
                setattr(this_module, name, _class)


# Call this function during module initialization
_register_program_output_classes()
