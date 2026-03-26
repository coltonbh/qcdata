# Structure & Identifiers

A `Structure` is the core `qcdata` object for representing a molecule or molecular super structure in 3D space. `Structure` objects can be created directly from `symbol` and `geometry` information (geometry must be in `Bohr`), from SMILES strings, from `xyz` files, or opened from `Structure` objects previously saved to disk.

::: qcdata.Structure
    options:
        members:
            - from_smiles
            - from_xyz
            - to_smiles
            - to_xyz
            - distance
            - add_smiles
            - add_identifier

::: qcdata.Identifiers