import os
from typing import Any, Dict

from schemas import EchoServerSettings

def get_server_settings()->EchoServerSettings:
    PORT = int(os.getenv("PORT") or 8000)
    TIMEOUT_TIME = int(os.getenv("TIMEOUT_TIME") or 2)
    return EchoServerSettings(**{"port": PORT, "timeout_time": TIMEOUT_TIME})