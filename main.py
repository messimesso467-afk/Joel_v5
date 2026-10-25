"""
API web y panel central de JOEL.
Rutas públicas:
    GET  /                  Panel web (HTML)
    GET  /api/info          Información básica del servidor
    GET  /health            Estado resumido (sin datos privados)
    GET  /api/auth/session  Indica si la sesión del navegador es válida
Rutas privadas (X-API-Key o cookie de sesión):
    POST /api/auth/login    Abre sesión con la API key
    POST /api/auth/logout   Cierra la sesión
    GET  /api/metrics       Métricas de proveedores
    POST /api/chat          Conversación con el cerebro de JOEL
    GET  /api/minecraft/status
    POST /api/minecraft/control
    GET  /api/minecraft/servidor
    POST /api/minecraft/servidor/iniciar
    POST /api/minecraft/servidor/detener
    GET  /api/roblox/status
    POST /api/roblox/open
    GET  /api/system/status
    POST /api/system/minecraft/start
    POST /api/system/minecraft/stop
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from fastapi import Cookie, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
import minecraft_client
import minecraft_server
import roblox_client
import system_manager
from auth import (
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    cerrar_sesion,
    crear_sesion,
    requerir_acceso,
    sesion_valida,
    verificar_api_key,
)
from health import health_checker
from config import debe_iniciar_telegram, obtener_host_web, obtener_puerto_web
from joel_core import procesar_respuesta_joel
from logger_config import setup_logger
from providers import providers_manager
from rate_limiter import check_rate_limit

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app = FastAPI(title="Joel AI - Servidor Principal")

@app.on_event("startup")
def _telegram_al_iniciar():
    _iniciar_telegram_en_segundo_plano()

logger = setup_logger("web_api")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ChatRequest(BaseModel):
    user_id: str
    message: str

    @field_validator("user_id")
    @classmethod
    def validar_user_id(cls, valor: str) -> str:
        valor = (valor or "").strip()
        if not valor or len(valor) > 64:
            raise ValueError("user_id debe tener entre 1 y 64 caracteres")
        return valor

    @field_validator("message")
    @classmethod
    def validar_message(cls, valor: str) -> str:
        valor = (valor or "").strip()
        if not valor:
            raise ValueError("El mensaje no puede estar vacío")
        if len(valor) > 2000:
            raise ValueError("El mensaje es demasiado largo (máximo 2000 caracteres)")
        return valor


class LoginRequest(BaseModel):
    api_key: str


class MinecraftControlRequest(BaseModel):
    accion: str

    @field_validator("accion")
    @classmethod
    def validar_accion(cls, valor: str) -> str:
        valor = (valor or "").strip().lower()
        if valor not in minecraft_client.ACCIONES_PERMITIDAS:
            raise ValueError(
                f"Acción no permitida. Use una de: "
                f"{', '.join(minecraft_client.ACCIONES_PERMITIDAS)}"
            )
        return valor


def _estado_publico() -> dict:
    """Resumen de salud sin rutas de archivos ni métricas internas."""
    completo = health_checker.check_all()
    return {
        "status": completo.get("status", "desconocido"),
        "timestamp": completo.get("timestamp"),
        "components": {
            nombre: {"healthy": bool(datos.get("healthy", False))}
            for nombre, datos in completo.get("components", {}).items()
        },
    }


@app.get("/")
def home():
    """Panel web de JOEL."""
    if INDEX_FILE.is_file():
        return FileResponse(str(INDEX_FILE))
    return _info()


@app.get("/api/info")
def info():
    """Información básica del servidor (JSON)."""
    return _info()


def _info() -> dict:
    try:
        proveedor = providers_manager.obtener_proveedor_principal()
    except Exception:
        proveedor = "sin_configurar"
    return {
        "status": "Joel AI Web Server Online",
        "proveedor": proveedor,
        "version": "2.0",
    }


@app.get("/health")
def health_check():
    """Health check del sistema (sin secretos ni datos privados)."""
    return _estado_publico()


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response, request: Request):
    """Abre una sesión web usando la API key del propietario."""
    verificar_api_key(req.api_key)
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    seguro = proto.split(",")[0].strip().lower() == "https"
    token = crear_sesion()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        secure=seguro,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    logger.info("Sesión web iniciada")
    return {"ok": True, "expira_en": SESSION_TTL_SECONDS}


@app.post("/api/auth/logout")
def logout(
    response: Response,
    joel_session: Optional[str] = Cookie(None),
):
    """Cierra la sesión web actual."""
    cerrar_sesion(joel_session)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/session")
def estado_sesion(joel_session: Optional[str] = Cookie(None)):
    """Indica si el navegador tiene una sesión válida."""
    return {"autenticado": sesion_valida(joel_session)}


@app.get("/api/metrics")
def metrics(_: str = Depends(requerir_acceso)):
    """Métricas de proveedores y salud del sistema."""
    try:
        return {
            "providers": providers_manager.obtener_metricas(),
            "health": health_checker.check_all(),
        }
    except Exception as error:
        logger.error("Error en /api/metrics: %s", error)
        raise HTTPException(status_code=500, detail="Error al obtener métricas") from error


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest, _: str = Depends(requerir_acceso)):
    """Conversación con el cerebro de JOEL."""
    check_rate_limit(f"chat:{req.user_id}")
    try:
        logger.info("Petición /api/chat de %s", req.user_id)
        reply = procesar_respuesta_joel(req.user_id, req.message)
        return {"response": reply}
    except Exception as error:
        logger.error("Error en /api/chat: %s", error)
        raise HTTPException(status_code=500, detail="Error interno de Joel") from error


@app.get("/api/minecraft/status")
def minecraft_status(_: str = Depends(requerir_acceso)):
    """Estado real del bot de Minecraft."""
    return minecraft_client.estado()


@app.post("/api/minecraft/control")
def minecraft_control(
    req: MinecraftControlRequest,
    _: str = Depends(requerir_acceso),
):
    """Ejecuta una orden permitida sobre el bot de Minecraft."""
    check_rate_limit("minecraft:control")
    resultado = minecraft_client.ejecutar(req.accion)
    if not resultado["ok"] and resultado["estado"] == "no_disponible":
        raise HTTPException(status_code=503, detail=resultado["mensaje"])
    return resultado


@app.get("/api/minecraft/servidor")
def minecraft_servidor_estado(_: str = Depends(requerir_acceso)):
    """Estado del servidor local de Minecraft (Paper)."""
    return minecraft_server.estado()


@app.post("/api/minecraft/servidor/iniciar")
def minecraft_servidor_iniciar(_: str = Depends(requerir_acceso)):
    """Arranca el servidor local de Minecraft con su orden fija."""
    check_rate_limit("minecraft:servidor")
    resultado = minecraft_server.iniciar()
    if not resultado["ok"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=resultado["mensaje"])
    return resultado


@app.post("/api/minecraft/servidor/detener")
def minecraft_servidor_detener(_: str = Depends(requerir_acceso)):
    """Detiene el servidor local de Minecraft guardando el mundo."""
    check_rate_limit("minecraft:servidor")
    resultado = minecraft_server.detener()
    if not resultado["ok"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=resultado["mensaje"])
    return resultado


@app.get("/api/roblox/status")
def roblox_status(_: str = Depends(requerir_acceso)):
    """Comprueba si Roblox Studio está instalado."""
    return roblox_client.estado()


@app.post("/api/roblox/open")
def roblox_open(_: str = Depends(requerir_acceso)):
    """Abre Roblox Studio si está instalado."""
    resultado = roblox_client.abrir()
    if not resultado["ok"]:
        raise HTTPException(status_code=409, detail=resultado["mensaje"])
    return resultado


@app.get("/api/system/status")
def system_status(_: str = Depends(requerir_acceso)):
    """Estado de los servicios locales de JOEL."""
    return system_manager.estado_servicios()


@app.post("/api/system/minecraft/start")
def system_minecraft_start(_: str = Depends(requerir_acceso)):
    """Arranca el bot de Minecraft (orden fija 'node bot.js')."""
    resultado = system_manager.iniciar_minecraft_bot()
    if not resultado["ok"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=resultado["mensaje"])
    return resultado


@app.post("/api/system/minecraft/stop")
def system_minecraft_stop(_: str = Depends(requerir_acceso)):
    """Detiene el bot de Minecraft si lo inició este panel."""
    resultado = system_manager.detener_minecraft_bot()
    if not resultado["ok"]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=resultado["mensaje"])
    return resultado


def _pid_telegram_activo(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _iniciar_telegram_en_segundo_plano() -> None:
    """Arranca Telegram en segundo plano. Un fallo aquí NUNCA cierra la web."""
    if not debe_iniciar_telegram():
        logger.info("JOEL_START_TELEGRAM desactivado: no se lanza bot_telegram.py")
        return
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logger.warning("Sin TELEGRAM_BOT_TOKEN: el panel web arranca, Telegram no.")
        return
    script = BASE_DIR / "bot_telegram.py"
    if not script.is_file():
        logger.warning("No se encontró bot_telegram.py; el panel web arranca igual.")
        return
    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    pid_file = logs_dir / "telegram.pid"
    if pid_file.is_file():
        try:
            pid_previo = int(pid_file.read_text(encoding="utf-8").strip())
        except ValueError:
            pid_previo = 0
        if pid_previo and _pid_telegram_activo(pid_previo):
            logger.warning(
                "Ya hay un bot de Telegram (pid %s). No se lanza otro polling.",
                pid_previo,
            )
            return
    try:
        log_telegram = open(logs_dir / "telegram_nube.log", "a", encoding="utf-8")
        proceso = subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(BASE_DIR),
            stdout=log_telegram,
            stderr=log_telegram,
        )
        pid_file.write_text(str(proceso.pid), encoding="utf-8")
        logger.info("Bot de Telegram en segundo plano (pid %s)", proceso.pid)
    except Exception as error:
        logger.error("Telegram no arrancó; el panel web sigue: %s", error)


if __name__ == "__main__":
    import uvicorn
    _iniciar_telegram_en_segundo_plano()
    host = obtener_host_web()
    puerto = obtener_puerto_web()
    logger.info("Panel web escuchando en %s:%s", host, puerto)
    uvicorn.run(app, host=host, port=puerto, log_level="info")
