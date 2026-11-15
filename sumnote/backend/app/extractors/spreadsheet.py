import csv
from datetime import date, datetime, time
from io import BytesIO, StringIO
from pathlib import PurePosixPath

import openpyxl
import xlrd

from app.core.config import MAX_VISIBLE_SHEETS
from app.services.errors import ProcessingError
from app.services.text_normalization import ExtractedDocument, SheetContent, format_sheet_text, normalize_text


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return normalize_text(str(value))


def _rows_to_sheet(name: str, values) -> SheetContent:
    rows = [[_cell_text(value) for value in row] for row in values]
    while rows and not any(rows[-1]):
        rows.pop()
    if not rows:
        return SheetContent(name=name)

    header_row = rows[0]
    headers = [value or f"열 {index + 1}" for index, value in enumerate(header_row)]
    data_rows = [row for row in rows[1:] if any(row)]
    return SheetContent(name=name, headers=headers, rows=data_rows)


def extract_xlsx(data: bytes) -> ExtractedDocument:
    workbook = None
    try:
        workbook = openpyxl.load_workbook(BytesIO(data), data_only=True, read_only=True)
        visible_sheets = [sheet for sheet in workbook.worksheets if sheet.sheet_state == "visible"]
        if len(visible_sheets) > MAX_VISIBLE_SHEETS:
            raise ProcessingError(
                "SHEET_LIMIT_EXCEEDED",
                f"숨김 시트를 제외한 표시 시트가 10개를 초과했습니다. 현재 시트 수: {len(visible_sheets)}",
                422,
            )

        sheets = [_rows_to_sheet(sheet.title, sheet.iter_rows(values_only=True)) for sheet in visible_sheets]
        text = "\n\n".join(format_sheet_text(sheet) for sheet in sheets)
        return ExtractedDocument(text=normalize_text(text), sheets=sheets)
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError(
            "XLSX_READ_FAILED",
            "XLSX 파일을 읽지 못했습니다. 파일이 손상되지 않았는지 확인해 주세요.",
            422,
        ) from error
    finally:
        if workbook is not None:
            workbook.close()


def extract_xls(data: bytes) -> ExtractedDocument:
    workbook = None
    try:
        workbook = xlrd.open_workbook(file_contents=data, on_demand=True)
        visible_sheets = [sheet for sheet in workbook.sheets() if getattr(sheet, "visibility", 0) == 0]
        if len(visible_sheets) > MAX_VISIBLE_SHEETS:
            raise ProcessingError(
                "SHEET_LIMIT_EXCEEDED",
                f"숨김 시트를 제외한 표시 시트가 10개를 초과했습니다. 현재 시트 수: {len(visible_sheets)}",
                422,
            )

        sheets = []
        for source_sheet in visible_sheets:
            values = []
            for row_index in range(source_sheet.nrows):
                row = []
                for column_index in range(source_sheet.ncols):
                    cell = source_sheet.cell(row_index, column_index)
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        value = xlrd.xldate.xldate_as_datetime(cell.value, workbook.datemode)
                    elif cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                        value = ""
                    else:
                        value = cell.value
                    row.append(value)
                values.append(row)
            sheets.append(_rows_to_sheet(source_sheet.name, values))

        text = "\n\n".join(format_sheet_text(sheet) for sheet in sheets)
        return ExtractedDocument(text=normalize_text(text), sheets=sheets)
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError(
            "XLS_READ_FAILED",
            "XLS 파일을 읽지 못했습니다. 파일이 손상되지 않았는지 확인해 주세요.",
            422,
        ) from error
    finally:
        if workbook is not None:
            workbook.release_resources()


def _decode_csv(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ProcessingError(
        "CSV_ENCODING_UNSUPPORTED",
        "CSV 파일의 문자 인코딩을 읽을 수 없습니다. UTF-8 또는 CP949로 저장해 주세요.",
        422,
    )


def extract_csv(data: bytes, filename: str) -> ExtractedDocument:
    try:
        text = _decode_csv(data)
        if not text.strip():
            return ExtractedDocument(text="", sheets=[SheetContent(name=PurePosixPath(filename).stem or "CSV")])

        sample = text[:4096]
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(StringIO(text), dialect))
        sheet_name = PurePosixPath(filename.replace("\\", "/")).stem or "CSV"
        sheet = _rows_to_sheet(sheet_name, rows)
        return ExtractedDocument(text=format_sheet_text(sheet), sheets=[sheet])
    except ProcessingError:
        raise
    except Exception as error:
        raise ProcessingError(
            "CSV_READ_FAILED",
            "CSV 파일을 읽지 못했습니다. 구분자와 파일 인코딩을 확인해 주세요.",
            422,
        ) from error
