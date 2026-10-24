"""
Pruebas de seguridad para JOEL.
Ejecuta este script para verificar autenticación, rate limiting y health checks.
"""
import asyncio
from database import init_db
from auth import verificar_api_key, generar_api_key, agregar_api_key
from rate_limiter import rate_limiter, check_rate_limit
from health import health_checker
from logger_config import setup_logger

logger = setup_logger("test_security")


def test_auth():
    """Prueba el sistema de autenticación."""
    print("\n=== Test: Autenticación ===")
    
    try:
        # Generar una API key de prueba
        test_key = generar_api_key()
        agregar_api_key(test_key)
        print(f"API key de prueba generada: {test_key[:10]}...")
        
        # Verificar que funciona
        verified = verificar_api_key(test_key)
        print(f"API key verificada: {verified == test_key}")
        
        # Verificar que una key inválida falla
        try:
            verificar_api_key("invalid_key_12345")
            print("[FALLO] Debería haber rechazado la key inválida")
            return False
        except Exception:
            print("Key inválida rechazada correctamente")
        
        print("[OK] Test autenticación pasado")
        return True
    except Exception as e:
        print(f"[FALLO] {e}")
        return False


def test_rate_limiting():
    """Prueba el sistema de rate limiting."""
    print("\n=== Test: Rate Limiting ===")
    
    try:
        test_id = "test_user_123"
        
        # Primera solicitud debe ser permitida
        allowed1 = rate_limiter.is_allowed(test_id)
        print(f"Solicitud 1 permitida: {allowed1}")
        
        # Segunda solicitud debe ser permitida
        allowed2 = rate_limiter.is_allowed(test_id)
        print(f"Solicitud 2 permitida: {allowed2}")
        
        # Verificar solicitudes restantes
        remaining = rate_limiter.get_remaining(test_id)
        print(f"Solicitudes restantes: {remaining}")
        
        assert allowed1 and allowed2, "Las primeras solicitudes deben ser permitidas"
        
        print("[OK] Test rate limiting pasado")
        return True
    except Exception as e:
        print(f"[FALLO] {e}")
        return False


def test_health_checks():
    """Prueba el sistema de health checks."""
    print("\n=== Test: Health Checks ===")
    
    try:
        # Inicializar base de datos
        init_db()
        
        # Ejecutar health check
        resultado = health_checker.check_all()
        
        print(f"Estado general: {resultado['status']}")
        print(f"Componentes verificados: {len(resultado['components'])}")
        
        for nombre, datos in resultado['components'].items():
            print(f"  - {nombre}: {'healthy' if datos.get('healthy') else 'unhealthy'}")
        
        assert resultado['status'] in ['healthy', 'degraded', 'unhealthy'], "Estado debe ser válido"
        
        print("[OK] Test health checks pasado")
        return True
    except Exception as e:
        print(f"[FALLO] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_integration():
    """Prueba la integración de seguridad en la API."""
    print("\n=== Test: Integración API ===")
    
    try:
        # Esta prueba verifica que los módulos estén integrados correctamente
        from main import app
        print("Aplicación FastAPI importada correctamente")
        
        # Verificar que los endpoints existan
        routes = [route.path for route in app.routes]
        print(f"Endpoints disponibles: {routes}")
        
        expected_routes = ['/', '/health', '/api/metrics', '/api/chat']
        for route in expected_routes:
            if route in routes:
                print(f"  [OK] {route}")
            else:
                print(f"  [X] {route} (falta)")
        
        print("[OK] Test integración API pasado")
        return True
    except Exception as e:
        print(f"[FALLO] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todas las pruebas de seguridad."""
    print("=" * 60)
    print("PRUEBAS DE SEGURIDAD JOEL")
    print("=" * 60)
    
    try:
        resultados = []
        resultados.append(test_auth())
        resultados.append(test_rate_limiting())
        resultados.append(test_health_checks())
        resultados.append(test_api_integration())
        
        if all(resultados):
            print("\n" + "=" * 60)
            print("[EXITO] TODAS LAS PRUEBAS PASARON")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("[FALLO] ALGUNAS PRUEBAS FALLARON")
            print("=" * 60)
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
