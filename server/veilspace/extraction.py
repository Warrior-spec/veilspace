from pathlib import Path
import zipfile
from xml.etree import ElementTree

from pypdf import PdfReader


class ExtractionError(ValueError):
    pass


def extract_text(path: Path, max_characters: int = 100000, max_pages: int = 30) -> str:
    extension = path.suffix.lower()
    try:
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ExtractionError("File exceeds the 10 MB limit")
        if extension == ".txt":
            text = path.read_text(encoding="utf-8-sig")
            if "\x00" in text:
                raise ExtractionError("Text file contains binary content")
        elif extension == ".docx":
            text = extract_docx(path)
        elif extension == ".pdf":
            reader = PdfReader(path, strict=False)
            if reader.is_encrypted:
                raise ExtractionError("Password-protected PDFs need review")
            if len(reader.pages) > max_pages:
                raise ExtractionError(f"PDF exceeds the {max_pages} page limit")
            pages = []
            length = 0
            for page in reader.pages:
                content = page.get_contents()
                if content and len(content.get_data()) > 5 * 1024 * 1024:
                    raise ExtractionError("PDF page is too complex to process")
                value = page.extract_text() or ""
                if not value.strip():
                    raise ExtractionError("A PDF page has no readable text and needs review")
                length += len(value)
                if length > max_characters:
                    raise ExtractionError("Document contains too much text")
                pages.append(value)
            text = "\n\n".join(pages)
        else:
            raise ExtractionError("Supported formats are DOCX, PDF, and TXT")
    except ExtractionError:
        raise
    except Exception as error:
        raise ExtractionError("Document could not be read") from error
    if not text.strip():
        raise ExtractionError("Document has no readable text")
    if len(text) > max_characters:
        raise ExtractionError("Document contains too much text")
    return text.strip()


def extract_docx(path: Path) -> str:
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 2000 or sum(entry.file_size for entry in entries) > 20 * 1024 * 1024:
            raise ExtractionError("Word document is too large to unpack")
        names = archive.namelist()
        if "word/document.xml" not in names:
            raise ExtractionError("Invalid Word document")
        selected = ["word/document.xml"] + sorted(
            name for name in names if name.startswith(("word/header", "word/footer")) and name.endswith(".xml")
        )
        paragraphs = []
        for name in selected:
            content = archive.read(name)
            if b"<!doctype" in content.lower() or b"<!entity" in content.lower():
                raise ExtractionError("Unsupported Word XML content")
            root = ElementTree.fromstring(content)
            for paragraph in root.iter(namespace + "p"):
                paragraphs.append("".join(node.text or "" for node in paragraph.iter(namespace + "t")))
    return "\n".join(paragraphs)
