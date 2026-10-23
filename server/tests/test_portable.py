import socket
import subprocess
import sys

from fastapi.testclient import TestClient

from veilspace.config import Settings
from veilspace.database import connect_database, initialize_database
from veilspace.main import create_app


def test_initialization_preserves_existing_data(tmp_path):
    data = tmp_path / "data"
    initialize_database(data)
    with connect_database(data) as connection:
        connection.execute("CREATE TABLE sample(value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('preserved')")
    initialize_database(data)
    with connect_database(data) as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "preserved"
        assert connection.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_private_storage_is_not_served(tmp_path):
    settings = Settings(environment="production", data_dir=tmp_path)
    with TestClient(create_app(settings)) as client:
        (tmp_path / "staging" / "private.txt").write_text("private")
        assert client.get("/").status_code == 200
        assert client.get("/staging/private.txt").status_code == 404
        assert client.get("/veilspace.db").status_code == 404


def test_launcher_initializes_without_network(tmp_path):
    data = tmp_path / "portable"
    result = subprocess.run(
        [sys.executable, "-m", "veilspace.launcher", "--data-dir", str(data), "--initialize-only"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "Database ready." in result.stdout
    assert (data / "veilspace.db").is_file()


def test_launcher_reports_occupied_port(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        result = subprocess.run(
            [sys.executable, "-m", "veilspace.launcher", "--host", "127.0.0.1",
             "--port", str(port), "--data-dir", str(tmp_path), "--no-firewall", "--no-public-ip"],
            capture_output=True, text=True, timeout=15,
        )
    assert result.returncode == 1
    assert "Cannot listen" in result.stderr
