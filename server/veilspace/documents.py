from contextlib import closing
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sqlite3
import time
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from veilspace.auth import current_user
from veilspace.database import connect_database

router = APIRouter(prefix="/api/documents", tags=["documents"])
Member = Annotated[dict, Depends(current_user)]


def list_documents(settings, user_id: str, shared: bool = False) -> list[dict]:
    with closing(connect_database(settings.data_dir)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT d.id,d.owner_id,d.name,u.display_name AS uploader,r.number AS revision,r.status,"
            "r.reason,r.finding_count AS redactions,r.cached,r.created_at,"
            "EXISTS(SELECT 1 FROM revisions p WHERE p.document_id=d.id AND p.status='published') AS downloadable "
            "FROM documents d JOIN users u ON u.id=d.owner_id JOIN revisions r ON r.id=("
            "SELECT x.id FROM revisions x WHERE x.document_id=d.id "
            + ("AND x.status='published' " if shared else "")
            + "ORDER BY x.number DESC LIMIT 1) "
            + ("" if shared else "WHERE d.owner_id=? ") + "ORDER BY r.created_at DESC",
            () if shared else (user_id,),
        ).fetchall()
    result = [dict(row) for row in rows]
    for item in result:
        item["is_owner"] = item.pop("owner_id") == user_id
        if shared:
            item["name"] = "Document-" + item["id"][:8] + ".pdf"
    return result


@router.get("")
def own_files(request: Request, user: Member):
    return list_documents(request.app.state.settings, user["id"])


@router.get("/shared")
def shared_files(request: Request, user: Member):
    return list_documents(request.app.state.settings, user["id"], shared=True)


@router.get("/usage")
def usage(request: Request, user: Member):
    settings = request.app.state.settings
    today = datetime.now(timezone.utc).date().isoformat()
    with closing(connect_database(settings.data_dir)) as connection:
        row = connection.execute("SELECT requests,reserved_microdollars FROM ai_usage WHERE day=?", (today,)).fetchone()
    return {"requests": row[0] if row else 0, "reserved_usd": (row[1] if row else 0) / 1000000,
            "daily_limit_usd": settings.ai_daily_budget_usd,
            "ai_configured": bool(settings.openai_api_key.get_secret_value())}


@router.post("", status_code=202)
async def upload(request: Request, user: Member,
                 filename: str = Query(min_length=1, max_length=180),
                 source_id: str | None = Query(default=None, max_length=128)):
    settings = request.app.state.settings
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    extension = Path(name).suffix.lower()
    if extension not in (".txt", ".pdf", ".docx") or any(ord(char) < 32 for char in name):
        raise HTTPException(415, "Choose a DOCX, PDF, or TXT file")
    content_length = request.headers.get("content-length")
    if content_length and (not content_length.isdecimal() or int(content_length) > settings.max_upload_bytes):
        raise HTTPException(413, "Maximum file size is 10 MB")
    identifier = uuid.uuid4().hex
    staging_name = identifier + extension
    path = settings.data_dir / "staging" / staging_name
    size = 0
    digest = hashlib.sha256()
    try:
        with path.open("xb") as stream:
            async for chunk in request.stream():
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, "Maximum file size is 10 MB")
                digest.update(chunk)
                stream.write(chunk)
        if not size:
            raise HTTPException(400, "The file is empty")
        content_hash = digest.hexdigest()
        source_key = "watch:" + source_id if source_id else "manual:" + name.casefold()
        with closing(connect_database(settings.data_dir)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            document = connection.execute("SELECT id FROM documents WHERE owner_id=? AND source_key=?", (user["id"], source_key)).fetchone()
            if document:
                document_id = document[0]
                latest = connection.execute("SELECT number,content_hash,status FROM revisions WHERE document_id=? ORDER BY number DESC LIMIT 1", (document_id,)).fetchone()
                if latest and latest[1] == content_hash:
                    path.unlink(missing_ok=True)
                    return {"id": document_id, "revision": latest[0], "status": latest[2], "duplicate": True}
                number = latest[0] + 1 if latest else 1
                connection.execute("UPDATE documents SET name=? WHERE id=?", (name, document_id))
            else:
                duplicate = connection.execute("SELECT d.id,r.number,r.status FROM documents d JOIN revisions r ON r.document_id=d.id WHERE d.owner_id=? AND r.content_hash=? ORDER BY r.number DESC LIMIT 1", (user["id"], content_hash)).fetchone()
                if duplicate:
                    connection.execute("UPDATE documents SET source_key=?,name=? WHERE id=?", (source_key, name, duplicate[0]))
                    path.unlink(missing_ok=True)
                    return {"id": duplicate[0], "revision": duplicate[1], "status": duplicate[2], "duplicate": True}
                document_id, number = uuid.uuid4().hex, 1
                connection.execute("INSERT INTO documents VALUES (?, ?, ?, ?, ?)", (document_id, user["id"], name, source_key, int(time.time())))
            connection.execute("INSERT INTO revisions(id,document_id,number,content_hash,size,status,original_file,created_at) VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
                               (identifier, document_id, number, content_hash, size, staging_name, int(time.time())))
        return {"id": document_id, "revision": number, "status": "queued", "duplicate": False}
    except Exception:
        path.unlink(missing_ok=True)
        raise


@router.post("/{document_id}/retry", status_code=202)
def retry(document_id: str, request: Request, user: Member):
    with closing(connect_database(request.app.state.settings.data_dir)) as connection, connection:
        row = connection.execute("SELECT r.id,r.status,r.original_file FROM revisions r JOIN documents d ON d.id=r.document_id WHERE d.id=? AND d.owner_id=? ORDER BY r.number DESC LIMIT 1", (document_id, user["id"])).fetchone()
        if not row:
            raise HTTPException(404, "File not found")
        if row[1] != "pending" or not row[2]:
            raise HTTPException(409, "This file cannot be retried. Upload the original again if needed.")
        connection.execute("UPDATE revisions SET status='queued',reason=NULL WHERE id=?", (row[0],))
    return {"status": "queued"}


@router.get("/{document_id}/download")
def download(document_id: str, request: Request, user: Member):
    settings = request.app.state.settings
    with closing(connect_database(settings.data_dir)) as connection:
        row = connection.execute("SELECT sanitized_file FROM revisions WHERE document_id=? AND status='published' ORDER BY number DESC LIMIT 1", (document_id,)).fetchone()
    if not row or not row[0]:
        raise HTTPException(404, "No published version is available")
    path = settings.data_dir / "published" / row[0]
    if not path.is_file() or not path.resolve().is_relative_to((settings.data_dir / "published").resolve()):
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type="application/pdf", filename="Document-" + document_id[:8] + ".pdf",
                        headers={"Cache-Control": "private, no-store"})


@router.delete("/{document_id}", status_code=204)
def delete(document_id: str, request: Request, user: Member):
    settings = request.app.state.settings
    with closing(connect_database(settings.data_dir)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        owner = connection.execute("SELECT owner_id FROM documents WHERE id=?", (document_id,)).fetchone()
        if not owner or owner[0] != user["id"]:
            raise HTTPException(404, "File not found")
        rows = connection.execute("SELECT original_file,sanitized_file,status FROM revisions WHERE document_id=?", (document_id,)).fetchall()
        if any(row[2] == "processing" for row in rows):
            raise HTTPException(409, "Wait for processing to finish before deleting")
        connection.execute("DELETE FROM documents WHERE id=?", (document_id,))
    for original, sanitized, _ in rows:
        for folder, filename in (("staging", original), ("published", sanitized)):
            if filename:
                try:
                    (settings.data_dir / folder / filename).unlink(missing_ok=True)
                except OSError:
                    pass
