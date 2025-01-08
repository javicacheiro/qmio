import pytest
import os
from unittest.mock import patch, call
from qmio.clients import SlurmClient
from qmio.utils import BackendError, OutputParsingError
from config import TUNNEL_TIME_LIMIT


class TestSlurmClient:
    @patch("qmio.clients.run")  # Reemplaza con el path correcto
    def test_scancel(self, mock_run):
        # Instancia del cliente
        client = SlurmClient()
        client._job_id = "12345"
        # Llamamos al método scancel con un job_id específico
        client.scancel("12345")
        # Verificamos que se llame a 'run' con el comando correcto
        client.scancel()
        mock_run.assert_has_calls([
            call("scancel 12345"),
            call("scancel 12345")
        ])

    @patch("qmio.clients.run")
    def test_is_job_running(self, mock_run):
        # Instancia del cliente
        client = SlurmClient()
        # Caso cuando el trabajo está corriendo
        mock_run.return_value = ("RUNNING", "")
        assert client._is_job_running(12345) is True
        # Caso cuando el trabajo no está corriendo
        mock_run.return_value = ("", "")
        assert client._is_job_running(12345) is False
        # Verificamos que se llamó con el comando correcto
        mock_run.assert_called_with("scontrol show job 12345")
        client._job_id = 54321
        client._is_job_running(job_id=None)
        mock_run.assert_called_with("scontrol show job 54321")

    @patch("qmio.clients.run")
    def test_check_backend_node(self, mock_run):
        client = SlurmClient()
        # Simulamos la salida de 'scontrol show partition'
        mock_run.return_value = ("Nodes=c1-10", "")

        # Verificamos que el método retorna la IP correcta
        ip = client._check_backend_node("backend1")
        assert ip == "10.120.1.10"

        # Verificamos que se llama con el comando correcto
        mock_run.assert_called_with("scontrol show partition backend1")

        # Probamos que lanza una excepción si no encuentra nodos
        mock_run.return_value = ("", "")
        with pytest.raises(ValueError):
            client._check_backend_node("backend1")

        with pytest.raises(BackendError):
            client._check_backend_node(backend=None)

    @patch("qmio.clients.run")
    @patch("random.randint")
    @patch("time.sleep")
    @patch.object(SlurmClient, '_is_job_running')
    @patch.object(SlurmClient, '_check_backend_node')
    def test_submit_and_wait(self, mock_check_backend_node, mock_is_job_running, mock_sleep, mock_randint, mock_run):
        # Instancia del cliente
        client = SlurmClient()

        # Mock de valores que devuelve cada función
        mock_randint.return_value = 650
        mock_run.return_value = ("Submitted batch job 12345", "")
        mock_is_job_running.side_effect = [False, False, True]  # Simula que el trabajo empieza después de algunos intentos
        mock_check_backend_node.return_value = "10.120.1.10"

        # Llamamos al método a probar
        job_id, endpoint = client.submit_and_wait(backend="backend1")

        # Verificamos los resultados
        assert job_id == "12345"
        assert endpoint == "tcp://10.120.1.10:650"

        current_dir = os.path.dirname(os.path.dirname(__file__))
        expected_script_path = os.path.join(current_dir, "qmio", "slurm_scripts", "backend1.sh")
        expected_time_limit = TUNNEL_TIME_LIMIT
        # Verificamos que se generaron los comandos correctos
        mock_run.assert_called_with(f"sbatch --time={expected_time_limit} {expected_script_path} 650")
        mock_is_job_running.assert_called_with("12345")
        mock_check_backend_node.assert_called_with("backend1")

        with pytest.raises(ValueError):
            client.submit_and_wait(backend=None)

    @patch("qmio.clients.run")
    @patch("random.randint")
    @patch("time.sleep")
    @patch.object(SlurmClient, '_is_job_running')
    @patch.object(SlurmClient, '_check_backend_node')
    def test_submit_and_wait_reservation(self, mock_check_backend_node, mock_is_job_running, mock_sleep, mock_randint, mock_run):
        # Instancia del cliente
        reservation_name = "reserva_alvaro"
        client = SlurmClient(reservation_name=reservation_name)

        # Mock de valores que devuelve cada función
        mock_randint.return_value = 650
        mock_run.return_value = ("Submitted batch job 12345", "")
        mock_is_job_running.side_effect = [False, False, True]  # Simula que el trabajo empieza después de algunos intentos
        mock_check_backend_node.return_value = "10.120.1.10"

        # Llamamos al método a probar
        job_id, endpoint = client.submit_and_wait(backend="backend1")

        # Verificamos los resultados
        assert job_id == "12345"
        assert endpoint == "tcp://10.120.1.10:650"

        current_dir = os.path.dirname(os.path.dirname(__file__))
        expected_script_path = os.path.join(current_dir, "qmio", "slurm_scripts", "backend1.sh")
        expected_time_limit = TUNNEL_TIME_LIMIT
        # Verificamos que se generaron los comandos correctos

        mock_run.assert_called_with(f"sbatch --reservation='{reservation_name}' --time={expected_time_limit} {expected_script_path} 650")
        mock_is_job_running.assert_called_with("12345")
        mock_check_backend_node.assert_called_with("backend1")

        with pytest.raises(ValueError):
            client.submit_and_wait(backend=None)

    @patch("qmio.clients.run")
    @patch("random.randint")
    @patch("time.sleep")
    @patch.object(SlurmClient, '_is_job_running')
    @patch.object(SlurmClient, '_check_backend_node')
    def test_submit_and_wait_failed_job_id_found(self, mock_check_backend_node, mock_is_job_running, mock_sleep, mock_randint, mock_run):
        # Instancia del cliente
        client = SlurmClient()

        # Mock de valores que devuelve cada función
        mock_randint.return_value = 650
        mock_run.return_value = ("Submitted batch job NON_JOB_ID", "")
        mock_is_job_running.side_effect = [False, False, True]  # Simula que el trabajo empieza después de algunos intentos
        mock_check_backend_node.return_value = "NON_IP"

        # Llamamos al método a probar
        with pytest.raises(OutputParsingError):
            job_id, endpoint = client.submit_and_wait(backend="backend1")

    @patch.object(SlurmClient, '_is_job_running', return_value=False)  # Simular que el job no arranca nunca
    @patch("qmio.clients.run")
    @patch('time.sleep', return_value=None)  # Simular que sleep no tarda nada
    def test_submit_and_wait_timeout(self, mock_sleep, mock_run, mock_is_job_running):
        client = SlurmClient()

        # Asegúrate de que mock_run devuelva dos valores como espera el código
        mock_run.return_value = ("Submitted batch job 12345", "")  # stdout, stderr
        client._max_retries = 2  # Poco tiempo para el time out

        # Verificamos que al alcanzar el timeout se lanza el TimeoutError
        with pytest.raises(TimeoutError, match="Tunnel did not start withing the 8h time frame"):
            client.submit_and_wait(backend="backend1")

    @patch.object(SlurmClient, '_is_job_running', side_effect=KeyboardInterrupt)  # Simular un KeyboardInterrupt
    @patch.object(SlurmClient, 'scancel')  # Mockear el método scancel
    @patch("qmio.clients.run")
    def test_submit_and_wait_keyboard_interrupt(self, mock_run, mock_scancel, mock_is_job_running):
        client = SlurmClient()
        client._job_id = "12345"  # Mockear el job_id
        # Simular que run devuelve stdout y stderr (tupla con dos valores)
        mock_run.return_value = ("Submitted batch job 12345", "")
        # Verificamos que se lanza SystemExit al interrumpir con teclado
        client.submit_and_wait(backend="backend1")
        mock_scancel.assert_called_once_with("12345")
        assert client._job_id is None
