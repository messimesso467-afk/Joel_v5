from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TipoTarea(str, Enum):
    CHAT_GENERAL = "chat_general"
    PROGRAMACION = "programacion"
    ANALISIS = "analisis"
    CREATIVO = "creativo"
    RAZONAMIENTO = "razonamiento"
    RESUMEN = "resumen"


@dataclass
class Mensaje:
    role: str
    content: str


@dataclass
class RespuestaProvider:
    exito: bool
    contenido: str
    proveedor: str
    modelo: str
    latencia_ms: float
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseProvider:
    nombre: str = "base"
    modelo: str = "base-model"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or ""

    async def generar(
        self,
        mensajes: list[Mensaje],
        system_prompt: str | None = None,
        tipo_tarea: TipoTarea | None = None,
    ) -> RespuestaProvider:
        raise NotImplementedError


__all__ = ["TipoTarea", "Mensaje", "RespuestaProvider", "BaseProvider"]
