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
            if not connection.execute("SELECT 1 FROM schema_migrations WHERE version=2").fetchone():
                connection.execute(
                    "CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                    "display_name TEXT NOT NULL, password_hash TEXT NOT NULL, created_at INTEGER NOT NULL)"
                )
                connection.execute(
                    "CREATE TABLE workspaces (id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
                )
                connection.execute("INSERT INTO workspaces VALUES (1, 'Shared Workspace')")
                connection.execute(
                    "CREATE TABLE memberships (workspace_id INTEGER NOT NULL REFERENCES workspaces(id), "
                    "user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, "
                    "PRIMARY KEY(workspace_id, user_id))"
                )
                connection.execute(
                    "CREATE TABLE sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL "
                    "REFERENCES users(id) ON DELETE CASCADE, expires_at INTEGER NOT NULL, "
                    "created_at INTEGER NOT NULL)"
                )
                connection.execute("CREATE INDEX sessions_expiry ON sessions(expires_at)")
                connection.execute("INSERT INTO schema_migrations(version) VALUES (2)")
            if not connection.execute("SELECT 1 FROM schema_migrations WHERE version=3").fetchone():
                statements = (
                    "CREATE TABLE documents (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id), name TEXT NOT NULL, source_key TEXT, created_at INTEGER NOT NULL, UNIQUE(owner_id, source_key))",
                    "CREATE TABLE revisions (id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE, number INTEGER NOT NULL, content_hash TEXT NOT NULL, size INTEGER NOT NULL, status TEXT NOT NULL, reason TEXT, original_file TEXT, sanitized_file TEXT, finding_count INTEGER NOT NULL DEFAULT 0, cached INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL, UNIQUE(document_id, number))",
                    "CREATE INDEX revisions_queue ON revisions(status, created_at)",
                    "CREATE TABLE assessments (content_hash TEXT PRIMARY KEY, result_json TEXT NOT NULL, created_at INTEGER NOT NULL)",
                    "CREATE TABLE identities (kind TEXT NOT NULL, identity TEXT NOT NULL, alias TEXT NOT NULL UNIQUE, PRIMARY KEY(kind, identity))",
                    "CREATE TABLE ai_usage (day TEXT PRIMARY KEY, reserved_microdollars INTEGER NOT NULL DEFAULT 0, requests INTEGER NOT NULL DEFAULT 0)",
                )
                for statement in statements:
                    connection.execute(statement)
                connection.execute("INSERT INTO schema_migrations(version) VALUES (3)")
    finally:
        connection.close()
