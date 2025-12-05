import os
import logging

from schemas import EchoServerSettings

def initialize_logger() -> logging.Logger:
    LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, LOG_LEVEL_NAME, logging.INFO)

    def off_loggers() -> None:
        pass

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    off_loggers()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Logger initialized with level: {LOG_LEVEL_NAME}")
    return logger 

def get_server_settings()->EchoServerSettings:
    is_container = str(os.getenv("CONTAINERIZED")).lower() == "true"

    PORT = int(os.getenv("PORT", 8356) if not is_container else 8356)
    PORT_METRICS = int(os.getenv("PORT", 8000) if not is_container else 8000)
    HOST = "0.0.0.0" if is_container else "127.0.0.1"
    TIMEOUT_TIME = int(os.getenv("TIMEOUT_TIME") or 2)
    
    return EchoServerSettings(**{"port": PORT, 
        "timeout_time": TIMEOUT_TIME, "host": HOST, "port_metrics": PORT_METRICS})

logger = initialize_logger()