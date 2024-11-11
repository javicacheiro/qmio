### Tests de las funciones del backend qpu ###
from qmio.backends import _config_builder, _optimization_options_builder, _results_format_builder
import pytest


def test_config_builder():
    result_config = _config_builder(shots=100, repetition_period=500*10**-6, optimization=0, res_format="binary_count")
    assert result_config == '{"$type": "<class \'qat.purr.compiler.config.CompilerConfig\'>", "$data": {"repeats": 100, "repetition_period": 0.0005, "results_format": {"$type": "<class \'qat.purr.compiler.config.QuantumResultsFormat\'>", "$data": {"format": {"$type": "<enum \'qat.purr.compiler.config.InlineResultsProcessing\'>", "$value": 1}, "transforms": {"$type": "<enum \'qat.purr.compiler.config.ResultsFormatting\'>", "$value": 3}}}, "metrics": {"$type": "<enum \'qat.purr.compiler.config.MetricsType\'>", "$value": 6}, "active_calibrations": [], "optimizations": {"$type": "<enum \'qat.purr.compiler.config.TketOptimizations\'>", "$value": 1}}}'


def test_optimization_options_builder():
    result_optimization_builder_empty = _optimization_options_builder(optimization=0)
    result_optimization_builder_one = _optimization_options_builder(optimization=1)
    result_optimization_builder_two = _optimization_options_builder(optimization=2)
    result_optimization_builder_type = _optimization_options_builder(optimization_backend="Tket", optimization=0)
    # Test con opciones invalidas pendiente
    with pytest.raises(TypeError):
        _optimization_options_builder(optimization_backend="Fast", optimization=0)
    with pytest.raises(ValueError):
        _optimization_options_builder(optimization=99)

    assert result_optimization_builder_empty == 1
    assert result_optimization_builder_one == 18
    assert result_optimization_builder_two == 30
    assert result_optimization_builder_empty == result_optimization_builder_type


def test_results_format_builder():
    result_format_builder_format, result_format_builder_transforms = _results_format_builder()
    result_format_builder_binary_count_format, result_format_builder_binary_count_transforms = _results_format_builder(res_format="binary_count")
    result_format_builder_raw_format, result_format_builder_raw_transforms = _results_format_builder(res_format="raw")
    result_format_builder_binary_format, result_format_builder_binary_transforms = _results_format_builder(res_format="binary")
    result_format_builder_squash_binary_result_arrays_format, result_format_builder_squash_binary_result_arrays_transforms = _results_format_builder(res_format="squash_binary_result_arrays")
    # Test con opciones invalidas pendiente
    with pytest.raises(KeyError):
        result_format_builder_fail_format, result_format_builder_fail_transforms = _results_format_builder(res_format="fail")

    assert result_format_builder_format ==  result_format_builder_binary_count_format
    assert result_format_builder_transforms ==  result_format_builder_binary_count_transforms
    assert result_format_builder_binary_count_format == 1
    assert result_format_builder_binary_count_transforms == 3
    assert result_format_builder_raw_format == 1
    assert result_format_builder_raw_transforms == 2
    assert result_format_builder_binary_format == 2
    assert result_format_builder_binary_transforms == 2
    assert result_format_builder_squash_binary_result_arrays_format == 2
    assert result_format_builder_squash_binary_result_arrays_transforms == 6
