import os
import secrets
import time
from typing import Optional

from fastapi import Cookie, Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv(override=True)

SESSION_COOKIE = "joel_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
_SESIONES: dict[str, dict] = {}

API_KEY = (os.getenv("API_KEY") or "").strip()


def _log_error(message: str) -> None:
    pass


def crear_sesion() -> str:
    token = secrets.token_urlsafe(32)
    _SESIONES[token] = {"created_at": time.time(), "expires_at": time.time() + SESSION_TTL_SECONDS}
    return token


def sesion_valida(token: Optional[str]) -> bool:
    if not token:
        return False
    session = _SESIONES.get(token)
    if not session:
        return False
    if time.time() > session["expires_at"]:
        _SESIONES.pop(token, None)
        return False
    return True


def cerrar_sesion(token: Optional[str]) -> None:
    if token:
        _SESIONES.pop(token, None)


def verificar_api_key(api_key: Optional[str]) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_KEY no configurada. Configure la variable de entorno.",
        )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta la API key.",
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key incorrecta.",
        )


def requerir_acceso(
    api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    joel_session: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE),
) -> str:
    if api_key:
        verificar_api_key(api_key)
        return api_key
    if sesion_valida(joel_session):
        return joel_session
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Se requiere X-API-Key o sesión válida.",
    )
