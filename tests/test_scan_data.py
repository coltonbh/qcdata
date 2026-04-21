from qcdata import ScanData

ScanData.model_rebuild()


def test_scan_data_properties(opt_output):
    """Test that the number of energies matches the number of conformers"""
    # No energies is fine
    scan_res = ScanData(
        trajectory=[opt_output],
    )

    # Test properties
    assert scan_res.energies == [opt_output.data.final_energy]
    assert scan_res.structures == [opt_output.data.final_structure]
    # Test custom __repr_args__
    repr_args = scan_res.__repr_args__()
    assert isinstance(repr_args, list)
    for arg in repr_args:
        assert isinstance(arg, tuple)
        assert len(arg) == 2
        assert isinstance(arg[0], str)
        assert isinstance(arg[1], str)


def test_scan_save_to_xyz(opt_output, tmp_path):
    scan_res = ScanData(
        trajectory=[opt_output] * 3,
    )
    scan_res.save(tmp_path / "scan_res.xyz")

    text = (tmp_path / "scan_res.xyz").read_text()

    # Text must be de-dented exactly as below
    correct_text = """3
qcdata_charge=0 qcdata_multiplicity=1 qcdata__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
3
qcdata_charge=0 qcdata_multiplicity=1 qcdata__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
3
qcdata_charge=0 qcdata_multiplicity=1 qcdata__identifiers_name=water
O  0.01340919176202180 0.01026321207824930 -0.00368477733600419
H  0.12112430307330672 0.97600619725464122 0.08599884278042236
H  0.75016279902412597 -0.33132205318865016 -0.54481406902570462
"""
    assert text == correct_text


def test_scan_save_non_xyz(opt_output, tmp_path):
    scan_res = ScanData(
        trajectory=[opt_output] * 3,
    )
    scan_res.save(tmp_path / "scan_res.json")
    scan_res_copy = ScanData.open(tmp_path / "scan_res.json")
    assert scan_res == scan_res_copy
