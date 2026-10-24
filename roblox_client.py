"""
Detección local de Roblox Studio.

Solo realiza comprobaciones no invasivas del sistema de archivos
(búsqueda de los ejecutables oficiales de Roblox Studio) y, si el
propietario lo pide de forma explícita, puede abrir la aplicación
instalada.

No descarga nada, no modifica el sistema y no automatiza Roblox Studio.
"""
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from logger_config import setup_logger

logger = setup_logger("roblox_client")

URL_OFICIAL = "https://create.roblox.com/"
NOMBRE_EJECUTABLE = "RobloxStudioBeta.exe"

# Rutas candidatas (relativas a variables de entorno del usuario)
_PLANTILLAS = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Roblox" / "Versions",
    Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
    / "Roblox"
    / "Versions",
    Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Roblox" / "Versions",
)


def _buscar_ejecutable() -> Optional[Path]:
    """Busca Roblox Studio en las carpetas oficiales. Solo lectura."""
    for base in _PLANTILLAS:
        try:
            if not base.exists():
                continue
            for version in sorted(base.iterdir(), reverse=True):
                ejecutable = version / NOMBRE_EJECUTABLE
                if ejecutable.is_file():
                    return ejecutable
        except OSError as error:
            logger.debug("No pude revisar %s: %s", base, error)
    return None


def estado() -> Dict[str, Any]:
    """
    Comprueba si Roblox Studio está instalado.

    Returns:
        dict con "instalado", "ruta", "version" y "detalle"
    """
    ejecutable = _buscar_ejecutable()

    if ejecutable is None:
        return {
            "instalado": False,
            "ruta": None,
            "version": None,
            "url_oficial": URL_OFICIAL,
            "detalle": (
                "No instalado o no verificado. Instálelo manualmente desde la "
                "web oficial de Roblox (create.roblox.com) y pulse "
                "'Comprobar instalación' de nuevo."
            ),
        }

    return {
        "instalado": True,
        "ruta": str(ejecutable),
        "version": ejecutable.parent.name,
        "url_oficial": URL_OFICIAL,
        "detalle": (
            "Roblox Studio detectado. Puede abrirlo desde este panel. "
            "La automatización de Studio (Luau, creación de juegos) aún no "
            "está implementada."
        ),
    }


def abrir() -> Dict[str, Any]:
    """
    Abre Roblox Studio si está instalado. Acción explícita del propietario.

    Returns:
        dict con "ok" y "mensaje"
    """
    ejecutable = _buscar_ejecutable()

    if ejecutable is None:
        return {
            "ok": False,
            "mensaje": (
                "Roblox Studio no está instalado en este equipo. "
                f"Descárguelo desde {URL_OFICIAL}"
            ),
        }

    try:
        subprocess.Popen([str(ejecutable)])
    except OSError as error:
        logger.error("No pude abrir Roblox Studio: %s", error)
        return {"ok": False, "mensaje": "No pude abrir Roblox Studio."}

    logger.info("Roblox Studio abierto desde el panel.")
    return {"ok": True, "mensaje": "Abriendo Roblox Studio..."}
