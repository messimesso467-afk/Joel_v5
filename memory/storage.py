from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CategoriaMemoria(str, Enum):
    PREFERENCIA = "preferencia"
    PROYECTO = "proyecto"
    RECORDATORIO = "recordatorio"
    INSTRUCCION = "instruccion"
    DATO = "dato"
    TAREA = "tarea"


@dataclass
class Memoria:
    user_id: str
    categoria: CategoriaMemoria | str
    contenido: str
    activo: bool = True
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
