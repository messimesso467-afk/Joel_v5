from enum import Enum
class CategoriaMemoria(str, Enum):
    PREFERENCIA = "preferencia"
    PROYECTO = "proyecto"
    RECORDATORIO = "recordatorio"
    INSTRUCCION = "instruccion"
    DATO = "dato"
    TAREA = "tarea"
class _MemoryManager:
    def guardar(self, *a, **k): pass
    def buscar(self, *a, **k): return []
    def listar_por_categoria(self, *a, **k): return []
    def obtener_preferencias(self, *a, **k): return {}
    def eliminar(self, *a, **k): pass
memory_manager = _MemoryManager()
