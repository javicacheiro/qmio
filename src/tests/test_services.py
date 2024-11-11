import pytest

from qmio.backends import QPUBackend
from qmio.services import QmioRuntimeService


@pytest.fixture
def runtime_service():
    return QmioRuntimeService()


def test_backend_selection(runtime_service):
    backend = runtime_service.backend(name="qpu")
    assert isinstance(backend, QPUBackend)


def test_invalid_backend_name(runtime_service):
    with pytest.raises(ValueError):
        runtime_service.backend(name="invalidBackend")
