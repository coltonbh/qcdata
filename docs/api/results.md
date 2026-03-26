# Results

`Results` is the core object that captures all information from a QC calculation including all input data, the computed values and files (collectively called [`Data`](#data)), and additional metadata such as `logs` and [`Provenance`](./provenance.md) information. The `.data` attribute will correspond to the [`CalcType`](./calctype.md) requested, e.g., a [`SinglePointData`](#qcdata.SinglePointData), [`OptimizationsData`](#qcdata.OptimizationData), etc.

::: qcdata.Results
options:
members: false

## Data

::: qcdata.Data

::: qcdata.SinglePointData
options:
members: false

::: qcdata.OptimizationData
options:
members: - structures - final_structure - energies - final_energy - to_xyz - save

::: qcdata.ConformerSearchData

::: qcdata.Wavefunction
