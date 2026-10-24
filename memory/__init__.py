#!/usr/bin/env python3
"""Verificador rápido de dependencias y configuración de JOEL."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _check_python() -> tuple[bool, str]:
    return (True, f"Python {sys.version.split()[0]}")


def _check_file(path: str) -> tuple[bool, str]:
    file_path = BASE_DIR / path
    return (file_path.exists(), str(file_path))


def main() -> int:
    checks = []
    checks.append(("Python", *_check_python()))
    checks.append(("main.py", *_check_file("main.py")))
    checks.append(("requirements.txt", *_check_file("requirements.txt")))
    checks.append((".env", *_check_file(".env")))
    checks.append(("API_KEY", bool(os.getenv("API_KEY", "").strip()), "API_KEY configurada"))
    checks.append(("TELEGRAM_BOT_TOKEN", bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip()), "Token de Telegram"))
    checks.append(("GROQ_API_KEY", bool(os.getenv("GROQ_API_KEY", "").strip()), "Clave de Groq"))
    checks.append(("GEMINI_API_KEY", bool(os.getenv("GEMINI_API_KEY", "").strip()), "Clave de Gemini"))

    print("Verificación de dependencias JOEL")
    print("-" * 40)
    ok = True
    for name, present, detail in checks:
        mark = "OK" if present else "FALTA"
        print(f"[{mark}] {name}: {detail}")
        if not present and name not in {"Python", "main.py", "requirements.txt"}:
            ok = False

    if not ok:
        print("\nNo todo está configurado. Puedes crear .env a partir de .env.example o variables de entorno.")
        return 1

    print("\nTodo parece estar listo para arrancar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
