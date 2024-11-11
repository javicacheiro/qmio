import pytest
from unittest.mock import patch, MagicMock
from qmio.utils import run, RunCommandError  # Asegúrate de importar la función y la excepción


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
