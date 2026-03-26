Data structures for specifying quantum chemistry calculations. The most commonly used structure is a `ProgramInput` which defines a single calculation.

A `DualProgramInput` is used when two inputs are required for a calculation. For example, doing a geometry optimization with `geomeTRIC` while using a `subprogram` like `TeraChem` or `Psi4` to compute the gradients.

A `FileInput` is an escape hatch that allows you to run _any_ calculation in any QC program (or any program for that matter), even if it isn't a supported [`CalcType`](./calctype.md) in `qcdata` yet. You can use a `FileInput` to store the native input files (text and binary) for a QC program along with the relevant command line args. Using [qcop](https://github.com/coltonbh/qcop) you can submit a `FileInput` a QC program and all output files and `logs` produced by that program will be collected and returned in a user-friendly `Results` object. `FileInput` allows you to continue to use `qcdata` even for calculations that haven't yet been standardized.

  
::: qcdata.Inputs

::: qcdata.ProgramInput
    options:
        inherited_members: true
        members: 
            - add_file 
            - add_files 
            - save_files

::: qcdata.DualProgramInput
    options:
        inherited_members: true
        members: 
            - add_file 
            - add_files 
            - save_files 

::: qcdata.FileInput
    options:
        inherited_members: true
        members: 
        - add_file 
        - add_files 
        - save_files 
        - from_directory

::: qcdata.ProgramArgs
    options:
        inherited_members: true
        members: 
        - add_file 
        - add_files 
        - save_files
