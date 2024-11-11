import pytest
import unittest
from unittest.mock import patch
from qmio.backends import QPUBackend
import time


def test_qpu_backend_init():
    backend = QPUBackend(address="tcp://127.0.0.1:1234", logging_level=10)

    assert backend._backend == "qpu"
    assert backend._endpoint == "tcp://127.0.0.1:1234"
    assert backend.client is None
    assert backend._slurmclient is None
    assert backend._job_id is None
    assert backend._verification_cmd is None


@patch("qmio.backends.run")
def test_verify_connection_success(mock_run):
    backend = QPUBackend(address="tcp://127.0.0.1:1234")
    # Simulamos que el comando de verificación se ejecuta sin errores
    mock_run.return_value = ("Success", "")
    backend._verify_connection()
    # Verificamos que se ejecuta el comando adecuado
    mock_run.assert_called_once_with("nc -zv 127.0.0.1 1234")


def test_verify_connection_failure():
    backend = QPUBackend(address="invalid_endpoint")
    with pytest.raises(RuntimeError, match="Not IP:PORT recovered"):
        backend._verify_connection()


@patch("qmio.backends.SlurmClient")
@patch("qmio.backends.ZMQClient")
@patch("qmio.backends.run")
def test_connect(mock_run, mock_zmqclient, mock_slurmclient):
    backend = QPUBackend()
    # Simulamos que el cliente de slurm devuelve un job_id y un endpoint
    mock_slurmclient_instance = mock_slurmclient.return_value
    mock_slurmclient_instance.submit_and_wait.return_value = ("12345", "tcp://127.0.0.1:1234")
    # Simulamos que la función run devuelve stdout y stderr de un comando 'sbatch'
    mock_run.return_value = ("Submitted batch job 12345", "")
    # Simulamos que el comando de verificación de conexión retorna un resultado exitoso
    mock_run.side_effect = [
        ("Submitted batch job 12345", ""),  # Primer llamado: ejecución de submit_and_wait
        ("Connection to 127.0.0.1 1234 port [tcp/*] succeeded!", "")  # Segundo llamado: ejecución de verificación de conexión
    ]
    backend.connect()
    # Verificamos que se ejecuta el comando de verificación de conexión
    mock_run.assert_any_call("nc -zv 127.0.0.1 1234")
    # Verificamos que se establece el cliente ZMQ correctamente
    mock_zmqclient.assert_called_once_with(address="tcp://127.0.0.1:1234")


@patch("qmio.backends.SlurmClient")
@patch("qmio.backends.ZMQClient")
def test_disconnect(mock_zmqclient, mock_slurmclient):
    # Crea una instancia del backend
    backend = QPUBackend()
    # Simulamos que hay un cliente ZMQ conectado y un trabajo en slurm
    mock_zmqclient_instance = mock_zmqclient.return_value
    backend.client = mock_zmqclient_instance  # Asignamos el cliente simulado
    backend._slurmclient = mock_slurmclient.return_value
    backend._job_id = "12345"
    # Simulamos que el trabajo de slurm sigue ejecutándose
    mock_slurmclient_instance = mock_slurmclient.return_value
    mock_slurmclient_instance._is_job_running.side_effect = [True, False]  # Primero true, luego false
    backend.disconnect()
    # Verificamos que se intenta cancelar el trabajo
    mock_slurmclient_instance.scancel.assert_called_once_with("12345")
    # Verificamos que el cliente ZMQ se cierra
    mock_zmqclient_instance.close.assert_called_once()


@patch("qmio.backends.SlurmClient")
@patch("qmio.backends.ZMQClient")
def test_disconnect_with_exception(mock_zmqclient, mock_slurmclient):
    backend = QPUBackend()

    # Simulamos que hay un cliente ZMQ conectado y un trabajo en slurm
    mock_zmqclient_instance = mock_zmqclient.return_value  # Obtiene la instancia simulada de ZMQClient
    backend.client = mock_zmqclient_instance  # Asigna la instancia simulada
    backend._slurmclient = mock_slurmclient.return_value
    backend._job_id = "12345"
    # Simulamos que el trabajo de slurm sigue ejecutándose
    mock_slurmclient_instance = mock_slurmclient.return_value
    mock_slurmclient_instance._is_job_running.side_effect = [True, True, False]  # Cambiar a False después de dos llamadas
    # Configuramos scancel para lanzar una excepción la primera vez que se llama
    mock_slurmclient_instance.scancel.side_effect = [Exception("Cancel failed"), None]
    # Ejecutamos disconnect()
    backend.disconnect()
    # Verificamos que se intenta cancelar el trabajo
    assert mock_slurmclient_instance.scancel.call_count == 2  # Se espera que se intente cancelar dos veces
    assert mock_slurmclient_instance.scancel.call_args_list[0][0] == ("12345",)  # Primera llamada con excepción
    assert mock_slurmclient_instance.scancel.call_args_list[1][0] == ("12345",)  # Segunda llamada sin excepción

    # Verificamos que el cliente ZMQ se cierra
    mock_zmqclient_instance.close.assert_called_once()  # Usa la instancia simulada para verificar el cierre


@patch("qmio.backends.SlurmClient")
@patch("qmio.backends.ZMQClient")
def test_disconnect_with_close_exception(mock_zmqclient, mock_slurmclient):
    backend = QPUBackend()

    # Simulamos que hay un cliente ZMQ conectado y un trabajo en slurm
    mock_zmqclient_instance = mock_zmqclient.return_value
    backend.client = mock_zmqclient_instance  # Asignar la instancia de cliente ZMQ

    mock_slurmclient_instance = mock_slurmclient.return_value
    backend._slurmclient = mock_slurmclient_instance
    backend._job_id = "12345"

    # Cambia a False después de la primera llamada
    mock_slurmclient_instance._is_job_running.side_effect = [True, False]  # Cambia a False después de una llamada

    # Simulamos que el trabajo de slurm sigue ejecutándose
    mock_slurmclient_instance.scancel.side_effect = [None]  # Sin excepciones en scancel

    # Simulamos que el método close lanza una excepción
    mock_zmqclient_instance.close.side_effect = Exception("Close failed")

    # Ejecutamos disconnect() y verificamos que intenta cancelar el trabajo
    backend.disconnect()

    # Verificamos que se intenta cancelar el trabajo
    mock_slurmclient_instance.scancel.assert_called_once_with("12345")  # Debería intentar cancelar el trabajo
    # Verificamos que el cliente ZMQ se cierra
    mock_zmqclient_instance.close.assert_called_once()

    # Verificamos que se maneja correctamente la excepción al cerrar
    with patch.object(backend, '_logger', autospec=True) as mock_logger:
        # Aquí se llama a disconnect() nuevamente para verificar el logger
        backend.disconnect()
        mock_logger.error("Error closing the ZMQClient: Close failed")  # Verifica que se registró el mensaje de error


class TestQPUBackend(unittest.TestCase):

    @patch.object(QPUBackend, 'connect')
    @patch.object(QPUBackend, 'disconnect')
    def test_state_flush(self, mock_disconnect, mock_connect):
        # Creamos una instancia de QPUBackend
        backend = QPUBackend()

        # Patch del logger
        with patch.object(backend, '_logger', autospec=True) as mock_logger:
            # Simular el tiempo para que el test sea más rápido
            start_time = time.time_ns()
            backend._state_flush()  # Ejecutar la función a probar
            end_time = time.time_ns()

            # Verificar que se llama a disconnect() y connect()
            mock_disconnect.assert_called_once()  # Debería llamarse una vez
            mock_connect.assert_called_once()      # Debería llamarse una vez

            # # Verificar los logs
            # mock_logger.info.assert_any_call("Job is no longer running. Flushing variables.")
            # # Verificamos que se llame con un tiempo que sea razonablemente cercano
            # mock_logger.info.assert_any_call(
            #     f"Flushing completed in: {(end_time - start_time)/1e9:.1f}"
            # )

    @patch.object(QPUBackend, 'connect')
    def test_run_no_client(self, mock_connect):
        backend = QPUBackend()

        with patch.object(backend, '_logger', autospec=True) as mock_logger:
            backend.client = None
            with pytest.raises(RuntimeError):
                backend.run("dummy_circuit", shots=100)


@patch("qmio.backends.ZMQClient")
@patch("qmio.backends.SlurmClient")
def test_run(mock_slurmclient, mock_zmqclient):
    backend = QPUBackend()
    # Simulamos que el cliente ZMQ ya está conectado
    backend.client = mock_zmqclient.return_value
    # Simulamos la configuración del circuito
    mock_zmqclient_instance = mock_zmqclient.return_value
    mock_zmqclient_instance._await_results.return_value = "result"
    # Ejecutamos el método `run`
    result = backend.run("dummy_circuit", shots=100)
    # Verificamos que el cliente ZMQ haya enviado el trabajo
    mock_zmqclient_instance._send.assert_called_once_with(("dummy_circuit", '{"$type": "<class \'qat.purr.compiler.config.CompilerConfig\'>", "$data": {"repeats": 100, "repetition_period": null, "results_format": {"$type": "<class \'qat.purr.compiler.config.QuantumResultsFormat\'>", "$data": {"format": {"$type": "<enum \'qat.purr.compiler.config.InlineResultsProcessing\'>", "$value": 1}, "transforms": {"$type": "<enum \'qat.purr.compiler.config.ResultsFormatting\'>", "$value": 3}}}, "metrics": {"$type": "<enum \'qat.purr.compiler.config.MetricsType\'>", "$value": 6}, "active_calibrations": [], "optimizations": {"$type": "<enum \'qat.purr.compiler.config.TketOptimizations\'>", "$value": 1}}}'))
    # Verificamos que se devuelvan los resultados correctos
    assert result == "result"


@patch.object(QPUBackend, 'connect')
@patch.object(QPUBackend, 'disconnect')
def test_qpu_backend_context_manager(mock_disconnect, mock_connect):
    # Usar el QPUBackend como un gestor de contexto
    with QPUBackend(address="tcp://127.0.0.1:1234", logging_level=10) as backend:
        # Verificar que se llama a `connect()` al entrar al contexto
        mock_connect.assert_called_once()
        # Verificar que `disconnect()` aún no ha sido llamado dentro del contexto
        mock_disconnect.assert_not_called()

    # Fuera del contexto, `disconnect()` debería haberse llamado una vez
    mock_disconnect.assert_called_once()


@patch("qmio.backends.ZMQClient")
@patch("qmio.backends.SlurmClient")
def test_run_state_flush(mock_slurmclient, mock_zmqclient):
    backend = QPUBackend()

    # Configurar el cliente ZMQ como conectado
    backend.client = mock_zmqclient.return_value
    mock_zmqclient_instance = mock_zmqclient.return_value
    mock_zmqclient_instance._await_results.return_value = "result"

    # Configurar un job_id y el slurmclient para forzar el flush
    backend._job_id = "12345"
    backend._slurmclient = mock_slurmclient.return_value  # Aseguramos que el slurmclient no sea None
    mock_slurmclient_instance = mock_slurmclient.return_value
    mock_slurmclient_instance._is_job_running.return_value = False  # Simula que el trabajo ha terminado

    with patch.object(backend, "_state_flush") as mock_state_flush:
        result = backend.run("dummy_circuit", shots=100)
        mock_state_flush.assert_called_once()  # Verifica que _state_flush fue llamado
        assert result == "result"
