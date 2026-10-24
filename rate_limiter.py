"""
Sistema de rate limiting para JOEL.
"""
import time
from collections import defaultdict
from typing import Dict
from fastapi import HTTPException, status

from logger_config import setup_logger

logger = setup_logger("rate_limiter")


class RateLimiter:
    """Limitador de tasa de solicitudes."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Inicializa el limitador.
        
        Args:
            max_requests: Máximo de solicitudes permitidas
            window_seconds: Ventana de tiempo en segundos
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """
        Verifica si una solicitud está permitida.
        
        Args:
            identifier: Identificador único (IP, API key, etc.)
        
        Returns:
            True si la solicitud está permitida
        """
        now = time.time()
        
        # Obtener solicitudes anteriores del identificador
        user_requests = self.requests[identifier]
        
        # Eliminar solicitudes fuera de la ventana
        self.requests[identifier] = [
            req_time for req_time in user_requests
            if now - req_time < self.window_seconds
        ]
        
        # Verificar si excede el límite
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit excedido para {identifier}")
            return False
        
        # Registrar esta solicitud
        self.requests[identifier].append(now)
        return True
    
    def get_remaining(self, identifier: str) -> int:
        """
        Obtiene el número de solicitudes restantes.
        
        Args:
            identifier: Identificador único
        
        Returns:
            Número de solicitudes restantes
        """
        now = time.time()
        user_requests = self.requests[identifier]
        
        # Contar solicitudes en la ventana
        in_window = sum(
            1 for req_time in user_requests
            if now - req_time < self.window_seconds
        )
        
        return max(0, self.max_requests - in_window)
    
    def reset(self, identifier: str):
        """
        Resetea el contador para un identificador.
        
        Args:
            identifier: Identificador único
        """
        if identifier in self.requests:
            del self.requests[identifier]
            logger.info(f"Rate limit reseteado para {identifier}")


# Instancia global del rate limiter
rate_limiter = RateLimiter(max_requests=60, window_seconds=60)


def check_rate_limit(identifier: str):
    """
    Verifica el rate limit y lanza excepción si excede.
    
    Args:
        identifier: Identificador único
    
    Raises:
        HTTPException: Si excede el rate limit
    """
    if not rate_limiter.is_allowed(identifier):
        remaining = rate_limiter.get_remaining(identifier)
        reset_time = rate_limiter.window_seconds
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit excedido",
                "remaining": remaining,
                "reset_after": reset_time,
            },
        )
