import json

from qcdata import FileInput


def test_from_directory(test_data_dir):
    file_inp = FileInput.from_directory(
        directory=test_data_dir / "file_inputs",
        # program="terachem",
        extras={"my_extra": "123"},
    )

    # assert generic_inp.args.program == "terachem"
    assert file_inp.extras == {"my_extra": "123"}
    for filename, file in file_inp.files.items():
        data = (test_data_dir / "file_inputs" / filename).read_bytes()
        try:
            str_data = data.decode("utf-8")
        except UnicodeDecodeError:
            assert file == data
        else:
            assert file == str_data


def test_to_directory(test_data_dir, tmp_path):
    file_inp = FileInput.from_directory(
        directory=test_data_dir / "file_inputs",
        # program="terachem",
        extras={"my_extra": "123"},
    )
    file_inp.save_files(tmp_path)
    for filename in file_inp.files:
        # Ensure files were written
        assert (tmp_path / filename).exists()
        # Ensure files are identical to input files
        assert (tmp_path / filename).read_bytes() == (
            test_data_dir / "file_inputs" / filename
        ).read_bytes()


def test_to_from_file_with_binary_data(test_data_dir, tmp_path):
    file_inp = FileInput.from_directory(
        directory=test_data_dir / "file_inputs",
        # program="terachem",
        extras={"my_extra": "123"},
    )
    # Ensure that we have binary data
    assert isinstance(file_inp.files["c0"], bytes)
    # Write GenericInput to disk using .json() serialization
    file_inp.save(tmp_path / "file_input.json")
    # Ensure data was properly json serialized
    data = json.loads((tmp_path / "file_input.json").read_text())
    assert data["files"]["c0"].startswith("base64:")
    # Parse GenericInput from disk using deserialization
    file_inp_reloaded = FileInput.open(tmp_path / "file_input.json")
    # Assure all data returned to correct bytes or str representation
    assert file_inp_reloaded == file_inp
