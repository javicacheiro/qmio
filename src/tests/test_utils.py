from config import MAX_TUNNEL_TIME_LIMIT
import pytest
from unittest.mock import patch, MagicMock
from qmio.utils import run, RunCommandError, time_to_seconds, time_within_time_limit


@patch("qmio.utils.subprocess.run")
def test_run_success(mock_subprocess_run):
    # Simular la salida exitosa de subprocess.run
    mock_completed_process = MagicMock()
    mock_completed_process.returncode = 0
    mock_completed_process.stdout = b'Success output'
    mock_completed_process.stderr = b''
    mock_subprocess_run.return_value = mock_completed_process
    # Llamamos a la función run con el comando ficticio
    stdout, stderr = run("fake command")
    # Verificamos que la función devuelva stdout y stderr correctamente
    assert stdout == "Success output"
    assert stderr == ""
    # Verificamos que subprocess.run fue llamado correctamente
    mock_subprocess_run.assert_called_once_with("fake command", shell=True, capture_output=True, check=False)


@patch("qmio.utils.subprocess.run")
def test_run_failure(mock_subprocess_run):
    # Simular que subprocess.run falla con un código de error
    mock_completed_process = MagicMock()
    mock_completed_process.returncode = 1
    mock_completed_process.stdout = b''
    mock_completed_process.stderr = b'Error occurred'
    mock_subprocess_run.return_value = mock_completed_process
    # Verificamos que la excepción RunCommandError se lanza en caso de error
    with pytest.raises(RunCommandError, match="Error occurred"):
        run("fake command")
    # Verificamos que subprocess.run fue llamado correctamente
    mock_subprocess_run.assert_called_once_with("fake command", shell=True, capture_output=True, check=False)


def test_time_to_seconds():
    assert time_to_seconds("00:03:00") == 180
    time_limit_str = "00:70:00"
    with pytest.raises(ValueError, match=f"Time limit: '{time_limit_str}' has values out of range."):
        time_to_seconds(time_limit_str=time_limit_str)
    time_limit_str = "DDDDDD"
    with pytest.raises(ValueError, match=f"Time format specified not valid '{time_limit_str}'. Must be HH:MM:SS."):
        time_to_seconds(time_limit_str=time_limit_str)


def test_time_within_time_limit():
    assert time_within_time_limit("") == True
    assert time_within_time_limit("00:03:00") == True
    assert time_within_time_limit(MAX_TUNNEL_TIME_LIMIT) == True
    time_limit = "00:50:00"
    with pytest.raises(ValueError, match=f"Time limit provided '{time_limit}' is outside of the maximun time limit '{MAX_TUNNEL_TIME_LIMIT}'."):
        time_within_time_limit(time_limit=time_limit)
