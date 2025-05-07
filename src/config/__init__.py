import os
from typing import Final
from pathlib import Path

ZMQ_SERVER = os.getenv('ZMQ_SERVER')
TUNNEL_TIME_LIMIT = "00:03:00"
MAX_TUNNEL_TIME_LIMIT: Final = "00:15:00"

# Directorio base oculto en el home del usuario
_QMIO_BASE_DIR = Path.home() / ".qmio_logs"
_QMIO_BASE_DIR.mkdir(parents=True, exist_ok=True)  # Crea si no existe

# Archivo de log para accounting (si usas otro distinto)
ACCOUNT_PATH = _QMIO_BASE_DIR / "qmio_account.log"
