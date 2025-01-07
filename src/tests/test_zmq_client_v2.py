import pytest
import zmq
from unittest.mock import MagicMock
from qmio.clients import ZMQClient, Messages  # Asegúrate de cambiar esto a tu nombre de módulo


@pytest.fixture
def zmq_client(mocker):
    # Mockear el contexto y el socket de zmq
    mock_context = mocker.patch('zmq.Context', autospec=True)
    mock_socket = MagicMock()
    mock_context.return_value.socket.return_value = mock_socket

    client = ZMQClient(address="tcp://10.133.29.226:5556")
    client._context = mock_context.return_value
    client._socket = mock_socket

    return client, mock_socket


def test_initialization(zmq_client):
    client, mock_socket = zmq_client
    assert client._address == "tcp://10.133.29.226:5556"
    mock_socket.connect.assert_called_once_with("tcp://10.133.29.226:5556")


def test_send_message_success(zmq_client):
    client, mock_socket = zmq_client
    mock_socket.send_pyobj = MagicMock(return_value=None)  # Simular envío exitoso

    client._send("test_message")
    mock_socket.send_pyobj.assert_called_once_with("test_message")


def test_send_message_timeout(zmq_client):
    client, mock_socket = zmq_client
    mock_socket.send_pyobj = MagicMock(side_effect=zmq.ZMQError)  # Simular error

    # Establecer el tiempo de espera para que se agote
    client._timeout = 0.1

    # Verificar que se lanza un TimeoutError después de varios intentos
    with pytest.raises(TimeoutError):
        client._send("test_message")


def test_receive_message_success(zmq_client):
    client, mock_socket = zmq_client
    mock_socket.recv_pyobj = MagicMock(return_value="received_message")  # Simular recepción exitosa

    result = client._check_recieved()
    assert result == "received_message"


def test_receive_message_failure(zmq_client):
    client, mock_socket = zmq_client
    mock_socket.recv_pyobj = MagicMock(side_effect=zmq.ZMQError)  # Simular error

    result = client._check_recieved()
    assert result is None


def test_await_results_success(zmq_client):
    client, mock_socket = zmq_client
    mock_socket.recv_pyobj = MagicMock(return_value="result")  # Simular recepción exitosa

    result = client._await_results()
    assert result == "result"


def test_close_socket(zmq_client):
    client, mock_socket = zmq_client
    # Cerrar el socket
    mock_socket.closed = False
    client.close()
    # Verificar que se llamó a close() en el mock
    mock_socket.close.assert_called_once()
    # Repetir la llamada a close no debería causar errores
    client.close()


# def test_destructor_calls_close(zmq_client):
#     client, mock_socket = zmq_client
#     mock_socket.closed = False
#     mock_close = MagicMock()
#     client.close = mock_close

#     # Borra el cliente, lo que debería llamar al destructor
#     del client
#     # Verifica que `close` fue llamado una vez en el mock
#     mock_close.assert_called_once()

def test_rpc_version(zmq_client):
    client, mock_socket = zmq_client
    expected_response = {'qat_rpc_version': '0.6.0'}
    mock_socket.recv_pyobj.return_value = expected_response
    rpc_version = client.rpc_version()
    client._socket.send_pyobj.assert_called_once_with(
        (Messages.VERSION.value,)
    )
    assert rpc_version == expected_response
