"""
Module for the qmio low level clients

Classes
--------
ZMQBase
    Used as base class for ZMQClient

ZMQClient
    Is used by QPUBackend to init a connection with the server
    and exchange mesages.

SlurmBaseClient
    Abstract class to organize SlurmClient.

SlurmClient
    When no direct connection is provided, the SlurmClient is
    used to get a tunnel going.

"""
import abc
import logging
import os
import random
import re

# Under testing
from time import sleep, time, time_ns

import zmq
from typing import Optional

from config import TUNNEL_TIME_LIMIT
from qmio.utils import RunCommandError, run

logger = logging.getLogger(__name__)

base_dir = os.path.dirname(os.path.abspath(__file__))
slurm_scripts_dir = os.path.join(base_dir, 'slurm_scripts/')


class ZMQBase:
    """
    Base class for ZeroMQ communication.

    This class initializes a ZeroMQ context and socket for communication.

    Parameters
    ----------
    socket_type : int
        The type of socket to create. This is typically a ZeroMQ socket type (e.g., zmq.REQ, zmq.REP).

    Attributes
    ----------
    _context : zmq.Context
        The ZeroMQ context for managing sockets.
    _socket : zmq.Socket
        The ZeroMQ socket used for communication.
    _timeout : float
        The timeout period for sending messages, in seconds. Defaults to 30.0.
    _address : str or None
        The address of the socket. Defaults to None.
    _logger : logging.Logger
        Logger instance for logging messages related to this class.
    """
    def __init__(self, socket_type):
        self._context = zmq.Context()
        self._socket = self._context.socket(socket_type)
        self._timeout = 30.0
        self._address = None
        self._logger = logging.getLogger(self.__class__.__name__)

    def _check_recieved(self):
        """
        Check for and receive a message from the socket.

        Returns
        -------
        Any or None
            The received message if available, None otherwise.
        """
        start = time_ns()
        try:
            # This NONBLOCK is in qat-rpc class
            # msg = self._socket.recv_pyobj(zmq.NOBLOCK)
            msg = self._socket.recv_pyobj()
            end = time_ns()
            self._logger.info(f"Results received in: {(end - start)/1e9}")
            return msg
        except zmq.ZMQError:
            return None

    def _send(self, message) -> None:
        """
        Send a message through the socket.

        This method attempts to send a message and logs the time taken.
        If sending fails, it retries until a timeout occurs.

        Parameters
        ----------
        message : Any
            The message to be sent through the socket.

        Raises
        ------
        TimeoutError
            If sending the message times out.
        """
        sent = False
        t0 = time_ns()
        while not sent:
            try:
                self._socket.send_pyobj(message)
                sent = True
                end = time_ns()
                self._logger.info(f"Message sent in: {(end - t0)/1e9}")
            except zmq.ZMQError as e:
                if time() > t0/1e9 + self._timeout:
                    raise TimeoutError(
                        f"Sending {message} on {self._address} timedout"
                    )
                self._logger.error(f"Error sending message: {e}")

    def close(self):
        """Disconnect the link to the socket."""
        if self._socket.closed:
            return
        self._socket.close()
        self._context.destroy()

    def __del__(self):
        self.close()


class ZMQClient(ZMQBase):
    """
    Client used to communicate with a ZeroMQ server.

    This class extends `ZMQBase` to provide a client socket for sending
    requests and receiving responses from a ZeroMQ server.

    Parameters
    ----------
    address : str or None, optional
        The address of the ZeroMQ server to connect to. Defaults to None.

    Attributes
    ----------
    _address : str or None
        The address of the server that this client will connect to.
    """
    def __init__(self, address=None):
        super().__init__(zmq.REQ)
        self._socket.setsockopt(zmq.LINGER, 0)
        self._address = address
        self._logger = logging.getLogger(self.__class__.__name__)
        self._logger.debug(f"Address for ZMQClient: {self._address}")
        self._socket.connect(self._address)

    def _await_results(self):
        """
        Await results from the server.

        This method checks for results until they are received.

        Returns
        -------
        Any
            The result received from the server.

        Raises
        ------
        RuntimeError
            If the connection fails or results cannot be received.
        """
        start = time_ns()
        result = None
        while result is None:
            result = self._check_recieved()
        end = time_ns()
        self._logger.info(f"Results awaited for: {(end - start)/1e9}")
        return result


class SlurmBaseClient(abc.ABC):
    """
    Slurm Base Client Abstract Class
    """
    def __init__(self):
        self._job_id = None
        self._endpoint_port = None
        self._submit_cmd = None
        self._scancel_cmd = None
        self._check_cmd = None

    @abc.abstractmethod
    def scancel(self, job_id): # pragma: no cover
        pass

    @abc.abstractmethod
    def _is_job_running(self, job_id=None) -> bool: # pragma: no cover
        pass

    @abc.abstractmethod
    def submit_and_wait(self, endpoint_port=None, backend=None, time_limit: Optional[str] = None) -> tuple[Optional[str], Optional[str]]: # pragma: no cover
        pass


class SlurmClient(SlurmBaseClient):
    """
    Slurm client class.

    This class aggregates Slurm utilities to manage jobs submitted to
    a Slurm workload manager.

    Attributes
    ----------
    _job_id : str
        Job ID assigned by Slurm for tracking the submitted job.
    _endpoint_port : int
        Port used to redirect connections.
    _scancel_cmd : str
        Command to cancel a job in Slurm.
    _check_cmd : str
        Command to check if a job is currently running.
    _submit_cmd : str
        Command to allocate and submit a job to Slurm.
    _max_retries : int
        Number to stablish a time limit to wait for resources in tunneled jobs

    Methods
    -------
    scancel(job_id):
        Cancels the job with the given job ID.
    submit(endpoint_port):
        Submits a tunnel job to redirect connections to the specified endpoint port.
    _is_job_running(job_id):
        Checks if the job with the specified job ID is currently running.
    """
    def __init__(
            self,
            time_limit: Optional[str] = None,
            reservation_name: Optional[str] = None,
    ):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._max_retries: int = 288000
        self._tunnel_time_limit: Optional[str] = TUNNEL_TIME_LIMIT or None
        self.reservation_name = reservation_name or None

    def scancel(self, job_id: Optional[str] = None):
        """
        Cancel a job to deallocate the frontal node.

        Parameters
        ----------
        job_id : str, optional
            The ID of the job to be canceled. If None, the instance's job ID is used.

        Returns
        -------
        None
        """
        start = time_ns()
        if job_id is None:
            job_id = self._job_id
        self._scancel_cmd = f"scancel {job_id}"
        run(self._scancel_cmd)
        end = time_ns()
        self._logger.info(f"Slurm cancelation happended in: {(end - start)/1e9}")

    def _is_job_running(self, job_id=None) -> bool:
        """
        Check if the specified job is currently running.

        Executes the Slurm command to check job status and looks for
        the 'RUNNING' string in the output.

        Parameters
        ----------
        job_id : str, optional
            The ID of the job to check. If None, the instance's job ID is used.

        Returns
        -------
        bool
            True if the job is running, False otherwise.
        """
        start = time_ns()
        if job_id is None:
            job_id = self._job_id
        self._check_cmd = f"scontrol show job {job_id}"
        stdout, stderr = run(self._check_cmd)

        end = time_ns()
        self._logger.info(f"Job checked running in: {(end - start)/1e9}")
        if "RUNNING" in stdout:
            return True
        else:
            return False

    def _check_backend_node(self, backend: str = "") -> str:
        """
        Retrieve the IP of the specified backend partition node from Slurm.

        Parameters
        ----------
        backend : str
            The name of the backend partition.

        Returns
        -------
        str
            The IP address of the backend node.

        Raises
        ------
        RunCommandError
            If no backend is specified or if the command fails to retrieve the node IP.
        """
        start = time_ns()
        if not backend:
            raise RunCommandError('No backend spedified')
        _check_node_cmd = f'scontrol show partition {backend}'
        stdout, stderr = run(_check_node_cmd)
        self._logger.debug(f'stdout: {stdout}\n stderr: {stderr}')
        result = re.search(r'Nodes=c(\d+)-(\d+)', stdout)

        if result:
            rack = result.group(1)
            self._logger.debug(f'Rack encountered: {rack}')
            node = result.group(2)
            self._logger.debug(f'Node encountered: {node}')
            ip = f'10.120.{rack}.{node}'
            self._logger.debug(f'Ip encountered {ip}')
            end = time_ns()
            self._logger.info(f"backend node checked in: {(end - start)/1e9}")
            return ip
        else:
            raise ValueError(f'No result came from: "{_check_node_cmd}" Does not fit a NodeName')

    def submit_and_wait(self, endpoint_port=None, backend=None, time_limit: Optional[str] = None):
        """
        Submit the tunnel job to Slurm and wait for it to start.

        If not on the frontal node, submits a job to redirect connections.
        This method blocks until the job starts running.

        Parameters
        ----------
        endpoint_port : int, optional
            The port for redirecting connections. If None, a random port between 600 and 699 is used.
        backend : str, optional
            The name of the backend partition where the job is submitted.
        time_limit: str, optional
            The time limit for the tunner job. If not explicitly set will use the class default -> module default.

        Returns
        -------
        tuple
            Contains the job ID and the endpoint string.

        Raises
        ------
        ValueError
            If the backend is not specified.
        TimeoutError
            If the job does not start within the allowed timeframe.
        """
        start = time_ns()
        if backend is None:
            raise ValueError("Backend not specified")
        try:
            if endpoint_port is None:
                self._endpoint_port = random.randint(600, 699)
                end_endpoint_get = time_ns()
                self._logger.info(f"Endpoint port got in: {(end_endpoint_get - start)/1e9}")

            if not self.reservation_name:
                self._submit_cmd = f"sbatch --time={time_limit or self._tunnel_time_limit} {slurm_scripts_dir}{backend}.sh {self._endpoint_port}"
            else:
                self._submit_cmd = f"sbatch --reservation='{self.reservation_name}' --time={time_limit or self._tunnel_time_limit} {slurm_scripts_dir}{backend}.sh {self._endpoint_port}"

            stdout, stderr = run(self._submit_cmd)

            self._logger.debug(f"Submission command: {self._submit_cmd}")
            self._logger.debug(f"Command output: {stdout}")
            self._logger.debug(f"Command error: {stderr}")

            match = re.search(r"Submitted batch job (\d+)", stdout)
            if not match:
                raise RunCommandError(f"Failed to find job ID in command output: {stdout}")

            self._job_id = match.group(1)

            self._logger.info(f"Submitting Tunnel job to slurm: {self._job_id}")
            end_submission = time_ns()
            self._logger.info(f"Tunnel Job submitted in: {(end_submission - start)/1e9}")

            count = 0
            # Max number of retries to not allow anf infinite loop
            # (8hours*60*60)*0,1timeslice = 288000
            while not self._is_job_running(self._job_id) and count < self._max_retries:
                sleep(0.1)
                if count % 30 == 0:
                    print("Waiting for resources\r", end="")
                count += 1
                if count >= self._max_retries:
                    raise TimeoutError("Tunnel did not start withing the 8h time frame")

            self._logger.info("The job started")
            print("\r")
            print("Job started\r", end="")

            # endpoint ip hardcoded
            # endpoint = f"tcp://10.120.7.23:{self._endpoint_port}"
            node_ip = self._check_backend_node(backend)
            endpoint = f'tcp://{node_ip}:{self._endpoint_port}'

            self._logger.debug(f"Endpoint port value {self._endpoint_port}")

            end_submit_and_wait = time_ns()
            self._logger.info(f"Tunnel Job running in: {(end_submit_and_wait - start)/1e9}")
            return self._job_id, endpoint
        except KeyboardInterrupt:
            self.scancel(self._job_id)
            self._logger.info(f"Job {self._job_id} cancelled by Keyboard Interruption")
            self._job_id = endpoint = None
            # sys.exit(1)
            return self._job_id, endpoint
