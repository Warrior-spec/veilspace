import zipfile

import pytest

from veilspace.extraction import ExtractionError, extract_text


def test_text_encoding_and_length_limits(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("\ufeffPrivate notes", encoding="utf-8")
    assert extract_text(path) == "Private notes"
    with pytest.raises(ExtractionError, match="too much text"):
        extract_text(path, max_characters=5)


def test_docx_includes_body_tables_and_headers(tmp_path):
    path = tmp_path / "sample.docx"
    namespace = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document {namespace}><w:body>'
                         '<w:p><w:r><w:t>Body text</w:t></w:r></w:p>'
                         '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Table text</w:t></w:r></w:p>'
                         '</w:tc></w:tr></w:tbl></w:body></w:document>')
        archive.writestr("word/header1.xml", f'<w:hdr {namespace}>'
                         '<w:p><w:r><w:t>Header text</w:t></w:r></w:p></w:hdr>')
    text = extract_text(path)
    assert all(value in text for value in ("Body text", "Table text", "Header text"))


def test_pdf_text_extraction(tmp_path):
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    content = b'BT /F1 12 Tf 30 200 Td (Private notes) Tj ET'
    objects.append(b'<< /Length ' + str(len(content)).encode() + b' >>\nstream\n' + content + b'\nendstream')
    data = b'%PDF-1.4\n'
    offsets = [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{number} 0 obj\n'.encode() + value + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 6\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    data += f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()
    path = tmp_path / "sample.pdf"
    path.write_bytes(data)
    assert "Private notes" in extract_text(path)


@pytest.mark.parametrize("name,content", [("empty.txt", b""), ("binary.txt", b"a\x00b"),
                                         ("old.doc", b"legacy"), ("broken.pdf", b"bad")])
def test_unreadable_files_need_review(tmp_path, name, content):
    path = tmp_path / name
    path.write_bytes(content)
    with pytest.raises(ExtractionError):
        extract_text(path)
