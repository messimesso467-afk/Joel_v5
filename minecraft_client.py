"""
Cliente local para el control de Minecraft de JOEL.

Habla con dos servidores levantados por ``bot.js``:
  - Estado (solo lectura): MC_STATUS_URL, por defecto
    http://127.0.0.1:3847/minecraft/status
  - Control (protegido): MC_CONTROL_URL si está definida (por ejemplo un
    túnel hacia la PC); si no, http://127.0.0.1:<MC_CONTROL_PORT>.
    En ambos casos exige la cabecera X-API-Key.

Solo permite las acciones de la lista blanca. No ejecuta comandos del
sistema ni acepta texto libre: las órdenes se traducen a rutas fijas.
"""
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

from logger_config import setup_logger

load_dotenv(override=True)
logger = setup_logger("minecraft_client")

# Acciones permitidas (lista blanca). No agregar texto libre aquí.
ACCIONES_PERMITIDAS = ("ven", "sigueme", "para", "salir")

TIMEOUT_SEGUNDOS = 5


def _puerto_control() -> int:
    try:
        return int(os.getenv("MC_CONTROL_PORT", "3848"))
    except ValueError:
        return 3848


def _url_estado() -> str:
    return os.getenv(
        "MC_STATUS_URL", "http://127.0.0.1:3847/minecraft/status"
    ).strip()


def _clave_control() -> str:
    return os.getenv("MC_CONTROL_API_KEY", "").strip()


def _url_control(accion: str) -> str:
    base = os.getenv("MC_CONTROL_URL", "").strip().rstrip("/")
    if base:
        return f"{base}/minecraft/control/{accion}"
    return f"http://127.0.0.1:{_puerto_control()}/minecraft/control/{accion}"


def control_disponible() -> bool:
    """Indica si hay una clave de control configurada."""
    return bool(_clave_control())


def estado() -> Dict[str, Any]:
    """
    Consulta el estado real del bot de Minecraft.

    Returns:
        dict con:
          - estado: "conectado" | "desconectado" | "no_disponible"
          - detalle: texto legible para el usuario
          - control_api: si el control autenticado está configurado
    """
    disponible = control_disponible()
    resultado: Dict[str, Any] = {
        "estado": "no_disponible",
        "detalle": "",
        "control_api": disponible,
        "salud": None,
        "jugador": None,
        "host": None,
        "puerto": None,
    }

    try:
        respuesta = httpx.get(_url_estado(), timeout=TIMEOUT_SEGUNDOS)
        respuesta.raise_for_status()
        datos = respuesta.json()
    except Exception as error:
        logger.info("Estado de Minecraft no disponible: %s", type(error).__name__)
        resultado["detalle"] = (
            "El bot de Minecraft no está en ejecución. Inícielo con 'node bot.js'."
        )
        return resultado

    resultado["salud"] = datos.get("salud")
    resultado["jugador"] = datos.get("jugador")
    resultado["host"] = datos.get("host")
    resultado["puerto"] = datos.get("port")

    if datos.get("conectado"):
        resultado["estado"] = "conectado"
        resultado["detalle"] = "JOEL está dentro del mundo de Minecraft."
    else:
        resultado["estado"] = "desconectado"
        resultado["detalle"] = (
            "El cliente de Minecraft está activo, pero JOEL aún no entró al mundo."
        )

    if not disponible:
        resultado["detalle"] += (
            " El control remoto está desactivado: falta MC_CONTROL_API_KEY en .env."
        )

    return resultado


def ejecutar(accion: str) -> Dict[str, Any]:
    """
    Ejecuta una acción permitida sobre el bot de Minecraft.

    Args:
        accion: una de ACCIONES_PERMITIDAS

    Returns:
        dict con "ok" (bool), "accion", "estado" y "mensaje"

    Raises:
        ValueError: si la acción no está en la lista blanca
    """
    accion_normalizada = (accion or "").strip().lower()

    if accion_normalizada not in ACCIONES_PERMITIDAS:
        logger.warning("Acción de Minecraft rechazada: %r", accion)
        raise ValueError(
            f"Acción no permitida. Use una de: {', '.join(ACCIONES_PERMITIDAS)}"
        )

    if not control_disponible():
        return {
            "ok": False,
            "accion": accion_normalizada,
            "estado": "no_disponible",
            "mensaje": (
                "El control de Minecraft está desactivado. "
                "Configure MC_CONTROL_API_KEY en .env y reinicie el bot."
            ),
        }

    try:
        respuesta = httpx.post(
            _url_control(accion_normalizada),
            headers={"X-API-Key": _clave_control()},
            timeout=TIMEOUT_SEGUNDOS,
        )
    except Exception as error:
        logger.info("Control de Minecraft no disponible: %s", type(error).__name__)
        return {
            "ok": False,
            "accion": accion_normalizada,
            "estado": "no_disponible",
            "mensaje": (
                "No pude hablar con el bot de Minecraft. "
                "Ejecute 'node bot.js' y vuelva a intentarlo."
            ),
        }

    if respuesta.status_code == 200:
        logger.info("Acción de Minecraft ejecutada: %s", accion_normalizada)
        return {
            "ok": True,
            "accion": accion_normalizada,
            "estado": "conectado",
            "mensaje": f"Orden '{accion_normalizada}' enviada al bot.",
        }

    if respuesta.status_code == 401:
        logger.error("El control de Minecraft rechazó la clave configurada.")
        return {
            "ok": False,
            "accion": accion_normalizada,
            "estado": "no_disponible",
            "mensaje": (
                "El bot rechazó la clave de control. Verifique que "
                "MC_CONTROL_API_KEY sea la misma en el bot y en la API."
            ),
        }

    if respuesta.status_code == 503:
        return {
            "ok": False,
            "accion": accion_normalizada,
            "estado": "desconectado",
            "mensaje": "El bot no está dentro del mundo de Minecraft.",
        }

    if respuesta.status_code == 400:
        return {
            "ok": False,
            "accion": accion_normalizada,
            "estado": "conectado",
            "mensaje": "No hay ningún jugador cerca para ejecutar esa orden.",
        }

    return {
        "ok": False,
        "accion": accion_normalizada,
        "estado": "no_disponible",
        "mensaje": f"El bot respondió con un error ({respuesta.status_code}).",
    }
