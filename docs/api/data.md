# Data

`Data` objects contains the structured calculation data. When contained in a [`ProgramOutput`](./outputs.md), the concrete type depends on the requested [`CalcType`](./calctype.md).

::: qcdata.Data

::: qcdata.SinglePointData
options:
members: false

::: qcdata.OptimizationData
options:
members:
  - structures
  - final_structure
  - energies
  - final_energy
  - to_xyz
  - save

::: qcdata.ConformerSearchData

::: qcdata.Wavefunction
