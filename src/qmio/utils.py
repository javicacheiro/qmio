"""
Centralized helper methods.

This module provides centralized utility functions and classes
to support various operations within the application,
including logging setup and command execution.
"""
import logging
import os
import subprocess
import re

from config import MAX_TUNNEL_TIME_LIMIT

# Logger config env attribution
_LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}


def _setup_logging():
    """Private logger setup function.

    This function configures the logging settings based on the
    environment variable 'LOG_LEVEL'. The default log level is
    set to 'WARNING'.

    Parameters
    ----------
    None

    Returns
    -------
    None
    """
    log_level_str = os.getenv('LOG_LEVEL', 'WARNING').upper()
    log_level = _LOG_LEVELS.get(log_level_str, logging.WARNING)

    logging.basicConfig(
        level=log_level,
        format=(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ),
        handlers=[logging.StreamHandler()])


class OutputParsingError(Exception):
    def __init__(self, message, output, hint=None):
        hint_message = f"\nHint: {hint}" if hint else ""
        super().__init__(f"{message}\nOutput: {output}{hint_message}")
        self.output = output
        self.hint = hint


class BackendError(Exception):
    def __init__(self, message, hint=None):
        hint_message = f"\nHint: {hint}" if hint else ""
        super().__init__(f"{message}\n {hint_message}")
        self.hint = hint


class RunCommandError(Exception):
    """Exception raised for errors in running a command."""
    def __init__(self, cmd, returncode, stderr, hint=None):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        self.hint = hint or ("Ensure the required software is installed and"
                             " available in your PATH.")
        super().__init__(f"Command '{cmd}' failed with return code"
                         f" {returncode}:\n{stderr}\nHint: {self.hint}")


class CommandNotFoundError(RunCommandError):
    """Raised when a required command is not found."""
    def __init__(self, cmd):
        hint = (f"Ensure the command '{cmd}' is installed and available in "
                "your PATH.")
        super().__init__(cmd, 127, "", hint)


class ReservationError(RunCommandError):
    """Raised when there is an issue with the reservation system."""
    def __init__(self, cmd, stderr):
        hint = (
            "Check if there is an active reservation using "
            "`scontrol show reservations`, "
            "or verify that your reservation parameters are correct."
        )
        super().__init__(cmd, 1, stderr, hint)


class GenericSystemError(RunCommandError):
    """Generic system error for unexpected failures."""
    def __init__(self, cmd, returncode, stderr):
        hint = "Review the system configuration and logs for more details."
        super().__init__(cmd, returncode, stderr, hint)


def run(cmd: str) -> tuple[str, str]:
    """Execute a shell command.

    This function runs the specified command in the shell and
    returns its standard output and standard error.

    Parameters
    ----------
    cmd : str
        The command to be executed in the shell.

    Returns
    -------
    tuple[str, str]
        A tuple containing the standard output and standard error
        of the command execution.

    Raises
    ------
    RunCommandError
        If the command returns a non-zero exit status, indicating
        that an error occurred during execution.
    """
    logging.debug(f"Executing command: {cmd}")
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        logging.error(f"Command failed: {cmd} | Return code: {p.returncode} | Error: {p.stderr}")
        if p.returncode == 127:
            raise CommandNotFoundError(cmd)
        elif "reservation is invalid" in p.stderr:
            raise ReservationError(cmd, p.stderr)
        else:
            raise GenericSystemError(cmd, p.returncode, p.stderr)
    return p.stdout, p.stderr


def time_to_seconds(time_limit_str: str) -> int:
    """Change a time format HH:MM:SS to seconds

    Parameters
    ----------
    time_limit_str : str
        Time limit string formated as HH:MM:SS

    Returns
    -------
    : int
        Number of seconds

    Raises
    ------
    ValueError
        If the time string has not a valid format. Valid format is HH:MM:SS

    ValueError
        If there is a value out of range in the format specified
    """
    if not re.match(
            r'^\d{2}:\d{2}:\d{2}$', time_limit_str
    ):
        raise ValueError(
            f"Time format specified not valid '{time_limit_str}'."
            " Must be HH:MM:SS."
        )

    hours, minutes, seconds = map(int, time_limit_str.split(":"))

    if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
        raise ValueError(
            f"Time limit: '{time_limit_str}' has values out of range."
        )
    return hours * 3600 + minutes * 60 + seconds


def time_within_time_limit(
        time_limit,
        max_time_limit: str = MAX_TUNNEL_TIME_LIMIT
) -> bool:

    """Check if the provided time is within the maximun time limit

    Parameters
    ----------
    time_limit : str
        User provided time limit following the format HH:MM:SS

    max_time_limit : str
        Maximun time limit allowed by the system

    Returns
    -------
    : Bool
        True if the time is within the range

    Raises
    ------
    ValueError
        If the time limit is outside of the time range
    """
    if not time_limit:
        return True
    current_seconds = time_to_seconds(time_limit)
    max_seconds = time_to_seconds(max_time_limit)

    if current_seconds > max_seconds:
        raise ValueError(
            f"Time limit provided '{time_limit}' is outside of the maximun"
            f" time limit '{max_time_limit}'."
        )
    return True
