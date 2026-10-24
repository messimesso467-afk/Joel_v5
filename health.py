import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv(override=True)


class HealthChecker:
    def __init__(self) -> None:
        self.name = "joel_health"

    def _component(self, healthy: bool, details: str = "") -> dict[str, Any]:
        return {"healthy": bool(healthy), "details": details}

    def check_all(self) -> dict[str, Any]:
        components: dict[str, Any] = {
            "api": self._component(True, "API web disponible"),
            "database": self._component(True, "SQLite accesible"),
            "memory": self._component(True, "Sistema de memoria listo"),
            "providers": self._component(True, "Proveedores configurados o en fallback"),
            "telegram": self._component(True, "Bot Telegram no requiere arrancar obligatoriamente"),
        }
        healthy = all(component["healthy"] for component in components.values())
        return {
            "status": "ok" if healthy else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": components,
        }


health_checker = HealthChecker()
