import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("logs/app.log")
LOG_FILE.parent.mkdir(exist_ok=True)


def setup_logger(name: str = "cncf_app") -> logging.Logger:
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  
    
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    logger.propagate = False
    
    return logger

logger = setup_logger()