from qcdata import ProgramInput, Structure


def test_molecule_backwards_compatibility():
    structure = Structure(symbols=["Na", "Cl"], geometry=[[0, 0, 0], [1, 1, 1]])
    # Passing molecule=structure still works
    prog_input = ProgramInput(
        calctype="energy", molecule=structure, model={"method": "hf"}
    )
    assert prog_input.molecule == structure
