from qcdata import ProgramOutput


def test_serialization_to_disk_json(prog_output, tmp_path):
    """Test serialization to disk json"""

    filename = tmp_path / "prog_output.json"
    prog_output.save(filename)
    reopened = ProgramOutput.open(filename)
    assert prog_output == reopened

    # No filename or other extension to json by default
    filename = tmp_path / "prog_output.whatever"
    prog_output.save(filename)
    reopened = ProgramOutput.open(filename)
    assert prog_output == reopened


def test_serialization_to_disk_yaml(prog_output, tmp_path):
    """Test serialization to disk yaml"""
    for ext in [".yaml", ".yml"]:
        filename = tmp_path / f"prog_output{ext}"
        prog_output.save(filename)
        reopened = ProgramOutput.open(filename)
        assert prog_output == reopened


def test_serialization_to_disk_toml(prog_output, tmp_path):
    """Test serialization to disk toml"""

    filename = tmp_path / "prog_output.toml"
    prog_output.save(filename)
    reopened = ProgramOutput.open(filename)
    assert prog_output == reopened
