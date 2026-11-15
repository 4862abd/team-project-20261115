from io import BytesIO

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.services.errors import ProcessingError
from app.services.text_normalization import ExtractedDocument, normalize_text


def extract_docx(data: bytes) -> ExtractedDocument:
    try:
        document = Document(BytesIO(data))
        sections = []
        paragraph_number = 0
        table_number = 0

        for child in document.element.body.iterchildren():
            if isinstance(child, CT_P):
                paragraph_number += 1
                text = normalize_text(Paragraph(child, document).text)
                if text:
                    sections.append(f"[DOCX 문단 {paragraph_number}] {text}")
            elif isinstance(child, CT_Tbl):
                table_number += 1
                table = Table(child, document)
                table_lines = [f"[DOCX 표 {table_number}]"]
                for row_number, row in enumerate(table.rows, start=1):
                    values = [normalize_text(cell.text) for cell in row.cells]
                    if any(values):
                        table_lines.append(f"[DOCX 표 {table_number} 행 {row_number}] " + " | ".join(values))
                if len(table_lines) > 1:
                    sections.extend(table_lines)

        return ExtractedDocument(text="\n".join(sections))
    except Exception as error:
        raise ProcessingError(
            "DOCX_READ_FAILED",
            "DOCX 파일을 읽지 못했습니다. 파일이 손상되지 않았는지 확인해 주세요.",
            422,
        ) from error
