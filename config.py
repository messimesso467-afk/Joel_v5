import os
from dotenv import load_dotenv

load_dotenv(override=True)


def debe_iniciar_telegram() -> bool:
    value = (os.getenv("JOEL_START_TELEGRAM") or "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def obtener_host_web() -> str:
    host = (os.getenv("JOEL_HOST") or os.getenv("HOST") or "127.0.0.1").strip()
    return host or "127.0.0.1"


def obtener_puerto_web() -> int:
    value = (os.getenv("JOEL_PORT") or os.getenv("PORT") or "8000").strip()
    try:
        return int(value)
    except ValueError:
        return 8000
