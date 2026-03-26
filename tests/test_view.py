from qcdata import OptimizationData, ProgramInput, ProgramOutput
from qcdata.view import generate_optimization_plot


def test_generate_optimization_plot_with_single_prog_output_failure(
    prog_input_factory, results_failure
):
    opt_input = prog_input_factory("optimization")

    prog_output = ProgramOutput[ProgramInput, OptimizationData](
        input_data=opt_input,
        success=False,
        traceback="Traceback...",
        data=OptimizationData(trajectory=[results_failure]),
        provenance={"program": "fake-program"},
    )
    generate_optimization_plot(prog_output)
