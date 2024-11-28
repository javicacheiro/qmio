import os
from typing import Final

ZMQ_SERVER = os.getenv('ZMQ_SERVER')
TUNNEL_TIME_LIMIT = "00:03:00"
MAX_TUNNEL_TIME_LIMIT: Final = "00:15:00"
