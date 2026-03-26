import pickle

import numpy as np
import pytest
from pydantic import ValidationError

from qcdata import (
    FileInput,
    Files,
    OptimizationData,
    ProgramInput,
    ProgramOutput,
    Provenance,
    SinglePointData,
    Structure,
)


def test_return_result(prog_input_factory):
    """Test that return_result returns the requested result"""
    calc_input_energy = prog_input_factory("energy")
    energy = 1.0
    n_atoms = len(calc_input_energy.structure.symbols)
    gradient = np.arange(n_atoms * 3).reshape(n_atoms, 3)
    hessian = np.arange(n_atoms**2 * 3**2).reshape(n_atoms * 3, n_atoms * 3)

    results = ProgramOutput(
        input_data=calc_input_energy,
        success=True,
        data={
            "energy": energy,
            "gradient": gradient,
            "hessian": hessian,
        },
        provenance={"program": "qcdata-test-suite"},
    )
    assert results.return_result == energy
    assert results.return_result == results.data.energy

    pi_gradient = prog_input_factory("gradient")
    results = ProgramOutput(**{**results.model_dump(), **{"input_data": pi_gradient}})
    assert np.array_equal(results.return_result, gradient)
    assert np.array_equal(results.return_result, results.data.gradient)

    pi_hessian = prog_input_factory("hessian")
    results = ProgramOutput(**{**results.model_dump(), **{"input_data": pi_hessian}})

    assert np.array_equal(results.return_result, hessian)
    assert np.array_equal(results.return_result, results.data.hessian)


def test_successful_prog_output_serialization(prog_output):
    """Test that successful program output serializes and deserializes"""
    serialized = prog_output.model_dump_json()
    deserialized = ProgramOutput.model_validate_json(serialized)
    assert deserialized == prog_output
    assert deserialized.data == prog_output.data
    assert deserialized.input_data == prog_output.input_data
    assert deserialized.provenance.program == "qcdata-test-suite"
    assert deserialized.logs == prog_output.logs
    assert deserialized.extras == prog_output.extras
    assert deserialized.return_result == prog_output.return_result
    assert deserialized.data.energy == prog_output.data.energy
    assert np.array_equal(deserialized.data.gradient, prog_output.data.gradient)
    assert np.array_equal(deserialized.data.hessian, prog_output.data.hessian)


def test_correct_generic_instantiates_and_equality_checks_pass(prog_output, tmp_path):
    """
    This test checks the ProgramOutput.model_post_init method to ensure that the
    correct generic types are instantiated and that equality checks pass.
    """
    results_dict = prog_output.model_dump()
    wo_types = ProgramOutput(**results_dict)
    w_types = ProgramOutput[ProgramInput, SinglePointData](**results_dict)

    results_dict["input_data"]["calctype"] = "optimization"
    results_dict["data"] = OptimizationData(trajectory=[wo_types])
    wo_types_opt = ProgramOutput(**results_dict)
    w_types_opt = ProgramOutput[ProgramInput, OptimizationData](**results_dict)

    wo_types.save(tmp_path / "out.json")
    w_types_opt.save(tmp_path / "opt.json")

    wo_types_opened = ProgramOutput.open(tmp_path / "out.json")
    w_types_opened = ProgramOutput[ProgramInput, SinglePointData].open(
        tmp_path / "out.json"
    )

    wo_types_opened_opt = ProgramOutput.open(tmp_path / "opt.json")
    w_types_opened_opt = ProgramOutput[ProgramInput, OptimizationData].open(
        tmp_path / "opt.json"
    )

    assert wo_types == w_types == wo_types_opened == w_types_opened
    assert wo_types_opt == w_types_opt == wo_types_opened_opt == w_types_opened_opt


def test_non_file_success_always_has_result(prog_input_factory):
    pi_energy = prog_input_factory("energy")
    with pytest.raises(ValidationError):
        ProgramOutput[ProgramInput, SinglePointData](
            success=True,
            input_data=pi_energy,
            logs="program standard out...",
            data=None,
            provenance={"program": "qcdata-test-suite"},
        )


def test_primary_result_must_be_present_on_success(prog_output):
    for calctype in ["energy", "gradient", "hessian"]:
        po_dict = prog_output.model_dump()
        po_dict["input_data"]["calctype"] = calctype
        po_dict["data"][calctype] = None
        with pytest.raises(ValidationError):
            ProgramOutput[ProgramInput, SinglePointData](**po_dict)


@pytest.mark.parametrize(
    "input_data, data, success, expected_input_type, expected_result_type",
    [
        pytest.param("file_input", Files(), True, FileInput, Files, id="success"),
        pytest.param("file_input", Files(), False, FileInput, Files, id="failure"),
    ],
    indirect=["input_data"],
)
def test_pickle_serialization_of_program_output_parametrized(
    input_data,
    data,
    success,
    expected_input_type,
    expected_result_type,
    request,
):
    """This test checks that all the dynamic types are correctly set when pickled."""

    provenance = Provenance(program="qcdata-test-suite")
    traceback = None
    if success is False:
        traceback = "Fake traceback"

    prog_output = ProgramOutput[type(input_data), type(data)](
        input_data=input_data,
        data=data,
        success=success,
        provenance=provenance,
        traceback=traceback,
    )
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    prog_output = ProgramOutput(
        input_data=input_data,
        data=data,
        success=success,
        provenance=provenance,
        traceback=traceback,
    )
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    unspecified_po = ProgramOutput(**prog_output.model_dump())
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == unspecified_po

    prog_output_dict = prog_output.model_dump()
    prog_output_dict.update({"success": False, "traceback": "Traceback: ..."})
    no_prog_out = ProgramOutput(**prog_output_dict)
    serialized = pickle.dumps(no_prog_out)
    deserialized = pickle.loads(serialized)
    assert deserialized == no_prog_out

    dynamic_generics = ProgramOutput[
        type(prog_output.input_data), type(prog_output.data)
    ](**prog_output.model_dump())
    serialized = pickle.dumps(dynamic_generics)
    deserialized = pickle.loads(serialized)
    assert deserialized == dynamic_generics


def test_pickle_serialization_of_program_output():
    prog_output = ProgramOutput[ProgramInput, SinglePointData](
        input_data=ProgramInput(
            structure=Structure(
                symbols=["O", "H", "H"],
                geometry=np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0, 1.0, 0.0]),
                charge=0,
                multiplicity=1,
                connectivity=[(0, 1, 1.0), (0, 2, 1.0)],
            ),
            calctype="energy",
            model={"method": "hf", "basis": "sto-3g"},
            keywords={
                "maxiter": 100,
                "purify": "no",
                "some-bool": False,
                "displacement": 1e-3,
                "thermo_temp": 298.15,
            },
        ),
        success=True,
        logs="program standard out...",
        data=SinglePointData(
            energy=1.0,
            extras={"some_extra_result": 1},
        ),
        provenance={"program": "qcdata-test-suite", "scratch_dir": "/tmp/qcdata"},
        extras={"some_extra": 1},
    )
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == prog_output

    unspecified_po = ProgramOutput(**prog_output.model_dump())
    serialized = pickle.dumps(prog_output)
    deserialized = pickle.loads(serialized)
    assert deserialized == unspecified_po

    prog_output_dict = prog_output.model_dump()
    prog_output_dict.update(
        {"data": Files(), "success": False, "traceback": "Traceback: ..."}
    )
    no_data = ProgramOutput(**prog_output_dict)
    serialized = pickle.dumps(no_data)
    deserialized = pickle.loads(serialized)
    assert deserialized == no_data

    dynamic_generics = ProgramOutput[
        type(prog_output.input_data), type(prog_output.data)
    ](**prog_output.model_dump())
    serialized = pickle.dumps(dynamic_generics)
    deserialized = pickle.loads(serialized)
    assert deserialized == dynamic_generics


def test_compatibility_layer_for_files_on_prog_output(prog_input_factory):
    """Test that the compatibility layer for files on ProgramOutput works"""
    energy_input = prog_input_factory("energy")
    files = {"file1": "file1.txt", "file2": "file2.txt"}

    po = ProgramOutput(
        input_data=energy_input,
        success=True,
        data=SinglePointData(energy=-1.0),
        provenance={"program": "qcdata-test-suite"},
        files=files,
    )
    assert po.data.files == files


def test_compatibility_layer_for_noresults_prog_outputs(test_data_dir):
    """Ensure old ProgramOutput with NoResults can still be loaded."""
    ProgramOutput.model_validate_json((test_data_dir / "po_noresults.json").read_text())


def test_compatibility_layer_for_results_on_program_output(prog_input_factory):
    """Test that the compatibility layer for files on ProgramOutput works"""
    energy_input = prog_input_factory("energy")
    results_dict = {
        "input_data": energy_input,
        "success": True,
        "results": {"energy": -1.0},
        "provenance": {"program": "qcdata-test-suite"},
    }
    po = ProgramOutput(**results_dict)
    assert po.data.energy == -1.0


def test_compatibility_layer_for_stdout_on_prog_output(prog_input_factory):
    """Test that the compatibility layer for stdout on ProgramOutput works"""
    energy_input = prog_input_factory("energy")
    logs = "program standard out..."
    results_dict = {
        "input_data": energy_input,
        "success": True,
        "results": {"energy": -1.0},
        "provenance": {"program": "qcdata-test-suite"},
        "stdout": logs,
    }
    results = ProgramOutput(**results_dict)
    assert results.logs == logs
