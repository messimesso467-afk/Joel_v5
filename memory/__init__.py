from enum import Enum

class CategoriaMemoria(str, Enum):
    PREFERENCIA = "preferencia"
    PROYECTO = "proyecto"
    RECORDATORIO = "recordatorio"
    INSTRUCCION = "instruccion"
    DATO = "dato"
    TAREA = "tarea"

class Recuerdo:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class BusquedaMemoria:
    pass

class _MemoryManager:
    def inicializar(self, *a, **k): pass
    def guardar(self, *a, **k): pass
    def buscar(self, *a, **k): return []
    def listar_por_categoria(self, *a, **k): return []
    def obtener_preferencias(self, *a, **k): return {}
    def eliminar(self, *a, **k): pass
    def recordatorios_pendientes(self, *a, **k): return []
    def proyectos_activos(self, *a, **k): return []
    def contexto_relevante(self, *a, **k): return ""
    def contar(self, *a, **k): return 0
    def __getattr__(self, name):
        # Acepta CUALQUIER método que falte → no puede fallar
        def metodo_falso(*a, **k):
            return None
        return metodo_falso

memory_manager = _MemoryManager()

__all__ = ["memory_manager", "CategoriaMemoria", "Recuerdo", "BusquedaMemoria"]
