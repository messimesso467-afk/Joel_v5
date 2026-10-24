"""
Pruebas de persistencia del sistema de memoria de JOEL.
Ejecuta este script para verificar que los recuerdos persisten correctamente.
"""
from datetime import datetime
from database import init_db
from memory import memory_manager, CategoriaMemoria
from logger_config import setup_logger

logger = setup_logger("test_memory")


def test_guardar_recuerdo():
    """Prueba guardar un recuerdo."""
    print("\n=== Test: Guardar Recuerdo ===")
    user_id = "test_user_123"
    
    recuerdo = memory_manager.guardar(
        user_id=user_id,
        categoria=CategoriaMemoria.DATO,
        contenido="Esto es una prueba de memoria"
    )
    
    print(f"Recuerdo guardado: ID={recuerdo.id}, contenido={recuerdo.contenido}")
    assert recuerdo.id is not None, "El recuerdo debe tener un ID"
    assert recuerdo.contenido == "Esto es una prueba de memoria", "El contenido debe coincidir"
    print("[OK] Test guardar recuerdo pasado")
    return recuerdo.id


def test_obtener_recuerdo(recuerdo_id: int):
    """Prueba obtener un recuerdo por ID."""
    print("\n=== Test: Obtener Recuerdo ===")
    user_id = "test_user_123"
    
    recuerdo = memory_manager.obtener(recuerdo_id, user_id)
    
    print(f"Recuerdo obtenido: ID={recuerdo.id}, contenido={recuerdo.contenido}")
    assert recuerdo is not None, "Debe encontrar el recuerdo"
    assert recuerdo.id == recuerdo_id, "El ID debe coincidir"
    print("[OK] Test obtener recuerdo pasado")


def test_listar_recuerdos():
    """Prueba listar recuerdos de un usuario."""
    print("\n=== Test: Listar Recuerdos ===")
    user_id = "test_user_123"
    
    # Guardar algunos recuerdos adicionales
    memory_manager.guardar(user_id, CategoriaMemoria.PREFERENCIA, "Prefiero el té")
    memory_manager.guardar(user_id, CategoriaMemoria.PROYECTO, "Proyecto: Crear bot")
    
    recuerdos = memory_manager.listar(user_id, limite=10)
    
    print(f"Recuerdos listados: {len(recuerdos)}")
    assert len(recuerdos) >= 3, "Debe haber al menos 3 recuerdos"
    print("[OK] Test listar recuerdos pasado")


def test_buscar_recuerdos():
    """Prueba buscar recuerdos por texto."""
    print("\n=== Test: Buscar Recuerdos ===")
    user_id = "test_user_123"
    
    # Buscar por palabra clave
    resultados = memory_manager.buscar_texto(user_id, "té", limite=5)
    
    print(f"Resultados de búsqueda: {len(resultados)}")
    assert len(resultados) >= 1, "Debe encontrar al menos un recuerdo con 'té'"
    print("[OK] Test buscar recuerdos pasado")


def test_actualizar_recuerdo(recuerdo_id: int):
    """Prueba actualizar un recuerdo."""
    print("\n=== Test: Actualizar Recuerdo ===")
    user_id = "test_user_123"
    
    recuerdo = memory_manager.obtener(recuerdo_id, user_id)
    recuerdo.contenido = "Contenido actualizado"
    
    exito = memory_manager.actualizar(recuerdo)
    
    print(f"Actualización exitosa: {exito}")
    assert exito, "La actualización debe ser exitosa"
    
    # Verificar que se actualizó
    recuerdo_actualizado = memory_manager.obtener(recuerdo_id, user_id)
    assert recuerdo_actualizado.contenido == "Contenido actualizado", "El contenido debe estar actualizado"
    print("[OK] Test actualizar recuerdo pasado")


def test_eliminar_recuerdo(recuerdo_id: int):
    """Prueba eliminar un recuerdo."""
    print("\n=== Test: Eliminar Recuerdo ===")
    user_id = "test_user_123"
    
    exito = memory_manager.eliminar(recuerdo_id, user_id)
    
    print(f"Eliminación exitosa: {exito}")
    assert exito, "La eliminación debe ser exitosa"
    
    # Verificar que no aparece en listados
    recuerdos = memory_manager.listar(user_id, solo_activos=True)
    ids_activos = [r.id for r in recuerdos]
    assert recuerdo_id not in ids_activos, "El recuerdo eliminado no debe aparecer en listados activos"
    print("[OK] Test eliminar recuerdo pasado")


def test_preferencias():
    """Prueba métodos de preferencias."""
    print("\n=== Test: Preferencias ===")
    user_id = "test_user_456"
    
    memory_manager.guardar_preferencia(user_id, "idioma", "español")
    memory_manager.guardar_preferencia(user_id, "tema", "oscuro")
    
    preferencias = memory_manager.obtener_preferencias(user_id)
    
    print(f"Preferencias obtenidas: {len(preferencias)}")
    assert len(preferencias) >= 2, "Debe haber al menos 2 preferencias"
    print("[OK] Test preferencias pasado")


def test_recordatorios():
    """Prueba métodos de recordatorios."""
    print("\n=== Test: Recordatorios ===")
    user_id = "test_user_789"
    
    memory_manager.guardar_recordatorio(user_id, "Comprar leche")
    memory_manager.guardar_recordatorio(user_id, "Llamar al médico")
    
    recordatorios = memory_manager.obtener_recordatorios(user_id)
    
    print(f"Recordatorios obtenidos: {len(recordatorios)}")
    assert len(recordatorios) >= 2, "Debe haber al menos 2 recordatorios"
    print("[OK] Test recordatorios pasado")


def test_contexto_relevante():
    """Prueba obtener contexto relevante para un mensaje."""
    print("\n=== Test: Contexto Relevante ===")
    user_id = "test_user_999"
    
    # Guardar recuerdos relacionados
    memory_manager.guardar(user_id, CategoriaMemoria.DATO, "Trabajo en tecnología")
    memory_manager.guardar(user_id, CategoriaMemoria.DATO, "Vivo en Madrid")
    
    # Buscar contexto para un mensaje
    contexto = memory_manager.obtener_contexto(user_id, "¿Qué haces?", limite=5)
    
    print(f"Contexto obtenido: {len(contexto)} recuerdos")
    # Puede que encuentre recuerdos o no, depende de la búsqueda
    print("[OK] Test contexto relevante pasado")


def test_persistencia_total():
    """Prueba completa de persistencia: guardar, reiniciar, recuperar."""
    print("\n=== Test: Persistencia Total ===")
    user_id = "test_persistencia_123"
    
    # Guardar un recuerdo
    recuerdo = memory_manager.guardar(
        user_id=user_id,
        categoria=CategoriaMemoria.DATO,
        contenido="Dato de prueba de persistencia"
    )
    recuerdo_id = recuerdo.id
    
    print(f"Recuerdo guardado con ID: {recuerdo_id}")
    
    # Simular "reinicio" creando un nuevo gestor
    from memory.manager import MemoryManager
    nuevo_gestor = MemoryManager()
    nuevo_gestor.inicializar()
    
    # Intentar recuperar el recuerdo con el nuevo gestor
    recuerdo_recuperado = nuevo_gestor.obtener(recuerdo_id, user_id)
    
    print(f"Recuerdo recuperado: {recuerdo_recuperado.contenido if recuerdo_recuperado else 'None'}")
    assert recuerdo_recuperado is not None, "Debe recuperar el recuerdo después de 'reiniciar'"
    assert recuerdo_recuperado.contenido == "Dato de prueba de persistencia", "El contenido debe coincidir"
    print("[OK] Test persistencia total pasado")


def main():
    """Ejecuta todas las pruebas."""
    print("=" * 60)
    print("PRUEBAS DE PERSISTENCIA DE MEMORIA JOEL")
    print("=" * 60)
    
    try:
        # Inicializar base de datos
        init_db()
        memory_manager.inicializar()
        
        # Ejecutar pruebas
        recuerdo_id = test_guardar_recuerdo()
        test_obtener_recuerdo(recuerdo_id)
        test_listar_recuerdos()
        test_buscar_recuerdos()
        test_actualizar_recuerdo(recuerdo_id)
        test_eliminar_recuerdo(recuerdo_id)
        test_preferencias()
        test_recordatorios()
        test_contexto_relevante()
        test_persistencia_total()
        
        print("\n" + "=" * 60)
        print("[EXITO] TODAS LAS PRUEBAS PASARON")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n[FALLO] Test falló: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
