import logging
import sys
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"joel_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str = "joel", level: int = logging.INFO) -> logging.Logger:
    """Configura un logger con salida a consola y archivo."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "joel") -> logging.Logger:
    """Obtiene un logger existente o crea uno nuevo."""
    return logging.getLogger(name)
