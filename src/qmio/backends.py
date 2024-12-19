"""
Backends builder to handle Circuit execution.

Functions
---------
_optimization_options_builder(optimization, optimization_backend="Tket")
    Builds the optimization options for the backend.

_results_format_builder(res_format="binary_count")
    Builds the results format for the backend.

_config_builder(shots: int, repetition_period=None, optimization=0,
    res_format="binary_count")
    Builds the configuration for the circuit execution, including shots,
    repetition period, optimization level, and result format.

Classes
-------
QPUBackend
    Class to manage execution of quantum circuits on a Quantum Processing Unit.
"""

import json
import logging
import re
import time
from typing import Optional, Union

from config import ZMQ_SERVER
from qmio.clients import SlurmClient, ZMQClient
from qmio.utils import run, time_within_time_limit

logger = logging.getLogger(__name__)


def _optimization_options_builder(
    optimization: int, optimization_backend: str = "Tket"
) -> int:
    """
    Builds the optimization options for the backend.

    This helper function ensures that the optimization is not dependent on QAT.
    Currently, only Tket optimization is supported.

    Parameters
    ----------
    optimization : int
        The optimization level to use.
    optimization_backend : str, default="Tket"
        The optimization backend to use. Currently, only Tket is supported.

    Returns
    -------
    int
        The optimization value understood by the control server.

    Raises:
    -------
        TypeError
            If asked for a not valid optimization backend
        ValueError
            If asked for a not valid optimization level

    """
    start = time.time_ns()
    if optimization_backend != "Tket":
        raise TypeError(f"{optimization_backend}: Not a valid type")
    if optimization == 1:
        opt_value = 18
    elif optimization == 2:
        opt_value = 30
    elif optimization == 0:
        opt_value = 1
    else:
        raise ValueError(f"{optimization}: Not a valid Optimization Value")
    end = time.time_ns()
    logger.info(f"Optimization options built in: {(end - start)/1e9}")
    return opt_value


def _results_format_builder(res_format: str = "binary_count") -> tuple[int, int]:
    """
    Builds the results format without using QAT.

    This function returns the InlineResultsProcessing and ResultFormatting
    integers to be used as input for the configuration builder.

    Parameters
    ----------
    res_format : str, default="binary_count"
        The format in which the results will be processed.
        Possible values are:

        - "binary_count": Returns a count of each instance of measured qubit
    registers. Switches result format to raw.
        - "binary": Returns results as a binary string.
        - "raw": Returns raw results.
        - "squash_binary_result_arrays": Squashes binary result list into a
    singular bit string. Switches results to binary.

    Returns
    -------
    tuple of int
        A tuple containing two integers: InlineResultsProcessing and
    ResultsFormatting.

    Raises
    ------
    KeyError
        If the provided `res_format` is not a valid result format.
    """
    match = {
        "binary_count": {"InlineResultsProcessing": 1, "ResultsFormatting": 3},
        "raw": {"InlineResultsProcessing": 1, "ResultsFormatting": 2},
        "binary": {"InlineResultsProcessing": 2, "ResultsFormatting": 2},
        "squash_binary_result_arrays": {"InlineResultsProcessing": 2, "ResultsFormatting": 6}
    }
    if res_format not in match.keys():
        raise KeyError(f"{res_format}: Not a valid result format")
    return match[res_format]["InlineResultsProcessing"], match[res_format]["ResultsFormatting"]


def _config_builder(
    shots: int,
    repetition_period: Optional[float] = None,
    optimization: int = 0,
    res_format: str = "binary_count",
) -> str:
    """
    Builds a config json object from options. Non qat-dependent

    Args:
        shots: int : Number of shots
        repetition_period: float : Duration of the circuit execution window.
            Include relaxation time
        optimization: int : 0, 1, 2. Optimization level defined and processed
            in server side
        res_format: str : binary_count(default), raw, binary,
            squash_binary_arrays. Result formatting defined and applied in
            server side.
    Returns:
        config_str: str : json-string object that is sent and loaded in the
            server side
    """
    inlineResultsProcessing, resultsFormatting = _results_format_builder(res_format)
    opt_value = _optimization_options_builder(optimization=optimization)
    start = time.time_ns()
    config = {
        "$type": "<class 'qat.purr.compiler.config.CompilerConfig'>",
        "$data": {
            "repeats": shots,
            "repetition_period": repetition_period,
            "results_format": {
                "$type": "<class 'qat.purr.compiler.config.QuantumResultsFormat'>",
                "$data": {
                    "format": {
                        "$type": "<enum 'qat.purr.compiler.config.InlineResultsProcessing'>",
                        "$value": inlineResultsProcessing,
                    },
                    "transforms": {
                        "$type": "<enum 'qat.purr.compiler.config.ResultsFormatting'>",
                        "$value": resultsFormatting,
                    },
                },
            },
            "metrics": {
                "$type": "<enum 'qat.purr.compiler.config.MetricsType'>",
                "$value": 6,
            },
            "active_calibrations": [],
            "optimizations": {
                "$type": "<enum 'qat.purr.compiler.config.TketOptimizations'>",
                "$value": opt_value,
            },
        },
    }
    config_str = json.dumps(config)
    end = time.time_ns()
    logger.info(f"Config built in: {(end - start)/1e9}")
    return config_str


class QPUBackend:
    """
    Class to handle the QPU Execution
    ---------------------------------

    Parameters:
    -----------
        client : Optional[any], default = None
            Communication client to talk with server side.
        _backend : str, default = "qpu"
            Identifier to select bash script to tunnel connection if needed.
        _endpoint : str, default = address or ZMQ_SERVER
            Endpoint to connect the client to.
        _slurmclient : Optional[Any], default = None
            If the Tunnel, this _slurmclient is used.
        _job_id : str, default = None
            Job id returned from slurm.
        _verification_cmd : str, default = None
            Connection verification command.
        _tunnel_time_limit: str, Optional
            User provided time limit to stablish the tunnel job
        reservation_name: str, Optional
            User provided reservation name to stablish tunnel to. Just active if
    provided.

    PrivateMethods
    --------------
    _verify_connection()
        Runs a connection verification command before trying to send any message

    ContextHandlers
    ---------------
    __enter__()
        When in context, connect.
    __exit__()
        When in context, disconnect.

    """
    def __init__(
        self,
        address: Optional[str] = None,
        logging_level: Union[int, str] = logging.NOTSET,
        logging_filename: Optional[str] = None,
        tunnel_time_limit: Optional[str] = None,
        reservation_name: Optional[str] = None,
    ):

        """
        Initialize a QPUBackend instance.

        Parameters
        ----------
        address : str or None, optional
            The address of the QPU server. Defaults to None.
        logging_level : int or str, optional
            The level of logging to use. Defaults to 0.
        logging_filename : str or None, optional
            The filename for logging output. Defaults to None.
        tunnel_time_limit : str or None, optional
            Time limit user specified for stablish interactive tunnels
        reservation_name : str or None, optional
            reservation name user specified
        """
        self._backend = "qpu"
        self._endpoint = address or ZMQ_SERVER
        self.client: Optional[ZMQClient] = None
        self._slurmclient: Optional[SlurmClient] = None
        self._job_id = None
        self._verification_cmd: Optional[str] = None
        if time_within_time_limit(tunnel_time_limit):
            self._tunnel_time_limit = tunnel_time_limit or None
        self.reservation_name = reservation_name or None
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.setLevel(logging_level)
        self._logger.info("QPUBackend created")

    def _verify_connection(self, endpoint: Optional[str] = None) -> None:
        """
        Helper method to verify connection with the control server.

        Parameters
        ----------
        endpoint : Optional[str], default=None
            The endpoint to connect to. If not provided, it's picked up from the
        class attribute.

        Returns
        -------
        None
            If the connection is successfully established.

        Raises
        ------
        ConnectionRefusedError
            Raised if it's not possible to establish a connection.

        """
        # If no enpoint provided, use the class attribute
        self._logger.debug("Verify connection started")
        start = time.time_ns()
        if not endpoint:
            endpoint = self._endpoint
            self._logger.debug(f"Endpoint from QPUBackend: {self._endpoint}")

        pattern = r"tcp://(\d+\.\d+\.\d+\.\d+):(\d+)"
        if endpoint:
            match = re.match(pattern, endpoint)
            if match:
                ip = match.group(1)
                port = match.group(2)
                self._logger.debug(f"Endpoint IP found: {ip}")
                self._logger.debug(f"Endpoint PORT found: {port}")
                self._verification_cmd = f"nc -zv {ip} {port}"
                self._logger.debug(f"Running verification cmd: {self._verification_cmd}")
                run(self._verification_cmd)
            else:
                raise RuntimeError("Not IP:PORT recovered")
                # self._logger.error("Not IP:PORT recovered")
                # sys.exit(1)

        end = time.time_ns()
        self._logger.info(f"Connection verified in: {(end - start)/1e9}")

    def __enter__(self):
        """
        Handles the connection when used as a context

        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Handles the disconnection when used as a context

        """
        self.disconnect()

    def connect(self) -> None:
        """
        Creates a connection establishing a ZMQClient
        ---------------------------------------------

        Works differently if in the frontal node or not.

        Parameters:
        -----------
        None

        Returns:
        --------
        None

        """
        self._logger.info("Connect started")
        start = time.time_ns()
        # Check if endpoint is provided before trying to submit and wait for job
        if not self._endpoint:
            self._logger.debug("You are outside of the frontal node.")
            self._logger.debug("Starting the redirection process.")

            if not self._slurmclient:
                self._slurmclient = SlurmClient(reservation_name=self.reservation_name) if self.reservation_name else SlurmClient()

            self._job_id, self._endpoint = self._slurmclient.submit_and_wait(
                backend=self._backend,
                time_limit=self._tunnel_time_limit
            )
            self._logger.debug(
                f"Returns of submit and wait: job_id = {self._job_id}& endpoint = {self._endpoint}"
            )
            time.sleep(0.3)
            end_tunnel_job = time.time_ns()
            self._logger.info(f"Tunnel job stablished in: {(end_tunnel_job - start)/1e9}")

        # Verify the connection
        self._verify_connection()

        if not self.client:
            self.client = ZMQClient(address=self._endpoint)
        end = time.time_ns()
        self._logger.info(f"Connection stablished in: {(end - start)/1e9}")

    def disconnect(self) -> None:
        """
        Closes the connection dropping the ZMQClient
        --------------------------------------------

        This method restores the backend to the original state

        Also removes the _job_id and _endpoint_port attributes
        to reuse the methods in the same process

        Parameters:
        -----------
        None

        Returns:
        --------
        None

        """
        self._logger.info("Disconnect method started")
        start = time.time_ns()
        # Check if job is running before trying to cancel it
        if self._job_id:
            while self._slurmclient._is_job_running(self._job_id):
                try:
                    self._slurmclient.scancel(self._job_id)
                    self._logger.debug(f"Sending scancel to Tunnel job {self._job_id}.")
                except Exception as e:
                    self._logger.debug(f"Error cancelling the job: {e}")
                time.sleep(0.5)

            # Reset _job_id and _endpoint_port if job is cancelled
            self._job_id = None
            self._endpoint_port = None
            self._endpoint = None

        # Close the client connection
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                self._logger.error(f"Error closing the ZMQClient: {e}")

            self.client = None
        end = time.time_ns()
        self._logger.info(f"Disconnection happened in: {(end - start)/1e9}")

    def _state_flush(self) -> None:
        """
        Clean all variables to not allow dirty states

        Parameters:
        -----------
        None

        Returns:
        --------
        None

        """
        start_flush = time.time_ns()
        self._logger.info("Job is no longer running. Flushing variables.")
        self.disconnect()
        self.connect()
        end_flush = time.time_ns()
        self._logger.info(f"Flushing completed in: {(end_flush - start_flush)/1e9}")

    def run(
        self,
        circuit: str,
        shots: int,
        repetition_period: Optional[float] = None,
        optimization: int = 0,
        res_format: str = "binary_count",
    ) -> object:
        """
        Run a circuit in the QPU.

        This method submits a circuit with specified options to the QPU for
        execution.

        Parameters
        ----------
        circuit : str
            The circuit to be executed. It can be in OpenQASM 3.0, OpenPulse
        grammar, or QIR string format.
        shots : int
            The number of times the circuit is executed.
        repetition_period : Optional[float], default=None
            The computation time slice, equivalent to CPU clocks.
        optimization : int, default=0
            Levels of optimization applied by QAT. It is turned off by default.
        res_format : str, default="binary_count"
            Options for how to retrieve results. Possible values include:

            - "raw": Raw results.
            - "binary": Results as a binary string.
            - "binary_count": Returns a count of each instance of measured qubit
        registers.
            - "squash_binary_result_arrays": Squashes binary result list into a
        singular bit string.

        Returns
        -------
        Any
            The results coming from the quantum hardware.

        Examples
        --------
        >>> from qmio import QmioRuntimeService
        >>> from qmio.circuits import bell

        >>> service = QmioRuntimeService()
        >>> circuit = bell
        >>> shots = 100
        >>> repetition_period = 500 * 10**-6
        >>> optimization = 0
        >>> res_format = "binary_count"

        >>> with service.backends(name="qpu") as backend:
        >>>     results = backend.run(circuit,
        >>>                           shots,
        >>>                           repetition_period,
        >>>                           optimization,
        >>>                           res_format)
        """
        start = time.time_ns()
        self._logger.info("Run started")
        # Check if client is connected before trying to send job
        if not self.client:
            raise RuntimeError("Not connected to the server")

        # If there is a job_id but it is not running
        # reopen the connection. The Tunnel job ended unexpectedly
        if self._job_id and not self._slurmclient._is_job_running(self._job_id):
            self._state_flush()

        # Build config using _config_builder function
        config = _config_builder(
            shots,
            repetition_period=repetition_period,
            optimization=optimization,
            res_format=res_format,
        )


        # Create a job tuple with the circuit and config
        job = (circuit, config)

        # Send the job to the server
        self.client._send(job)

        # Wait for results from the server
        result = self.client._await_results()

        end = time.time_ns()
        self._logger.info(f"Job took: {(end - start)/1e9}")
        return result
