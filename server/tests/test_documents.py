from contextlib import closing
import io

from fastapi.testclient import TestClient
from pypdf import PdfReader
import pytest

from veilspace.assessment import Assessment, Finding
from veilspace.config import Settings
from veilspace.database import connect_database
from veilspace.main import create_app


@pytest.fixture
def workspace(tmp_path):
    settings = Settings(data_dir=tmp_path, worker_enabled=False, OPENAI_API_KEY="test-key")
    with TestClient(create_app(settings)) as client:
        calls = []
        def assess(text, key):
            calls.append(text)
            return Assessment(findings=[Finding(text="Alice Khan", kind="person")], needs_review=False, note="")
        client.app.state.processor.assessor = assess
        first = client.post("/api/auth/register", json={"email": "first@example.com", "display_name": "First Member", "password": "DocumentDemo2026!"}).json()
        second = client.post("/api/auth/register", json={"email": "second@example.com", "display_name": "Second Member", "password": "DocumentDemo2026!"}).json()
        yield client, {"Authorization": "Bearer " + first["access_token"]}, {"Authorization": "Bearer " + second["access_token"]}, calls


def upload(client, headers, text="Alice Khan, alice@example.com", filename="private.txt"):
    return client.post("/api/documents", params={"filename": filename}, content=text.encode(), headers=headers)


def test_pipeline_publishes_only_redacted_pdf_and_removes_original(workspace):
    client, first, second, calls = workspace
    response = upload(client, first)
    assert response.status_code == 202
    identifier = response.json()["id"]
    assert client.get("/api/documents/shared", headers=second).json() == []
    assert client.get(f"/api/documents/{identifier}/download", headers=second).status_code == 404
    assert client.app.state.processor.process_once()
    shared = client.get("/api/documents/shared", headers=second).json()
    assert len(shared) == 1
    assert shared[0]["name"].startswith("Document-")
    pdf = client.get(f"/api/documents/{identifier}/download", headers=second)
    assert pdf.status_code == 200
    text = "".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "Alice Khan" not in text and "alice@example.com" not in text
    assert "Person-001" in text and "EMAIL REMOVED" in text
    preview = client.get(f"/api/documents/{identifier}/preview", headers=second)
    assert preview.status_code == 200
    assert "Person-001" in preview.json()["text"] and "Alice Khan" not in preview.json()["text"]
    assert not list((client.app.state.settings.data_dir / "staging").iterdir())
    assert len(calls) == 1


def test_duplicate_content_and_cross_member_cache_avoid_more_ai_calls(workspace):
    client, first, second, calls = workspace
    original = upload(client, first).json()
    client.app.state.processor.process_once()
    duplicate = upload(client, first).json()
    assert duplicate["duplicate"] and duplicate["id"] == original["id"]
    upload(client, second)
    client.app.state.processor.process_once()
    assert len(calls) == 1
    assert client.get("/api/documents", headers=second).json()[0]["cached"] == 1


def test_revisions_keep_previous_publication_while_new_version_is_pending(workspace):
    client, first, second, _ = workspace
    original = upload(client, first).json()
    client.app.state.processor.process_once()
    changed = upload(client, first, "Alice Khan has an updated report").json()
    assert changed["id"] == original["id"] and changed["revision"] == 2
    assert client.get("/api/documents/shared", headers=second).json()[0]["revision"] == 1
    client.app.state.processor.process_once()
    assert client.get("/api/documents/shared", headers=second).json()[0]["revision"] == 2
    assert client.get("/api/documents", headers=first).json()[0]["redactions"] == 1


def test_private_pending_files_and_owner_actions_are_isolated(workspace):
    client, first, second, _ = workspace
    identifier = upload(client, first).json()["id"]
    client.app.state.processor.assessor = lambda text, key: Assessment(findings=[], needs_review=True, note="Ambiguous identity")
    client.app.state.processor.process_once()
    assert client.get("/api/documents/shared", headers=second).json() == []
    assert client.get("/api/documents", headers=second).json() == []
    assert client.post(f"/api/documents/{identifier}/retry", headers=second).status_code == 404
    assert client.delete(f"/api/documents/{identifier}", headers=second).status_code == 404
    assert client.get("/api/documents", headers=first).json()[0]["status"] == "pending"


def test_budget_exhaustion_never_calls_ai_or_publishes(workspace):
    client, first, second, calls = workspace
    client.app.state.settings.ai_daily_budget_usd = 0
    upload(client, first)
    client.app.state.processor.process_once()
    assert not calls
    assert client.get("/api/documents/shared", headers=second).json() == []
    assert "allowance" in client.get("/api/documents", headers=first).json()[0]["reason"]


def test_upload_validation_and_original_files_are_not_downloadable(workspace):
    client, first, second, _ = workspace
    assert upload(client, {}, filename="x.txt").status_code == 401
    assert upload(client, first, filename="x.exe").status_code == 415
    assert upload(client, first, text="").status_code == 400
    assert client.post("/api/documents?filename=x.txt", content=b"small", headers={**first, "Content-Length": "99999999"}).status_code == 413
    upload(client, first)
    with closing(connect_database(client.app.state.settings.data_dir)) as connection:
        name = connection.execute("SELECT original_file FROM revisions").fetchone()[0]
    assert client.get("/staging/" + name, headers=second).status_code == 404
