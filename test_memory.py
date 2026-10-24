from __future__ import annotations

from typing import Any

from .base import Mensaje, RespuestaProvider, TipoTarea
from .gemini import GeminiProvider
from .groq import GroqProvider


class ProvidersManager:
    def __init__(self) -> None:
        self.proveedores: dict[str, Any] = {}
        self.proveedor_principal: str | None = None

    def inicializar(self) -> None:
        self.proveedores = {}
        for provider in (GeminiProvider(), GroqProvider()):
            if provider.api_key:
                self.proveedores[provider.nombre] = provider
        self.proveedor_principal = next(iter(self.proveedores), None)

    def _seleccionar_proveedor(self, tipo_tarea: TipoTarea | None = None) -> str | None:
        if not self.proveedores:
            return None
        if tipo_tarea == TipoTarea.PROGRAMACION and "groq" in self.proveedores:
            return "groq"
        return next(iter(self.proveedores))

    def obtener_proveedor_principal(self) -> str | None:
        return self.proveedor_principal

    async def generar_respuesta(
        self,
        mensajes: list[Mensaje],
        system_prompt: str | None = None,
        tipo_tarea: TipoTarea | None = None,
    ) -> RespuestaProvider:
        if not self.proveedores:
            return RespuestaProvider(
                exito=False,
                contenido="",
                proveedor="sin_proveedor",
                modelo="sin_modelo",
                latencia_ms=0,
                error="No hay proveedores configurados (faltan claves API).",
            )
        nombre = self._seleccionar_proveedor(tipo_tarea)
        provider = self.proveedores[nombre]
        return await provider.generar(mensajes, system_prompt=system_prompt, tipo_tarea=tipo_tarea)

    def obtener_metricas(self) -> dict[str, Any]:
        return {
            "proveedores": list(self.proveedores.keys()),
            "proveedor_principal": self.proveedor_principal,
            "cantidad": len(self.proveedores),
        }


providers_manager = ProvidersManager()
