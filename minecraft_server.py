"""
Gestión del servidor local de Minecraft de JOEL (Paper 1.20.4).

Solo puede arrancar y detener el servidor oficial que vive en la carpeta
``servidor_minecraft/``, con una orden fija y sin aceptar texto del
usuario. Igual que el bot, el navegador nunca ejecuta nada: solo llama a
la API.

El servidor se apaga de forma ordenada enviando ``stop`` a su entrada
estándar, para que guarde el mundo antes de cerrarse.
"""
import os
import shutil
import socket
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from logger_config import setup_logger

load_dotenv(override=True)
logger = setup_logger("minecraft_server")

BASE_DIR = Path(__file__).resolve().parent
SERVIDOR_DIR = BASE_DIR / "servidor_minecraft"
RUTA_LOG = BASE_DIR / "logs" / "servidor_minecraft.log"

# Ajustado a un equipo con poca memoria libre.
MEMORIA_MINIMA = "256M"
MEMORIA_MAXIMA = "1024M"
ESPERA_APAGADO = 30  # segundos que se espera a que el servidor guarde y cierre

_proceso: Optional[subprocess.Popen] = None
_archivo_log = None
_candado = threading.Lock()


def _puerto() -> int:
    try:
        return int(os.getenv("MC_PORT", "25565"))
    except ValueError:
        return 25565


def java_disponible() -> bool:
    """Indica si hay una máquina virtual de Java accesible."""
    return shutil.which("java") is not None


def ruta_jar() -> Optional[Path]:
    """Devuelve el ejecutable de Paper instalado, si existe."""
    if not SERVIDOR_DIR.is_dir():
        return None
    candidatos = sorted(SERVIDOR_DIR.glob("paper-*.jar"))
    return candidatos[0] if candidatos else None


def _puerto_abierto() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", _puerto())) == 0


def en_ejecucion() -> bool:
    """Indica si el servidor de Minecraft está escuchando."""
    if _proceso is not None and _proceso.poll() is None:
        return True
    return _puerto_abierto()


def _ultimas_lineas(cantidad: int = 5) -> List[str]:
    """Lee el final del registro del servidor para mostrarlo en el panel."""
    if not RUTA_LOG.is_file():
        return []
    try:
        with open(RUTA_LOG, "r", encoding="utf-8", errors="replace") as archivo:
            lineas = [linea.strip() for linea in archivo.readlines()[-40:]]
    except OSError:
        return []
    return [linea for linea in lineas if linea][-cantidad:]


def _listo_para_jugar() -> bool:
    """Comprueba en el registro si el mundo ya terminó de cargarse."""
    return any("Done (" in linea for linea in _ultimas_lineas(40))


def estado() -> Dict[str, Any]:
    """
    Estado real del servidor local de Minecraft.

    Returns:
        dict con instalado, java_disponible, activo, puerto y detalle.
    """
    jar = ruta_jar()
    activo = en_ejecucion()

    if activo and _listo_para_jugar():
        detalle = "El servidor está en marcha y el mundo ya se cargó."
    elif activo:
        detalle = "El servidor está arrancando. Espere unos segundos."
    elif jar is None:
        detalle = "No se encontró el servidor de Minecraft (falta el archivo paper-*.jar)."
    elif not java_disponible():
        detalle = "Falta Java en el equipo: instálelo para poder usar el servidor."
    else:
        detalle = "El servidor de Minecraft está detenido."

    return {
        "instalado": jar is not None,
        "java_disponible": java_disponible(),
        "activo": activo,
        "listo": activo and _listo_para_jugar(),
        "puerto": _puerto(),
        "host": os.getenv("MC_HOST", "127.0.0.1"),
        "memoria_maxima": MEMORIA_MAXIMA,
        "archivo": jar.name if jar else None,
        "carpeta": str(SERVIDOR_DIR),
        "iniciado_por_la_api": _proceso is not None and _proceso.poll() is None,
        "detalle": detalle,
        "ultimas_lineas": _ultimas_lineas(),
    }


def iniciar() -> Dict[str, Any]:
    """
    Arranca el servidor de Minecraft con la orden fija de Java.

    Returns:
        dict con "ok" y "mensaje"
    """
    global _proceso, _archivo_log

    if en_ejecucion():
        return {"ok": True, "ya_activo": True, "mensaje": "El servidor de Minecraft ya estaba en marcha."}

    jar = ruta_jar()
    if jar is None:
        return {"ok": False, "mensaje": "No se encontró el servidor de Minecraft en servidor_minecraft/."}

    if not java_disponible():
        return {"ok": False, "mensaje": "Java no está instalado o no está en el PATH del sistema."}

    RUTA_LOG.parent.mkdir(exist_ok=True)
    comando = [
        "java",
        f"-Xms{MEMORIA_MINIMA}",
        f"-Xmx{MEMORIA_MAXIMA}",
        "-XX:+UseG1GC",
        "-jar",
        jar.name,
        "nogui",
    ]

    try:
        _archivo_log = open(RUTA_LOG, "a", encoding="utf-8", errors="replace")
        _proceso = subprocess.Popen(
            comando,
            cwd=str(SERVIDOR_DIR),
            stdin=subprocess.PIPE,
            stdout=_archivo_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as error:
        logger.error("No pude iniciar el servidor de Minecraft: %s", error)
        return {"ok": False, "mensaje": "No pude iniciar el servidor de Minecraft."}

    logger.info("Servidor de Minecraft iniciado por la API (pid=%s)", _proceso.pid)
    return {
        "ok": True,
        "ya_activo": False,
        "pid": _proceso.pid,
        "mensaje": (
            "Servidor de Minecraft arrancando. Tarda unos segundos en cargar el mundo."
        ),
    }


def detener() -> Dict[str, Any]:
    """
    Detiene el servidor enviando la orden ``stop`` y esperando a que guarde.

    Returns:
        dict con "ok" y "mensaje"
    """
    global _proceso, _archivo_log

    if _proceso is None or _proceso.poll() is not None:
        if _puerto_abierto():
            return {
                "ok": False,
                "mensaje": (
                    "El servidor no lo inició este panel, así que no lo detengo. "
                    "Ciérrelo en su ventana de consola escribiendo 'stop'."
                ),
            }
        return {"ok": False, "mensaje": "El servidor de Minecraft ya estaba detenido."}

    with _candado:
        try:
            if _proceso.stdin:
                _proceso.stdin.write("stop\n")
                _proceso.stdin.flush()
        except OSError as error:
            logger.warning("No pude enviar 'stop' al servidor: %s", error)

        try:
            _proceso.wait(timeout=ESPERA_APAGADO)
        except subprocess.TimeoutExpired:
            logger.warning("El servidor no cerró a tiempo; lo termino de forma forzada.")
            _proceso.terminate()
            try:
                _proceso.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _proceso.kill()

        _proceso = None
        if _archivo_log is not None:
            _archivo_log.close()
            _archivo_log = None

    logger.info("Servidor de Minecraft detenido por la API.")
    return {"ok": True, "mensaje": "Servidor de Minecraft detenido y mundo guardado."}
