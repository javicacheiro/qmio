"""
Module to aggregate QMIO services.

This module provides a class for instantiating QMIO services
and managing backend connections.
"""

from qmio.backends import QPUBackend
import logging
import time

logger = logging.getLogger(__name__)


class QmioRuntimeService:
    """Class to instance QMIO services.

    This class is responsible for creating instances of QMIO services
    and managing backend requests.

    Attributes
    ----------
    None

    Methods
    -------
    backend(name):
        Requests a backend service by name.
    """
    def __init__(self):
        """Initialize the QmioRuntimeService instance.

        Logs the creation of a new QmioRuntimeService instance.
        """
        logger.info("QmioRuntimeService created")

    def backend(self, name):
        """Method to request a backend service.

        Currently supports the "qpu" backend. Additional backends
        can be added in the future.

        Parameters
        ----------
        name : str
            The name of the backend service to be requested.
            Supported value: "qpu".

        Returns
        -------
        QPUBackend
            An instance of the QPUBackend class if the requested
            backend is "qpu".

        Raises
        ------
        ValueError
            If the requested backend name is unknown.
        """
        start = time.time_ns()
        if name == "qpu":
            return QPUBackend()
        # if name == "qulacs":
        #     pass

        end = time.time_ns()
        logger.info(f"backend recovery time: {(end - start)/1e9}")
        raise ValueError(f"Backend unknown: {name}")
