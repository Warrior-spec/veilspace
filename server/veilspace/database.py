import sqlite3
from pathlib import Path


def connect_database(data_dir: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(data_dir / "veilspace.db", timeout=15)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=15000")
    return connection


def initialize_database(data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for name in ("staging", "published", "logs"):
        (data_dir / name).mkdir(exist_ok=True)
    connection = connect_database(data_dir)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        with connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )
            connection.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)")
    finally:
        connection.close()
