import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "joel_memoria.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recuerdos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                categoria TEXT NOT NULL,
                contenido TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def guardar_mensaje(user_id: str, role: str, content: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        conn.commit()


def obtener_historial(user_id: str, limite: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM chat_history
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, int(limite)),
        ).fetchall()
    return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def guardar_recuerdo(user_id: str, categoria: str, contenido: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO recuerdos (user_id, categoria, contenido) VALUES (?, ?, ?)",
            (user_id, categoria, contenido),
        )
        conn.commit()


def obtener_recuerdos(user_id: str, limite: int = 20) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, categoria, contenido, activo, created_at, updated_at
            FROM recuerdos
            WHERE user_id = ? AND activo = 1
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, int(limite)),
        ).fetchall()
    return [dict(row) for row in rows]
