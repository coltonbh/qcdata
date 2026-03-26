from qcdata import Results


def test_serialization_to_disk_json(results, tmp_path):
    """Test serialization to disk json"""

    filename = tmp_path / "prog_output.json"
    results.save(filename)
    reopened = Results.open(filename)
    assert results == reopened

    # No filename or other extension to json by default
    filename = tmp_path / "prog_output.whatever"
    results.save(filename)
    reopened = Results.open(filename)
    assert results == reopened


def test_serialization_to_disk_yaml(results, tmp_path):
    """Test serialization to disk yaml"""
    for ext in [".yaml", ".yml"]:
        filename = tmp_path / f"prog_output{ext}"
        results.save(filename)
        reopened = Results.open(filename)
        assert results == reopened


def test_serialization_to_disk_toml(results, tmp_path):
    """Test serialization to disk toml"""

    filename = tmp_path / "prog_output.toml"
    results.save(filename)
    reopened = Results.open(filename)
    assert results == reopened
