from __future__ import annotations

import os

from .base import BaseProvider, Mensaje, RespuestaProvider, TipoTarea


class GroqProvider(BaseProvider):
    nombre = "groq"
    modelo = "llama-3.1-8b-instant"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or os.getenv("GROQ_API_KEY", ""))

    async def generar(
        self,
        mensajes: list[Mensaje],
        system_prompt: str | None = None,
        tipo_tarea: TipoTarea | None = None,
    ) -> RespuestaProvider:
        if not self.api_key:
            return RespuestaProvider(
                exito=False,
                contenido="",
                proveedor=self.nombre,
                modelo=self.modelo,
                latencia_ms=0,
                error="Falta GROQ_API_KEY",
            )
        text = " ".join(m.content for m in mensajes)
        return RespuestaProvider(
            exito=True,
            contenido=f"[Groq] {text[:200]}",
            proveedor=self.nombre,
            modelo=self.modelo,
            latencia_ms=120,
        )
