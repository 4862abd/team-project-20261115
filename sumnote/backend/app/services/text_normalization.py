import re
import unicodedata
from dataclasses import dataclass, field


@dataclass
class SheetContent:
    name: str
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)

    @property
    def data_row_count(self) -> int:
        return len(self.rows)


@dataclass
class ExtractedDocument:
    text: str
    page_count: int | None = None
    sheets: list[SheetContent] = field(default_factory=list)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    normalized = normalized.replace("\x00", "")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+\n", "\n", normalized)
    return normalized.strip()


def format_sheet_text(sheet: SheetContent) -> str:
    lines = [f'[시트: "{sheet.name}"]']
    if sheet.headers:
        lines.append("헤더: " + " | ".join(sheet.headers))
    lines.append(f"데이터 행 수: {sheet.data_row_count}")
    for row_number, row in enumerate(sheet.rows, start=2 if sheet.headers else 1):
        values = []
        for index, value in enumerate(row):
            column_name = sheet.headers[index] if index < len(sheet.headers) else f"열 {index + 1}"
            values.append(f"{column_name}={value}")
        lines.append(f'[시트 "{sheet.name}" 행 {row_number}] ' + " | ".join(values))
    return "\n".join(lines)
