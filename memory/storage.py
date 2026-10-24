from __future__ import annotations

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "joel_memoria.db"


class MemoryStorage:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
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

    def guardar(self, user_id: str, categoria: str, contenido: str):
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO recuerdos (user_id, categoria, contenido) VALUES (?, ?, ?)",
                (user_id, categoria, contenido),
            )
            conn.commit()
            return cursor.lastrowid

    def obtener(self, memoria_id: int, user_id: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM recuerdos WHERE id = ? AND user_id = ?",
                (memoria_id, user_id),
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def listar(self, user_id: str, limite: int = 20, solo_activos: bool = True):
        with self._connect() as conn:
            query = "SELECT * FROM recuerdos WHERE user_id = ?"
            params = [user_id]
            if solo_activos:
                query += " AND activo = 1"
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limite)
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def buscar_texto(self, user_id: str, texto: str, limite: int = 20):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM recuerdos
                WHERE user_id = ? AND activo = 1 AND LOWER(contenido) LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, f"%{texto.lower()}%", limite),
            ).fetchall()
        return [dict(r) for r in rows]

    def actualizar(self, memoria_id: int, user_id: str, contenido: str):
        with self._connect() as conn:
            updated = conn.execute(
                "UPDATE recuerdos SET contenido = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (contenido, memoria_id, user_id),
            )
            conn.commit()
        return updated.rowcount > 0

    def eliminar(self, memoria_id: int, user_id: str):
        with self._connect() as conn:
            deleted = conn.execute(
                "UPDATE recuerdos SET activo = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (memoria_id, user_id),
            )
            conn.commit()
        return deleted.rowcount > 0

    def guardar_preferencia(self, user_id: str, clave: str, valor: str):
        return self.guardar(user_id, "preferencia", f"{clave}: {valor}")

    def obtener_preferencias(self, user_id: str):
        return self.buscar_texto(user_id, "", limite=100)


__all__ = ["MemoryStorage"]
