"""
Centralized helper methods.

This module provides centralized utility functions and classes
to support various operations within the application,
including logging setup and command execution.
"""
import logging
import os
import subprocess

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

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()])


class RunCommandError(Exception):
    """Exception raised for errors in running a command.

    This exception is raised when a command executed by the
    `run` function fails to execute successfully.
    """
    pass


def run(cmd: "str") -> tuple[str, str]:
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
    p = subprocess.run(cmd, shell=True, capture_output=True, check=False)
    if p.returncode != 0:
        raise RunCommandError(p.stderr)
    return p.stdout.decode('utf8'), p.stderr.decode('utf8')
