from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from threading import Event, Thread
import time
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from veilspace.assessment import Assessment, MODEL, assess, reservation_microdollars, rule_findings
from veilspace.database import connect_database
from veilspace.extraction import extract_text


def span_pattern(value: str) -> str:
    return (r"(?<!\w)" if value[0].isalnum() else "") + re.escape(value) + (r"(?!\w)" if value[-1].isalnum() else "")


def write_pdf(text: str, path: Path) -> None:
    font = "Helvetica"
    for candidate in (Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if candidate.exists():
            if "VeilSpaceFont" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("VeilSpaceFont", str(candidate)))
            font = "VeilSpaceFont"
            break
    style = ParagraphStyle("body", fontName=font, fontSize=10, leading=16, spaceAfter=6)
    story = []
    for line in text.splitlines():
        story.append(Paragraph(escape(line), style) if line.strip() else Spacer(1, 8))
    SimpleDocTemplate(str(path), title="Shared document", author="VeilSpace",
                      leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42).build(story)


class Processor:
    def __init__(self, settings, assessor=assess):
        self.settings = settings
        self.assessor = assessor
        self.stop = Event()
        self.thread = Thread(target=self.run, name="document-worker", daemon=True)

    def start(self):
        with closing(connect_database(self.settings.data_dir)) as connection, connection:
            connection.execute("UPDATE revisions SET status='queued' WHERE status='processing'")
        self.thread.start()

    def run(self):
        while not self.stop.is_set():
            try:
                if not self.process_once():
                    self.stop.wait(0.7)
            except Exception:
                self.stop.wait(1)

    def process_once(self) -> bool:
        with closing(connect_database(self.settings.data_dir)) as connection, connection:
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM revisions WHERE status='queued' ORDER BY created_at, number LIMIT 1").fetchone()
            if row is None:
                return False
            revision = dict(row)
            connection.execute("UPDATE revisions SET status='processing',reason=NULL WHERE id=?", (revision["id"],))
        try:
            self.process(revision)
        except Exception as error:
            reason = str(error) if isinstance(error, ValueError) else "Processing failed. Please review or retry."
            with closing(connect_database(self.settings.data_dir)) as connection, connection:
                connection.execute("UPDATE revisions SET status='pending',reason=? WHERE id=?", (reason[:300], revision["id"]))
        return True

    def process(self, revision: dict):
        original = self.settings.data_dir / "staging" / revision["original_file"]
        text = extract_text(original, max_characters=20000)
        digest = hashlib.sha256((MODEL + "|policy-1|" + text).encode()).hexdigest()
        with closing(connect_database(self.settings.data_dir)) as connection:
            cached = connection.execute("SELECT result_json FROM assessments WHERE content_hash=?", (digest,)).fetchone()
        if cached:
            result = Assessment.model_validate_json(cached[0])
        else:
            key = self.settings.openai_api_key.get_secret_value()
            if not key:
                raise ValueError("AI service is not configured. File remains private.")
            today = datetime.now(timezone.utc).date().isoformat()
            reserve = reservation_microdollars(text)
            with closing(connect_database(self.settings.data_dir)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("INSERT OR IGNORE INTO ai_usage(day) VALUES (?)", (today,))
                used, calls = connection.execute("SELECT reserved_microdollars,requests FROM ai_usage WHERE day=?", (today,)).fetchone()
                if used + reserve > int(self.settings.ai_daily_budget_usd * 1000000) or calls >= 100:
                    raise ValueError("Daily AI allowance reached. File remains private.")
                connection.execute("UPDATE ai_usage SET reserved_microdollars=reserved_microdollars+?,requests=requests+1 WHERE day=?", (reserve, today))
            result = self.assessor(text, key)
            with closing(connect_database(self.settings.data_dir)) as connection, connection:
                connection.execute("INSERT OR REPLACE INTO assessments VALUES (?, ?, ?)", (digest, result.model_dump_json(), int(time.time())))
        if result.needs_review:
            raise ValueError("Review required: " + result.note[:240])
        findings = result.findings + rule_findings(text)
        replacements = {}
        with closing(connect_database(self.settings.data_dir)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            for finding in sorted(findings, key=lambda item: -len(item.text)):
                pattern = span_pattern(finding.text)
                if not re.search(pattern, text, re.IGNORECASE):
                    raise ValueError("An AI finding could not be matched. Review required.")
                if pattern in replacements:
                    continue
                if finding.kind == "person":
                    identity = " ".join(finding.text.split()).casefold()
                    saved = connection.execute("SELECT alias FROM identities WHERE kind='person' AND identity=?", (identity,)).fetchone()
                    alias = saved[0] if saved else f"Person-{connection.execute('SELECT count(*) FROM identities').fetchone()[0] + 1:03d}"
                    if not saved:
                        connection.execute("INSERT INTO identities VALUES ('person', ?, ?)", (identity, alias))
                else:
                    alias = "[" + finding.kind.upper() + " REMOVED]"
                replacements[pattern] = alias
        patterns = list(replacements)
        if patterns:
            combined = re.compile("|".join(f"(?P<e{index}>{pattern})" for index, pattern in enumerate(patterns)), re.IGNORECASE)
            clean, count = combined.subn(lambda match: replacements[patterns[int(match.lastgroup[1:])]], text)
        else:
            clean, count = text, 0
        filename = revision["id"] + ".pdf"
        output = self.settings.data_dir / "published" / filename
        try:
            write_pdf(clean, output)
            exported = "\n".join(page.extract_text() or "" for page in PdfReader(output).pages)
            if any(re.search(pattern, exported, re.IGNORECASE) for pattern in patterns):
                raise ValueError("Output verification failed. File remains private.")
            with closing(connect_database(self.settings.data_dir)) as connection, connection:
                connection.execute("UPDATE revisions SET status='published',sanitized_file=?,finding_count=?,cached=?,reason=NULL,original_file=NULL WHERE id=?",
                                   (filename, count, int(bool(cached)), revision["id"]))
        except Exception:
            output.unlink(missing_ok=True)
            raise
        try:
            original.unlink(missing_ok=True)
        except OSError:
            pass
