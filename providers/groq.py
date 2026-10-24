from __future__ import annotations

import os

from .base import BaseProvider, Mensaje, RespuestaProvider, TipoTarea


class GeminiProvider(BaseProvider):
    nombre = "gemini"
    modelo = "gemini-2.0-flash"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or os.getenv("GEMINI_API_KEY", ""))

    async def generar(self, mensajes: list[Mensaje], system_prompt: str | None = None, tipo_tarea: TipoTarea | None = None) -> RespuestaProvider:
        if not self.api_key:
            return RespuestaProvider(
                exito=False,
                contenido="",
                proveedor=self.nombre,
                modelo=self.modelo,
                latencia_ms=0,
                error="Falta GEMINI_API_KEY",
            )
        text = " ".join(m.content for m in mensajes)
        return RespuestaProvider(
            exito=True,
            contenido=f"[Gemini] {text[:200]}",
            proveedor=self.nombre,
            modelo=self.modelo,
            latencia_ms=100,
        )
