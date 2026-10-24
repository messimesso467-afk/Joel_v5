"""
Gestión segura de los servicios locales de JOEL.

Solo puede arrancar y detener el bot de Minecraft, y siempre con la
orden fija ``node bot.js`` dentro de la carpeta del proyecto. No acepta
comandos del usuario ni texto libre, por lo que la web no puede
ejecutar nada arbitrario.

El servidor web de la API no se reinicia desde aquí: si está apagado,
no hay nadie que pueda atender la petición. Para eso existe el lanzador
``iniciar_joel.bat``.
"""
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from logger_config import setup_logger

load_dotenv(override=True)
logger = setup_logger("system_manager")

BASE_DIR = Path(__file__).resolve().parent

_puerto_api = int((os.getenv("JOEL_API_PORT", "") or "8000").strip() or "8000")
_proceso_minecraft: Optional[subprocess.Popen] = None


def _puerto_abierto(host: str, puerto: int) -> bool:
    """Comprueba si hay algo escuchando en el puerto indicado."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, puerto)) == 0


def _puerto_control() -> int:
    try:
        return int(os.getenv("MC_CONTROL_PORT", "3848"))
    except ValueError:
        return 3848


def _puerto_estado() -> int:
    try:
        return int(os.getenv("MC_STATUS_PORT", "3847"))
    except ValueError:
        return 3847


def bot_en_ejecucion() -> bool:
    """Indica si el bot de Minecraft está en marcha."""
    if _proceso_minecraft is not None and _proceso_minecraft.poll() is None:
        return True
    return _puerto_estado_abierto()


def _puerto_estado_abierto() -> bool:
    return _puerto_abierto("127.0.0.1", _puerto_estado())


def node_disponible() -> bool:
    """Indica si Node.js está instalado y accesible."""
    return shutil.which("node") is not None


def estado_servicios() -> Dict[str, Any]:
    """
    Estado real de los servicios locales de JOEL.

    Returns:
        dict con la situación de la API web, el bot de Minecraft y el control.
    """
    api_activa = _puerto_abierto("127.0.0.1", _puerto_api)
    mc_bot = bot_en_ejecucion()
    control = _puerto_abierto("127.0.0.1", _puerto_control())

    return {
        "api": {
            "activo": api_activa,
            "puerto": _puerto_api,
            "estado": "activo" if api_activa else "no_disponible",
        },
        "minecraft_bot": {
            "activo": mc_bot,
            "puerto_estado": _puerto_estado(),
            "puerto_control": _puerto_control(),
            "node_disponible": node_disponible(),
            "estado": "activo" if mc_bot else "detenido",
            "iniciado_por_la_api": _proceso_minecraft is not None
            and _proceso_minecraft.poll() is None,
        },
        "control_minecraft": {
            "activo": control,
            "clave_configurada": bool(os.getenv("MC_CONTROL_API_KEY", "").strip()),
        },
        "lanzador": str(BASE_DIR / "iniciar_joel.bat"),
        "python": sys.executable,
    }


def iniciar_minecraft_bot() -> Dict[str, Any]:
    """
    Arranca el bot de Minecraft con la orden fija ``node bot.js``.

    Returns:
        dict con "ok" y "mensaje"
    """
    global _proceso_minecraft

    if bot_en_ejecucion():
        return {
            "ok": True,
            "ya_activo": True,
            "mensaje": "El bot de Minecraft ya estaba en ejecución.",
        }

    if not node_disponible():
        return {
            "ok": False,
            "mensaje": "Node.js no está disponible en el PATH. Instálelo para usar el bot.",
        }

    try:
        _proceso_minecraft = subprocess.Popen(
            ["node", "bot.js"],
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as error:
        logger.error("No pude iniciar el bot de Minecraft: %s", error)
        return {"ok": False, "mensaje": "No pude iniciar el bot de Minecraft."}

    logger.info("Bot de Minecraft iniciado por la API (pid=%s)", _proceso_minecraft.pid)
    return {
        "ok": True,
        "ya_activo": False,
        "pid": _proceso_minecraft.pid,
        "mensaje": "Bot de Minecraft iniciado.",
    }


def detener_minecraft_bot() -> Dict[str, Any]:
    """
    Detiene el bot de Minecraft, solo si lo inició esta API.

    Returns:
        dict con "ok" y "mensaje"
    """
    global _proceso_minecraft

    if _proceso_minecraft is None or _proceso_minecraft.poll() is not None:
        return {
            "ok": False,
            "mensaje": (
                "El bot no fue iniciado desde este panel, así que no lo detengo. "
                "Ciérrelo manualmente si lo arrancó usted."
            ),
        }

    _proceso_minecraft.terminate()
    try:
        _proceso_minecraft.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _proceso_minecraft.kill()

    logger.info("Bot de Minecraft detenido por la API.")
    _proceso_minecraft = None
    return {"ok": True, "mensaje": "Bot de Minecraft detenido."}
