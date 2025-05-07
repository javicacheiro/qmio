"""
Centralized Accounting methods.

This module provides centralized accounting
functionalities in a form of an Accounting Unit Class
"""
import logging
from datetime import datetime
import socket
import getpass
import json
import uuid
from typing import Optional, Final

from config import ACCOUNT_PATH


class AccountUnit:
    def __init__(self, account_path: Optional[str]) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._start_time: datetime = datetime.now()
        self._end_time: Optional[datetime] = None
        self._hostname: Final[str] = socket.gethostname()
        self._username: Final[str] = getpass.getuser()

        self.total_circuit_bytes: int = 0
        self.total_shots: int = 0
        self.calls: int = 0
        self._job_id: Optional[str] = None

        self._account_path = account_path or ACCOUNT_PATH
        self._logger.info("Initialized Account Unit")

    def set_job_id(self, job_id: Optional[str]):
        self._job_id = job_id
        if self._job_id is None:
            self._job_id = str(uuid.uuid4())
        self._logger.info("Logged Job ID info")

    def finish(self):
        self._end_time = datetime.now()
        self._logger.info(f"Logged end time info: {self._end_time}")

    def publish_to_log_file(self):
        if not self._end_time:
            self.finish()

        duration = (self._end_time - self._start_time).total_seconds() if self._end_time else None
        self._logger.info(f"Computing duration: {duration}")

        record = {
                    "timestamp": self._start_time.isoformat(),
                    "job_id": self._job_id,
                    "user": self._username,
                    "hostname": self._hostname,
                    "duration_sec": duration,
                    "total_circuit_bytes": self.total_circuit_bytes,
                    "total_shots": self.total_shots,
                    "calls": self.calls
                }
        self._logger.info(f"Building account record: {record}")

        try:
            with open(self._account_path, "a") as f:
                f.write(json.dumps(record) + "\n")
            self._logger.info(f"Published accounting record to {self._account_path}")
        except Exception as e:
            self._logger.error(f"Failed to write accounting record: {e}")
