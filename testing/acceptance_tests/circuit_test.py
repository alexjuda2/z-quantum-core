import pytest
import os
import sys
import json
import numpy as np
from zquantum.core.utils import RNDSEED
from zquantum.core.circuit import (
    load_circuit_template_params,
    save_circuit_template_params,
    load_circuit,
    load_parameter_grid,
    load_circuit_layers,
    load_circuit_connectivity,
    Circuit,
)

sys.path.append("../..")
from steps.circuit import (
    build_ansatz_circuit,
    generate_random_ansatz_params,
    combine_ansatz_params,
    build_uniform_param_grid,
    build_circuit_layers_and_connectivity,
)


class Test_generate_random_ansatz_params:
    @pytest.mark.parametrize(
        "number_of_layers, problem_size",
        [
            (1, 1),
            (0, 1),
            (1, 6),
            (4, 3),
        ],
    )
    def test_generate_random_ansatz_params_using_mock_ansatz_specs(
        self, number_of_layers, problem_size
    ):
        # Given
        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": number_of_layers,
            "problem_size": problem_size,
        }
        seed = RNDSEED

        filename = "params.json"
        if os.path.exists(filename):
            os.remove(filename)

        # When
        generate_random_ansatz_params(ansatz_specs=ansatz_specs, seed=seed)

        # Then
        assert os.path.exists(filename)
        parameters = load_circuit_template_params(filename)
        assert len(parameters) == number_of_layers
        for parameter in parameters:
            assert parameter < np.pi * 0.5
            assert parameter > -np.pi * 0.5
            assert isinstance(parameter, float)

        if os.path.exists(filename):
            os.remove(filename)

    @pytest.mark.parametrize(
        "number_of_parameters",
        [i for i in range(12)],
    )
    def test_generate_random_ansatz_params_using_number_of_parameters(
        self,
        number_of_parameters,
    ):
        # Given
        seed = RNDSEED

        filename = "params.json"
        if os.path.exists(filename):
            os.remove(filename)

        # When
        generate_random_ansatz_params(
            number_of_parameters=number_of_parameters, seed=seed
        )

        # Then
        assert os.path.exists(filename)
        parameters = load_circuit_template_params(filename)
        assert len(parameters) == number_of_parameters
        for parameter in parameters:
            assert parameter < np.pi * 0.5
            assert parameter > -np.pi * 0.5
            assert isinstance(parameter, float)

        if os.path.exists(filename):
            os.remove(filename)

    def test_generate_random_ansatz_params_fails_with_both_ansatz_specs_and_number_of_parameters(
        self,
    ):
        # Given
        number_of_parameters = 2
        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": 2,
            "problem_size": 1,
        }
        seed = RNDSEED

        # When
        with pytest.raises(AssertionError):
            generate_random_ansatz_params(
                ansatz_specs=ansatz_specs,
                number_of_parameters=number_of_parameters,
                seed=seed,
            )

    def test_generate_random_ansatz_params_fails_with_neither_ansatz_specs_nor_number_of_parameters(
        self,
    ):
        # Given
        seed = RNDSEED

        # When
        with pytest.raises(AssertionError):
            generate_random_ansatz_params(
                seed=seed,
            )


class Test_combine_ansatz_params:
    @pytest.mark.parametrize(
        "params1, params2",
        [
            ([], []),
            ([1.0], []),
            ([], [1.0]),
            ([0.0], [1.0]),
            ([0.0, 1.0, 3.0, 5.0, -2.3], [1.0]),
        ],
    )
    def test_combine_ansatz_params(self, params1, params2):
        # Given
        params1_filename = "params1.json"
        save_circuit_template_params(np.array(params1), params1_filename)

        params2_filename = "params2.json"
        save_circuit_template_params(np.array(params2), params2_filename)

        # When
        combine_ansatz_params(params1_filename, params2_filename)

        # Then
        combined_parameters_filename = "combined-params.json"
        assert os.path.exists(combined_parameters_filename)
        parameters = load_circuit_template_params(combined_parameters_filename)
        assert all(parameters == params1 + params2)

        os.remove(params1_filename)
        os.remove(params2_filename)
        os.remove(combined_parameters_filename)


class Test_build_ansatz_circuit:
    @pytest.mark.parametrize(
        "number_of_layers, number_of_parameters",
        [
            (0, 0),
            (2, 0),
            (2, 2),
            (2, 4),
        ],
    )
    def test_build_ansatz_circuit(self, number_of_layers, number_of_parameters):
        # Given
        params = np.random.uniform(low=0, high=np.pi, size=number_of_parameters)
        number_of_layers = 0
        params_filename = None
        if params is not None:
            number_of_layers = len(params)
            params_filename = "params.json"
            save_circuit_template_params(np.array(params), params_filename)

        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": number_of_layers,
            "problem_size": 2,
        }

        # When
        build_ansatz_circuit(ansatz_specs=ansatz_specs, params=params_filename)

        # Then
        circuit_filename = "circuit.json"
        circuit = load_circuit(circuit_filename)
        assert isinstance(circuit, Circuit)

        os.remove(circuit_filename)
        os.remove(params_filename)

    def test_build_ansatz_circuit_raises_exception_on_invalid_inputs(self):
        # Given
        params_filename = "params.json"
        save_circuit_template_params(np.array([1.0]), params_filename)

        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": 0,
            "problem_size": 2,
        }

        # When
        with pytest.raises(Exception):
            build_ansatz_circuit(ansatz_specs=ansatz_specs, params=params_filename)

        os.remove(params_filename)


class Test_build_uniform_param_grid:
    @pytest.mark.parametrize(
        "number_of_ansatz_layers, problem_size, number_of_layers, min_value, max_value, step",
        [
            (0, 2, 2, 0, 1, 0.5),
            (1, 2, 2, 0, 1, 0.5),
            (1, 0, 2, 0, 1, 0.5),
            (6, 2, 2, 0, 1, 0.5),
            (1, 2, 6, 0, 1, 0.5),
            (1, 2, 6, -np.pi, 1, 0.5),
            (1, 2, 6, -np.pi, np.pi, 0.5),
            (1, 2, 6, 0, 1, 0.01),
        ],
    )
    def test_build_uniform_param_grid_ansatz_specs(
        self,
        number_of_ansatz_layers,
        problem_size,
        number_of_layers,
        min_value,
        max_value,
        step,
    ):
        # Given
        expected_parameter_grid_filename = "parameter-grid.json"
        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": number_of_ansatz_layers,
            "problem_size": problem_size,
        }

        # When
        build_uniform_param_grid(
            ansatz_specs=ansatz_specs,
            number_of_layers=number_of_layers,
            min_value=min_value,
            max_value=max_value,
            step=step,
        )

        # Then
        param_grid = load_parameter_grid(expected_parameter_grid_filename)
        os.remove(expected_parameter_grid_filename)

    @pytest.mark.parametrize(
        "number_of_ansatz_layers, problem_size, number_of_layers, min_value, max_value, step",
        [
            (0, 2, 2, 0, 1, 0.5),
            (1, 2, 2, 0, 1, 0.5),
            (1, 0, 2, 0, 1, 0.5),
            (6, 2, 2, 0, 1, 0.5),
            (1, 2, 6, 0, 1, 0.5),
            (1, 2, 6, -np.pi, 1, 0.5),
            (1, 2, 6, -np.pi, np.pi, 0.5),
            (1, 2, 6, 0, 1, 0.01),
        ],
    )
    def test_build_uniform_param_grid_ansatz_specs_as_string(
        self,
        number_of_ansatz_layers,
        problem_size,
        number_of_layers,
        min_value,
        max_value,
        step,
    ):
        # Given
        expected_parameter_grid_filename = "parameter-grid.json"
        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": number_of_ansatz_layers,
            "problem_size": problem_size,
        }

        # When
        build_uniform_param_grid(
            ansatz_specs=json.dumps(ansatz_specs),
            number_of_layers=number_of_layers,
            min_value=min_value,
            max_value=max_value,
            step=step,
        )

        # Then
        param_grid = load_parameter_grid(expected_parameter_grid_filename)
        os.remove(expected_parameter_grid_filename)

    @pytest.mark.parametrize(
        "number_of_params_per_layer, number_of_layers, min_value, max_value, step",
        [
            (0, 2, 0, 1, 0.5),
            (1, 2, 0, 1, 0.5),
            (6, 2, 0, 1, 0.5),
            (1, 6, 0, 1, 0.5),
            (1, 6, -np.pi, 1, 0.5),
            (1, 6, -np.pi, np.pi, 0.5),
            (1, 6, 0, 1, 0.01),
        ],
    )
    def test_build_uniform_param_grid_number_of_params_per_layer(
        self, number_of_params_per_layer, number_of_layers, min_value, max_value, step
    ):
        # Given
        expected_parameter_grid_filename = "parameter-grid.json"

        # When
        build_uniform_param_grid(
            number_of_params_per_layer=number_of_params_per_layer,
            number_of_layers=number_of_layers,
            min_value=min_value,
            max_value=max_value,
            step=step,
        )

        # Then
        param_grid = load_parameter_grid(expected_parameter_grid_filename)
        os.remove(expected_parameter_grid_filename)

    def test_build_uniform_param_grid_fails_with_both_ansatz_specs_and_number_of_params_per_layer(
        self,
    ):
        # Given
        number_of_params_per_layer = 2
        ansatz_specs = {
            "module_name": "zquantum.core.interfaces.mock_objects",
            "function_name": "MockAnsatz",
            "number_of_layers": 2,
            "problem_size": 1,
        }

        # When
        with pytest.raises(AssertionError):
            build_uniform_param_grid(
                ansatz_specs=ansatz_specs,
                number_of_params_per_layer=number_of_params_per_layer,
            )

    def test_build_uniform_param_grid_fails_with_neither_ansatz_specs_nor_number_of_params_per_layer(
        self,
    ):
        # When
        with pytest.raises(AssertionError):
            build_uniform_param_grid()


class Test_build_circuit_layers_and_connectivity:
    @pytest.mark.parametrize(
        "x_dimension, y_dimension, layer_type",
        [
            (0, None, "nearest-neighbor"),
            (1, None, "nearest-neighbor"),
            (2, None, "nearest-neighbor"),
            (0, 0, "nearest-neighbor"),
            (1, 0, "nearest-neighbor"),
            (2, 0, "nearest-neighbor"),
            (0, 1, "nearest-neighbor"),
            (1, 1, "nearest-neighbor"),
            (2, 1, "nearest-neighbor"),
            (0, 2, "nearest-neighbor"),
            (1, 2, "nearest-neighbor"),
            (2, 2, "nearest-neighbor"),
            (1, 1, "sycamore"),
            (2, 1, "sycamore"),
            (1, 2, "sycamore"),
            (2, 2, "sycamore"),
        ],
    )
    def test_build_circuit_layers_and_connectivity(
        self, x_dimension, y_dimension, layer_type
    ):
        # Given
        expected_circuit_layers_filename = "circuit-layers.json"
        expected_circuit_connectivity_filename = "circuit-connectivity.json"

        # When
        build_circuit_layers_and_connectivity(
            x_dimension=x_dimension, y_dimension=y_dimension, layer_type=layer_type
        )

        # Then
        circuit_layers = load_circuit_layers(expected_circuit_layers_filename)
        circuit_connectivity = load_circuit_connectivity(
            expected_circuit_connectivity_filename
        )

        os.remove(expected_circuit_layers_filename)
        os.remove(expected_circuit_connectivity_filename)