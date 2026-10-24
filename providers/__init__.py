from __future__ import annotations

from typing import Any

from .models import CategoriaMemoria, Memoria
from .storage import MemoryStorage


class MemoryManager:
    def __init__(self, storage: MemoryStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def inicializar(self) -> None:
        self.storage._init_db()

    def guardar(self, user_id: str, categoria: CategoriaMemoria | str, contenido: str):
        memoria_id = self.storage.guardar(user_id, str(categoria), contenido)
        row = self.storage.obtener(memoria_id, user_id)
        return Memoria(
            id=row["id"],
            user_id=row["user_id"],
            categoria=row["categoria"],
            contenido=row["contenido"],
            activo=bool(row["activo"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def obtener(self, memoria_id: int, user_id: str):
        row = self.storage.obtener(memoria_id, user_id)
        if row is None:
            return None
        return Memoria(
            id=row["id"],
            user_id=row["user_id"],
            categoria=row["categoria"],
            contenido=row["contenido"],
            activo=bool(row["activo"]),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def listar(self, user_id: str, limite: int = 20, solo_activos: bool = True):
        rows = self.storage.listar(user_id, limite, solo_activos)
        return [Memoria(**{**r, "activo": bool(r["activo"])}) for r in rows]

    def buscar_texto(self, user_id: str, texto: str, limite: int = 20):
        rows = self.storage.buscar_texto(user_id, texto, limite)
        return [Memoria(**{**r, "activo": bool(r["activo"])}) for r in rows]

    def actualizar(self, memoria: Memoria):
        return self.storage.actualizar(memoria.id, memoria.user_id, memoria.contenido)

    def eliminar(self, memoria_id: int, user_id: str):
        return self.storage.eliminar(memoria_id, user_id)

    def guardar_preferencia(self, user_id: str, clave: str, valor: str):
        return self.guardar(user_id, CategoriaMemoria.PREFERENCIA, f"{clave}: {valor}")

    def obtener_preferencias(self, user_id: str):
        return self.buscar_texto(user_id, ":", limite=50)

    def guardar_recordatorio(self, user_id: str, texto: str):
        return self.guardar(user_id, CategoriaMemoria.RECORDATORIO, texto)

    def obtener_recordatorios(self, user_id: str):
        return self.buscar_texto(user_id, "", limite=50)

    def obtener_contexto(self, user_id: str, texto: str, limite: int = 5):
        return self.buscar_texto(user_id, texto, limite)

    def formatear_recuerdos_para_ia(self, user_id: str, texto: str, limite: int = 5):
        recuerdos = self.obtener_contexto(user_id, texto, limite)
        if not recuerdos:
            return ""
        return "\n".join(f"- {r.contenido}" for r in recuerdos)


memory_manager = MemoryManager()
